from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.engine import MockEngine
from src.sdk import Minimizer


class MinimizerTests(unittest.TestCase):
    def test_minimizer_line_reduction(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sol = Path(tmpdir) / "sol.py"
            sol.write_text("# STATUS: OK\n", encoding="utf-8")

            mock_engine = MockEngine()
            minimizer = Minimizer(
                target_binary=sol,
                oracle=lambda inp: (
                    "Simulated output." if "CRASH" not in inp else "MISMATCH"
                ),
                engine=mock_engine,
            )

            lines = [f"line_{i}" for i in range(20)]
            lines[10] = "CRASH"
            failing_input = "\n".join(lines) + "\n"

            minimized = minimizer.minimize(failing_input)
            self.assertIn("CRASH", minimized)
            self.assertLess(
                len(minimized.splitlines()), len(failing_input.splitlines())
            )

    def test_minimizer_token_reduction(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sol = Path(tmpdir) / "sol.py"
            sol.write_text("# STATUS: OK\n", encoding="utf-8")

            mock_engine = MockEngine()
            minimizer = Minimizer(
                target_binary=sol,
                oracle=lambda inp: (
                    "Simulated output." if "BAD_TOKEN" not in inp else "MISMATCH"
                ),
                engine=mock_engine,
            )

            failing_input = "val1 val2 val3 BAD_TOKEN val4 val5 val6"
            minimized = minimizer.minimize(failing_input)
            self.assertIn("BAD_TOKEN", minimized)
            self.assertLess(len(minimized.split()), len(failing_input.split()))

    def test_minimizer_non_failing_input_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sol = Path(tmpdir) / "sol.py"
            sol.write_text("# STATUS: OK\n", encoding="utf-8")

            mock_engine = MockEngine()
            minimizer = Minimizer(
                target_binary=sol,
                oracle=lambda inp: "Simulated output.",
                engine=mock_engine,
            )

            safe_input = "all elements are completely safe"
            res = minimizer.minimize(safe_input)
            self.assertEqual(res, safe_input)

    def test_minimizer_step_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sol = Path(tmpdir) / "sol.py"
            sol.write_text("# STATUS: OK\n", encoding="utf-8")

            mock_engine = MockEngine()
            minimizer = Minimizer(
                target_binary=sol,
                oracle=lambda inp: (
                    "Simulated output." if "TRIGGER" not in inp else "MISMATCH"
                ),
                engine=mock_engine,
            )

            failing_input = "\n".join(f"line_{i}" for i in range(100)) + "\nTRIGGER\n"
            # Setting max_steps=0 should immediately return input or minimally modified
            res_zero = minimizer.minimize(failing_input, max_steps=0)
            self.assertIn("TRIGGER", res_zero)


if __name__ == "__main__":
    unittest.main()
