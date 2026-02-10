#!/bin/bash
set -euo pipefail

echo "--- Starting CI Check ---"
PYTHON_BIN="${PYTHON_BIN:-python3}"

# 1. Environment Setup (Check dependencies)
echo "1. Checking environment..."
"${PYTHON_BIN}" --version

# 2. Linting
echo "2. Linting..."
# ruff check src tests # Commented out until ruff is configured/installed properly in this env, but intended for future.

# 3. Tests + Coverage Gate (phased baseline)
echo "3. Running Tests with Coverage..."
COVERAGE_STAGE="${COVERAGE_STAGE:-3}"
if [ -z "${COVERAGE_MIN:-}" ]; then
  case "${COVERAGE_STAGE}" in
    1) COVERAGE_MIN=40 ;;
    2) COVERAGE_MIN=45 ;;
    3) COVERAGE_MIN=50 ;;
    4) COVERAGE_MIN=55 ;;
    *) COVERAGE_MIN=50 ;;
  esac
fi
CI_COVERAGE_JSON="${CI_COVERAGE_JSON:-status/ci_coverage.json}"
mkdir -p "$(dirname "${CI_COVERAGE_JSON}")"
PYTEST_TARGETS="${PYTEST_TARGETS:-tests}"
"${PYTHON_BIN}" -m pytest \
  --cov=src \
  --cov-report=term-missing:skip-covered \
  --cov-report=json:"${CI_COVERAGE_JSON}" \
  --cov-fail-under="${COVERAGE_MIN}" \
  -q \
  ${PYTEST_TARGETS}

echo "3b. Critical Module Coverage Check..."
"${PYTHON_BIN}" - <<'PY' "${CI_COVERAGE_JSON}"
import json
import os
import sys

coverage_path = sys.argv[1]
critical_modules = [
    "src/foundation/cli/main.py",
    "src/analysis/admissibility/manager.py",
    "src/foundation/core/queries.py",
]
min_coverage = float(os.environ.get("CRITICAL_MODULE_MIN", "20"))
enforce = os.environ.get("CRITICAL_MODULE_ENFORCE", "1") != "0"

with open(coverage_path, "r", encoding="utf-8") as f:
    data = json.load(f)

files = data.get("files", {})
failures = []
for module in critical_modules:
    percent = files.get(module, {}).get("summary", {}).get("percent_covered")
    if percent is None:
        failures.append((module, "missing"))
        continue
    if percent < min_coverage:
        failures.append((module, f"{percent:.2f}%"))

if failures:
    print("Critical module coverage below threshold:")
    for module, actual in failures:
        print(f"  - {module}: {actual} (< {min_coverage:.2f}%)")
    if enforce:
        raise SystemExit(1)
else:
    print("  [OK] Critical module coverage checks passed.")
PY

# 4. Determinism Check
echo "4. Checking Determinism..."
VERIFY_SENTINEL="$(mktemp /tmp/verify_reproduction_sentinel.XXXXXX)"
cleanup_ci() {
  rm -f "${VERIFY_SENTINEL:-}"
}
trap cleanup_ci EXIT

PYTHON_BIN="${PYTHON_BIN}" VERIFY_SENTINEL_PATH="${VERIFY_SENTINEL}" ./scripts/verify_reproduction.sh
if ! grep -qx "VERIFY_REPRODUCTION_COMPLETED" "${VERIFY_SENTINEL}"; then
  echo "  [FAIL] Reproduction verification did not emit completion sentinel."
  exit 1
fi

echo "--- CI Check PASSED ---"
