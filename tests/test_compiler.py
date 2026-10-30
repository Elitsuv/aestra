from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.compiler import CompilerManager


class CompilerTests(unittest.TestCase):
    def test_compiler_detection(self) -> None:
        compilers = CompilerManager.detect_compilers()
        self.assertIn("Python", compilers)
        self.assertIn("C++", compilers)
        self.assertIn("C", compilers)
        self.assertIn("Rust", compilers)
        self.assertIn("Go", compilers)
        self.assertIsNotNone(compilers["Python"])

    def test_compiler_manager_caching_and_passthrough(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            dummy_py = tmp_path / "solution.py"
            dummy_py.write_text("print('test')\n")
            res = CompilerManager.prepare(dummy_py)
            self.assertTrue(res.success)
            self.assertEqual(res.executable_path, dummy_py.resolve())
            self.assertTrue(res.cached)

            dummy_bin = tmp_path / "solution.exe"
            dummy_bin.write_text("mock")
            res_bin = CompilerManager.prepare(dummy_bin)
            self.assertEqual(res_bin.executable_path, dummy_bin.resolve())
            self.assertTrue(res_bin.cached)

            h1 = CompilerManager.get_source_hash(dummy_py)
            dummy_py.write_text("print('modified')\n")
            h2 = CompilerManager.get_source_hash(dummy_py)
            self.assertNotEqual(h1, h2)

    def test_compiler_clean_cache(self) -> None:
        CompilerManager.BUILD_DIR.mkdir(parents=True, exist_ok=True)
        dummy_file = CompilerManager.BUILD_DIR / "temp_test_artifact.tmp"
        dummy_file.write_text("test")
        cleaned = CompilerManager.clean_cache()
        self.assertGreaterEqual(cleaned, 1)
        self.assertFalse(dummy_file.exists())

    def test_security_compiler_flag_injection(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            CompilerManager.prepare("-fplugin=malicious.cpp")
        self.assertIn("leading dash", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
