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

# 2a. Release Gate-Health Artifact
echo "2a. Building release gate-health artifact..."
"${PYTHON_BIN}" scripts/audit/build_release_gate_health_status.py > /dev/null

# 2b. Claim-Boundary Policy
echo "2b. Checking claim boundaries..."
"${PYTHON_BIN}" scripts/skeptic/check_claim_boundaries.py --mode ci

# 2c. Control-Comparability Policy
echo "2c. Building control matching/data-availability artifacts..."
"${PYTHON_BIN}" scripts/synthesis/run_control_matching_audit.py --preflight-only > /dev/null
echo "2c. Checking control comparability policy..."
"${PYTHON_BIN}" scripts/skeptic/check_control_comparability.py --mode ci
echo "2c. Checking control data-availability policy..."
"${PYTHON_BIN}" scripts/skeptic/check_control_data_availability.py --mode ci

# 2d. Closure-Conditionality Policy
echo "2d. Checking closure conditionality policy..."
"${PYTHON_BIN}" scripts/skeptic/check_closure_conditionality.py --mode ci

# 2e. Comparative-Uncertainty Policy
echo "2e. Checking comparative uncertainty policy..."
"${PYTHON_BIN}" scripts/skeptic/check_comparative_uncertainty.py --mode ci

# 2f. Report-Coherence Policy
echo "2f. Checking report coherence policy..."
"${PYTHON_BIN}" scripts/skeptic/check_report_coherence.py --mode ci

# 2g. Provenance-Uncertainty Policy
echo "2g. Building provenance health artifact..."
"${PYTHON_BIN}" scripts/audit/build_provenance_health_status.py > /dev/null
echo "2g. Synchronizing provenance register..."
"${PYTHON_BIN}" scripts/audit/sync_provenance_register.py > /dev/null
echo "2g. Checking provenance uncertainty policy..."
"${PYTHON_BIN}" scripts/skeptic/check_provenance_uncertainty.py --mode ci

# 2h. Provenance Runner Contract
echo "2h. Checking provenance runner contract..."
"${PYTHON_BIN}" scripts/audit/check_provenance_runner_contract.py --mode ci

# 2i. Sensitivity artifact/report contract
echo "2i. Checking sensitivity artifact contract..."
"${PYTHON_BIN}" scripts/audit/check_sensitivity_artifact_contract.py --mode ci

# 2j. Multimodal coupling status contract
echo "2j. Checking multimodal coupling policy..."
"${PYTHON_BIN}" scripts/skeptic/check_multimodal_coupling.py --mode ci

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
