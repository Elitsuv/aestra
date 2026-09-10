from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.checker import CheckerMode
from src.config import ExecutionLimits
from src.engine import get_engine
from src.runner import BatchRunner

BANNER = """
  +-------------------------------------------------------------+
  |  AESTRA  *  Deterministic CP Execution Sandbox  v0.1.0-beta |
  |  Microsecond telemetry & hardware-level resource limits     |
  +-------------------------------------------------------------+
"""


def run_command(args: argparse.Namespace) -> int:
    source_path = Path(args.binary)
    if not source_path.exists():
        print(f"Error: Binary '{source_path}' not found.", file=sys.stderr)
        return 1

    engine = get_engine()
    limits = ExecutionLimits(
        time_limit_ms=args.time_limit,
        memory_limit_mb=args.memory_limit,
    )

    input_data = args.input if args.input is not None else ""
    result = engine.execute(source_path, limits, input_data=input_data)

    print("\n  +-- [Telemetry] ----------------------------------------------+")
    print(f"  |  Status     : {result.status.value:<46} |")
    print(f"  |  CPU Time   : {f'{result.cpu_time_ms:.1f}ms':<46} |")
    print(f"  |  Peak Memory: {f'{result.peak_memory_mb:.1f}MB':<46} |")
    print(f"  |  Exit Code  : {result.exit_code!s:<46} |")
    print("  +-------------------------------------------------------------+")

    if result.stdout:
        print("\n[Output]")
        print(result.stdout.rstrip())
    if result.stderr:
        print("\n[Error]")
        print(result.stderr.rstrip(), file=sys.stderr)

    return 0 if result.is_success else 1


def test_command(args: argparse.Namespace) -> int:
    source_path = Path(args.binary)
    if not source_path.exists():
        print(f"Error: Binary '{source_path}' not found.", file=sys.stderr)
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

    print("\n  +-- [Batch Runner] -------------------------------------------+")
    print(f"  |  Binary : {source_path.name:<48} |")
    print(f"  |  Cases  : {f'{len(cases)} testcases from {cases_dir.name}/':<48} |")
    print(
        f"  |  Limits : {f'{limits.time_limit_ms}ms CPU, {limits.memory_limit_mb}MB RAM':<48} |"
    )
    print("  +-------------------------------------------------------------+\n")

    batch_res = runner.run_batch(source_path, cases_dir, limits, mode=mode)

    for res in batch_res.results:
        badge = f"[{res.verdict}]"
        print(
            f"  {badge:<24} {res.case_name:<16} {res.cpu_time_ms:>6.1f}ms  {res.peak_memory_mb:>5.1f}MB"
        )
        if not res.is_accepted and res.diff:
            for line in res.diff.splitlines():
                print(f"      {line}")

    summary_status = "ALL PASSED" if batch_res.passed == batch_res.total else "FAILED"
    print("\n  =============================================================")
    print(
        f"  Summary: {batch_res.passed}/{batch_res.total} accepted ({summary_status}) "
        f"* {batch_res.total_cpu_time_ms:.1f}ms * {batch_res.max_peak_memory_mb:.1f}MB"
    )
    print("  =============================================================\n")
    return 0 if batch_res.passed == batch_res.total else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="aestra",
        description="Aestra - Deterministic execution sandbox for competitive programming",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  aestra run ./solution.exe --time-limit 1000 --memory-limit 256
  aestra test ./solution.exe --cases ./testcases/ --mode token
""",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # run subcommand
    run_parser = subparsers.add_parser(
        "run", help="Run a binary under hardware resource limits"
    )
    run_parser.add_argument("binary", help="Path to executable binary")
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

    # test subcommand
    test_parser = subparsers.add_parser(
        "test", help="Run batch test cases against a binary"
    )
    test_parser.add_argument("binary", help="Path to executable binary")
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

    args = parser.parse_args(argv)

    if args.command == "run":
        return run_command(args)
    elif args.command == "test":
        return test_command(args)
    else:
        print(BANNER)
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
