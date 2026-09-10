<p align="left">
  <img src="assets/aestra.png" width="70" alt="Aestra Logo" align="left" style="margin-right: 15px;">
  <strong><font size="6">Aestra</font></strong><br>
  <a href="https://github.com/Elitsuv/aestra/releases"><img src="https://img.shields.io/badge/version-v0.1.1-blue.svg" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
  <a href="https://github.com/Elitsuv/aestra/actions/workflows/ci.yml"><img src="https://github.com/Elitsuv/aestra/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://elitsuv.github.io/aestra/"><img src="https://img.shields.io/badge/docs-live-cyan.svg" alt="Docs"></a>
</p>

<br><br>

**Aestra** is a deterministic execution sandbox and competitive programming testing engine designed to enforce hardware-level constraints—CPU time and peak memory limits—with microsecond accuracy.

Built with a low-overhead **Rust POSIX kernel core**, a universal cross-platform fallback, an **ICPC-grade differential output checker**, and a modern **terminal CLI**.

📖 **[Read the Full Documentation & Guides](https://elitsuv.github.io/aestra/)**

---

## ⚡ Quickstart

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

## 🎯 Competitive Programming User Guide

Aestra is built from the ground up to test competitive programming solutions (Python, C++, Rust, Go) against directories of test cases.

### 1. Write Your Solution

Create your problem solution (e.g., `solution.py` or compiled `solution.exe`):

**Example: A + B Problem (`solution.py`)**
```python
import sys

for line in sys.stdin:
    if line.strip():
        a, b = map(int, line.split())
        print(a + b)
```

*(For C++, compile first: `g++ -O3 solution.cpp -o solution.exe`)*

### 2. Prepare Test Cases

Organize your test cases in a folder with matching `.in` (inputs) and `.out` or `.ans` (expected outputs):

```text
testcases/
├── case1.in       # Content: 3 5
├── case1.out      # Content: 8
├── case2.in       # Content: 100 250
├── case2.out      # Content: 350
├── case3.in       # Content: -10 25
└── case3.out      # Content: 15
```

### 3. Run the Batch Judge

Run Aestra against your solution:

```bash
aestra test solution.py --cases testcases/
```

**Real Terminal Output:**
```text
  +-- [Batch Runner] -------------------------------------------+
  |  Binary : solution.py                                       |
  |  Cases  : 3 testcases from testcases/                       |
  |  Limits : 2000ms CPU, 512MB RAM                             |
  +-------------------------------------------------------------+

  [ACCEPTED]               case1.in             55.9ms    0.0MB
  [ACCEPTED]               case2.in             45.8ms    0.0MB
  [ACCEPTED]               case3.in             44.3ms    0.0MB

  =============================================================
  Summary: 3/3 accepted (ALL PASSED) * 146.0ms * 0.0MB
  =============================================================
```

---

### 4. Catching Bugs & Wrong Answers (`WA`)

If your solution produces incorrect output, Aestra immediately pinpoints the mismatch:

```text
  [WRONG_ANSWER]           case2.in             42.1ms    0.0MB
      Expected:
      350
      Got:
      25000
```

---

## 🔍 Single Program Execution with Live Telemetry

To benchmark a single binary or script under strict hardware limits:

```bash
aestra run ./solution.exe --time-limit 1000 --memory-limit 256
```

**Telemetry Output:**
```text
  +-- [Telemetry] ----------------------------------------------+
  |  Status     : OK                                             |
  |  CPU Time   : 64.6ms                                         |
  |  Peak Memory: 12.4MB                                         |
  |  Exit Code  : 0                                              |
  +-------------------------------------------------------------+
```

---

## ⚙️ Output Checker Modes

Configure how outputs are compared with the `--mode` flag:

| Mode | Flag | Description | Parity |
| :--- | :--- | :--- | :--- |
| **Token** *(default)* | `--mode token` | Compares whitespace-separated tokens. Ignores extra spaces and blank lines. | Codeforces / ICPC standard |
| **Exact** | `--mode exact` | Strict byte-by-byte comparison including exact newlines and whitespace. | Strict diff |
| **Ignore Whitespace** | `--mode ignore_whitespace` | Strips all leading, trailing, and redundant whitespace. | Lenient grading |

---

## 🐍 Python SDK

You can also embed Aestra into automated contest runners or grading bots:

```python
from pathlib import Path
from src import ExecutionLimits, get_engine, BatchRunner, OutputChecker, CheckerMode

# 1. Single execution
engine = get_engine()
result = engine.execute(
    Path("./solution.py"),
    limits=ExecutionLimits(time_limit_ms=1000, memory_limit_mb=256),
    input_data="10 20\n",
)
print(f"Status: {result.status} | Time: {result.cpu_time_ms:.1f}ms")

# 2. Batch testing
runner = BatchRunner()
batch = runner.run_batch(
    Path("./solution.py"),
    Path("./testcases"),
    limits=ExecutionLimits(time_limit_ms=2000, memory_limit_mb=512),
    mode=CheckerMode.TOKEN,
)
print(f"Passed: {batch.passed}/{batch.total} ({batch.overall_verdict})")
```

---

## 🏗️ Architecture

Aestra features an **adaptive dual-engine** architecture:

```
                      +-------------------+
                      |    Aestra CLI     |
                      +---------+---------+
                                |
                    +-----------v-----------+
                    |  get_engine() Factory |
                    +-----+-----------+-----+
                          |           |
            [Linux / POSIX]           [Windows / Fallback]
                          |           |
           +--------------v--+     +--v---------------+
           |  NativeEngine   |     | SubprocessEngine |
           |  (Rust PyO3)    |     | (Zero-build)     |
           +--------+--------+     +--------+---------+
                    |                       |
           +--------v--------+              |
           | POSIX setrlimit |              |
           | wait4 telemetry |     +--------v---------+
           +--------+--------+     | Wall-clock timer |
                    |              | Process monitor  |
           +--------v--------+     +--------+---------+
           | Target Binary   |              |
           +-----------------+     +--------v---------+
                                   | Target Binary    |
                                   +------------------+
```

1. **`NativeEngine` (POSIX / Linux / macOS):** Uses low-level `fork`, `execve`, and `setrlimit` (`RLIMIT_CPU`, `RLIMIT_AS`) with microsecond `wait4` kernel telemetry.
2. **`SubprocessEngine` (Cross-Platform / Windows):** Automatic zero-configuration fallback requiring zero Rust compiler or C toolchain installations.

---

## 🧪 Development & Testing

Run the complete 13-test engine suite:

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

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.