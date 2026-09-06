# Contributing Guidelines

Contributions to Aestra are welcome. We maintain strict engineering standards to preserve deterministic execution and FFI boundary safety.

## Development Setup

### Prerequisites
- **Rust**: 1.75.0+ (`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`)
- **Python**: 3.10+

### Environment Setup
```bash
git clone https://github.com/Elitsuv/aestra.git
cd aestra

python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install maturin
maturin develop
```

## Quality Standards

Before submitting a Pull Request, verify that all linters pass locally:

### Python
```bash
ruff check .
ruff format --check .
mypy src/
```

### Rust
```bash
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings
```

## Pull Request Lifecycle

1. **Branch Naming**: Use scoped branch names (`feat/sandbox-limits`, `fix/zombie-pid`).
2. **Atomic Commits**: Write clear, imperative commit messages (`feat(rust-core): enforce rlimit AS`).
3. **PR Submission**: Target `main`. Ensure CI checks and PR quality audit pass.

## Label Taxonomy

Attach appropriate labels to your PR:

- **Size**: `size: xsmall` (<10 lines), `size: small` (<50 lines), `size: mid` (<250 lines), `size: large` (<1000 lines).
- **Type**: `type: feature`, `type: bug`, `type: perf`, `type: refactor`, `type: chore`, `type: docs`.
- **Domain**: `domain: rust-core` (Rust engine, PyO3 FFI, sandbox) or `domain: python-core` (CLI, config, checker).
