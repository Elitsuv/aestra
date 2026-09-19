from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from src.checker import CheckerMode


@dataclass(frozen=True)
class ExecutionLimits:
    time_limit_ms: int = 2000
    memory_limit_mb: int = 512
    output_limit_bytes: int = 10 * 1024 * 1024

    @property
    def time_limit(self) -> int:
        return max(1, self.time_limit_ms // 1000)

    @property
    def memory_limit_bytes(self) -> int:
        return self.memory_limit_mb * 1024 * 1024


@dataclass
class Config:
    time_limit_ms: int = 2000
    memory_limit_mb: int = 512
    checker_mode: CheckerMode = CheckerMode.TOKEN
    output_limit_bytes: int = 10 * 1024 * 1024

    def to_limits(self) -> ExecutionLimits:
        return ExecutionLimits(
            time_limit_ms=self.time_limit_ms,
            memory_limit_mb=self.memory_limit_mb,
            output_limit_bytes=self.output_limit_bytes,
        )

    @classmethod
    def from_toml(cls, path: str | Path) -> Config:
        toml_path = Path(path)
        if not toml_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {toml_path}")

        raw_text = toml_path.read_text(encoding="utf-8")
        parsed: dict[str, object] = {}

        if sys.version_info >= (3, 11):
            import tomllib

            parsed = tomllib.loads(raw_text)
        else:
            parsed = cls._parse_simple_toml(raw_text)

        limits_data = (
            parsed.get("limits") if isinstance(parsed.get("limits"), dict) else parsed
        )
        checker_data = (
            parsed.get("checker") if isinstance(parsed.get("checker"), dict) else parsed
        )

        time_limit = (
            limits_data.get("time_limit_ms", 2000)
            if isinstance(limits_data, dict)
            else 2000
        )
        memory_limit = (
            limits_data.get("memory_limit_mb", 512)
            if isinstance(limits_data, dict)
            else 512
        )
        output_limit = (
            limits_data.get("output_limit_bytes", 10 * 1024 * 1024)
            if isinstance(limits_data, dict)
            else 10 * 1024 * 1024
        )

        raw_mode = (
            checker_data.get("mode", "TOKEN")
            if isinstance(checker_data, dict)
            else "TOKEN"
        )
        raw_mode_str = str(raw_mode).upper()
        mode = (
            CheckerMode(raw_mode_str)
            if raw_mode_str in CheckerMode.__members__
            else CheckerMode.TOKEN
        )

        return cls(
            time_limit_ms=int(time_limit),
            memory_limit_mb=int(memory_limit),
            checker_mode=mode,
            output_limit_bytes=int(output_limit),
        )

    @staticmethod
    def _parse_simple_toml(text: str) -> dict[str, object]:
        data: dict[str, object] = {}
        current_section = data
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                sec_name = line[1:-1].strip()
                sub: dict[str, object] = {}
                data[sec_name] = sub
                current_section = sub
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if val.isdigit():
                    current_section[key] = int(val)
                elif val.lower() == "true":
                    current_section[key] = True
                elif val.lower() == "false":
                    current_section[key] = False
                else:
                    current_section[key] = val
        return data
