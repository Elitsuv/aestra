from __future__ import annotations

import unittest

from src.checker import (
    CallableChecker,
    CheckerMode,
    CheckResult,
    FloatToleranceChecker,
    OutputChecker,
)


class CheckerTests(unittest.TestCase):
    def test_checker_token_whitespace(self) -> None:
        checker = OutputChecker(CheckerMode.TOKEN)
        result = checker.check("1 2 3\n", "1  2  3")
        self.assertTrue(result.is_correct)
        self.assertIsNone(result.diff)

    def test_checker_token_mismatch(self) -> None:
        checker = OutputChecker(CheckerMode.TOKEN)
        result = checker.check("1 2 4", "1 2 3")
        self.assertFalse(result.is_correct)
        self.assertIsNotNone(result.diff)
        self.assertIn("Expected:\n1 2 3", result.diff or "")

    def test_checker_exact_strictness(self) -> None:
        checker = OutputChecker(CheckerMode.EXACT)
        self.assertFalse(checker.check("hello\n", "hello").is_correct)
        self.assertTrue(checker.check("hello\n", "hello\n").is_correct)

    def test_checker_ignore_whitespace(self) -> None:
        checker = OutputChecker(CheckerMode.IGNORE_WHITESPACE)
        self.assertTrue(checker.check("  hello world  \n", "hello world").is_correct)
        self.assertFalse(checker.check("hello", "world").is_correct)

    def test_checker_diff_truncation(self) -> None:
        checker = OutputChecker(mode=CheckerMode.EXACT, max_diff_bytes=20)
        actual = "A" * 100
        expected = "B" * 100
        res = checker.check(actual, expected)
        self.assertFalse(res.is_correct)
        self.assertIsNotNone(res.diff)
        self.assertIn("[TRUNCATED]", res.diff or "")
        self.assertLess(len(res.diff or ""), 200)

    def test_float_tolerance_checker_success(self) -> None:
        checker = FloatToleranceChecker(epsilon=0.01)
        res = checker.check("3.1415 2.718", "3.1420 2.710")
        self.assertTrue(res.is_correct)
        self.assertIsNone(res.diff)

    def test_float_tolerance_checker_failure(self) -> None:
        checker = FloatToleranceChecker(epsilon=0.001)
        res = checker.check("3.1415 2.718", "3.1500 2.718")
        self.assertFalse(res.is_correct)
        self.assertIn("outside epsilon", res.diff or "")

    def test_float_tolerance_checker_tokens(self) -> None:
        checker = FloatToleranceChecker(epsilon=0.01)
        res_len = checker.check("1.0 2.0", "1.0")
        self.assertFalse(res_len.is_correct)
        self.assertIn("Token count mismatch", res_len.diff or "")

        res_str_ok = checker.check("1.0 YES", "1.0 YES")
        self.assertTrue(res_str_ok.is_correct)

        res_str_fail = checker.check("1.0 NO", "1.0 YES")
        self.assertFalse(res_str_fail.is_correct)
        self.assertIn("Token 1 mismatch", res_str_fail.diff or "")

    def test_float_tolerance_checker_nan_and_inf(self) -> None:
        checker = FloatToleranceChecker(epsilon=1e-4)
        self.assertTrue(checker.check("nan", "nan").is_correct)
        self.assertFalse(checker.check("nan", "1.0").is_correct)
        self.assertTrue(checker.check("inf", "inf").is_correct)
        self.assertTrue(checker.check("-inf", "-inf").is_correct)
        self.assertFalse(checker.check("inf", "-inf").is_correct)
        self.assertFalse(checker.check("inf", "1e9").is_correct)

    def test_callable_checker(self) -> None:
        bool_checker = CallableChecker(
            lambda act, exp: act.strip().lower() == exp.strip().lower()
        )
        self.assertTrue(bool_checker.check("HELLO", "hello").is_correct)
        self.assertFalse(bool_checker.check("WORLD", "hello").is_correct)

        custom_checker = CallableChecker(
            lambda act, exp: (
                CheckResult(is_correct=False, diff="Custom reason")
                if "bad" in act
                else CheckResult(is_correct=True)
            )
        )
        self.assertFalse(custom_checker.check("bad input", "any").is_correct)
        self.assertEqual(custom_checker.check("bad input", "any").diff, "Custom reason")
        self.assertTrue(custom_checker.check("good input", "any").is_correct)


if __name__ == "__main__":
    unittest.main()
