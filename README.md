# Aestra
Deterministic local judge, concurrent fuzzer, and test-case minimizer with microsecond kernel telemetry.

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CI](https://github.com/Elitsuv/aestra/actions/workflows/ci.yml/badge.svg)](https://github.com/Elitsuv/aestra/actions/workflows/ci.yml)

---

## Problem

Local code runners and test harnesses fail competitive programmers and systems engineers in three fundamental ways:

1. **Jitter & Inaccurate Telemetry**: Measuring execution with naive wall-clock timers (`time.time()` or shell `time`) includes operating system scheduling jitter, paging latency, and background system interference. Solutions pass locally only to fail with Time Limit Exceeded (TLE) on online judges.
2. **Missing Memory Enforcement**: Standard subprocess runners cannot track peak working-set RAM or enforce hard limits. Memory allocation spikes and leaks go completely undetected until a remote platform issues Memory Limit Exceeded (MLE).
3. **Leaked Processes & Inefficient Debugging**: Subprocess timeouts frequently leave orphan child processes executing in the background, skewing subsequent runs. When differential stress testing does find a failure, the input is typically thousands of lines of noise, forcing tedious manual reduction.

---

## Solution

Aestra provides deterministic local judgment by decoupling execution telemetry from host jitter and enforcing hardware-level constraints directly:

- **Microsecond Kernel Telemetry**: Measures actual user and kernel CPU time down to microseconds (`rusage` on POSIX systems, `K32GetProcessMemoryInfo` on Windows), completely isolating benchmarks from OS scheduling anomalies.
- **Hardware-Enforced Resource Constraints**: Imposes hard limits on CPU duration, peak memory address space (`RLIMIT_AS`), and maximum output volume. Violating allocations trigger immediate termination.
- **Tree-Scoped Process Isolation**: Executes all targets in isolated sessions, ensuring full tree termination on timeout or failure with zero orphaned zombie processes.
- **Concurrent Fuzzing & Hierarchical Minimization**: Multi-threaded fuzzing stress-tests targets against an oracle at scale. When a failure is detected, an automated hierarchical delta-debugging (DDmin) engine shrinks the counterexample to its minimal irreducible reproduction.
- **Universal Dual-Engine Architecture**: Employs a compiled Rust core via PyO3 for zero-overhead POSIX isolation, alongside an immediate zero-compiler fallback that provides native kernel memory telemetry on Windows without requiring a C++ or Rust toolchain.

---

## Features

- **Hardware-enforced CPU and memory limits**: Enforces CPU timeouts and peak RAM quotas with hard OS-level termination.
- **Microsecond-resolution telemetry**: Reports exact process CPU runtime and peak physical memory consumption.
- **Concurrent fuzzing + delta-debugging minimizer**: High-throughput multi-threaded randomized stress testing paired with automated line- and token-level input minimization.
- **Multi-language support with caching**: Native zero-configuration compilation for C++, C, Rust, and Go with SHA-256 binary caching, plus direct execution for Python.
- **Interactive CLI + Python SDK**: Features both a terminal interface and a scriptable Python SDK for CI/CD and custom judges.
- **Cross-platform (native + fallback)**: High-performance Rust PyO3 core for POSIX systems and pure kernel API querying on Windows.

---

## Installation

### Windows (Native MSI Installer)

Download the latest `Aestra-Setup.msi` from [Releases](https://github.com/Elitsuv/aestra/releases).

Double-click to install. The installer registers `aestra` on your system `PATH`, adds a desktop shortcut, and enables clean 1-click uninstallation from Windows Settings. Upgrades are seamless: installing a newer `.msi` replaces prior versions automatically via Windows MSI `MajorUpgrade`.

Alternatively, install via Windows Package Manager:
```powershell
winget install Aestra.Aestra
```

### Manual / Cross-Platform Setup

Requirements: Python 3.10+ (and optionally Rust 1.75+ for the POSIX native core).

```bash
git clone https://github.com/Elitsuv/aestra.git
cd aestra

# Install directly in editable mode
pip install -e .

# Or build the native Rust extension (POSIX)
pip install maturin
maturin develop
```

Verify the installation:

```bash
aestra doctor
```

---

## Quick Start

### 1. Execute a Single Solution with Telemetry

Run any source file (`.cpp`, `.py`, `.rs`, `.go`) or compiled binary under strict resource constraints:

```bash
aestra run solution.cpp --time-limit 1000 --memory-limit 256
```

Output:
```text
  +-- [Telemetry] ----------------------------------------------+
  |  Status     : OK                                             |
  |  CPU Time   : 14.2ms                                         |
  |  Peak Memory: 3.1MB                                          |
  |  Exit Code  : 0                                              |
  +-------------------------------------------------------------+
```

### 2. Batch Test Suite Evaluation

Test your solution against a directory containing matching `*.in` and `*.out` (or `*.ans`) files:

```bash
aestra test solution.py --cases ./cases --mode token
```

Output:
```text
  +-- [Batch Runner] -------------------------------------------+
  |  Binary : solution.py                                      |
  |  Cases  : 3 testcases from cases/                          |
  |  Limits : 2000ms CPU, 512MB RAM                            |
  +-------------------------------------------------------------+

  [ACCEPTED]                01.in              18.4ms    9.8MB
  [ACCEPTED]                02.in              16.1ms    9.7MB
  [WRONG_ANSWER]            03.in              17.9ms    9.9MB
      Expected:
      42
      Actual:
      0

  =============================================================
  Summary: 2/3 accepted (FAILED) * 52.4ms * 9.9MB
  =============================================================
```

### 3. Concurrent Fuzzing & Automated Minimization

Stress-test a solution against a reference oracle across multiple worker threads and automatically minimize counterexamples:

```bash
aestra fuzz solution.py --oracle reference.py --iterations 500 --workers 4 --minimize
```

When a divergence occurs, Aestra reports the failure and minimizes the input:
```text
  +-- [Concurrent Fuzzer] --------------------------------------+
  |  Target     : solution.py                                   |
  |  Oracle     : reference.py                                  |
  |  Iterations : 500                                           |
  |  Workers    : 4                                             |
  +-------------------------------------------------------------+

  [BUG DISCOVERED] at iteration 84!
  Error: Wrong Answer: Output mismatch.

  [Minimizing] Delta-debugging failing input...
  [Minimization complete]

[Minimal Reproducible Input]
-1
```

### 4. Interactive Terminal Shell

Launch the interactive console dashboard by running `aestra` without arguments:

```bash
aestra
```

---

## Python SDK

Aestra provides a programmatic API for integrating local judging, fuzzing, and minimization into custom pipelines.

```python
from src import (
    CheckerMode,
    Config,
    ExecutionStatus,
    Fuzzer,
    Judge,
    Minimizer,
    TestCase,
)

# 1. Run a single execution under strict limits
judge = Judge(config=Config(time_limit_ms=1000, memory_limit_mb=256))
result = judge.run_single("solution.py", input_data="10 20\n")

if result.is_success:
    print(
        f"Output: {result.stdout.strip()} ({result.cpu_time_ms:.1f}ms, {result.peak_memory_mb:.1f}MB)"
    )

# 2. Evaluate batch test cases (directory or in-memory)
batch = judge.run("solution.py", cases_dir="./cases")
print(f"Verdict: {batch.overall_verdict} ({batch.passed}/{batch.total} passed)")


# 3. Concurrent fuzzing against an oracle function or binary
def brute_force_oracle(inp: str) -> str:
    nums = [int(x) for x in inp.split()]
    return str(sum(nums))


fuzzer = Fuzzer(
    target_binary="solution.py",
    oracle=brute_force_oracle,
    config=Config(time_limit_ms=500),
)
report = fuzzer.run(iterations=200, workers=4)

if report.found_bug:
    print(f"Divergence found on input: {report.failing_input}")

    # 4. Minimize failing input using delta debugging
    minimizer = Minimizer(target_binary="solution.py", oracle=brute_force_oracle)
    minimal_input = minimizer.minimize(report.failing_input)
    print(f"Minimal reproduction: {minimal_input}")
```

---

## License

Distributed under the [MIT License](LICENSE).
