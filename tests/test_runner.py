from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.checker import CheckerMode, OutputChecker
from src.config import ExecutionLimits
from src.engine import MockEngine
from src.runner import BatchRunner, TestCase
from src.sdk import Judge


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

    def test_runner_parallel_execution(self) -> None:
        mock_engine = MockEngine()
        runner = BatchRunner(engine=mock_engine)
        limits = ExecutionLimits()

        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            source_file = folder / "sol.py"
            source_file.write_text("# STATUS: OK\n", encoding="utf-8")

            cases: list[TestCase] = []
            for i in range(1, 9):
                in_f = folder / f"{i:02d}.in"
                out_f = folder / f"{i:02d}.out"
                in_f.write_text(f"inp_{i}", encoding="utf-8")
                out_f.write_text("Simulated output.", encoding="utf-8")
                cases.append(
                    TestCase(
                        name=f"{i:02d}.in", input_path=in_f, expected_output_path=out_f
                    )
                )

            batch_res = runner.evaluate_cases(source_file, cases, limits, workers=4)
            self.assertEqual(batch_res.total, 8)
            self.assertEqual(batch_res.passed, 8)
            self.assertEqual(batch_res.overall_verdict, "ACCEPTED")
            # Verify exact ordering preserved
            self.assertEqual(
                [r.case_name for r in batch_res.results],
                [f"{i:02d}.in" for i in range(1, 9)],
            )

    def test_case_caching_and_invalidation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            in_file = folder / "test.in"
            out_file = folder / "test.out"
            in_file.write_text("initial input", encoding="utf-8")
            out_file.write_text("initial output", encoding="utf-8")

            case = TestCase(
                name="test.in", input_path=in_file, expected_output_path=out_file
            )
            self.assertEqual(case.get_input(), "initial input")
            self.assertEqual(case.get_expected_output(), "initial output")

            # Calling again returns cached data
            self.assertEqual(case.get_input(), "initial input")
            self.assertEqual(case.get_expected_output(), "initial output")

            # Updating file on disk modifies mtime and invalidates cache
            import time

            time.sleep(0.01)  # Ensure mtime_ns advances
            in_file.write_text("updated input", encoding="utf-8")
            out_file.write_text("updated output", encoding="utf-8")

            self.assertEqual(case.get_input(), "updated input")
            self.assertEqual(case.get_expected_output(), "updated output")

    def test_judge_parallel_workers(self) -> None:
        mock_engine = MockEngine()
        judge = Judge(engine=mock_engine)

        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            source_file = folder / "sol.py"
            source_file.write_text("# STATUS: OK\n", encoding="utf-8")

            cases_dir = folder / "cases"
            cases_dir.mkdir()
            (cases_dir / "01.in").write_text("1")
            (cases_dir / "01.out").write_text("Simulated output.")
            (cases_dir / "02.in").write_text("2")
            (cases_dir / "02.out").write_text("Simulated output.")

            # Test run with cases_dir and workers=2
            res1 = judge.run(source_file, cases_dir=cases_dir, workers=2)
            self.assertEqual(res1.total, 2)
            self.assertEqual(res1.passed, 2)

            # Test run with test_cases and workers=2
            cases = [
                TestCase(
                    name="c1", input_data="a", expected_output="Simulated output."
                ),
                TestCase(
                    name="c2", input_data="b", expected_output="Simulated output."
                ),
            ]
            res2 = judge.run(source_file, test_cases=cases, workers=2)
            self.assertEqual(res2.total, 2)
            self.assertEqual(res2.passed, 2)


if __name__ == "__main__":
    unittest.main()
