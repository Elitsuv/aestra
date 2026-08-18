<div align="center">
  <img src="assets/aestra.png" width="120" alt="Aestra Logo">
  <h1>Aestra</h1>
  <p>Local Execution Sandbox and Fuzzer for Competitive Programming</p>

  [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
</div>

---

Aestra is a deterministic, local execution harness built to accurately enforce hardware constraints (Time Limit and Memory Limit) on untrusted binaries.

## For Users

### Installation
*(Currently, Aestra must be built from source. See **Build Instructions** below.)*

### Usage
Execute a compiled target with enforced POSIX limits:

```bash
aestra run ./solution.out \
  --time-limit 2000 \
  --memory-limit 512 \
```

**Output Example:**

```text
[Telemetry]
Status: TIME_LIMIT_EXCEEDED
CPU Time: 2003ms
Peak Memory: 12.1MB
Exit Code: 137 (SIGKILL)
```

## For Developers

Aestra uses a hybrid architecture: a **Rust backend** (`aestra_core`) for low-overhead POSIX `fork()`/`execve()` system calls, and a **Python frontend** (`aestra`) for CLI orchestration. They communicate via a zero-cost **PyO3 FFI** bridge.

### Prerequisites
* **Rust (1.70.0+)**
* **Python (3.10+)**
* **Maturin** (Build backend)

### Build Instructions

```bash
git clone https://github.com/Elitsuv/aestra.git
cd aestra

python -m venv .venv
source .venv/bin/activate

pip install maturin
maturin develop --release
```

## License

Distributed under the MIT License. See the `LICENSE` file for details.