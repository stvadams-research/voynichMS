#!/bin/bash
# Pre-submission Sanity Check
# Mandatory for all agents to run this before declaring a task complete.

set -e

echo "=== [1/3] Running Lint Check (Ruff) ==="
./.venv/bin/python3 -m ruff check .

echo "=== [2/3] Running Unit Tests (Pytest) ==="
./.venv/bin/python3 -m pytest tests/ --ignore=tests/integration -x -q --tb=short

echo "=== [3/3] Running Provenance Contract Check ==="
./.venv/bin/python3 scripts/core_audit/check_provenance_runner_contract.py --root . --mode ci

echo "=== [SUCCESS] Pre-submission checks passed. ==="
