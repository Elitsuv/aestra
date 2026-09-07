from __future__ import annotations

import abc
from pathlib import Path

from src.config import ExecutionLimits
from src.models import ExecutionResult, ExecutionStatus


class BaseEngine(abc.ABC):
    @abc.abstractmethod
    def execute(self, source_path: Path, limits: ExecutionLimits) -> ExecutionResult:
        """Executes the source file strictly within the provided hardware limits."""


class MockEngine(BaseEngine):
    def execute(self, source_path: Path, limits: ExecutionLimits) -> ExecutionResult:
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

    def execute(self, source_path: Path, limits: ExecutionLimits) -> ExecutionResult:
        try:
            import aestra_core  # type: ignore[import-not-found]

            raw_stdout = aestra_core.execute_native(
                str(source_path),
                [],
                limits.time_limit_ms,
                limits.memory_limit_mb,
            )
            return ExecutionResult(
                status=ExecutionStatus.OK,
                stdout=raw_stdout,
                exit_code=0,
                cpu_time_ms=0.5,
                peak_memory_bytes=1024 * 1024,
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
