#!/usr/bin/env python3
"""
Helper script to sync GitHub labels for Aestra repository according to contributing.md.
Requires GitHub CLI (`gh`) installed and authenticated (`gh auth login`).
"""

import subprocess

LABELS = [
    # Size Labels
    {"name": "size: xsmall", "color": "0E8A16", "description": "<10 lines changed"},
    {"name": "size: small", "color": "0E8A16", "description": "<50 lines changed"},
    {"name": "size: mid", "color": "FBCA04", "description": "<250 lines changed"},
    {"name": "size: large", "color": "D93F0B", "description": "<1000 lines changed"},
    {"name": "size: xlarge", "color": "B60205", "description": ">1000 lines changed"},
    # Type Labels
    {
        "name": "type: feature",
        "color": "A2EEEF",
        "description": "New feature or algorithm",
    },
    {
        "name": "type: bug",
        "color": "D73A4A",
        "description": "Critical execution or logic bug",
    },
    {
        "name": "type: perf",
        "color": "006B75",
        "description": "Performance optimization",
    },
    {
        "name": "type: refactor",
        "color": "1D76DB",
        "description": "Code restructuring without behavior alteration",
    },
    {
        "name": "type: chore",
        "color": "CFD3D7",
        "description": "Tooling, CI/CD, Maturin or dependencies",
    },
    {"name": "type: docs", "color": "0075CA", "description": "Documentation updates"},
    # Domain Labels
    {
        "name": "domain: rust-core",
        "color": "F9D0C4",
        "description": "Rust backend, POSIX/Win32 sandbox, PyO3 FFI",
    },
    {
        "name": "domain: python-core",
        "color": "3572A5",
        "description": "Python CLI, configuration, domain models",
    },
]


def main() -> None:
    print("Syncing Aestra GitHub Labels...")
    for label in LABELS:
        name = label["name"]
        color = label["color"]
        desc = label["description"]

        cmd = [
            "gh",
            "label",
            "create",
            name,
            "--color",
            color,
            "--description",
            desc,
            "--force",
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"  ✓ Label '{name}' synced.")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Failed to sync '{name}': {e.stderr.strip()}")
            print("    (Ensure `gh auth login` is run).")


if __name__ == "__main__":
    main()
