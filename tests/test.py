from __future__ import annotations

import sys
import unittest
from collections.abc import Callable

from tests.test_checker import CheckerTests
from tests.test_cli import CLITests
from tests.test_compiler import CompilerTests
from tests.test_config import ConfigTests
from tests.test_engine import EngineTests
from tests.test_fuzzer import FuzzerTests
from tests.test_minimizer import MinimizerTests
from tests.test_runner import RunnerTests

TEST_CLASSES: list[type[unittest.TestCase]] = [
    EngineTests,
    CheckerTests,
    RunnerTests,
    FuzzerTests,
    MinimizerTests,
    CompilerTests,
    ConfigTests,
    CLITests,
]


def _build_test_list() -> list[tuple[str, Callable[[], None]]]:
    tests: list[tuple[str, Callable[[], None]]] = []
    for test_cls in TEST_CLASSES:
        for attr in dir(test_cls):
            if attr.startswith("test_"):
                inst = test_cls(attr)
                readable_name = f"{test_cls.__name__}.{attr}"
                tests.append((readable_name, getattr(inst, attr)))
    return tests


ALL_TESTS = _build_test_list()


def run_all() -> int:
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for test_cls in TEST_CLASSES:
        suite.addTests(loader.loadTestsFromTestCase(test_cls))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_all())
