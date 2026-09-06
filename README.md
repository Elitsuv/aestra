<p align="left">
  <img src="assets/aestra.png" width="70" alt="Aestra Logo" align="left" style="margin-right: 15px;">
  <strong><font size="6">Aestra</font></strong><br>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="https://github.com/Elitsuv/aestra/actions/workflows/ci.yml"><img src="https://github.com/Elitsuv/aestra/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
</p>

<br><br>

Aestra is a deterministic execution sandbox and testcase engine built to accurately enforce hardware constraints (CPU Time Limit and Peak RAM Limit) on untrusted binaries with microsecond precision.

## Quickstart

### Installation
Build from source:

```bash
git clone https://github.com/Elitsuv/aestra.git
cd aestra

python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install maturin
maturin develop
```

### Usage
Execute a target binary under POSIX hardware limits:

```bash
aestra run ./solution.out --time-limit 2000 --memory-limit 512
```

Sample Telemetry:

```text
[Telemetry]
Status: TIME_LIMIT_EXCEEDED
CPU Time: 2003ms
Peak Memory: 12.1MB
Exit Code: 137 (SIGKILL)
```

## Architecture

Aestra combines a **Rust core (`aestra_core`)** for low-overhead POSIX system calls (`fork`, `execve`, `setrlimit`, `wait4`) with a **Python frontend (`aestra`)** for CLI orchestration and answer verification, linked via a zero-cost **PyO3 FFI** bridge.

## Contributing

Please read [contributing.md](contributing.md) for development setup, code quality standards, and Pull Request guidelines.

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.