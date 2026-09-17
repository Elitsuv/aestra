from __future__ import annotations

import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

from src.checker import CheckerMode, OutputChecker
from src.cli import main as cli_main
from src.config import ExecutionLimits
from src.engine import BaseEngine, MockEngine, SubprocessEngine, get_engine
from src.models import ExecutionStatus
from src.runner import BatchRunner, TestCase


# =====================================================================
# 1. ENGINE TESTS
# =====================================================================
def test_engine_factory() -> None:
    engine = get_engine()
    assert isinstance(engine, BaseEngine)


def test_subprocess_engine_execution() -> None:
    engine = SubprocessEngine()
    limits = ExecutionLimits(time_limit_ms=2000, memory_limit_mb=128)
    res = engine.execute(
        Path(sys.executable),
        limits,
        args=["-c", "import sys; sys.stdout.write('hello aestra')"],
    )
    assert res.status == ExecutionStatus.OK
    assert res.stdout == "hello aestra"
    assert res.exit_code == 0


def test_subprocess_engine_timeout() -> None:
    engine = SubprocessEngine()
    limits = ExecutionLimits(time_limit_ms=200, memory_limit_mb=128)
    res = engine.execute(
        Path(sys.executable),
        limits,
        args=["-c", "import time; time.sleep(1.0)"],
    )
    assert res.status == ExecutionStatus.TIME_LIMIT_EXCEEDED
    assert res.exit_code == -1


# =====================================================================
# 2. OUTPUT CHECKER TESTS
# =====================================================================
def test_checker_token_whitespace() -> None:
    checker = OutputChecker(CheckerMode.TOKEN)
    result = checker.check("1 2 3\n", "1  2  3")
    assert result.is_correct is True
    assert result.diff is None


def test_checker_token_mismatch() -> None:
    checker = OutputChecker(CheckerMode.TOKEN)
    result = checker.check("1 2 4", "1 2 3")
    assert result.is_correct is False
    assert result.diff is not None
    assert "Expected:\n1 2 3" in result.diff


def test_checker_exact_strictness() -> None:
    checker = OutputChecker(CheckerMode.EXACT)
    result = checker.check("hello\n", "hello")
    assert result.is_correct is False


def test_checker_ignore_whitespace() -> None:
    checker = OutputChecker(CheckerMode.IGNORE_WHITESPACE)
    result = checker.check("  hello world  \n", "hello world")
    assert result.is_correct is True


# =====================================================================
# 3. BATCH RUNNER TESTS
# =====================================================================
def test_runner_empty_or_missing() -> None:
    runner = BatchRunner(engine=MockEngine())
    assert runner.discover_test_cases(Path("non_existent_dir_9999")) == []


def test_runner_case_pairing() -> None:
    runner = BatchRunner(engine=MockEngine())
    with tempfile.TemporaryDirectory() as tmpdir:
        folder = Path(tmpdir)
        (folder / "01.in").write_text("10 20\n", encoding="utf-8")
        (folder / "01.out").write_text("30\n", encoding="utf-8")
        (folder / "02.in").write_text("5 5\n", encoding="utf-8")
        (folder / "02.ans").write_text("10\n", encoding="utf-8")
        (folder / "03.in").write_text("orphan\n", encoding="utf-8")

        cases = runner.discover_test_cases(folder)
        assert len(cases) == 2
        assert cases[0].name == "01.in"
        assert cases[1].name == "02.in"


def test_runner_run_case_verdicts() -> None:
    mock_engine = MockEngine()
    runner = BatchRunner(engine=mock_engine)
    limits = ExecutionLimits(time_limit_ms=2000, memory_limit_mb=128)
    checker = OutputChecker(mode=CheckerMode.TOKEN)

    with tempfile.TemporaryDirectory() as tmpdir:
        folder = Path(tmpdir)
        source_file = folder / "solution.py"
        source_file.write_text("# STATUS: OK\n", encoding="utf-8")

        in_file = folder / "test.in"
        out_file = folder / "test.out"
        in_file.write_text("input", encoding="utf-8")
        out_file.write_text("Simulated output.", encoding="utf-8")

        case = TestCase(
            name="test.in", input_path=in_file, expected_output_path=out_file
        )
        res_ok = runner.run_case(source_file, case, limits, checker)
        assert res_ok.verdict == "ACCEPTED"
        assert res_ok.is_accepted is True

        out_file.write_text("Wrong output.", encoding="utf-8")
        res_wa = runner.run_case(source_file, case, limits, checker)
        assert res_wa.verdict == "WRONG_ANSWER"
        assert res_wa.is_accepted is False


def test_runner_batch_aggregation() -> None:
    mock_engine = MockEngine()
    runner = BatchRunner(engine=mock_engine)
    limits = ExecutionLimits(time_limit_ms=1000, memory_limit_mb=128)

    with tempfile.TemporaryDirectory() as tmpdir:
        folder = Path(tmpdir)
        source_file = folder / "solution.py"
        source_file.write_text("# STATUS: OK\n", encoding="utf-8")

        (folder / "1.in").write_text("in1", encoding="utf-8")
        (folder / "1.out").write_text("Simulated output.", encoding="utf-8")
        (folder / "2.in").write_text("in2", encoding="utf-8")
        (folder / "2.out").write_text("Mismatch.", encoding="utf-8")

        batch_res = runner.run_batch(
            source_file, folder, limits, mode=CheckerMode.TOKEN
        )
        assert batch_res.total == 2
        assert batch_res.passed == 1
        assert batch_res.overall_verdict == "WRONG_ANSWER"


# =====================================================================
# 4. CLI TESTS
# =====================================================================
def test_cli_executable() -> None:
    exit_code = cli_main(
        ["run", sys.executable, "--time-limit", "1000", "--memory-limit", "128"]
    )
    assert exit_code == 0


def test_cli_missing_binary() -> None:
    exit_code = cli_main(["run", "non_existent_binary_xyz_123.exe"])
    assert exit_code == 1


# =====================================================================
# 5. SDK TESTS
# =====================================================================
def test_sdk_imports_and_exports() -> None:
    from aestra import Config, Fuzzer, FuzzResult, Judge, Minimizer

    assert Judge is not None
    assert Fuzzer is not None
    assert Minimizer is not None
    assert Config is not None
    assert FuzzResult is not None


def test_sdk_config_toml() -> None:
    from aestra import Config

    with tempfile.TemporaryDirectory() as tmpdir:
        toml_file = Path(tmpdir) / "aestra.toml"
        toml_file.write_text(
            """
[limits]
time_limit_ms = 1500
memory_limit_mb = 256
output_limit_bytes = 1048576

[checker]
mode = "EXACT"
            """,
            encoding="utf-8",
        )
        cfg = Config.from_toml(toml_file)
        assert cfg.time_limit_ms == 1500
        assert cfg.memory_limit_mb == 256
        assert cfg.checker_mode == CheckerMode.EXACT
        limits = cfg.to_limits()
        assert limits.time_limit_ms == 1500
        assert limits.memory_limit_mb == 256


def test_sdk_judge_single() -> None:
    from aestra import Config, Judge

    judge = Judge(
        config=Config(time_limit_ms=2000, memory_limit_mb=128),
        engine=SubprocessEngine(),
    )
    res = judge.run_single(sys.executable, args=["-c", "print('sdk_ok')"])
    assert res.status == ExecutionStatus.OK
    assert "sdk_ok" in res.stdout


def test_sdk_judge_batch() -> None:
    from aestra import Judge

    mock_engine = MockEngine()
    judge = Judge(engine=mock_engine)

    with tempfile.TemporaryDirectory() as tmpdir:
        folder = Path(tmpdir)
        source_file = folder / "solution.py"
        source_file.write_text("# STATUS: OK\n", encoding="utf-8")

        (folder / "01.in").write_text("in", encoding="utf-8")
        (folder / "01.out").write_text("Simulated output.", encoding="utf-8")

        batch_res = judge.run(source_file, cases_dir=folder)
        assert batch_res.passed == 1
        assert batch_res.overall_verdict == "ACCEPTED"

        case = TestCase("custom.in", folder / "01.in", folder / "01.out")
        res_list = judge.run(source_file, test_cases=[case])
        assert res_list.passed == 1
        assert res_list.overall_verdict == "ACCEPTED"


def test_sdk_fuzzer_clean() -> None:
    from aestra import Fuzzer

    with tempfile.TemporaryDirectory() as tmpdir:
        sol = Path(tmpdir) / "sol.py"
        sol.write_text("# STATUS: OK\n", encoding="utf-8")

        mock_engine = MockEngine()
        fuzzer = Fuzzer(
            target_binary=sol,
            oracle=lambda inp: "Simulated output.",
            engine=mock_engine,
        )
        result = fuzzer.run(iterations=5)
        assert result.found_bug is False
        assert result.iterations_run == 5


def test_sdk_fuzzer_catches_bug() -> None:
    from aestra import Fuzzer

    with tempfile.TemporaryDirectory() as tmpdir:
        sol = Path(tmpdir) / "sol.py"
        sol.write_text("# STATUS: OK\n", encoding="utf-8")

        mock_engine = MockEngine()
        fuzzer = Fuzzer(
            target_binary=sol,
            oracle=lambda inp: "Expected something else",
            engine=mock_engine,
        )
        result = fuzzer.run(iterations=5)
        assert result.found_bug is True
        assert result.iterations_run == 1
        assert result.failing_input is not None
        assert "Wrong Answer" in (result.error_message or "")


def test_sdk_minimizer() -> None:
    from aestra import Minimizer

    with tempfile.TemporaryDirectory() as tmpdir:
        sol = Path(tmpdir) / "sol.py"
        sol.write_text("# STATUS: OK\n", encoding="utf-8")

        mock_engine = MockEngine()
        minimizer = Minimizer(
            target_binary=sol,
            oracle=lambda inp: "Simulated output." if "FAIL" not in inp else "MISMATCH",
            engine=mock_engine,
        )

        failing_input = "line1\nline2\nFAIL\nline3\nline4\n"
        minimized = minimizer.minimize(failing_input)
        assert "FAIL" in minimized
        assert len(minimized.splitlines()) < len(failing_input.splitlines())


# =====================================================================
# MAIN RUNNER
# =====================================================================
ALL_TESTS: list[tuple[str, Callable[[], None]]] = [
    ("Engine Factory", test_engine_factory),
    ("Subprocess Engine Success", test_subprocess_engine_execution),
    ("Subprocess Engine Timeout", test_subprocess_engine_timeout),
    ("Checker Token Whitespace", test_checker_token_whitespace),
    ("Checker Token Mismatch", test_checker_token_mismatch),
    ("Checker Exact Strictness", test_checker_exact_strictness),
    ("Checker Ignore Whitespace", test_checker_ignore_whitespace),
    ("Runner Empty/Missing Dir", test_runner_empty_or_missing),
    ("Runner Case Pairing", test_runner_case_pairing),
    ("Runner Case Verdicts", test_runner_run_case_verdicts),
    ("Runner Batch Aggregation", test_runner_batch_aggregation),
    ("CLI Executable Run", test_cli_executable),
    ("CLI Missing Binary Handling", test_cli_missing_binary),
    ("SDK Imports and Exports", test_sdk_imports_and_exports),
    ("SDK Config TOML Parsing", test_sdk_config_toml),
    ("SDK Judge Single Execution", test_sdk_judge_single),
    ("SDK Judge Batch Execution", test_sdk_judge_batch),
    ("SDK Fuzzer Clean Run", test_sdk_fuzzer_clean),
    ("SDK Fuzzer Catches Bug", test_sdk_fuzzer_catches_bug),
    ("SDK Minimizer Delta Debugging", test_sdk_minimizer),
]


def run_all() -> int:
    print(f"Running all {len(ALL_TESTS)} Aestra tests in one unified suite...\n")
    passed = 0
    failed = 0

    for name, test_func in ALL_TESTS:
        try:
            test_func()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:  # noqa: BLE001
            print(f"  [FAIL] {name}: {e}")
            failed += 1

    print("\n==========================================")
    print(f"Test Summary: {passed}/{len(ALL_TESTS)} passed ({failed} failed)")
    print("==========================================")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all())
