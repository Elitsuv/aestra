<p align="left">
  <img src="assets/aestra.png" width="70" alt="Aestra Logo" align="left" style="margin-right: 15px;">
  <strong><font size="6">Aestra</font></strong><br>
  <a href="https://github.com/Elitsuv/aestra/releases"><img src="https://img.shields.io/badge/version-v1.0.0-blue.svg" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
  <a href="https://github.com/Elitsuv/aestra/actions/workflows/ci.yml"><img src="https://github.com/Elitsuv/aestra/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://elitsuv.github.io/aestra/"><img src="https://img.shields.io/badge/docs-live-cyan.svg" alt="Docs"></a>
</p>

<br><br>

**Aestra** is a deterministic execution sandbox and competitive programming testing engine designed to enforce hardware constraints—CPU time and peak memory limits—with microsecond accuracy.

Built with a low-overhead **Rust POSIX kernel core**, a universal cross-platform fallback, an automated **differential output checker**, multi-language compilation with incremental caching (C++, C, Rust, Go, Python), an extensible **plugin system**, and an interactive terminal CLI.

[Read the Full Documentation & Guides](https://elitsuv.github.io/aestra/)

> [!NOTE]
> **v1.0.0 Stable Launch (Windows)**: Aestra is built specifically for Windows. **You DO NOT need Rust, MSVC, or any C++ compiler to run Aestra.** Standard Python 3.10+ is all that is required. The universal `SubprocessEngine` directly queries Windows kernel memory via `K32GetProcessMemoryInfo` for microsecond peak RAM and execution tracking with zero host pollution.

---

## 1-Click Installation (Windows Only)

Install Aestra in seconds with the graphical Setup Wizard (**Zero Rust or compilers required**):

### Method A: Graphical Wizard (Double-Click)
If you downloaded or extracted Aestra, double-click [`install.bat`](file:///c:/Users/jeezh/OneDrive/Desktop/aestra/aestra/install.bat) in the root folder.
- Launches a native Windows Setup Wizard window with the branded **Aestra App Icon**
- Adds `aestra` permanently to your User `PATH` (no admin rights needed)
- Creates an **Aestra** Desktop shortcut
- Verifies your environment automatically

### Method B: PowerShell One-Liner
```powershell
iex (irm https://raw.githubusercontent.com/Elitsuv/aestra/main/scripts/install.ps1)
```

Once installed, open **any** terminal and run:
```bash
aestra
```

---

## Interactive AI-CLI Window

When you type `aestra` in your terminal without flags, Aestra opens an interactive console window:

```text
  +-------------------------------------------------------------+
  |  AESTRA  *  Deterministic CP Execution Sandbox     v1.0.0  |
  |  Microsecond telemetry * Multi-language * Zero PC footprint |
  +-------------------------------------------------------------+

  [1] Run Solution      - Execute source or binary with microsecond telemetry
  [2] Batch Test Suite  - Test solution against .in / .out cases directory
  [3] Stress & Fuzz     - Automated randomized fuzzing against edge cases
  [4] System Doctor     - Inspect system compilers and environment health
  [5] Clean Cache       - Wipe local compilation artifacts (.aestra/build)
  [0] Exit              - Quit Aestra

  aestra> 
```

---

## CLI Commands

You can also use Aestra directly as a scriptable command-line utility:

### Batch Testcase Runner

Run a solution (supports `.cpp`, `.rs`, `.go`, `.py`, or `.exe`) against a directory of `.in` and `.out` / `.ans` test pairs:

```bash
aestra test solution.cpp --cases testcases/
```

### Single Program Execution with Live Telemetry

Benchmark a binary or script under strict hardware limits:

```bash
aestra run ./solution.cpp --time-limit 1000 --memory-limit 256
```

### System Toolchain Doctor

Inspect your active execution engine and detected compilers:

```bash
aestra doctor
```

## Python SDK

Aestra provides a programmatic Python SDK designed for automated testing pipelines, custom judge platforms, stress-testing harnesses, and testcase reduction.

Import the SDK interfaces directly:

```python
from aestra import (
    CheckerMode,
    Config,
    ExecutionStatus,
    Fuzzer,
    Judge,
    Minimizer,
    TestCase,
)
```

---

### Programmatic Judge (`Judge`)

The `Judge` class provides single-binary execution and automated batch evaluation under hardware constraints.

#### 1. Single Execution with Resource Telemetry

Execute a target binary or script once with standard input and inspect CPU and memory telemetry:

```python
from aestra import Config, Judge

# Initialize judge with custom resource limits
config = Config(time_limit_ms=1000, memory_limit_mb=256)
judge = Judge(config=config)

# Run target program
result = judge.run_single("solution.py", input_data="42 58\n")

print(f"Status     : {result.status.value}")
print(f"CPU Time   : {result.cpu_time_ms:.2f} ms")
print(f"Peak Memory: {result.peak_memory_mb:.2f} MB")
print(f"Output     : {result.stdout.strip()}")
```

#### 2. Evaluating Against a Testcase Directory

Evaluate a solution across a directory containing `.in` and `.out` / `.ans` pairs:

```python
from aestra import Config, Judge

judge = Judge(config=Config(time_limit_ms=2000, memory_limit_mb=512))
batch = judge.run("solution.py", cases_dir="./testcases")

print(f"Verdict: {batch.overall_verdict} ({batch.passed}/{batch.total} passed)")
for test in batch.results:
    print(
        f"  [{test.verdict:<14}] {test.case_name:<15} {test.cpu_time_ms:.1f}ms  {test.peak_memory_mb:.1f}MB"
    )
```

#### 3. In-Memory Test Suites

Evaluate test cases defined dynamically in code without creating temporary files:

```python
from aestra import Judge, TestCase

judge = Judge()
cases = [
    TestCase(name="sample_1", input_data="3 5\n", expected_output="8\n"),
    TestCase(name="sample_2", input_data="10 -4\n", expected_output="6\n"),
]

batch = judge.run("solution.py", test_cases=cases)
print(f"Passed {batch.passed} of {batch.total} tests.")
```

---

### Automated Fuzzing & Differential Testing (`Fuzzer`)

The `Fuzzer` generates randomized inputs to identify edge cases, timeouts, host resource exhaustion, or logic divergences.

#### 1. Crash & Timeout Detection

Stress-test a solution to verify it terminates safely without runtime errors or resource limit breaches:

```python
from aestra import Config, Fuzzer

fuzzer = Fuzzer(
    target_binary="solution.py",
    config=Config(time_limit_ms=500, memory_limit_mb=128),
)

report = fuzzer.run(iterations=500)
if report.found_bug:
    print(f"Bug discovered on iteration {report.iterations_run}:")
    print(f"Error: {report.error_message}")
    print(f"Failing Input:\n{report.failing_input}")
else:
    print(f"All {report.iterations_run} fuzz iterations passed.")
```

#### 2. Differential Testing Against an Oracle

Compare outputs against a trusted reference binary or Python function:

```python
from aestra import Fuzzer


# Trusted reference solution (e.g. brute-force or Python model)
def reference_oracle(input_str: str) -> str:
    nums = [int(x) for x in input_str.split() if x.strip()]
    return str(sum(nums))


# Custom input generator for stress testing
def generate_random_case(iteration: int) -> str:
    import random

    n = random.randint(1, 50)
    vals = [str(random.randint(-1000, 1000)) for _ in range(n)]
    return f"{n}\n" + " ".join(vals) + "\n"


fuzzer = Fuzzer(
    target_binary="optimized_solution.exe",
    oracle=reference_oracle,
    generator=generate_random_case,
)

report = fuzzer.run(iterations=250)
if report.found_bug:
    print("Divergence identified!")
    print(f"Failing input: {report.failing_input}")
    print(f"Details: {report.error_message}")
```

---

### Delta-Debugging Testcase Minimizer (`Minimizer`)

When fuzzing uncovers a failure with a large input, `Minimizer` uses hierarchical Delta Debugging (DDmin) across line and token granularities to shrink the input to the smallest reproducible failure:

```python
from aestra import Minimizer


def reference_oracle(input_str: str) -> str:
    nums = [int(x) for x in input_str.split() if x.strip()]
    return str(sum(nums))


minimizer = Minimizer(
    target_binary="solution.py",
    oracle=reference_oracle,
)

large_failing_input = "50\n" + " ".join(str(i) for i in range(500)) + "\n"

# Reduces multi-line and multi-token inputs down to minimal reproduction
minimal_input = minimizer.minimize(large_failing_input, max_steps=200)

print("Minimal reproducible input:")
print(minimal_input)
```

---

### Configuration & TOML Integration (`Config`)

Aestra configuration can be defined programmatically or loaded directly from an `aestra.toml` file:

```python
from aestra import CheckerMode, Config, Judge

# Programmatic configuration
config = Config(
    time_limit_ms=1500,
    memory_limit_mb=256,
    checker_mode=CheckerMode.TOKEN,  # TOKEN, EXACT, IGNORE_WHITESPACE
    output_limit_bytes=10 * 1024 * 1024,  # Maximum captured output bytes
)

# Or load from an aestra.toml file
config_from_file = Config.from_toml("aestra.toml")

judge = Judge(config=config_from_file)
```

---

## Development & Testing

Run the complete 27-test unified suite:

```bash
python -m tests.test
```

Verify code quality with strict type checking and linting:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy src
```

---

## License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.

