from __future__ import annotations

import abc
import contextlib
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

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

            stdout_str = str(telemetry.get("stdout", ""))
            stderr_str = str(telemetry.get("stderr", ""))
            err_msg = telemetry.get("error_message")

            if limits.output_limit_bytes > 0:
                stdout_b = stdout_str.encode("utf-8", errors="replace")
                if len(stdout_b) > limits.output_limit_bytes:
                    status = ExecutionStatus.OUTPUT_LIMIT_EXCEEDED
                    err_msg = (
                        f"Output limit exceeded ({limits.output_limit_bytes} bytes)"
                    )
                    stdout_str = (
                        stdout_b[: limits.output_limit_bytes].decode(
                            "utf-8", errors="ignore"
                        )
                        + "\n[TRUNCATED - OUTPUT LIMIT EXCEEDED]"
                    )

                stderr_b = stderr_str.encode("utf-8", errors="replace")
                if len(stderr_b) > limits.output_limit_bytes:
                    stderr_str = (
                        stderr_b[: limits.output_limit_bytes].decode(
                            "utf-8", errors="ignore"
                        )
                        + "\n[TRUNCATED - OUTPUT LIMIT EXCEEDED]"
                    )

            return ExecutionResult(
                status=status,
                exit_code=int(telemetry.get("exit_code", 0)),
                cpu_time_ms=float(telemetry.get("cpu_time_ms", 0.0)),
                peak_memory_bytes=int(telemetry.get("peak_memory_bytes", 0)),
                stdout=stdout_str,
                stderr=stderr_str,
                error_message=err_msg,
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


def _measure_windows_peak_memory(proc_handle: int) -> int:
    """Measure peak working set size of a Windows process handle in bytes."""
    if sys.platform != "win32":
        return 0
    with contextlib.suppress(Exception):
        import ctypes
        from ctypes import wintypes

        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        pmc = ProcessMemoryCounters()
        pmc.cb = ctypes.sizeof(ProcessMemoryCounters)
        windll = getattr(ctypes, "windll", None)
        if windll is not None:
            kernel32 = getattr(windll, "kernel32", None)
            func = (
                getattr(kernel32, "K32GetProcessMemoryInfo", None) if kernel32 else None
            )
            if func is None and hasattr(windll, "psapi"):
                func = getattr(windll.psapi, "GetProcessMemoryInfo", None)
            if func is not None and bool(func(proc_handle, ctypes.byref(pmc), pmc.cb)):
                return int(pmc.PeakWorkingSetSize)
    return 0


def _measure_posix_peak_memory() -> int:
    """Measure peak memory of child processes on POSIX systems in bytes."""
    if sys.platform == "win32":
        return 0
    with contextlib.suppress(Exception):
        import resource

        getrusage: Any = getattr(resource, "getrusage", None)
        rusage_children = getattr(resource, "RUSAGE_CHILDREN", None)
        if callable(getrusage) and rusage_children is not None:
            usage = getrusage(rusage_children)
            if sys.platform == "darwin":
                return int(usage.ru_maxrss)
            return int(usage.ru_maxrss * 1024)
    return 0


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
        proc: subprocess.Popen[str] | None = None
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            proc_handle_raw = getattr(proc, "_handle", None)
            proc_handle: int | None = (
                int(proc_handle_raw) if proc_handle_raw is not None else None
            )

            stdout_str, stderr_str = proc.communicate(
                input=input_data,
                timeout=timeout_sec,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            peak_mem = 0
            if sys.platform == "win32" and proc_handle is not None:
                peak_mem = _measure_windows_peak_memory(proc_handle)
            else:
                peak_mem = _measure_posix_peak_memory()

            status = (
                ExecutionStatus.OK
                if proc.returncode == 0
                else ExecutionStatus.RUNTIME_ERROR
            )
            if limits.memory_limit_bytes > 0 and peak_mem > limits.memory_limit_bytes:
                status = ExecutionStatus.MEMORY_LIMIT_EXCEEDED

            err_msg: str | None = None
            if limits.output_limit_bytes > 0:
                stdout_b = stdout_str.encode("utf-8", errors="replace")
                if len(stdout_b) > limits.output_limit_bytes:
                    status = ExecutionStatus.OUTPUT_LIMIT_EXCEEDED
                    err_msg = (
                        f"Output limit exceeded ({limits.output_limit_bytes} bytes)"
                    )
                    stdout_str = (
                        stdout_b[: limits.output_limit_bytes].decode(
                            "utf-8", errors="ignore"
                        )
                        + "\n[TRUNCATED - OUTPUT LIMIT EXCEEDED]"
                    )

                stderr_b = stderr_str.encode("utf-8", errors="replace")
                if len(stderr_b) > limits.output_limit_bytes:
                    stderr_str = (
                        stderr_b[: limits.output_limit_bytes].decode(
                            "utf-8", errors="ignore"
                        )
                        + "\n[TRUNCATED - OUTPUT LIMIT EXCEEDED]"
                    )

            return ExecutionResult(
                status=status,
                stdout=stdout_str,
                stderr=stderr_str,
                exit_code=proc.returncode if proc.returncode is not None else 0,
                cpu_time_ms=elapsed_ms,
                peak_memory_bytes=peak_mem,
                error_message=err_msg,
            )
        except subprocess.TimeoutExpired:
            if proc is not None:
                with contextlib.suppress(Exception):
                    proc.kill()
                try:
                    out, err = proc.communicate()
                except Exception:  # noqa: BLE001
                    out, err = "", ""
            else:
                out, err = "", ""
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return ExecutionResult(
                status=ExecutionStatus.TIME_LIMIT_EXCEEDED,
                stdout=out or "",
                stderr=err or "",
                exit_code=-1,
                cpu_time_ms=elapsed_ms,
                peak_memory_bytes=0,
                error_message=f"Time limit exceeded ({limits.time_limit_ms}ms)",
            )
        except Exception as e:  # noqa: BLE001
            if proc is not None:
                with contextlib.suppress(Exception):
                    proc.kill()
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
