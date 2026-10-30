from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src.checker import BaseChecker, CheckerMode, OutputChecker
from src.config import ExecutionLimits
from src.engine import BaseEngine, get_engine
from src.models import ExecutionStatus


@dataclass(frozen=True, slots=True)
class TestCase:
    """Test case definition supporting file paths or in-memory strings."""

    name: str
    input_path: Path | None = None
    expected_output_path: Path | None = None
    input_data: str | None = None
    expected_output: str | None = None

    def get_input(self) -> str:
        """Retrieves input data from memory or reads from file."""
        if self.input_data is not None:
            return self.input_data
        if self.input_path is not None and self.input_path.is_file():
            with open(self.input_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        return ""

    def get_expected_output(self) -> str:
        """Retrieves expected output from memory or reads from file."""
        if self.expected_output is not None:
            return self.expected_output
        if (
            self.expected_output_path is not None
            and self.expected_output_path.is_file()
        ):
            with open(
                self.expected_output_path, "r", encoding="utf-8", errors="replace"
            ) as f:
                return f.read()
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

    def run_batch(
        self,
        source_path: Path,
        cases_dir: Path,
        limits: ExecutionLimits,
        mode: CheckerMode = CheckerMode.TOKEN,
        checker: BaseChecker | None = None,
    ) -> BatchResult:
        """Discovers and runs all testcases in cases_dir, aggregating verdicts."""
        cases = self.discover_test_cases(cases_dir)
        active_checker: BaseChecker = (
            checker if checker is not None else OutputChecker(mode=mode)
        )

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

        total = len(cases)
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
