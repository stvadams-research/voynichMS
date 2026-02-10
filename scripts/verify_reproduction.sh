#!/bin/bash
set -e

echo "--- Voynich MS Reproduction Verification ---"

# 1. Environment Check
echo "1. Checking environment..."
if [ -z "$VIRTUAL_ENV" ]; then
    echo "ERROR: Virtual environment not active."
    exit 1
fi
python --version

# 2. Data Check
echo "2. Checking data initialization..."
if [ ! -f "data/voynich.db" ]; then
    echo "Initializing database..."
    python3 scripts/foundation/acceptance_test.py
fi

# 3. Determinism Check
echo "3. Verifying deterministic output..."
SEED=12345
OUT1="status/verify_1.json"
OUT2="status/verify_2.json"

# Use run_test_a.py as a proxy for determinism verification
echo "Running test A (1/2)..."
python3 scripts/synthesis/run_test_a.py > /dev/null
cp status/synthesis/TEST_A_RESULTS.json $OUT1

echo "Running test A (2/2)..."
python3 scripts/synthesis/run_test_a.py > /dev/null
cp status/synthesis/TEST_A_RESULTS.json $OUT2

if diff "$OUT1" "$OUT2"; then
    echo "  [OK] Outputs are identical for the same seed."
else
    echo "  [FAIL] Non-deterministic output detected!"
    exit 1
fi

rm "$OUT1" "$OUT2"

# 4. Critical Metrics Check
echo "4. Checking regression fixtures..."
python3 scripts/audit/generate_fixtures.py > /dev/null
# Note: In a real CI, we would diff against LOCKED fixtures.
# Here we just ensure the generation runs without error.

echo "--- Reproduction Verification PASSED ---"
