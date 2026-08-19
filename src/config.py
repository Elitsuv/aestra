from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionLimits:
    time_limit_ms: int = 2000
    memory_limit_mb: int = 512

    @property
    def time_limit(self) -> int:
        return max(1, self.time_limit_ms // 1000)

    @property
    def memory_limit_bytes(self) -> int:
        return self.memory_limit_mb * 1024 * 1024