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
                    # Safely attempt to match the enum, fallback to OK
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
