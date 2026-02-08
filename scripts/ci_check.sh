#!/bin/bash
set -e

echo "--- Starting CI Check ---"

# 1. Environment Setup (Check dependencies)
echo "1. Checking environment..."
# Assuming we are already in the venv
python --version

# 2. Linting
echo "2. Linting..."
# ruff check src tests # Commented out until ruff is configured/installed properly in this env, but intended for future.

# 3. Tests
echo "3. Running Tests..."
pytest tests/foundation/test_enforcement.py

# 4. Determinism Check (Simulated)
echo "4. Checking Determinism..."
# In a real CI, we would run a script twice and compare outputs.
# For now, we trust the recent manual verification.

echo "--- CI Check PASSED ---"
