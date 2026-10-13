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
    EXACT = "EXACT"
    TOKEN = "TOKEN"
    IGNORE_WHITESPACE = "IGNORE_WHITESPACE"


@dataclass(frozen=True, slots=True)
class CheckResult:
    is_correct: bool
    diff: str | None = None


class BaseChecker(abc.ABC):
    @abc.abstractmethod
    def check(self, actual: str, expected: str) -> CheckResult: ...


class OutputChecker(BaseChecker):
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
                if (
                    math.isnan(a_val)
                    or math.isnan(e_val)
                    or abs(a_val - e_val) > self.epsilon
                ):
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
    __slots__ = ("_fn",)

    def __init__(self, fn: Callable[[str, str], bool | CheckResult]) -> None:
        self._fn = fn

    def check(self, actual: str, expected: str) -> CheckResult:
        res = self._fn(actual, expected)
        return res if isinstance(res, CheckResult) else CheckResult(bool(res))
