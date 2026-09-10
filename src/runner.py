from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src.checker import CheckerMode, OutputChecker
from src.config import ExecutionLimits
from src.engine import BaseEngine, get_engine
from src.models import ExecutionStatus


@dataclass(frozen=True)
class TestCase:
    name: str
    input_path: Path
    expected_output_path: Path


@dataclass
class TestResult:
    case_name: str
    verdict: str
    cpu_time_ms: float
    peak_memory_mb: float
    diff: str | None = None
    is_accepted: bool = False


@dataclass
class BatchResult:
    passed: int
    total: int
    overall_verdict: str
    total_cpu_time_ms: float
    max_peak_memory_mb: float
    results: list[TestResult] = field(default_factory=list)


class BatchRunner:
    def __init__(self, engine: BaseEngine | None = None) -> None:
        self.engine = engine if engine is not None else get_engine()

    def discover_test_cases(self, directory: Path) -> list[TestCase]:
        """Finds all *.in files and pairs them with *.out or *.ans files."""
        if not directory.is_dir():
            return []

        cases: list[TestCase] = []
        for in_file in sorted(directory.glob("*.in")):
            base_name = in_file.stem
            out_file = directory / f"{base_name}.out"
            if not out_file.exists():
                out_file = directory / f"{base_name}.ans"

            if out_file.exists():
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
        checker: OutputChecker,
    ) -> TestResult:
        """Executes a single testcase and compares output."""
        with open(case.input_path, "r", encoding="utf-8", errors="replace") as f:
            input_text = f.read()

        with open(case.expected_output_path, "r", encoding="utf-8", errors="replace") as f:
            expected_output = f.read()

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
    ) -> BatchResult:
        """Discovers and runs all testcases in cases_dir, aggregating verdicts."""
        cases = self.discover_test_cases(cases_dir)
        checker = OutputChecker(mode=mode)

        results: list[TestResult] = []
        passed = 0
        total_cpu = 0.0
        max_ram = 0.0
        first_failure: str | None = None

        for case in cases:
            res = self.run_case(source_path, case, limits, checker)
            results.append(res)
            total_cpu += res.cpu_time_ms
            max_ram = max(max_ram, res.peak_memory_mb)

            if res.is_accepted:
                passed += 1
            elif first_failure is None:
                first_failure = res.verdict

        total = len(cases)
        overall = "ACCEPTED" if (total > 0 and passed == total) else (first_failure or "NO_TESTS")

        return BatchResult(
            passed=passed,
            total=total,
            overall_verdict=overall,
            total_cpu_time_ms=total_cpu,
            max_peak_memory_mb=max_ram,
            results=results,
        )
