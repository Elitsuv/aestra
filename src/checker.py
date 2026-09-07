from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CheckerMode(str, Enum):
    EXACT = "EXACT"
    TOKEN = "TOKEN"
    IGNORE_WHITESPACE = "IGNORE_WHITESPACE"


@dataclass
class CheckResult:
    is_correct: bool
    diff: str | None = None


class OutputChecker:
    def __init__(self, mode: CheckerMode = CheckerMode.TOKEN) -> None:
        self.mode = mode

    def check(self, actual: str, expected: str) -> CheckResult:
        if self.mode == CheckerMode.EXACT:
            matched = actual == expected
        elif self.mode == CheckerMode.IGNORE_WHITESPACE:
            matched = actual.strip() == expected.strip()
        elif self.mode == CheckerMode.TOKEN:
            matched = actual.split() == expected.split()
        else:
            matched = False

        if matched:
            return CheckResult(is_correct=True)

        diff = f"Expected:\n{expected.strip()}\n\nActual:\n{actual.strip()}"
        return CheckResult(is_correct=False, diff=diff)
