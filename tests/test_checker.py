from src.checker import CheckerMode, OutputChecker


def test_token_checker_matches_whitespace():
    checker = OutputChecker(CheckerMode.TOKEN)
    result = checker.check("1 2 3\n", "1  2  3")
    assert result.is_correct is True
    assert result.diff is None


def test_token_checker_detects_mismatch():
    checker = OutputChecker(CheckerMode.TOKEN)
    result = checker.check("1 2 4", "1 2 3")
    assert result.is_correct is False
    assert result.diff is not None
    assert "Expected:\n1 2 3" in result.diff


def test_exact_checker_strictness():
    checker = OutputChecker(CheckerMode.EXACT)
    result = checker.check("hello\n", "hello")
    assert result.is_correct is False