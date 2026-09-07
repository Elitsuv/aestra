### Summary
<!-- Provide a clear, concise 1-2 sentence overview of what this PR introduces or fixes -->

### Context & Motivation
<!-- Why is this change necessary? What problem or feature does it address? -->

### Key Changes
<!-- Group changes logically (e.g. Rust Core, Python Engine, Tests, CI/Tooling) -->
- **Component Name**:
  - Description of change 1
  - Description of change 2

### Related Issue
<!-- Reference the issue number this PR closes or relates to -->
Closes #

### Testing & Verification
<!-- Describe the tests you ran to verify your changes. Include commands and results -->
- **Automated Tests**:
  - `pytest` (passed)
  - `cargo test --all` (passed)
- **Manual / Integration Checks**:
  - Details of any manual CLI or binary tests performed

### Pre-Merge Checklist
- [ ] All automated tests pass locally
- [ ] Code is formatted (`ruff format .` / `cargo fmt --all`)
- [ ] Linters & type checkers pass with 0 errors (`ruff check .`, `mypy src/`, `cargo clippy`)
- [ ] No temporary debug code or extraneous files committed
