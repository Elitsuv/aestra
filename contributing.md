# Contributing to Aestra

We welcome high-quality contributions to Aestra. To ensure deterministic execution, kernel telemetry accuracy, and FFI safety, all code submissions must meet the engineering standards outlined below.

---

## Development Workflow

### Prerequisites

- **Python**: 3.10+
- **Rust** (optional, for compiling POSIX native extension): 1.75+ with `cargo` and `rustfmt`

### Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Elitsuv/aestra.git
   cd aestra
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install ruff mypy maturin pytest
   ```

4. **Build native extension (optional on POSIX platforms):**
   ```bash
   maturin develop
   ```

---

## Code Quality Standards

All pull requests must pass formatting, linting, and type verification before merge:

### Python
```bash
ruff check .
ruff format --check .
mypy src/
```

### Rust Core
```bash
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all
```

---

## Running the Test Suite

Execute the unified test suite:
```bash
python -m tests.test
```

Or run via unittest discovery:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

All 50+ unit and integration tests must pass cleanly.

---

## Pull Request Guidelines

1. **Focused Scope**: Keep changes atomic and focused on a single feature, bugfix, or performance optimization.
2. **Deterministic Behavior**: Any modifications to process timing, limits, or telemetry must remain deterministic across runs.
3. **Test Coverage**: Add corresponding tests in `tests/test_<subsystem>.py` covering positive paths, boundary conditions, and failure modes.
4. **Clean Commits**: Use conventional commits (e.g. `feat(fuzzer): add concurrent workers`, `fix(telemetry): sanitize environment`).

---

## License

By contributing to Aestra, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).

