<p align="left">
  <img src="assets/aestra.png" width="70" alt="Aestra Logo" align="left" style="margin-right: 15px;">
  <strong><font size="6">Aestra</font></strong><br>
  <a href="https://github.com/Elitsuv/aestra/releases"><img src="https://img.shields.io/badge/version-v0.1.2-blue.svg" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
  <a href="https://github.com/Elitsuv/aestra/actions/workflows/ci.yml"><img src="https://github.com/Elitsuv/aestra/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://elitsuv.github.io/aestra/"><img src="https://img.shields.io/badge/docs-live-cyan.svg" alt="Docs"></a>
</p>

<br><br>

**Aestra** is a deterministic execution sandbox and competitive programming testing engine designed to enforce hardware constraints—CPU time and peak memory limits—with microsecond accuracy.

Built with a low-overhead **Rust POSIX kernel core**, a universal cross-platform fallback, an automated **differential output checker**, and a terminal CLI.

[Read the Full Documentation & Guides](https://elitsuv.github.io/aestra/)

> [!WARNING]
> **Active Development & Sandboxing Notice**: Aestra is currently in active development (`v0.1.x`). While hardware resource limits (CPU timeouts, memory bounds, and wall-clock watchdogs) are enforced, Aestra runs in user space and is designed for **local competitive programming benchmarking and testcase verification**. It should not be deployed as an uncontained multi-tenant public judge for untrusted or hostile code without additional containerized isolation (e.g Docker, cgroups v2, or dedicated VMs).

---

## Quickstart

Install Aestra globally with a single command (no admin privileges or Rust compiler required):

### Windows (PowerShell)
```powershell
iex (irm https://raw.githubusercontent.com/Elitsuv/aestra/main/scripts/install.ps1)
```

### Linux / macOS (Bash)
```bash
curl -sSL https://raw.githubusercontent.com/Elitsuv/aestra/main/scripts/install.sh | bash
```

Once installed, the `aestra` command is available globally in any terminal:
```bash
aestra --help
```

---

## CLI Usage

### Batch Testcase Runner

Run a solution against a directory of `.in` and `.out` / `.ans` test pairs:

```bash
aestra test solution.py --cases testcases/
```

### Single Program Execution with Live Telemetry

Benchmark a binary or script under strict hardware limits:

```bash
aestra run ./solution.exe --time-limit 1000 --memory-limit 256
```

For advanced CLI options, checker modes (`token`, `exact`, `ignore_whitespace`), and telemetry details, visit the [Full Documentation](https://elitsuv.github.io/aestra/#test).

---

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

Run the complete 23-test engine suite:

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
