from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

from src.config import ExecutionLimits
from src.engine import (
    BaseEngine,
    MockEngine,
    NativeEngine,
    SubprocessEngine,
    _kill_process_tree,
    get_engine,
    get_sanitized_environment,
)
from src.models import ExecutionStatus


class EngineTests(unittest.TestCase):
    def test_engine_factory(self) -> None:
        engine = get_engine()
        self.assertIsInstance(engine, BaseEngine)

    def test_subprocess_engine_execution(self) -> None:
        engine = SubprocessEngine()
        limits = ExecutionLimits(time_limit_ms=2000, memory_limit_mb=128)
        res = engine.execute(
            Path(sys.executable),
            limits,
            args=["-c", "import sys; sys.stdout.write('hello aestra')"],
        )
        self.assertEqual(res.status, ExecutionStatus.OK)
        self.assertEqual(res.stdout, "hello aestra")
        self.assertEqual(res.exit_code, 0)
        self.assertGreaterEqual(res.cpu_time_ms, 0.0)

    def test_subprocess_engine_timeout(self) -> None:
        engine = SubprocessEngine()
        limits = ExecutionLimits(time_limit_ms=200, memory_limit_mb=128)
        res = engine.execute(
            Path(sys.executable),
            limits,
            args=["-c", "import time; time.sleep(1.0)"],
        )
        self.assertEqual(res.status, ExecutionStatus.TIME_LIMIT_EXCEEDED)
        self.assertEqual(res.exit_code, -1)
        self.assertIn("Time limit exceeded", res.error_message or "")

    def test_output_limit_exceeded(self) -> None:
        engine = SubprocessEngine()
        limits = ExecutionLimits(
            time_limit_ms=2000, memory_limit_mb=128, output_limit_bytes=40
        )
        res = engine.execute(
            Path(sys.executable),
            limits,
            args=["-c", "import sys; sys.stdout.write('A' * 200)"],
        )
        self.assertEqual(res.status, ExecutionStatus.OUTPUT_LIMIT_EXCEEDED)
        self.assertIn("[TRUNCATED - OUTPUT LIMIT EXCEEDED]", res.stdout)
        self.assertLess(len(res.stdout), 200)

    def test_security_sanitized_environment(self) -> None:
        os.environ["MOCK_ACCESS_KEY"] = "leak_me"
        os.environ["MOCK_AUTH_TOKEN"] = "token_123"
        os.environ["MOCK_DATABASE_PASSWORD"] = "pass_secret"

        try:
            clean_env = get_sanitized_environment()
            self.assertNotIn("MOCK_ACCESS_KEY", clean_env)
            self.assertNotIn("MOCK_AUTH_TOKEN", clean_env)
            self.assertNotIn("MOCK_DATABASE_PASSWORD", clean_env)
            self.assertIn("PATH", clean_env)
        finally:
            os.environ.pop("MOCK_ACCESS_KEY", None)
            os.environ.pop("MOCK_AUTH_TOKEN", None)
            os.environ.pop("MOCK_DATABASE_PASSWORD", None)

    def test_process_tree_kill_none_safe(self) -> None:
        # Verify passing None or terminated process handles safely without exception
        _kill_process_tree(None)

    def test_mock_engine(self) -> None:
        engine = MockEngine()
        limits = ExecutionLimits()
        res = engine.execute(Path("non_existent_file.xyz"), limits)
        self.assertEqual(res.status, ExecutionStatus.INTERNAL_ERROR)

    def test_native_engine_availability(self) -> None:
        if sys.platform == "win32":
            self.assertFalse(NativeEngine.is_available())
            res = NativeEngine().execute(Path(sys.executable), ExecutionLimits())
            self.assertEqual(res.status, ExecutionStatus.INTERNAL_ERROR)


if __name__ == "__main__":
    unittest.main()
