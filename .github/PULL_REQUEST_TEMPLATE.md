## Description

Provide a clear and concise description of the changes introduced in this PR.

Fixes #(issue number)

## Type of Change

Select all that apply:
- [ ] `type: feature` (New feature or functionality)
- [ ] `type: bug` (Bug fix)
- [ ] `type: perf` (Performance optimization)
- [ ] `type: refactor` (Code restructuring without behavior changes)
- [ ] `type: chore` (Dependencies, tooling, CI/CD)
- [ ] `type: docs` (Documentation updates)

## PR Size Category

Select one:
- [ ] `size: xsmall` (<10 lines)
- [ ] `size: small` (<50 lines)
- [ ] `size: mid` (<250 lines)
- [ ] `size: large` (<1000 lines)
- [ ] `size: xlarge` (>1000 lines)

## Domain Boundary

Select all that apply:
- [ ] `domain: rust-core` (Rust native engine, PyO3 FFI, sandbox)
- [ ] `domain: python-core` (Python CLI, models, config, test harness)

## Checklist

- [ ] My code passes `ruff check .` and `ruff format --check .`
- [ ] My code passes `mypy src/`
- [ ] (If modifying Rust) `cargo fmt --all -- --check` and `cargo clippy` pass cleanly
- [ ] Automated tests pass locally
- [ ] I have updated the documentation accordingly
