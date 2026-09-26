"""Aestra CP Demo Solution.

Problem: Given a sequence of integers, calculate their sum and maximum value.
Input:  Arbitrary whitespace-separated integers via standard input.
Output: Sum and maximum value formatted as:
        SUM: <sum> | MAX: <max>
"""

from __future__ import annotations

import sys


def solve() -> None:
    raw_input = sys.stdin.read().split()
    if not raw_input:
        print("SUM: 0 | MAX: 0")
        return

    numbers: list[int] = []
    for token in raw_input:
        try:
            numbers.append(int(token))
        except ValueError:
            # Handle non-integer tokens safely during fuzzing
            pass

    if not numbers:
        print("SUM: 0 | MAX: 0")
        return

    total_sum = sum(numbers)
    max_val = max(numbers)
    print(f"SUM: {total_sum} | MAX: {max_val}")


if __name__ == "__main__":
    solve()
