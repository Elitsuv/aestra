from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from src.checker import OutputChecker
from src.config import Config
from src.engine import BaseEngine, get_engine
from src.models import ExecutionResult, ExecutionStatus
from src.runner import BatchResult, BatchRunner, TestCase, TestResult


class Judge:
    """High-level programmatic interface to evaluate binaries and test suites."""

    def __init__(
        self,
        config: Config | None = None,
        config_path: str | Path | None = None,
        engine: BaseEngine | None = None,
    ) -> None:
        if config_path is not None:
            self.config = Config.from_toml(config_path)
        elif config is not None:
            self.config = config
        else:
            self.config = Config()

        self.engine = engine if engine is not None else get_engine()
        self.runner = BatchRunner(engine=self.engine)

    def run_single(
        self,
        target_binary: str | Path,
        input_data: str = "",
        args: list[str] | None = None,
    ) -> ExecutionResult:
        """Executes a single run of the target binary under configured limits."""
        path = Path(target_binary)
        limits = self.config.to_limits()
        return self.engine.execute(path, limits, args=args, input_data=input_data)

    def run(
        self,
        target_binary: str | Path,
        cases_dir: str | Path | None = None,
        test_cases: list[TestCase] | None = None,
    ) -> BatchResult:
        """Evaluates target_binary across a test suite (directory or TestCase list)."""
        path = Path(target_binary)
        limits = self.config.to_limits()

        if cases_dir is not None:
            dir_path = Path(cases_dir)
            return self.runner.run_batch(
                path, dir_path, limits, mode=self.config.checker_mode
            )

        if test_cases is not None:
            checker = OutputChecker(mode=self.config.checker_mode)
            results: list[TestResult] = []
            passed = 0
            total_cpu = 0.0
            max_ram = 0.0
            first_failure: str | None = None

            for case in test_cases:
                res = self.runner.run_case(path, case, limits, checker)
                results.append(res)
                total_cpu += res.cpu_time_ms
                max_ram = max(max_ram, res.peak_memory_mb)

                if res.is_accepted:
                    passed += 1
                elif first_failure is None:
                    first_failure = res.verdict

            total = len(test_cases)
            overall = (
                "ACCEPTED"
                if (total > 0 and passed == total)
                else (first_failure or "NO_TESTS")
            )

            return BatchResult(
                passed=passed,
                total=total,
                overall_verdict=overall,
                total_cpu_time_ms=total_cpu,
                max_peak_memory_mb=max_ram,
                results=results,
            )

        raise ValueError("Either cases_dir or test_cases must be provided.")


@dataclass
class FuzzResult:
    found_bug: bool
    iterations_run: int
    failing_input: str | None = None
    execution_result: ExecutionResult | None = None
    oracle_output: str | None = None
    error_message: str | None = None


def _default_input_generator(iteration: int) -> str:
    """Generates varied randomized test inputs (numbers, lists, strings)."""
    rng = random.Random(iteration ^ 0x5DEECE66D)
    variant = iteration % 3
    if variant == 0:
        n = rng.randint(1, 20)
        nums = [str(rng.randint(-1000, 1000)) for _ in range(n)]
        return f"{n}\n" + " ".join(nums) + "\n"
    elif variant == 1:
        n = rng.randint(1, 10)
        return "\n".join(str(rng.randint(0, 100)) for _ in range(n)) + "\n"
    else:
        letters = "abcdefghijklmnopqrstuvwxyz"
        s = "".join(rng.choice(letters) for _ in range(rng.randint(5, 50)))
        return s + "\n"


class Fuzzer:
    """Stress-tests a binary using automated or custom input generation."""

    def __init__(
        self,
        target_binary: str | Path,
        oracle: str | Path | Callable[[str], str] | None = None,
        generator: Callable[[int], str] | None = None,
        config: Config | None = None,
        timeout_ms: int | None = None,
        memory_limit_mb: int | None = None,
        engine: BaseEngine | None = None,
    ) -> None:
        self.target_binary = Path(target_binary)
        self.oracle = oracle
        self.generator = (
            generator if generator is not None else _default_input_generator
        )

        base_config = config if config is not None else Config()
        t_ms = timeout_ms if timeout_ms is not None else base_config.time_limit_ms
        m_mb = (
            memory_limit_mb
            if memory_limit_mb is not None
            else base_config.memory_limit_mb
        )

        self.config = Config(
            time_limit_ms=t_ms,
            memory_limit_mb=m_mb,
            checker_mode=base_config.checker_mode,
            output_limit_bytes=base_config.output_limit_bytes,
        )
        self.engine = engine if engine is not None else get_engine()
        self.checker = OutputChecker(mode=self.config.checker_mode)

    def _run_oracle(self, input_data: str) -> tuple[str, bool, str | None]:
        if callable(self.oracle):
            try:
                out = self.oracle(input_data)
                return str(out), True, None
            except Exception as e:  # noqa: BLE001
                return (
                    "",
                    False,
                    f"Oracle callable raised {type(e).__name__}: {e}",
                )

        if isinstance(self.oracle, (str, Path)):
            oracle_path = Path(self.oracle)
            limits = self.config.to_limits()
            res = self.engine.execute(oracle_path, limits, input_data=input_data)
            if res.status != ExecutionStatus.OK:
                err_detail = res.error_message or res.stderr or ""
                return (
                    "",
                    False,
                    f"Oracle binary failed with status {res.status.value}: {err_detail}".strip(),
                )
            return res.stdout, True, None

        return "", True, None

    def run(self, iterations: int = 100) -> FuzzResult:
        """Runs fuzz iterations until a bug is found or all iterations pass."""
        limits = self.config.to_limits()

        for i in range(iterations):
            test_input = self.generator(i)
            target_res = self.engine.execute(
                self.target_binary, limits, input_data=test_input
            )

            # Check 1: Target execution crash, timeout, or OOM
            if target_res.status != ExecutionStatus.OK:
                return FuzzResult(
                    found_bug=True,
                    iterations_run=i + 1,
                    failing_input=test_input,
                    execution_result=target_res,
                    error_message=f"Target failed with status {target_res.status.value}: {target_res.error_message or ''}".strip(),
                )

            # Check 2: Oracle comparison if oracle provided
            if self.oracle is not None:
                oracle_out, oracle_ok, oracle_err = self._run_oracle(test_input)
                if not oracle_ok:
                    return FuzzResult(
                        found_bug=False,
                        iterations_run=i + 1,
                        failing_input=test_input,
                        error_message=f"Oracle evaluation failure: {oracle_err}",
                    )

                check_res = self.checker.check(target_res.stdout, oracle_out)
                if not check_res.is_correct:
                    return FuzzResult(
                        found_bug=True,
                        iterations_run=i + 1,
                        failing_input=test_input,
                        execution_result=target_res,
                        oracle_output=oracle_out,
                        error_message=f"Wrong Answer: Output mismatch.\nDiff:\n{check_res.diff or ''}".strip(),
                    )

        return FuzzResult(
            found_bug=False,
            iterations_run=iterations,
        )


class Minimizer:
    """Reduces large failing test cases to minimal reproducible inputs using delta debugging."""

    def __init__(
        self,
        target_binary: str | Path,
        oracle: str | Path | Callable[[str], str] | None = None,
        config: Config | None = None,
        engine: BaseEngine | None = None,
    ) -> None:
        self.target_binary = Path(target_binary)
        self.oracle = oracle
        self.config = config if config is not None else Config()
        self.engine = engine if engine is not None else get_engine()
        self.checker = OutputChecker(mode=self.config.checker_mode)

    def _is_failing(self, input_data: str) -> bool:
        limits = self.config.to_limits()
        res = self.engine.execute(self.target_binary, limits, input_data=input_data)
        if res.status != ExecutionStatus.OK:
            return True

        if self.oracle is not None:
            oracle_out: str = ""
            if callable(self.oracle):
                try:
                    oracle_out = str(self.oracle(input_data))
                except Exception:  # noqa: BLE001
                    return False
            else:
                oracle_res = self.engine.execute(
                    Path(self.oracle), limits, input_data=input_data
                )
                if oracle_res.status != ExecutionStatus.OK:
                    return False
                oracle_out = oracle_res.stdout

            check_res = self.checker.check(res.stdout, oracle_out)
            if not check_res.is_correct:
                return True

        return False

    def _ddmin_units(
        self,
        units: list[str],
        joiner: str,
        steps_remaining: list[int],
    ) -> list[str]:
        """Hierarchical delta debugging on discrete units (lines or tokens)."""
        if len(units) <= 1 or steps_remaining[0] <= 0:
            return units

        granularity = 2
        while len(units) >= 2 and granularity <= len(units) and steps_remaining[0] > 0:
            chunk_size = max(1, len(units) // granularity)
            chunks: list[list[str]] = []
            for i in range(0, len(units), chunk_size):
                chunks.append(units[i : i + chunk_size])

            reduced = False

            # Phase A: Test complements (drop each chunk)
            for i in range(len(chunks)):
                if steps_remaining[0] <= 0:
                    break
                steps_remaining[0] -= 1

                complement: list[str] = []
                for j, ch in enumerate(chunks):
                    if j != i:
                        complement.extend(ch)

                candidate_str = joiner.join(complement)
                if candidate_str and self._is_failing(candidate_str):
                    units = complement
                    granularity = max(granularity - 1, 2)
                    reduced = True
                    break

            if reduced:
                continue

            # Phase B: Test subsets (keep only chunk i if granularity > 2)
            if granularity > 2:
                for chunk in chunks:
                    if steps_remaining[0] <= 0:
                        break
                    steps_remaining[0] -= 1

                    candidate_str = joiner.join(chunk)
                    if candidate_str and self._is_failing(candidate_str):
                        units = chunk
                        granularity = 2
                        reduced = True
                        break

            if reduced:
                continue

            if granularity == len(units):
                break
            granularity = min(granularity * 2, len(units))

        return units

    def minimize(self, failing_input: str, max_steps: int = 200) -> str:
        """Minimizes failing_input while preserving failure using hierarchical delta debugging."""
        if not self._is_failing(failing_input):
            return failing_input

        steps_remaining = [max_steps]
        current = failing_input

        # Phase 1: Line-level hierarchical delta debugging
        lines = current.splitlines(keepends=True)
        if len(lines) > 1 and steps_remaining[0] > 0:
            lines = self._ddmin_units(lines, "", steps_remaining)
            current = "".join(lines)

        # Phase 2: Token-level hierarchical delta debugging
        tokens = current.split()
        if len(tokens) > 1 and steps_remaining[0] > 0:
            tokens = self._ddmin_units(tokens, " ", steps_remaining)
            current = " ".join(tokens)

        return current
