from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.checker import CheckerMode
from src.config import Config, ExecutionLimits


class ConfigTests(unittest.TestCase):
    def test_config_defaults(self) -> None:
        cfg = Config()
        self.assertEqual(cfg.time_limit_ms, 2000)
        self.assertEqual(cfg.memory_limit_mb, 512)
        self.assertEqual(cfg.checker_mode, CheckerMode.TOKEN)

        limits = cfg.to_limits()
        self.assertIsInstance(limits, ExecutionLimits)
        self.assertEqual(limits.time_limit_ms, 2000)
        self.assertEqual(limits.memory_limit_mb, 512)
        self.assertEqual(limits.memory_limit_bytes, 512 * 1024 * 1024)

    def test_config_from_toml(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            toml_file = Path(tmpdir) / "aestra.toml"
            toml_file.write_text(
                """
[limits]
time_limit_ms = 1500
memory_limit_mb = 256
output_limit_bytes = 1048576

[checker]
mode = "EXACT"
                """,
                encoding="utf-8",
            )
            cfg = Config.from_toml(toml_file)
            self.assertEqual(cfg.time_limit_ms, 1500)
            self.assertEqual(cfg.memory_limit_mb, 256)
            self.assertEqual(cfg.checker_mode, CheckerMode.EXACT)
            self.assertEqual(cfg.output_limit_bytes, 1048576)

    def test_config_fallback_parser(self) -> None:
        raw_toml = """
# Test comment
[limits]
time_limit_ms = 3000
memory_limit_mb = 1024
enabled = true

[checker]
mode = "IGNORE_WHITESPACE"
"""
        parsed = Config._parse_simple_toml(raw_toml)
        self.assertIn("limits", parsed)
        limits_dict = parsed["limits"]
        self.assertIsInstance(limits_dict, dict)
        self.assertEqual(limits_dict["time_limit_ms"], 3000)
        self.assertEqual(limits_dict["memory_limit_mb"], 1024)
        self.assertIs(limits_dict["enabled"], True)

    def test_config_missing_file_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            Config.from_toml("non_existent_config_file_123.toml")


if __name__ == "__main__":
    unittest.main()
