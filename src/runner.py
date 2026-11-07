from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass, field
from pathlib import Path

from src.checker import BaseChecker, CheckerMode, OutputChecker
from src.config import ExecutionLimits
from src.engine import BaseEngine, get_engine
from src.models import ExecutionStatus

MAX_CASE_CACHE_BYTES = 2 * 1024 * 1024  # 2MB in-memory cache boundary


@dataclass(frozen=True, slots=True)
class TestCase:
    """Test case definition supporting file paths or in-memory strings."""

    name: str
    input_path: Path | None = None
    expected_output_path: Path | None = None
    input_data: str | None = None
    expected_output: str | None = None
    _cached_input: str | None = field(default=None, init=False, repr=False)
    _cached_expected: str | None = field(default=None, init=False, repr=False)
    _cached_input_mtime: int | None = field(default=None, init=False, repr=False)
    _cached_expected_mtime: int | None = field(default=None, init=False, repr=False)

    def get_input(self) -> str:
        """Retrieves input data from memory or reads from file."""
        if self.input_data is not None:
            return self.input_data
        if self.input_path is not None and self.input_path.is_file():
            try:
                st = self.input_path.stat()
                if (
                    self._cached_input is not None
                    and self._cached_input_mtime == st.st_mtime_ns
                ):
                    return self._cached_input
                if st.st_size <= MAX_CASE_CACHE_BYTES:
                    with open(
                        self.input_path, "r", encoding="utf-8", errors="replace"
                    ) as f:
                        content = f.read()
                    object.__setattr__(self, "_cached_input", content)
                    object.__setattr__(self, "_cached_input_mtime", st.st_mtime_ns)
                    return content
                with open(
                    self.input_path, "r", encoding="utf-8", errors="replace"
                ) as f:
                    return f.read()
            except OSError:
                return ""
        return ""

    def get_expected_output(self) -> str:
        """Retrieves expected output from memory or reads from file."""
        if self.expected_output is not None:
            return self.expected_output
        if (
            self.expected_output_path is not None
            and self.expected_output_path.is_file()
        ):
            try:
                st = self.expected_output_path.stat()
                if (
                    self._cached_expected is not None
                    and self._cached_expected_mtime == st.st_mtime_ns
                ):
                    return self._cached_expected
                if st.st_size <= MAX_CASE_CACHE_BYTES:
                    with open(
                        self.expected_output_path,
                        "r",
                        encoding="utf-8",
                        errors="replace",
                    ) as f:
                        content = f.read()
                    object.__setattr__(self, "_cached_expected", content)
                    object.__setattr__(self, "_cached_expected_mtime", st.st_mtime_ns)
                    return content
                with open(
                    self.expected_output_path, "r", encoding="utf-8", errors="replace"
                ) as f:
                    return f.read()
            except OSError:
                return ""
        return ""


@dataclass(slots=True)
class TestResult:
    """Result and telemetry of an individual test case execution."""

    case_name: str
    verdict: str
    cpu_time_ms: float
    peak_memory_mb: float
    diff: str | None = None
    is_accepted: bool = False


@dataclass(slots=True)
class BatchResult:
    """Aggregated outcome across a batch test suite."""

    passed: int
    total: int
    overall_verdict: str
    total_cpu_time_ms: float
    max_peak_memory_mb: float
    results: list[TestResult] = field(default_factory=list)


class BatchRunner:
    """Test case discoverer and batch evaluation executor."""

    def __init__(self, engine: BaseEngine | None = None) -> None:
        self.engine = engine if engine is not None else get_engine()

    def discover_test_cases(self, directory: Path) -> list[TestCase]:
        """Finds all *.in files and pairs them with *.out or *.ans files."""
        if not directory.is_dir():
            return []

        resolved_dir = directory.resolve()
        cases: list[TestCase] = []
        for in_file in sorted(directory.glob("*.in")):
            try:
                resolved_in = in_file.resolve()
                if not resolved_in.is_relative_to(resolved_dir):
                    continue
            except (ValueError, RuntimeError):
                continue

            base_name = in_file.stem
            out_file = directory / f"{base_name}.out"
            if not out_file.exists():
                out_file = directory / f"{base_name}.ans"

            if out_file.exists():
                try:
                    resolved_out = out_file.resolve()
                    if not resolved_out.is_relative_to(resolved_dir):
                        continue
                except (ValueError, RuntimeError):
                    continue

                cases.append(
                    TestCase(
                        name=in_file.name,
                        input_path=in_file,
                        expected_output_path=out_file,
                    )
                )
        return cases

    def run_case(
        self,
        source_path: Path,
        case: TestCase,
        limits: ExecutionLimits,
        checker: BaseChecker,
    ) -> TestResult:
        """Executes a single testcase and compares output against expected."""
        input_text = case.get_input()
        expected_output = case.get_expected_output()

        res = self.engine.execute(source_path, limits, input_data=input_text)

        if res.status == ExecutionStatus.OK:
            check_res = checker.check(res.stdout, expected_output)
            if check_res.is_correct:
                return TestResult(
                    case_name=case.name,
                    verdict="ACCEPTED",
                    cpu_time_ms=res.cpu_time_ms,
                    peak_memory_mb=res.peak_memory_mb,
                    is_accepted=True,
                )
            return TestResult(
                case_name=case.name,
                verdict="WRONG_ANSWER",
                cpu_time_ms=res.cpu_time_ms,
                peak_memory_mb=res.peak_memory_mb,
                diff=check_res.diff,
                is_accepted=False,
            )

        return TestResult(
            case_name=case.name,
            verdict=res.status.value,
            cpu_time_ms=res.cpu_time_ms,
            peak_memory_mb=res.peak_memory_mb,
            diff=res.error_message,
            is_accepted=False,
        )

    def evaluate_cases(
        self,
        source_path: Path,
        cases: list[TestCase],
        limits: ExecutionLimits,
        mode: CheckerMode = CheckerMode.TOKEN,
        checker: BaseChecker | None = None,
        workers: int = 1,
    ) -> BatchResult:
        """Evaluates a list of testcases sequentially or concurrently."""
        active_checker: BaseChecker = (
            checker if checker is not None else OutputChecker(mode=mode)
        )

        total = len(cases)
        if total == 0:
            return BatchResult(
                passed=0,
                total=0,
                overall_verdict="NO_TESTS",
                total_cpu_time_ms=0.0,
                max_peak_memory_mb=0.0,
                results=[],
            )

        if workers <= 1 or total <= 1:
            results: list[TestResult] = []
            passed = 0
            total_cpu = 0.0
            max_ram = 0.0
            first_failure: str | None = None

            for case in cases:
                res = self.run_case(source_path, case, limits, active_checker)
                results.append(res)
                total_cpu += res.cpu_time_ms
                max_ram = max(max_ram, res.peak_memory_mb)

                if res.is_accepted:
                    passed += 1
                elif first_failure is None:
                    first_failure = res.verdict

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

        # Multi-worker parallel execution
        effective_workers = max(1, min(workers, total, 32))
        indexed_results: list[tuple[int, TestResult]] = []

        def _worker_task(item: tuple[int, TestCase]) -> tuple[int, TestResult]:
            idx, c = item
            return idx, self.run_case(source_path, c, limits, active_checker)

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=effective_workers
        ) as executor:
            indexed_results = list(executor.map(_worker_task, enumerate(cases)))

        indexed_results.sort(key=lambda x: x[0])
        ordered_results = [res for _, res in indexed_results]

        passed = sum(1 for r in ordered_results if r.is_accepted)
        total_cpu = sum(r.cpu_time_ms for r in ordered_results)
        max_ram = max((r.peak_memory_mb for r in ordered_results), default=0.0)
        first_failure = next(
            (r.verdict for r in ordered_results if not r.is_accepted), None
        )
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
            results=ordered_results,
        )

    def run_batch(
        self,
        source_path: Path,
        cases_dir: Path,
        limits: ExecutionLimits,
        mode: CheckerMode = CheckerMode.TOKEN,
        checker: BaseChecker | None = None,
        workers: int = 1,
    ) -> BatchResult:
        """Discovers and runs all testcases in cases_dir, aggregating verdicts."""
        cases = self.discover_test_cases(cases_dir)
        return self.evaluate_cases(
            source_path=source_path,
            cases=cases,
            limits=limits,
            mode=mode,
            checker=checker,
            workers=workers,
        )
