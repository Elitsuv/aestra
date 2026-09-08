import sys
from pathlib import Path

from src.config import ExecutionLimits
from src.engine import BaseEngine, SubprocessEngine, get_engine
from src.models import ExecutionStatus


def test_get_engine_returns_base_engine():
    engine = get_engine()
    assert isinstance(engine, BaseEngine)


def test_subprocess_engine_success():
    engine = SubprocessEngine()
    limits = ExecutionLimits(time_limit_ms=2000, memory_limit_mb=128)
    res = engine.execute(
        Path(sys.executable),
        limits,
        args=["-c", "import sys; sys.stdout.write('hello aestra')"],
    )
    assert res.status == ExecutionStatus.OK
    assert res.stdout == "hello aestra"
    assert res.exit_code == 0


def test_subprocess_engine_timeout():
    engine = SubprocessEngine()
    limits = ExecutionLimits(time_limit_ms=200, memory_limit_mb=128)
    res = engine.execute(
        Path(sys.executable),
        limits,
        args=["-c", "import time; time.sleep(1.0)"],
    )
    assert res.status == ExecutionStatus.TIME_LIMIT_EXCEEDED
    assert res.exit_code == -1
