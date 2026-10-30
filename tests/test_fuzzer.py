from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.engine import MockEngine
from src.sdk import Fuzzer


class FuzzerTests(unittest.TestCase):
    def test_fuzzer_sequential_clean_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sol = Path(tmpdir) / "sol.py"
            sol.write_text("# STATUS: OK\n", encoding="utf-8")

            mock_engine = MockEngine()
            fuzzer = Fuzzer(
                target_binary=sol,
                oracle=lambda inp: "Simulated output.",
                engine=mock_engine,
            )
            result = fuzzer.run(iterations=10, workers=1)
            self.assertFalse(result.found_bug)
            self.assertEqual(result.iterations_run, 10)

    def test_fuzzer_concurrent_clean_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sol = Path(tmpdir) / "sol.py"
            sol.write_text("# STATUS: OK\n", encoding="utf-8")

            mock_engine = MockEngine()
            fuzzer = Fuzzer(
                target_binary=sol,
                oracle=lambda inp: "Simulated output.",
                engine=mock_engine,
            )
            result = fuzzer.run(iterations=20, workers=4)
            self.assertFalse(result.found_bug)
            self.assertEqual(result.iterations_run, 20)

    def test_fuzzer_catches_target_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sol = Path(tmpdir) / "sol.py"
            sol.write_text("# STATUS: RUNTIME_ERROR\n", encoding="utf-8")

            mock_engine = MockEngine()
            fuzzer = Fuzzer(
                target_binary=sol,
                engine=mock_engine,
            )
            result = fuzzer.run(iterations=10)
            self.assertTrue(result.found_bug)
            self.assertIsNotNone(result.failing_input)
            self.assertIn("RUNTIME_ERROR", result.error_message or "")

    def test_fuzzer_catches_oracle_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sol = Path(tmpdir) / "sol.py"
            sol.write_text("# STATUS: OK\n", encoding="utf-8")

            mock_engine = MockEngine()
            fuzzer = Fuzzer(
                target_binary=sol,
                oracle=lambda inp: "Expected something else",
                engine=mock_engine,
            )
            result = fuzzer.run(iterations=10)
            self.assertTrue(result.found_bug)
            self.assertEqual(result.iterations_run, 1)
            self.assertIsNotNone(result.failing_input)
            self.assertIn("Wrong Answer", result.error_message or "")

    def test_fuzzer_concurrent_catches_bug(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sol = Path(tmpdir) / "sol.py"
            sol.write_text("# STATUS: OK\n", encoding="utf-8")

            mock_engine = MockEngine()
            # Fails only when iteration yields a certain condition
            fuzzer = Fuzzer(
                target_binary=sol,
                oracle=lambda inp: "Mismatch" if len(inp) > 5 else "Simulated output.",
                engine=mock_engine,
            )
            result = fuzzer.run(iterations=30, workers=4)
            self.assertTrue(result.found_bug)
            self.assertIsNotNone(result.failing_input)

    def test_fuzzer_oracle_crash_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sol = Path(tmpdir) / "sol.py"
            sol.write_text("# STATUS: OK\n", encoding="utf-8")

            mock_engine = MockEngine()

            def buggy_oracle(inp: str) -> str:
                raise ValueError("Simulated oracle crash")

            fuzzer = Fuzzer(
                target_binary=sol,
                oracle=buggy_oracle,
                engine=mock_engine,
            )
            result = fuzzer.run(iterations=5)
            self.assertFalse(result.found_bug)
            self.assertIsNotNone(result.error_message)
            self.assertIn("Oracle evaluation failure", result.error_message or "")

    def test_fuzzer_zero_iterations(self) -> None:
        fuzzer = Fuzzer(target_binary="dummy.py", engine=MockEngine())
        res = fuzzer.run(iterations=0)
        self.assertFalse(res.found_bug)
        self.assertEqual(res.iterations_run, 0)

    def test_fuzzer_custom_generator(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sol = Path(tmpdir) / "sol.py"
            sol.write_text("# STATUS: OK\n", encoding="utf-8")

            seen_inputs: list[str] = []

            def custom_gen(idx: int) -> str:
                inp = f"custom_case_{idx}"
                seen_inputs.append(inp)
                return inp

            fuzzer = Fuzzer(
                target_binary=sol,
                generator=custom_gen,
                engine=MockEngine(),
            )
            res = fuzzer.run(iterations=5)
            self.assertFalse(res.found_bug)
            self.assertEqual(len(seen_inputs), 5)
            self.assertEqual(seen_inputs[0], "custom_case_0")


if __name__ == "__main__":
    unittest.main()
