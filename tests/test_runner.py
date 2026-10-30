from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.checker import CheckerMode, OutputChecker
from src.config import ExecutionLimits
from src.engine import MockEngine
from src.runner import BatchRunner, TestCase


class RunnerTests(unittest.TestCase):
    def test_runner_empty_or_missing(self) -> None:
        runner = BatchRunner(engine=MockEngine())
        self.assertEqual(runner.discover_test_cases(Path("non_existent_dir_9999")), [])

    def test_runner_case_pairing(self) -> None:
        runner = BatchRunner(engine=MockEngine())
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            (folder / "01.in").write_text("10 20\n", encoding="utf-8")
            (folder / "01.out").write_text("30\n", encoding="utf-8")
            (folder / "02.in").write_text("5 5\n", encoding="utf-8")
            (folder / "02.ans").write_text("10\n", encoding="utf-8")
            (folder / "03.in").write_text("orphan\n", encoding="utf-8")

            cases = runner.discover_test_cases(folder)
            self.assertEqual(len(cases), 2)
            self.assertEqual(cases[0].name, "01.in")
            self.assertEqual(cases[1].name, "02.in")

    def test_runner_run_case_verdicts(self) -> None:
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
            self.assertEqual(res_ok.verdict, "ACCEPTED")
            self.assertTrue(res_ok.is_accepted)

            out_file.write_text("Wrong output.", encoding="utf-8")
            res_wa = runner.run_case(source_file, case, limits, checker)
            self.assertEqual(res_wa.verdict, "WRONG_ANSWER")
            self.assertFalse(res_wa.is_accepted)

    def test_runner_batch_aggregation(self) -> None:
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
            self.assertEqual(batch_res.total, 2)
            self.assertEqual(batch_res.passed, 1)
            self.assertEqual(batch_res.overall_verdict, "WRONG_ANSWER")

    def test_in_memory_test_cases(self) -> None:
        mock_engine = MockEngine()
        runner = BatchRunner(engine=mock_engine)
        limits = ExecutionLimits()
        checker = OutputChecker()

        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "sol.py"
            source_file.write_text("# STATUS: OK\n", encoding="utf-8")

            case = TestCase(
                name="in_memory_sample",
                input_data="1 2 3",
                expected_output="Simulated output.",
            )
            self.assertEqual(case.get_input(), "1 2 3")
            self.assertEqual(case.get_expected_output(), "Simulated output.")

            res = runner.run_case(source_file, case, limits, checker)
            self.assertTrue(res.is_accepted)
            self.assertEqual(res.verdict, "ACCEPTED")

    def test_security_runner_symlink_defense(self) -> None:
        runner = BatchRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            cases_dir = Path(tmpdir) / "cases"
            cases_dir.mkdir()
            outside_file = Path(tmpdir) / "secret.in"
            outside_file.write_text("outside data", encoding="utf-8")

            in1 = cases_dir / "01.in"
            out1 = cases_dir / "01.out"
            in1.write_text("inside", encoding="utf-8")
            out1.write_text("inside", encoding="utf-8")

            symlink_created = False
            try:
                symlink_in = cases_dir / "02.in"
                symlink_in.symlink_to(outside_file)
                symlink_out = cases_dir / "02.out"
                symlink_out.write_text("outside", encoding="utf-8")
                symlink_created = True
            except (OSError, NotImplementedError):
                pass

            cases = runner.discover_test_cases(cases_dir)
            case_names = [c.name for c in cases]
            self.assertIn("01.in", case_names)
            if symlink_created:
                self.assertNotIn("02.in", case_names)


if __name__ == "__main__":
    unittest.main()
