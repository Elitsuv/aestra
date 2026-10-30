from __future__ import annotations

import abc
import itertools
import math
import re
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

_DEFAULT_MAX_DIFF: int = 4096
_TOKEN_RE = re.compile(r"\S+")


class CheckerMode(str, Enum):
    """Supported output comparison modes."""

    EXACT = "EXACT"
    TOKEN = "TOKEN"
    IGNORE_WHITESPACE = "IGNORE_WHITESPACE"


@dataclass(frozen=True, slots=True)
class CheckResult:
    """Outcome of an output verification check."""

    is_correct: bool
    diff: str | None = None


class BaseChecker(abc.ABC):
    """Abstract base class for output checkers."""

    @abc.abstractmethod
    def check(self, actual: str, expected: str) -> CheckResult:
        """Compares actual output against expected output."""
        ...


class OutputChecker(BaseChecker):
    """Standard differential output checker with whitespace and token modes."""

    __slots__ = ("max_diff", "mode")

    def __init__(
        self,
        mode: CheckerMode = CheckerMode.TOKEN,
        max_diff_bytes: int = _DEFAULT_MAX_DIFF,
    ) -> None:
        self.mode = mode
        self.max_diff = max_diff_bytes

    def check(self, actual: str, expected: str) -> CheckResult:
        match self.mode:
            case CheckerMode.EXACT:
                matched = actual == expected
            case CheckerMode.IGNORE_WHITESPACE:
                matched = actual.strip() == expected.strip()
            case CheckerMode.TOKEN:
                sentinel = object()
                it_a = (m.group() for m in _TOKEN_RE.finditer(actual))
                it_e = (m.group() for m in _TOKEN_RE.finditer(expected))
                matched = all(
                    a == e
                    for a, e in itertools.zip_longest(it_a, it_e, fillvalue=sentinel)
                )
            case _:
                raise ValueError(f"Unsupported CheckerMode: {self.mode}")

        return (
            CheckResult(True)
            if matched
            else CheckResult(False, self._diff(actual, expected))
        )

    def _diff(self, actual: str, expected: str) -> str:
        exp, act = expected.strip(), actual.strip()
        if len(exp) > self.max_diff:
            exp = f"{exp[: self.max_diff]}... [TRUNCATED]"
        if len(act) > self.max_diff:
            act = f"{act[: self.max_diff]}... [TRUNCATED]"
        return f"Expected:\n{exp}\n\nActual:\n{act}"


class FloatToleranceChecker(BaseChecker):
    """Numerical output checker allowing relative or absolute epsilon tolerance."""

    __slots__ = ("epsilon",)

    def __init__(self, epsilon: float = 1e-4) -> None:
        self.epsilon = epsilon

    def check(self, actual: str, expected: str) -> CheckResult:
        it_a = (m.group() for m in _TOKEN_RE.finditer(actual))
        it_e = (m.group() for m in _TOKEN_RE.finditer(expected))
        sentinel = object()

        for idx, (a, e) in enumerate(
            itertools.zip_longest(it_a, it_e, fillvalue=sentinel)
        ):
            if not isinstance(a, str) or not isinstance(e, str):
                return CheckResult(False, f"Token count mismatch at index {idx}")
            try:
                a_val, e_val = float(a), float(e)
                if math.isnan(a_val) or math.isnan(e_val):
                    if not (math.isnan(a_val) and math.isnan(e_val)):
                        return CheckResult(
                            False, f"Token {idx} NaN mismatch: Expected {e}, got {a}"
                        )
                    continue

                if math.isinf(a_val) or math.isinf(e_val):
                    if a_val != e_val:
                        return CheckResult(
                            False,
                            f"Token {idx} infinite mismatch: Expected {e}, got {a}",
                        )
                    continue

                diff = abs(a_val - e_val)
                if diff > self.epsilon:
                    # Also check relative tolerance for large floating-point numbers
                    rel_tol = self.epsilon * max(abs(a_val), abs(e_val))
                    if diff > rel_tol:
                        return CheckResult(
                            False,
                            f"Token {idx} outside epsilon {self.epsilon}: Expected {e}, got {a}",
                        )
            except (ValueError, OverflowError):
                if a != e:
                    return CheckResult(
                        False, f"Token {idx} mismatch: Expected '{e}', got '{a}'"
                    )

        return CheckResult(True)


class CallableChecker(BaseChecker):
    """Custom verification wrapper around user-defined predicate functions."""

    __slots__ = ("_fn",)

    def __init__(self, fn: Callable[[str, str], bool | CheckResult]) -> None:
        self._fn = fn

    def check(self, actual: str, expected: str) -> CheckResult:
        res = self._fn(actual, expected)
        return res if isinstance(res, CheckResult) else CheckResult(bool(res))
