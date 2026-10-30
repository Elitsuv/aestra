from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from src.checker import CheckerMode
from src.compiler import CompilationError, CompilerManager
from src.config import ExecutionLimits
from src.engine import NativeEngine, get_engine
from src.runner import BatchRunner
from src.sdk import Fuzzer, Minimizer

VERSION = "1.1.1"


def _parse_version(v: str) -> tuple[int, ...]:
    clean = v.lstrip("v").strip()
    try:
        return tuple(int(x) for x in clean.split("."))
    except ValueError:
        return (0, 0, 0)


def check_for_updates() -> str | None:
    """Checks GitHub releases for updates with 24h cache and 1s timeout (0 user data)."""
    try:
        cache_dir = Path(".aestra")
        cache_file = cache_dir / "update_cache.json"
        now = time.time()

        if cache_file.exists():
            try:
                cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
                if now - cache_data.get("timestamp", 0) < 86400:
                    cached_tag = str(cache_data.get("latest_tag", ""))
                    if cached_tag and _parse_version(cached_tag) > _parse_version(
                        VERSION
                    ):
                        return cached_tag
                    return None
            except (OSError, ValueError, TypeError, KeyError):
                pass

        url = "https://api.github.com/repos/Elitsuv/aestra/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": "Aestra-CLI"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            latest_tag = str(data.get("tag_name", "")).strip()

            try:
                cache_dir.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(
                    json.dumps({"timestamp": now, "latest_tag": latest_tag}),
                    encoding="utf-8",
                )
            except OSError:
                pass

            if latest_tag and _parse_version(latest_tag) > _parse_version(VERSION):
                return latest_tag
    except (OSError, ValueError, urllib.error.URLError, TimeoutError):
        pass

    return None


def _enable_windows_ansi() -> None:
    """Enables virtual terminal processing on Windows consoles via Win32 API."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        h_stdout = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(h_stdout, ctypes.byref(mode)):
            kernel32.SetConsoleMode(h_stdout, mode.value | 0x0004)
    except (AttributeError, OSError):
        pass


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


BANNER = f"""
  {Color.CYAN}+-------------------------------------------------------------+
  |  {Color.BOLD}AESTRA{Color.RESET}{Color.CYAN}  *  Deterministic CP Execution Sandbox     {Color.YELLOW}v{VERSION}{Color.CYAN}  |
  |  Microsecond telemetry & hardware-level resource limits     |
  +-------------------------------------------------------------+{Color.RESET}
"""

SHELL_HEADER = f"""
  {Color.CYAN}+-------------------------------------------------------------+
  |  {Color.BOLD}AESTRA{Color.RESET}{Color.CYAN}  *  Deterministic CP Execution Sandbox     {Color.YELLOW}v{VERSION}{Color.CYAN}  |
  |  Microsecond telemetry * Multi-language * Zero PC footprint |
  +-------------------------------------------------------------+{Color.RESET}
"""


def _clean_path_input(raw: str) -> Path:
    cleaned = raw.strip().strip("'").strip('"')
    return Path(cleaned)


def _validate_source_file(path: Path) -> str | None:
    if not path.exists():
        return f"Target '{path}' not found."
    if not path.is_file():
        return f"Target '{path}' is a directory, not a file."
    try:
        if path.stat().st_size == 0:
            return (
                f"Target file '{path.name}' is empty (0 bytes). "
                f"Please add your solution code to the file before executing."
            )
        if (
            path.suffix.lower() in (".py", ".cpp", ".c", ".cc", ".rs", ".go")
            and path.stat().st_size < 50_000
        ):
            content = path.read_text(encoding="utf-8", errors="ignore").strip()
            if not content:
                return (
                    f"Target file '{path.name}' contains only whitespace. "
                    f"Please add your solution code to the file before executing."
                )
    except OSError as err:
        return f"Cannot read '{path}': {err}"
    return None


def run_command(args: argparse.Namespace) -> int:
    raw_path = Path(args.binary)
    validation_err = _validate_source_file(raw_path)
    if validation_err:
        print(f"Error: {validation_err}", file=sys.stderr)
        return 1

    try:
        comp_res = CompilerManager.prepare(raw_path)
        source_path = comp_res.executable_path
        if not comp_res.cached:
            print(
                f"  {Color.CYAN}[Compiled]{Color.RESET} {raw_path.name} -> {source_path.name}"
            )
    except CompilationError as e:
        print(
            f"\n  {Color.RED}[COMPILATION_ERROR]{Color.RESET}\n{e.message}",
            file=sys.stderr,
        )
        return 1

    engine = get_engine()
    limits = ExecutionLimits(
        time_limit_ms=args.time_limit,
        memory_limit_mb=args.memory_limit,
    )

    input_data = args.input if args.input is not None else ""
    result = engine.execute(source_path, limits, input_data=input_data)

    status_color = Color.GREEN if result.is_success else Color.RED
    print(
        f"\n  {Color.CYAN}+-- [Telemetry] ----------------------------------------------+{Color.RESET}"
    )
    print(f"  |  Status     : {status_color}{result.status.value:<46}{Color.RESET} |")
    print(
        f"  |  CPU Time   : {Color.BOLD}{f'{result.cpu_time_ms:.1f}ms':<46}{Color.RESET} |"
    )
    print(
        f"  |  Peak Memory: {Color.BOLD}{f'{result.peak_memory_mb:.1f}MB':<46}{Color.RESET} |"
    )
    print(f"  |  Exit Code  : {result.exit_code!s:<46} |")
    print(
        f"  {Color.CYAN}+-------------------------------------------------------------+{Color.RESET}"
    )

    if input_data:
        print(f"\n{Color.YELLOW}[Input (stdin)]{Color.RESET}")
        print(input_data.rstrip())

    if result.stdout:
        print(f"\n{Color.GREEN}[Output]{Color.RESET}")
        print(result.stdout.rstrip())
    if result.stderr:
        print(f"\n{Color.RED}[Error]{Color.RESET}", file=sys.stderr)
        print(result.stderr.rstrip(), file=sys.stderr)

    return 0 if result.is_success else 1


def test_command(args: argparse.Namespace) -> int:
    raw_path = Path(args.binary)
    validation_err = _validate_source_file(raw_path)
    if validation_err:
        print(f"Error: {validation_err}", file=sys.stderr)
        return 1

    try:
        comp_res = CompilerManager.prepare(raw_path)
        source_path = comp_res.executable_path
        if not comp_res.cached:
            print(
                f"  {Color.CYAN}[Compiled]{Color.RESET} {raw_path.name} -> {source_path.name}"
            )
    except CompilationError as e:
        print(
            f"\n  {Color.RED}[COMPILATION_ERROR]{Color.RESET}\n{e.message}",
            file=sys.stderr,
        )
        return 1

    cases_dir = Path(args.cases)
    if not cases_dir.is_dir():
        print(f"Error: Cases directory '{cases_dir}' not found.", file=sys.stderr)
        return 1

    mode_map = {
        "token": CheckerMode.TOKEN,
        "exact": CheckerMode.EXACT,
        "ignore_whitespace": CheckerMode.IGNORE_WHITESPACE,
    }
    mode = mode_map.get(args.mode.lower(), CheckerMode.TOKEN)

    limits = ExecutionLimits(
        time_limit_ms=args.time_limit,
        memory_limit_mb=args.memory_limit,
    )

    runner = BatchRunner()
    cases = runner.discover_test_cases(cases_dir)
    if not cases:
        print(
            f"No test cases (*.in with matching *.out/*.ans) found in '{cases_dir}'.",
            file=sys.stderr,
        )
        return 1

    print(
        f"\n  {Color.CYAN}+-- [Batch Runner] -------------------------------------------+{Color.RESET}"
    )
    print(f"  |  Binary : {source_path.name:<48} |")
    print(f"  |  Cases  : {f'{len(cases)} testcases from {cases_dir.name}/':<48} |")
    print(
        f"  |  Limits : {f'{limits.time_limit_ms}ms CPU, {limits.memory_limit_mb}MB RAM':<48} |"
    )
    print(
        f"  {Color.CYAN}+-------------------------------------------------------------+{Color.RESET}\n"
    )

    batch_res = runner.run_batch(source_path, cases_dir, limits, mode=mode)

    for res in batch_res.results:
        verdict_color = Color.GREEN if res.is_accepted else Color.RED
        badge = f"{verdict_color}[{res.verdict}]{Color.RESET}"
        print(
            f"  {badge:<34} {res.case_name:<16} {res.cpu_time_ms:>6.1f}ms  {res.peak_memory_mb:>5.1f}MB"
        )
        if not res.is_accepted and res.diff:
            for line in res.diff.splitlines():
                print(f"      {Color.YELLOW}{line}{Color.RESET}")

    is_all_passed = batch_res.passed == batch_res.total
    status_label = (
        f"{Color.GREEN}ALL PASSED{Color.RESET}"
        if is_all_passed
        else f"{Color.RED}FAILED{Color.RESET}"
    )
    print(
        f"\n  {Color.CYAN}============================================================={Color.RESET}"
    )
    print(
        f"  Summary: {batch_res.passed}/{batch_res.total} accepted ({status_label}) "
        f"* {batch_res.total_cpu_time_ms:.1f}ms * {batch_res.max_peak_memory_mb:.1f}MB"
    )
    print(
        f"  {Color.CYAN}============================================================={Color.RESET}\n"
    )
    return 0 if is_all_passed else 1


def fuzz_command(args: argparse.Namespace) -> int:
    raw_path = Path(args.binary)
    validation_err = _validate_source_file(raw_path)
    if validation_err:
        print(f"Error: {validation_err}", file=sys.stderr)
        return 1

    try:
        comp_res = CompilerManager.prepare(raw_path)
        target_exec = comp_res.executable_path
    except CompilationError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        return 1

    oracle_path = Path(args.oracle) if args.oracle else None
    if oracle_path is not None:
        val_err = _validate_source_file(oracle_path)
        if val_err:
            print(f"Error with oracle: {val_err}", file=sys.stderr)
            return 1
        try:
            oracle_comp = CompilerManager.prepare(oracle_path)
            oracle_path = oracle_comp.executable_path
        except CompilationError as e:
            print(f"Error compiling oracle: {e.message}", file=sys.stderr)
            return 1

    workers = getattr(args, "workers", 1)
    iterations = getattr(args, "iterations", 50)
    should_minimize = getattr(args, "minimize", False)

    print(
        f"\n  {Color.CYAN}+-- [Concurrent Fuzzer] --------------------------------------+{Color.RESET}"
    )
    print(f"  |  Target     : {target_exec.name:<45} |")
    print(
        f"  |  Oracle     : {(oracle_path.name if oracle_path else 'Crash & limit check'):<45} |"
    )
    print(f"  |  Iterations : {iterations:<45} |")
    print(f"  |  Workers    : {workers:<45} |")
    print(
        f"  {Color.CYAN}+-------------------------------------------------------------+{Color.RESET}\n"
    )

    fuzzer = Fuzzer(
        target_binary=target_exec,
        oracle=oracle_path,
        timeout_ms=args.time_limit,
        memory_limit_mb=args.memory_limit,
    )
    res = fuzzer.run(iterations=iterations, workers=workers)

    if res.found_bug:
        print(
            f"  {Color.RED}[BUG DISCOVERED]{Color.RESET} at iteration {res.iterations_run}!"
        )
        if res.error_message:
            print(f"  Error: {res.error_message}")
        if res.failing_input:
            failing_inp = res.failing_input
            if should_minimize:
                print(
                    f"\n  {Color.CYAN}[Minimizing]{Color.RESET} Delta-debugging failing input..."
                )
                minimizer = Minimizer(
                    target_binary=target_exec,
                    oracle=oracle_path,
                    config=fuzzer.config,
                )
                minimized_inp = minimizer.minimize(failing_inp)
                print(f"  {Color.GREEN}[Minimization complete]{Color.RESET}")
                print(
                    f"\n{Color.YELLOW}[Minimal Reproducible Input]{Color.RESET}\n{minimized_inp.rstrip()}"
                )
            else:
                print(
                    f"\n{Color.YELLOW}[Failing Input]{Color.RESET}\n{failing_inp.rstrip()}"
                )
        return 1

    print(
        f"  {Color.GREEN}[PASS]{Color.RESET} All {iterations} randomized stress iterations completed successfully.\n"
    )
    return 0


def doctor_command(_args: argparse.Namespace | None = None) -> int:
    """Diagnoses host environment and compiler availability."""
    engine = get_engine()
    engine_name = (
        "NativeEngine (Rust POSIX FFI)"
        if isinstance(engine, NativeEngine)
        else "SubprocessEngine (Universal Fallback)"
    )

    print(
        f"\n  {Color.CYAN}+-- [System Doctor] ------------------------------------------+{Color.RESET}"
    )
    print(f"  |  Aestra Version : {Color.BOLD}v{VERSION:<41}{Color.RESET} |")
    print(f"  |  Platform       : {platform.system()} {platform.release():<37} |")
    print(f"  |  Architecture   : {platform.machine():<45} |")
    print(f"  |  Active Engine  : {engine_name:<45} |")

    update_tag = check_for_updates()
    if update_tag:
        print(
            f"  |  Update Alert  : {Color.YELLOW}★ New version available: v{VERSION} -> {update_tag}{Color.RESET}"
        )

    print(
        f"  {Color.CYAN}+-------------------------------------------------------------+{Color.RESET}"
    )
    print("  | Detected Toolchains & Compilers:")

    compilers = CompilerManager.detect_compilers()
    for name, path in compilers.items():
        if path:
            status = f"{Color.GREEN}Ready ({path}){Color.RESET}"
        else:
            status = f"{Color.GRAY}Not Found{Color.RESET}"
        print(f"  |  - {name:<10} : {status}")

    cache_dir = CompilerManager.BUILD_DIR
    cache_count = len(list(cache_dir.glob("*.*"))) if cache_dir.is_dir() else 0
    print(f"  |  Build Cache    : {cache_count} binaries in {cache_dir}")
    print(
        f"  {Color.CYAN}+-------------------------------------------------------------+{Color.RESET}\n"
    )
    return 0


def uninstall_command(_args: argparse.Namespace | None = None) -> int:
    """Launches the clean native uninstallation wizard for Aestra."""
    print(
        f"\n  {Color.YELLOW}+-- [Aestra Uninstaller Wizard] ------------------------------+{Color.RESET}"
    )
    print("  | Cleanly removes Aestra binaries, PATH entries, and shortcuts |")
    print(
        f"  {Color.YELLOW}+-------------------------------------------------------------+{Color.RESET}\n"
    )

    try:
        confirm = (
            input(
                f"  {Color.RED}Are you sure you want to remove Aestra from this system? [y/N]:{Color.RESET} "
            )
            .strip()
            .lower()
        )
    except (KeyboardInterrupt, EOFError):
        print(f"\n  {Color.GRAY}Uninstallation cancelled.{Color.RESET}\n")
        return 0

    if confirm not in ("y", "yes"):
        print(f"  {Color.GRAY}Uninstallation cancelled.{Color.RESET}\n")
        return 0

    print(f"\n  {Color.CYAN}[*] Initiating system uninstallation...{Color.RESET}")

    if sys.platform == "win32":
        launched_msi = False
        try:
            print(
                f"  {Color.CYAN}[*] Opening Windows Uninstallation Wizard...{Color.RESET}"
            )
            res = subprocess.run(
                ["msiexec.exe", "/x", "{C8B7A124-4B29-4F58-8C61-5B26E50D6B19}"],
                check=False,
            )
            if res.returncode == 0:
                launched_msi = True
        except (OSError, subprocess.SubprocessError):
            pass

        if not launched_msi:
            try:
                subprocess.run(
                    ["cmd.exe", "/c", "start", "ms-settings:appsfeatures"], check=False
                )
                print(
                    f"  {Color.GREEN}[*] Opened Windows Installed Apps. Select 'Aestra' -> 'Uninstall'.{Color.RESET}"
                )
            except (OSError, subprocess.SubprocessError):
                pass

    local_aestra = Path.home() / ".aestra"
    if local_aestra.exists():
        shutil.rmtree(local_aestra, ignore_errors=True)
        print(
            f"  {Color.GREEN}[OK]{Color.RESET} Cleaned local user directory: {local_aestra}"
        )

    print(
        f"\n  {Color.GREEN}[Complete]{Color.RESET} Uninstallation routine finished. Thank you for using Aestra!\n"
    )
    return 0


def interactive_shell() -> int:
    """Launches an interactive console window for Aestra."""
    print(SHELL_HEADER)
    update_tag = check_for_updates()
    if update_tag:
        print(
            f"  {Color.YELLOW}+-------------------------------------------------------------+\n"
            f"  |  {Color.BOLD}★ UPDATE AVAILABLE:{Color.RESET} {Color.YELLOW}v{VERSION} -> {update_tag:<32}{Color.YELLOW}|\n"
            f"  |  Run 'winget upgrade Aestra' or download from:              |\n"
            f"  |  https://github.com/Elitsuv/aestra/releases                |\n"
            f"  +-------------------------------------------------------------+{Color.RESET}\n"
        )
    engine = get_engine()
    engine_type = (
        "Native FFI" if isinstance(engine, NativeEngine) else "Universal Fallback"
    )
    print(
        f"  Active Sandbox: {Color.GREEN}{engine_type}{Color.RESET} | Python {platform.python_version()} on {platform.system()}\n"
    )

    menu = f"""  {Color.CYAN}[1]{Color.RESET} {Color.BOLD}Run Solution{Color.RESET}      - Execute source or binary with microsecond telemetry
  {Color.CYAN}[2]{Color.RESET} {Color.BOLD}Batch Test Suite{Color.RESET}  - Test solution against .in / .out cases directory
  {Color.CYAN}[3]{Color.RESET} {Color.BOLD}Stress & Fuzz{Color.RESET}     - Automated randomized fuzzing against edge cases
  {Color.CYAN}[4]{Color.RESET} {Color.BOLD}System Doctor{Color.RESET}     - Inspect system compilers and environment health
  {Color.CYAN}[5]{Color.RESET} {Color.BOLD}Clean Cache{Color.RESET}       - Wipe local compilation artifacts (.aestra/build)
  {Color.CYAN}[6]{Color.RESET} {Color.BOLD}Uninstall{Color.RESET}         - Launch native uninstallation wizard
  {Color.CYAN}[0]{Color.RESET} {Color.BOLD}Exit{Color.RESET}              - Quit Aestra
"""

    while True:
        try:
            print(menu)
            choice = input(f"  {Color.CYAN}{Color.BOLD}aestra>{Color.RESET} ").strip()
            if not choice:
                continue

            if choice in ("0", "exit", "quit", "q"):
                print(f"\n  {Color.GREEN}Exiting Aestra. Happy coding!{Color.RESET}\n")
                return 0

            elif choice in ("1", "run"):
                raw_path = input("  Enter target file (e.g. solution.cpp, main.py): ")
                path = _clean_path_input(raw_path)
                validation_err = _validate_source_file(path)
                if validation_err:
                    print(f"  {Color.RED}[Error]{Color.RESET} {validation_err}\n")
                    continue

                inp_data = input("  Standard input (press Enter for none): ")
                t_str = input("  Time limit ms [default: 2000]: ").strip()
                m_str = input("  Memory limit MB [default: 512]: ").strip()

                time_limit = int(t_str) if t_str.isdigit() else 2000
                mem_limit = int(m_str) if m_str.isdigit() else 512

                ns = argparse.Namespace(
                    binary=str(path),
                    input=inp_data,
                    time_limit=time_limit,
                    memory_limit=mem_limit,
                )
                run_command(ns)
                print()

            elif choice in ("2", "test"):
                raw_path = input("  Enter target file (e.g. solution.cpp, main.py): ")
                path = _clean_path_input(raw_path)
                validation_err = _validate_source_file(path)
                if validation_err:
                    print(f"  {Color.RED}[Error]{Color.RESET} {validation_err}\n")
                    continue

                raw_cases = input("  Enter testcases directory: ")
                cases_dir = _clean_path_input(raw_cases)
                if not cases_dir.is_dir():
                    print(
                        f"  {Color.RED}[Error]{Color.RESET} Directory '{cases_dir}' does not exist.\n"
                    )
                    continue

                mode_str = (
                    input(
                        "  Checker mode [token / exact / ignore_whitespace] (default: token): "
                    )
                    .strip()
                    .lower()
                    or "token"
                )
                t_str = input("  Time limit ms [default: 2000]: ").strip()
                m_str = input("  Memory limit MB [default: 512]: ").strip()

                time_limit = int(t_str) if t_str.isdigit() else 2000
                mem_limit = int(m_str) if m_str.isdigit() else 512

                ns = argparse.Namespace(
                    binary=str(path),
                    cases=str(cases_dir),
                    mode=mode_str,
                    time_limit=time_limit,
                    memory_limit=mem_limit,
                )
                test_command(ns)
                print()

            elif choice in ("3", "fuzz"):
                raw_path = input("  Enter target file to fuzz: ")
                path = _clean_path_input(raw_path)
                validation_err = _validate_source_file(path)
                if validation_err:
                    print(f"  {Color.RED}[Error]{Color.RESET} {validation_err}\n")
                    continue

                iter_str = input("  Number of iterations [default: 50]: ").strip()
                iterations = int(iter_str) if iter_str.isdigit() else 50
                oracle_str = input(
                    "  Oracle file (press Enter for crash-only): "
                ).strip()
                oracle_val = oracle_str if oracle_str else None

                ns = argparse.Namespace(
                    binary=str(path),
                    oracle=oracle_val,
                    iterations=iterations,
                    workers=4,
                    minimize=True,
                    time_limit=2000,
                    memory_limit=512,
                )
                fuzz_command(ns)
                print()

            elif choice in ("4", "doctor"):
                doctor_command()

            elif choice in ("5", "clean"):
                cleaned = CompilerManager.clean_cache()
                print(
                    f"  {Color.GREEN}[Cache Cleaned]{Color.RESET} Removed {cleaned} binary artifacts from .aestra/build.\n"
                )

            elif choice in ("6", "uninstall"):
                uninstall_command()

            else:
                parts = choice.split()
                cmd = parts[0].lower()
                if cmd == "doctor":
                    doctor_command()
                elif cmd == "run" and len(parts) > 1:
                    path = _clean_path_input(parts[1])
                    val_err = _validate_source_file(path)
                    if val_err:
                        print(f"  {Color.RED}[Error]{Color.RESET} {val_err}\n")
                        continue
                    ns = argparse.Namespace(
                        binary=str(path), input="", time_limit=2000, memory_limit=512
                    )
                    run_command(ns)
                elif cmd == "test" and len(parts) > 2:
                    bin_p = _clean_path_input(parts[1])
                    val_err = _validate_source_file(bin_p)
                    if val_err:
                        print(f"  {Color.RED}[Error]{Color.RESET} {val_err}\n")
                        continue
                    cas_p = _clean_path_input(parts[2])
                    ns = argparse.Namespace(
                        binary=str(bin_p),
                        cases=str(cas_p),
                        mode="token",
                        time_limit=2000,
                        memory_limit=512,
                    )
                    test_command(ns)
                else:
                    print(
                        f"  {Color.YELLOW}[Unknown command]{Color.RESET} '{choice}'. Enter 0-5 to select an option.\n"
                    )

        except (KeyboardInterrupt, EOFError):
            print(f"\n  {Color.GRAY}Session closed.{Color.RESET}")
            return 0
    return 0


def main(argv: list[str] | None = None) -> int:
    _enable_windows_ansi()

    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        return interactive_shell()

    parser = argparse.ArgumentParser(
        prog="aestra",
        description=f"Aestra v{VERSION} - Deterministic execution sandbox for competitive programming",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  aestra                                  Launch interactive shell
  aestra doctor                           Inspect toolchains & environment health
  aestra run ./solution.cpp               Run with microsecond telemetry
  aestra test ./solution.py --cases ./in  Run batch test suite
  aestra fuzz ./solution.py --iterations 100 --workers 4
""",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    run_parser = subparsers.add_parser(
        "run", help="Run a binary or source file under hardware resource limits"
    )
    run_parser.add_argument("binary", help="Path to executable binary or source file")
    run_parser.add_argument(
        "--time-limit",
        type=int,
        default=2000,
        help="CPU time limit in ms (default: 2000)",
    )
    run_parser.add_argument(
        "--memory-limit",
        type=int,
        default=512,
        help="Memory limit in MB (default: 512)",
    )
    run_parser.add_argument(
        "--input", type=str, default=None, help="Input string to pass via stdin"
    )

    test_parser = subparsers.add_parser(
        "test", help="Run batch test cases against a binary or source file"
    )
    test_parser.add_argument("binary", help="Path to executable binary or source file")
    test_parser.add_argument(
        "--cases",
        required=True,
        help="Directory containing test cases (*.in with *.out/*.ans)",
    )
    test_parser.add_argument(
        "--mode",
        choices=["token", "exact", "ignore_whitespace"],
        default="token",
        help="Output comparison mode (default: token)",
    )
    test_parser.add_argument(
        "--time-limit",
        type=int,
        default=2000,
        help="CPU time limit in ms (default: 2000)",
    )
    test_parser.add_argument(
        "--memory-limit",
        type=int,
        default=512,
        help="Memory limit in MB (default: 512)",
    )

    fuzz_parser = subparsers.add_parser(
        "fuzz", help="Run automated concurrent fuzzing against edge cases"
    )
    fuzz_parser.add_argument("binary", help="Path to target binary or source file")
    fuzz_parser.add_argument(
        "--oracle",
        type=str,
        default=None,
        help="Path to trusted oracle binary or script for differential checking",
    )
    fuzz_parser.add_argument(
        "--iterations",
        type=int,
        default=50,
        help="Number of randomized fuzzing iterations (default: 50)",
    )
    fuzz_parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of concurrent fuzzing worker threads (default: 4)",
    )
    fuzz_parser.add_argument(
        "--minimize",
        action="store_true",
        help="Automatically delta-debug minimize failing testcase if a bug is found",
    )
    fuzz_parser.add_argument(
        "--time-limit",
        type=int,
        default=2000,
        help="CPU time limit in ms (default: 2000)",
    )
    fuzz_parser.add_argument(
        "--memory-limit",
        type=int,
        default=512,
        help="Memory limit in MB (default: 512)",
    )

    subparsers.add_parser(
        "doctor", help="Inspect compiler toolchains and sandbox health"
    )

    subparsers.add_parser("uninstall", help="Launch native uninstaller wizard")

    subparsers.add_parser("interactive", help="Open the interactive terminal dashboard")

    args = parser.parse_args(argv)

    if args.command == "run":
        return run_command(args)
    elif args.command == "test":
        return test_command(args)
    elif args.command == "fuzz":
        return fuzz_command(args)
    elif args.command == "doctor":
        return doctor_command(args)
    elif args.command == "uninstall":
        return uninstall_command(args)
    elif args.command == "interactive":
        return interactive_shell()
    else:
        print(BANNER)
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
