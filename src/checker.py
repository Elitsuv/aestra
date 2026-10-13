from __future__ import annotations

import abc
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

_DEFAULT_MAX_DIFF_BYTES: int = 4096


class CheckerMode(str, Enum):
    EXACT = "EXACT"
    TOKEN = "TOKEN"
    IGNORE_WHITESPACE = "IGNORE_WHITESPACE"


@dataclass(frozen=True)
class CheckResult:
    """Immutable verdict result of an output evaluation."""

    is_correct: bool
    diff: str | None = None


class BaseChecker(abc.ABC):
    """Abstract interface defining the output validation contract."""

    @abc.abstractmethod
    def check(self, actual: str, expected: str) -> CheckResult:
        """Evaluate program output against expected output."""


class OutputChecker(BaseChecker):
    """Standard multi-mode output checker supporting EXACT, TOKEN, and IGNORE_WHITESPACE."""

    def __init__(
        self,
        mode: CheckerMode = CheckerMode.TOKEN,
        max_diff_bytes: int = _DEFAULT_MAX_DIFF_BYTES,
    ) -> None:
        self.mode = mode
        self.max_diff_bytes = max_diff_bytes

    def check(self, actual: str, expected: str) -> CheckResult:
        if self.mode == CheckerMode.EXACT:
            is_match = actual == expected
        elif self.mode == CheckerMode.IGNORE_WHITESPACE:
            is_match = actual.strip() == expected.strip()
        elif self.mode == CheckerMode.TOKEN:
            is_match = actual.split() == expected.split()
        else:
            raise ValueError(f"Unsupported CheckerMode: {self.mode}")

        if is_match:
            return CheckResult(is_correct=True)

        return CheckResult(is_correct=False, diff=self._build_diff(actual, expected))

    def _build_diff(self, actual: str, expected: str) -> str:
        exp_clean = expected.strip()
        act_clean = actual.strip()

        if len(exp_clean) > self.max_diff_bytes:
            exp_clean = f"{exp_clean[: self.max_diff_bytes]}... [TRUNCATED]"
        if len(act_clean) > self.max_diff_bytes:
            act_clean = f"{act_clean[: self.max_diff_bytes]}... [TRUNCATED]"

        return f"Expected:\n{exp_clean}\n\nActual:\n{act_clean}"


class FloatToleranceChecker(BaseChecker):
    """Validates numerical output within an absolute or relative epsilon tolerance."""

    def __init__(self, epsilon: float = 1e-4) -> None:
        self.epsilon = epsilon

    def check(self, actual: str, expected: str) -> CheckResult:
        act_tokens = actual.split()
        exp_tokens = expected.split()

        if len(act_tokens) != len(exp_tokens):
            return CheckResult(
                is_correct=False,
                diff=f"Token count mismatch: Expected {len(exp_tokens)}, got {len(act_tokens)}",
            )

        for idx, (a, e) in enumerate(zip(act_tokens, exp_tokens, strict=True)):
            try:
                a_val = float(a)
                e_val = float(e)
            except ValueError:
                if a != e:
                    return CheckResult(
                        is_correct=False,
                        diff=f"Token {idx} mismatch: Expected '{e}', got '{a}'",
                    )
                continue

            if abs(a_val - e_val) > self.epsilon:
                return CheckResult(
                    is_correct=False,
                    diff=f"Token {idx} outside epsilon {self.epsilon}: Expected {e_val}, got {a_val}",
                )

        return CheckResult(is_correct=True)


class CallableChecker(BaseChecker):
    """Wraps an arbitrary predicate or function for ad-hoc validation."""

    def __init__(self, fn: Callable[[str, str], bool | CheckResult]) -> None:
        self._fn = fn

    def check(self, actual: str, expected: str) -> CheckResult:
        res = self._fn(actual, expected)
        if isinstance(res, CheckResult):
            return res
        return CheckResult(is_correct=bool(res))
