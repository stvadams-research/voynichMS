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

# 4. Determinism Check
echo "4. Checking Determinism..."
./scripts/verify_reproduction.sh

echo "--- CI Check PASSED ---"
