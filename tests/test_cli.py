from __future__ import annotations

import argparse
import sys
import tempfile
import unittest
from pathlib import Path

from src.cli import (
    _parse_version,
    check_for_updates,
    doctor_command,
    fuzz_command,
    run_command,
    uninstall_command,
)
from src.cli import (
    main as cli_main,
)


class CLITests(unittest.TestCase):
    def test_cli_executable_run(self) -> None:
        exit_code = cli_main(
            ["run", sys.executable, "--time-limit", "1000", "--memory-limit", "128"]
        )
        self.assertEqual(exit_code, 0)

    def test_cli_run_with_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sol = Path(tmpdir) / "solution.py"
            sol.write_text("import sys; print(f'ECHO: {sys.stdin.read().strip()}')")

            ns = argparse.Namespace(
                binary=str(sol),
                input="hello world",
                time_limit=2000,
                memory_limit=512,
            )
            exit_code = run_command(ns)
            self.assertEqual(exit_code, 0)

    def test_cli_batch_test(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            sol = folder / "solution.py"
            sol.write_text("import sys; print(sum(map(int, sys.stdin.read().split())))")

            cases_dir = folder / "cases"
            cases_dir.mkdir()
            (cases_dir / "01.in").write_text("10 20\n")
            (cases_dir / "01.out").write_text("30\n")

            exit_code = cli_main(
                ["test", str(sol), "--cases", str(cases_dir), "--mode", "token"]
            )
            self.assertEqual(exit_code, 0)

    def test_cli_fuzz_subcommand_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sol = Path(tmpdir) / "solution.py"
            sol.write_text("import sys; sys.exit(0)")

            exit_code = cli_main(
                ["fuzz", str(sol), "--iterations", "10", "--workers", "2"]
            )
            self.assertEqual(exit_code, 0)

    def test_cli_fuzz_subcommand_catches_bug(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sol = Path(tmpdir) / "solution.py"
            sol.write_text("import sys; sys.exit(1)")

            exit_code = cli_main(
                ["fuzz", str(sol), "--iterations", "10", "--workers", "1"]
            )
            self.assertEqual(exit_code, 1)

    def test_cli_fuzz_with_minimize_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sol = Path(tmpdir) / "solution.py"
            sol.write_text("import sys\nsys.exit(1)\n")

            ns = argparse.Namespace(
                binary=str(sol),
                oracle=None,
                iterations=5,
                workers=1,
                minimize=True,
                time_limit=2000,
                memory_limit=512,
            )
            exit_code = fuzz_command(ns)
            self.assertEqual(exit_code, 1)

    def test_cli_doctor(self) -> None:
        exit_code = doctor_command()
        self.assertEqual(exit_code, 0)

    def test_cli_validation_missing_file(self) -> None:
        exit_code = cli_main(["run", "non_existent_binary_xyz_123.exe"])
        self.assertEqual(exit_code, 1)

    def test_cli_validation_empty_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_file = Path(tmpdir) / "empty.py"
            empty_file.write_text("")
            exit_code = cli_main(["run", str(empty_file)])
            self.assertEqual(exit_code, 1)

    def test_cli_validation_whitespace_only_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ws_file = Path(tmpdir) / "whitespace.py"
            ws_file.write_text("   \n\n  \t  \n")
            exit_code = cli_main(["run", str(ws_file)])
            self.assertEqual(exit_code, 1)

    def test_cli_uninstall_cancel(self) -> None:
        from unittest.mock import patch

        with patch("builtins.input", return_value="n"):
            exit_code = uninstall_command()
            self.assertEqual(exit_code, 0)

    def test_check_for_updates_parse_version(self) -> None:
        self.assertEqual(_parse_version("v1.2.0"), (1, 2, 0))
        self.assertEqual(_parse_version("1.1.0"), (1, 1, 0))
        self.assertTrue(_parse_version("v1.2.0") > _parse_version("v1.1.0"))
        self.assertFalse(_parse_version("v1.0.9") > _parse_version("v1.1.0"))

    def test_check_for_updates_offline_safe(self) -> None:
        res = check_for_updates()
        self.assertTrue(res is None or isinstance(res, str))


if __name__ == "__main__":
    unittest.main()
