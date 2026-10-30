from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExecutionStatus(str, Enum):
    """Execution status verdict for sandboxed processes."""

    SUCCESS = "SUCCESS"
    OK = "OK"
    ACCEPTED = "ACCEPTED"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
    MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    OUTPUT_LIMIT_EXCEEDED = "OUTPUT_LIMIT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Telemetry and outcome data from a process execution run."""

    status: ExecutionStatus
    exit_code: int = 0
    cpu_time_ms: float = 0.0
    wall_time_ms: float = 0.0
    peak_memory_bytes: int = 0
    stdout: str = ""
    stderr: str = ""
    error_message: str | None = None

    @property
    def peak_memory_mb(self) -> float:
        return self.peak_memory_bytes / (1024 * 1024)

    @property
    def is_success(self) -> bool:
        return (
            self.status
            in (
                ExecutionStatus.SUCCESS,
                ExecutionStatus.OK,
                ExecutionStatus.ACCEPTED,
            )
            and self.exit_code == 0
        )
