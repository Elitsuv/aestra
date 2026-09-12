from __future__ import annotations

import abc
import subprocess
import sys
import time
from pathlib import Path

from src.config import ExecutionLimits
from src.models import ExecutionResult, ExecutionStatus


class BaseEngine(abc.ABC):
    @abc.abstractmethod
    def execute(
        self,
        source_path: Path,
        limits: ExecutionLimits,
        input_data: str = "",
        args: list[str] | None = None,
    ) -> ExecutionResult:
        """Executes the source file strictly within the provided hardware limits."""


class MockEngine(BaseEngine):
    def execute(
        self,
        source_path: Path,
        limits: ExecutionLimits,
        input_data: str = "",
        args: list[str] | None = None,
    ) -> ExecutionResult:
        status = ExecutionStatus.OK

        try:
            with open(source_path, "r") as f:
                first_line = f.readline().strip()
                if first_line.startswith("# STATUS: "):
                    raw_status = first_line.split("# STATUS: ")[1].strip()
                    try:
                        status = ExecutionStatus(raw_status)
                    except ValueError:
                        pass
        except FileNotFoundError:
            status = ExecutionStatus.INTERNAL_ERROR

        return ExecutionResult(
            status=status,
            stdout="Simulated output." if status == ExecutionStatus.OK else "",
            stderr="Simulated error." if status != ExecutionStatus.OK else "",
            exit_code=0 if status == ExecutionStatus.OK else 1,
            cpu_time_ms=15.5,
            peak_memory_bytes=1024 * 1024,
        )


class NativeEngine(BaseEngine):
    """Native execution engine using Rust aestra_core PyO3 FFI bridge."""

    def execute(
        self,
        source_path: Path,
        limits: ExecutionLimits,
        input_data: str = "",
        args: list[str] | None = None,
    ) -> ExecutionResult:
        try:
            import aestra_core

            cmd_args: list[str] = args if args is not None else []
            telemetry = aestra_core.execute_native(
                str(source_path),
                cmd_args,
                input_data,
                limits.time_limit_ms,
                limits.memory_limit_mb,
            )

            status_str = telemetry.get("status", "INTERNAL_ERROR")
            try:
                status = ExecutionStatus(status_str)
            except ValueError:
                status = ExecutionStatus.INTERNAL_ERROR

            return ExecutionResult(
                status=status,
                exit_code=int(telemetry.get("exit_code", 0)),
                cpu_time_ms=float(telemetry.get("cpu_time_ms", 0.0)),
                peak_memory_bytes=int(telemetry.get("peak_memory_bytes", 0)),
                stdout=str(telemetry.get("stdout", "")),
                stderr=str(telemetry.get("stderr", "")),
                error_message=telemetry.get("error_message"),
            )
        except ImportError:
            return ExecutionResult(
                status=ExecutionStatus.INTERNAL_ERROR,
                stderr="Native extension 'aestra_core' is not installed.",
                exit_code=1,
                error_message="aestra_core import failed",
            )
        except Exception as e:  # noqa: BLE001
            return ExecutionResult(
                status=ExecutionStatus.INTERNAL_ERROR,
                stderr=str(e),
                exit_code=1,
                error_message=f"Native execution crash: {e}",
            )


class SubprocessEngine(BaseEngine):
    def execute(
        self,
        source_path: Path,
        limits: ExecutionLimits,
        input_data: str = "",
        args: list[str] | None = None,
    ) -> ExecutionResult:
        extra_args: list[str] = args if args is not None else []
        if source_path.suffix == ".py":
            cmd = [sys.executable, str(source_path)] + extra_args
        else:
            cmd = [str(source_path)] + extra_args
        timeout_sec = limits.time_limit_ms / 1000.0

        start_time = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd,
                input=input_data,
                text=True,
                capture_output=True,
                timeout=timeout_sec,
                check=False,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            status = (
                ExecutionStatus.OK
                if proc.returncode == 0
                else ExecutionStatus.RUNTIME_ERROR
            )
            return ExecutionResult(
                status=status,
                stdout=proc.stdout,
                stderr=proc.stderr,
                exit_code=proc.returncode,
                cpu_time_ms=elapsed_ms,
                peak_memory_bytes=0,
            )
        except subprocess.TimeoutExpired as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            stdout_str = e.stdout if isinstance(e.stdout, str) else ""
            stderr_str = e.stderr if isinstance(e.stderr, str) else ""
            return ExecutionResult(
                status=ExecutionStatus.TIME_LIMIT_EXCEEDED,
                stdout=stdout_str,
                stderr=stderr_str,
                exit_code=-1,
                cpu_time_ms=elapsed_ms,
                peak_memory_bytes=0,
                error_message=f"Time limit exceeded ({limits.time_limit_ms}ms)",
            )
        except Exception as e:  # noqa: BLE001
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ExecutionResult(
                status=ExecutionStatus.INTERNAL_ERROR,
                stdout="",
                stderr=str(e),
                exit_code=1,
                cpu_time_ms=elapsed_ms,
                peak_memory_bytes=0,
                error_message=str(e),
            )


def get_engine() -> BaseEngine:
    try:
        import aestra_core  # noqa: F401

        return NativeEngine()
    except ImportError:
        return SubprocessEngine()
