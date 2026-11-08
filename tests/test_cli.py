from __future__ import annotations

import argparse
import sys
import tempfile
import unittest
from pathlib import Path

from src.cli import (
    _clean_path_input,
    _discover_default_cases_dir,
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

    def test_clean_path_input(self) -> None:
        self.assertEqual(
            _clean_path_input("& 'C:\\foo\\bar.cpp'"), Path("C:\\foo\\bar.cpp")
        )
        self.assertEqual(
            _clean_path_input('& "C:\\foo\\bar.cpp"'), Path("C:\\foo\\bar.cpp")
        )
        self.assertEqual(
            _clean_path_input("  'C:\\foo\\bar.cpp'  "), Path("C:\\foo\\bar.cpp")
        )
        self.assertEqual(
            _clean_path_input(Path("C:\\foo\\bar.cpp")), Path("C:\\foo\\bar.cpp")
        )

    def test_cli_batch_test_with_workers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            sol = folder / "solution.py"
            sol.write_text("import sys; print(sum(map(int, sys.stdin.read().split())))")

            cases_dir = folder / "cases"
            cases_dir.mkdir()
            (cases_dir / "01.in").write_text("10 20\n")
            (cases_dir / "01.out").write_text("30\n")
            (cases_dir / "02.in").write_text("5 5\n")
            (cases_dir / "02.out").write_text("10\n")

            exit_code = cli_main(
                ["test", str(sol), "--cases", str(cases_dir), "--workers", "2"]
            )
            self.assertEqual(exit_code, 0)

    def test_cli_smart_cases_auto_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            sol = folder / "solution.py"
            sol.write_text("import sys; print(sum(map(int, sys.stdin.read().split())))")

            cases_dir = folder / "cases"
            cases_dir.mkdir()
            (cases_dir / "01.in").write_text("10 20\n")
            (cases_dir / "01.out").write_text("30\n")

            discovered = _discover_default_cases_dir(sol)
            self.assertEqual(discovered, cases_dir)

            # Invoking `aestra test` without `--cases` uses auto-discovery
            exit_code = cli_main(["test", str(sol)])
            self.assertEqual(exit_code, 0)

    def test_cli_json_flags(self) -> None:
        import io
        import json
        from contextlib import redirect_stdout

        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            sol = folder / "solution.py"
            sol.write_text("import sys; print('TEST_OK')")

            # Test run --json
            buf = io.StringIO()
            with redirect_stdout(buf):
                exit_code = cli_main(["run", str(sol), "--json"])
            self.assertEqual(exit_code, 0)
            data = json.loads(buf.getvalue())
            self.assertEqual(data["status"], "OK")
            self.assertTrue(data["is_success"])
            self.assertIn("TEST_OK", data["stdout"])

            # Test doctor --json
            buf = io.StringIO()
            with redirect_stdout(buf):
                exit_code = cli_main(["doctor", "--json"])
            self.assertEqual(exit_code, 0)
            doc_data = json.loads(buf.getvalue())
            self.assertEqual(doc_data["version"], "1.1.2")
            self.assertIn("compilers", doc_data)

    def test_cli_engine_disclosure(self) -> None:
        import io
        import json
        from contextlib import redirect_stdout

        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            sol = folder / "solution.py"
            sol.write_text("import sys; print('DISCLOSE_OK')")

            # 1. Human-readable telemetry block disclosure
            buf = io.StringIO()
            with redirect_stdout(buf):
                exit_code = cli_main(["run", str(sol)])
            self.assertEqual(exit_code, 0)
            out = buf.getvalue()
            self.assertIn("Engine     :", out)
            self.assertIn("wall-clock timing, approximate", out)

            # 2. run --json payload disclosure
            buf_json = io.StringIO()
            with redirect_stdout(buf_json):
                exit_code = cli_main(["run", str(sol), "--json"])
            self.assertEqual(exit_code, 0)
            run_data = json.loads(buf_json.getvalue())
            self.assertIn("engine", run_data)
            self.assertIn("engine_precision", run_data)
            self.assertEqual(run_data["engine"], "fallback")
            self.assertEqual(
                run_data["engine_precision"], "wall-clock timing, approximate"
            )

            # 3. test --json payload disclosure
            cases_dir = folder / "cases"
            cases_dir.mkdir()
            (cases_dir / "01.in").write_text("")
            (cases_dir / "01.out").write_text("DISCLOSE_OK\n")
            buf_test = io.StringIO()
            with redirect_stdout(buf_test):
                exit_code = cli_main(
                    ["test", str(sol), "--cases", str(cases_dir), "--json"]
                )
            self.assertEqual(exit_code, 0)
            test_data = json.loads(buf_test.getvalue())
            self.assertEqual(test_data["engine"], "fallback")
            self.assertEqual(
                test_data["engine_precision"], "wall-clock timing, approximate"
            )

            # 4. fuzz --json payload disclosure
            buf_fuzz = io.StringIO()
            with redirect_stdout(buf_fuzz):
                exit_code = cli_main(["fuzz", str(sol), "--iterations", "2", "--json"])
            self.assertEqual(exit_code, 0)
            fuzz_data = json.loads(buf_fuzz.getvalue())
            self.assertEqual(fuzz_data["engine"], "fallback")
            self.assertEqual(
                fuzz_data["engine_precision"], "wall-clock timing, approximate"
            )

    def test_cli_float_checker_modes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            sol = folder / "solution.py"
            # Output is 3.14159
            sol.write_text("import sys; print('3.14159')")

            cases_dir = folder / "cases"
            cases_dir.mkdir()
            (cases_dir / "01.in").write_text("")
            # Expected is 3.14160 (difference is 0.00001 = 1e-5)
            (cases_dir / "01.out").write_text("3.14160\n")

            # 1. Under default token mode, 3.14159 != 3.14160 -> Failure
            exit_code_token = cli_main(
                ["test", str(sol), "--cases", str(cases_dir), "--mode", "token"]
            )
            self.assertEqual(exit_code_token, 1)

            # 2. Under float mode with default epsilon (1e-4), diff 1e-5 < 1e-4 -> Accepted (0)
            exit_code_float = cli_main(
                ["test", str(sol), "--cases", str(cases_dir), "--mode", "float"]
            )
            self.assertEqual(exit_code_float, 0)

            # 3. Under float mode with strict epsilon (1e-6), diff 1e-5 > 1e-6 -> Failure (1)
            exit_code_strict = cli_main(
                [
                    "test",
                    str(sol),
                    "--cases",
                    str(cases_dir),
                    "--mode",
                    "float",
                    "--epsilon",
                    "1e-6",
                ]
            )
            self.assertEqual(exit_code_strict, 1)

            # 4. Fuzz mode supports --mode float
            exit_code_fuzz = cli_main(
                [
                    "fuzz",
                    str(sol),
                    "--iterations",
                    "2",
                    "--mode",
                    "float",
                    "--epsilon",
                    "1e-4",
                ]
            )
            self.assertEqual(exit_code_fuzz, 0)

    def test_cli_no_color_support(self) -> None:
        import io
        import os
        from contextlib import redirect_stdout
        from unittest.mock import patch

        from src.cli import Color

        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir)
            sol = folder / "solution.py"
            sol.write_text("import sys; print('NO_COLOR_TEST')")

            # 1. Test --no-color flag strips ANSI escape codes
            buf_flag = io.StringIO()
            with redirect_stdout(buf_flag):
                exit_code = cli_main(["run", str(sol), "--no-color"])
            self.assertEqual(exit_code, 0)
            flag_output = buf_flag.getvalue()
            self.assertNotIn("\033[", flag_output)
            self.assertIn("NO_COLOR_TEST", flag_output)
            self.assertFalse(Color.is_enabled())

            # 2. Test NO_COLOR environment variable strips ANSI escape codes
            Color.enable()
            self.assertTrue(Color.is_enabled())
            with patch.dict(os.environ, {"NO_COLOR": "1"}):
                buf_env = io.StringIO()
                with redirect_stdout(buf_env):
                    exit_code = cli_main(["run", str(sol)])
                self.assertEqual(exit_code, 0)
                env_output = buf_env.getvalue()
                self.assertNotIn("\033[", env_output)
                self.assertIn("NO_COLOR_TEST", env_output)
                self.assertFalse(Color.is_enabled())

            # Reset Color to enabled state for subsequent tests
            Color.enable()


if __name__ == "__main__":
    unittest.main()
