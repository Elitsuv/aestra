# Contributing to Aestra

We operate under strict engineering standards to maintain a production-grade FFI boundary and execution sandbox. All contributions must adhere to the hybrid architecture design and utilize our standardized Pull Request (PR) lifecycle.

## Local Development Setup

Aestra relies on a zero-overhead Foreign Function Interface (FFI) utilizing PyO3, compiled via `maturin`.

### 1. Toolchain Requirements
* **Rust (1.70.0+)**: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
* **Python (3.10+)**: Ensure `pip` and `venv` are available.

### 2. Environment Initialization

```bash
git clone https://github.com/elitsuv/aestra.git
cd aestra

# Initialize the isolated Python environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install the build backend and compile the Rust core
pip install maturin
maturin develop --release
```

## Engineering Standards

To preserve bare-metal performance and deterministic execution, you must enforce the following standards before opening a PR:

### Rust (`aestra_core`)
* **Memory Safety**: Avoid `unsafe` blocks unless interfacing directly with `libc` or `nix` syscalls (`fork`, `execve`, `setrlimit`). Document all safety invariants.
* **Linting**: Code must pass standard strict lints.

```bash
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings
```

### Python (`aestra`)
* **Typing**: Strict type hinting is mandatory. Use dataclasses for immutable state transfer.
* **Linting**: Code must be formatted and linted using `ruff` and `mypy`.

```bash
ruff check .
ruff format --check .
mypy aestra/
```

## Pull Request Lifecycle

* **Branch Nomenclature**: Create a scoped branch (e.g., `feat/parallel-fuzzer`, `fix/zombie-process`, `perf/rayon-pool`).
* **Atomic Commits**: Keep commits logical and isolated. Write imperative commit messages ("Enforce rlimit AS boundaries" not "added memory limits").
* **PR Submission**: Open the PR against the `main` branch.
* **Mandatory Labels**: You must attach exactly one Size, one Type, and at least one Domain label before requesting a review.

## Repository Labeling System

Our automated changelogs and review pipelines depend on strict Git labeling hygiene. You must configure and use these exact labels:

### 1. Size Labels
Indicates the PR review overhead.

* **`size: xsmall`** — Under 10 lines (Typos, quick fixes).
* **`size: small`** — Under 50 lines.
* **`size: mid`** — Under 250 lines (Standard feature).
* **`size: large`** — Under 1,000 lines (Requires deep architectural review).
* **`size: xlarge`** — Over 1,000 lines (Should be split into atomic PRs).

### 2. Type Labels
Categorizes the nature of the change.

* **`type: feature`** — New functionality or algorithm.
* **`type: bug`** — Critical execution or logic flaw resolution.
* **`type: perf`** — Codebase optimization (e.g., threading, memory allocation).
* **`type: refactor`** — Restructuring existing logic without altering external behavior.
* **`type: chore`** — CI/CD, Maturin config, or dependency bumps.
* **`type: docs`** — README, docstrings, or architecture diagrams.

### 3. Domain Labels
Identifies the subsystem boundary.

* **`domain: rust-core`** — Changes to the POSIX sandbox, Rayon threading, or PyO3 bridge.
* **`domain: python-core`** — Changes to the CLI orchestrator, configuration, or algorithms.
