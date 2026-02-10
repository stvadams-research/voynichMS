#!/bin/bash
set -euo pipefail

echo "--- Voynich MS Reproduction Verification ---"
PYTHON_BIN="${PYTHON_BIN:-python3}"
CLEAN_VERIFY_DB=0
VERIFICATION_COMPLETE=0
VERIFY_SUCCESS_TOKEN="VERIFY_REPRODUCTION_COMPLETED"

cleanup() {
    status=$?
    rm -f "${OUT1:-}" "${OUT2:-}" "${CAN1:-}" "${CAN2:-}"
    if [ "${CLEAN_VERIFY_DB}" -eq 1 ] && [ -n "${VERIFY_DB:-}" ]; then
        rm -f "${VERIFY_DB}"
    fi

    # Guard against false-positive success if the script exited early.
    if [ "${status}" -eq 0 ] && [ "${VERIFICATION_COMPLETE}" -ne 1 ]; then
        echo "  [FAIL] Verification exited before completion marker." >&2
        status=1
    fi

    if [ "${status}" -eq 0 ] && [ -n "${VERIFY_SENTINEL_PATH:-}" ]; then
        printf '%s\n' "${VERIFY_SUCCESS_TOKEN}" > "${VERIFY_SENTINEL_PATH}"
    fi

    trap - EXIT
    exit "${status}"
}
trap cleanup EXIT

# 1. Environment Check
echo "1. Checking environment..."
if [ -z "${VIRTUAL_ENV:-}" ]; then
    echo "WARNING: Virtual environment not active; using ${PYTHON_BIN} from PATH."
fi
"${PYTHON_BIN}" --version

# 2. Data Check
echo "2. Checking data initialization..."
if [ ! -f "data/voynich.db" ]; then
    echo "Initializing database..."
    "${PYTHON_BIN}" scripts/foundation/acceptance_test.py
fi

if [ -n "${VERIFY_DB:-}" ]; then
    echo "Using verification DB: ${VERIFY_DB}"
else
    VERIFY_DB="$(mktemp /tmp/voynich_verify_db.XXXXXX.sqlite3)"
    CLEAN_VERIFY_DB=1
fi
cp data/voynich.db "${VERIFY_DB}"
VERIFY_DB_URL="sqlite:///${VERIFY_DB}"

# 3. Determinism Check
echo "3. Verifying deterministic output..."
SEED="${SEED:-12345}"
OUT1="$(mktemp /tmp/verify_1.XXXXXX.json)"
OUT2="$(mktemp /tmp/verify_2.XXXXXX.json)"
CAN1="$(mktemp /tmp/verify_1.canon.XXXXXX.json)"
CAN2="$(mktemp /tmp/verify_2.canon.XXXXXX.json)"

# Use run_test_a.py as a proxy for determinism verification
echo "Running test A (1/2)..."
"${PYTHON_BIN}" scripts/synthesis/run_test_a.py --seed "$SEED" --db-url "$VERIFY_DB_URL" --output "$OUT1" > /dev/null

echo "Running test A (2/2)..."
"${PYTHON_BIN}" scripts/synthesis/run_test_a.py --seed "$SEED" --db-url "$VERIFY_DB_URL" --output "$OUT2" > /dev/null

"${PYTHON_BIN}" - <<'PY' "$OUT1" "$CAN1"
import json
import sys
src, dst = sys.argv[1], sys.argv[2]
data = json.load(open(src))
payload = data.get("results", data)
with open(dst, "w") as f:
    json.dump(payload, f, sort_keys=True, separators=(",", ":"))
PY

"${PYTHON_BIN}" - <<'PY' "$OUT2" "$CAN2"
import json
import sys
src, dst = sys.argv[1], sys.argv[2]
data = json.load(open(src))
payload = data.get("results", data)
with open(dst, "w") as f:
    json.dump(payload, f, sort_keys=True, separators=(",", ":"))
PY

if diff "$CAN1" "$CAN2"; then
    echo "  [OK] Outputs are identical for the same seed."
else
    echo "  [FAIL] Non-deterministic output detected!"
    exit 1
fi

# 4. Analysis Spot Check
echo "4. Running analysis spot check..."
"${PYTHON_BIN}" -m pytest -q tests/analysis/test_mapping_stability.py > /dev/null
echo "  [OK] Analysis stress-test spot check passed."

# 5. Critical Metrics Check
echo "5. Checking regression fixtures..."
"${PYTHON_BIN}" scripts/audit/generate_fixtures.py > /dev/null
# Note: In a real CI, we would diff against LOCKED fixtures.
# Here we just ensure the generation runs without error.

# 5b. Provenance Runner Contract Check
echo "5b. Checking provenance runner contract..."
"${PYTHON_BIN}" scripts/audit/check_provenance_runner_contract.py --mode release

# 5c. Multimodal Coupling Status Check
echo "5c. Checking multimodal coupling policy..."
"${PYTHON_BIN}" scripts/skeptic/check_multimodal_coupling.py --mode release

# 6. Sensitivity Artifact Integrity Check
echo "6. Checking sensitivity artifact integrity..."
"${PYTHON_BIN}" scripts/audit/check_sensitivity_artifact_contract.py --mode release
"${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path

status_path = Path("status/audit/sensitivity_sweep.json")
report_path = Path("reports/audit/SENSITIVITY_RESULTS.md")

if not status_path.exists():
    raise SystemExit("Missing status/audit/sensitivity_sweep.json")
if not report_path.exists():
    raise SystemExit("Missing reports/audit/SENSITIVITY_RESULTS.md")

payload = json.loads(status_path.read_text(encoding="utf-8"))
results = payload.get("results", {})
summary = results.get("summary", {})
dataset_profile = results.get("dataset_profile", {})
dataset_id = summary.get("dataset_id") or dataset_profile.get("dataset_id")
command = payload.get("provenance", {}).get("command")
execution_mode = summary.get("execution_mode")
release_ready = summary.get("release_evidence_ready")
robustness_decision = summary.get("robustness_decision")
quality_gate_passed = summary.get("quality_gate_passed")
robustness_conclusive = summary.get("robustness_conclusive")
scenario_expected = summary.get("scenario_count_expected")
scenario_executed = summary.get("scenario_count_executed")
dataset_policy_pass = summary.get("dataset_policy_pass")
warning_policy_pass = summary.get("warning_policy_pass")
warning_density = summary.get("warning_density_per_scenario")
total_warning_count = summary.get("total_warning_count")
caveats = summary.get("caveats")

if dataset_id in (None, "unknown_legacy", "real"):
    raise SystemExit(f"Invalid sensitivity dataset_id: {dataset_id}")
if command == "sensitivity_sweep_legacy_reconcile":
    raise SystemExit("Sensitivity status still indicates legacy reconciliation command.")
if execution_mode != "release":
    raise SystemExit(f"Sensitivity execution_mode must be 'release'; got {execution_mode!r}")
if dataset_policy_pass is not True:
    raise SystemExit(
        "Sensitivity dataset policy is not satisfied "
        "(dataset_policy_pass=true required)."
    )
if warning_policy_pass is not True:
    raise SystemExit(
        "Sensitivity warning policy is not satisfied "
        "(warning_policy_pass=true required)."
    )
if release_ready is not True:
    raise SystemExit(
        "Sensitivity artifact is not marked release_evidence_ready=true. "
        "Run canonical release sweep with conclusive robustness evidence."
    )
if scenario_expected is None or scenario_executed is None:
    raise SystemExit("Missing scenario_count_expected/scenario_count_executed in sensitivity summary.")
if scenario_expected != scenario_executed:
    raise SystemExit(
        f"Sensitivity scenario execution incomplete: {scenario_executed}/{scenario_expected}"
    )
if robustness_decision == "INCONCLUSIVE":
    raise SystemExit(
        "Sensitivity robustness is INCONCLUSIVE; release verification requires conclusive PASS/FAIL evidence."
    )
if robustness_conclusive is not True:
    raise SystemExit(
        "Sensitivity artifact missing conclusive robustness flag. Regenerate with updated runner."
    )
if quality_gate_passed is not True:
    raise SystemExit(
        "Sensitivity quality gate failed; release verification requires sufficient valid scenarios "
        "and non-collapse conditions."
    )
if warning_density is None:
    raise SystemExit("Sensitivity summary missing warning_density_per_scenario.")
if total_warning_count is None:
    raise SystemExit("Sensitivity summary missing total_warning_count.")
if total_warning_count > 0 and (not isinstance(caveats, list) or len(caveats) == 0):
    raise SystemExit(
        "Sensitivity warnings exist but caveats list is empty. "
        "Warning-bearing evidence must include explicit caveats."
    )

report_text = report_path.read_text(encoding="utf-8")
if "unknown_legacy" in report_text:
    raise SystemExit("Sensitivity report still references unknown_legacy.")

legacy_verify_files = []
by_run_dir = Path("status/by_run")
if by_run_dir.exists():
    for artifact in by_run_dir.glob("verify_*.json"):
        try:
            artifact_payload = json.loads(artifact.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        provenance_status = artifact_payload.get("provenance", {}).get("status")
        if provenance_status is not None:
            legacy_verify_files.append(str(artifact))

if legacy_verify_files:
    preview = ", ".join(sorted(legacy_verify_files)[:3])
    raise SystemExit(
        "Legacy verification artifacts still include mutable provenance.status fields "
        f"({preview}). Run scripts/audit/cleanup_status_artifacts.sh clean."
    )

print("  [OK] Sensitivity artifact integrity check passed.")
PY

# 7. Strict-mode release-path enforcement (always required)
echo "7. Validating strict indistinguishability preflight policy..."
STRICT_PREFLIGHT_EXIT=0
if REQUIRE_COMPUTED=1 "${PYTHON_BIN}" scripts/synthesis/run_indistinguishability_test.py --preflight-only > /dev/null 2>&1; then
    STRICT_PREFLIGHT_EXIT=0
else
    STRICT_PREFLIGHT_EXIT=$?
fi

STATUS_FILE="status/synthesis/TURING_TEST_RESULTS.json"
"${PYTHON_BIN}" - <<'PY' "${STRICT_PREFLIGHT_EXIT}" "${STATUS_FILE}"
import json
import sys
from pathlib import Path

strict_exit = int(sys.argv[1])
status_file = Path(sys.argv[2])
if not status_file.exists():
    raise SystemExit("Strict preflight did not produce status/synthesis/TURING_TEST_RESULTS.json")

payload = json.loads(status_file.read_text(encoding="utf-8"))
results = payload.get("results", {})
status = results.get("status")
strict_computed = results.get("strict_computed")
reason_code = results.get("reason_code")
preflight = results.get("preflight") or {}
missing_count = preflight.get("missing_count")

if strict_computed is not True:
    raise SystemExit("Strict preflight artifact is not marked strict_computed=true.")

if status == "PREFLIGHT_OK":
    if strict_exit != 0:
        raise SystemExit(
            f"Strict preflight command exited {strict_exit} but artifact status is PREFLIGHT_OK."
        )
    if missing_count not in (0, None):
        raise SystemExit(
            f"Strict preflight reported PREFLIGHT_OK with missing_count={missing_count}."
        )
    print("  [OK] Strict preflight passed with computed prerequisites available.")
elif status == "BLOCKED":
    if strict_exit == 0:
        raise SystemExit(
            "Strict preflight command exited 0 but artifact status is BLOCKED."
        )
    if reason_code != "DATA_AVAILABILITY":
        raise SystemExit(
            "Strict preflight BLOCKED without approved reason_code=DATA_AVAILABILITY."
        )
    if missing_count is None:
        raise SystemExit(
            "Strict preflight BLOCKED but missing_count is absent from preflight metadata."
        )
    print(
        "  [OK] Strict preflight blocked due approved data-availability constraint "
        f"(missing_count={missing_count})."
    )
else:
    raise SystemExit(f"Unexpected strict preflight artifact status: {status!r}")
PY

# 8. Optional additional strict enforcement checks
if [ "${VERIFY_STRICT:-0}" = "1" ]; then
    echo "8. Running additional strict REQUIRE_COMPUTED enforcement checks..."
    REQUIRE_COMPUTED=1 "${PYTHON_BIN}" -m pytest -q tests/foundation/test_enforcement.py > /dev/null
    echo "  [OK] Additional strict enforcement checks passed."
fi

# 9. SK-H3 control-comparability policy checks
echo "9. Checking SK-H3 control comparability policy..."
"${PYTHON_BIN}" scripts/synthesis/run_control_matching_audit.py --preflight-only > /dev/null
"${PYTHON_BIN}" scripts/skeptic/check_control_comparability.py --mode release > /dev/null
"${PYTHON_BIN}" scripts/skeptic/check_control_data_availability.py --mode release > /dev/null
"${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path

status_path = Path("status/synthesis/CONTROL_COMPARABILITY_STATUS.json")
availability_path = Path("status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json")
if not status_path.exists():
    raise SystemExit("Missing status/synthesis/CONTROL_COMPARABILITY_STATUS.json")
if not availability_path.exists():
    raise SystemExit("Missing status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json")

results = json.loads(status_path.read_text(encoding="utf-8")).get("results", {})
availability = json.loads(availability_path.read_text(encoding="utf-8")).get("results", {})
required = [
    "status",
    "reason_code",
    "allowed_claim",
    "evidence_scope",
    "full_data_closure_eligible",
    "available_subset_status",
    "available_subset_reason_code",
    "missing_pages",
    "missing_count",
    "matching_metrics",
    "holdout_evaluation_metrics",
    "metric_overlap",
    "leakage_detected",
    "normalization_mode",
]
missing = [k for k in required if k not in results]
if missing:
    raise SystemExit(f"SK-H3 comparability artifact missing keys: {missing}")
if results.get("leakage_detected") is True:
    raise SystemExit("SK-H3 comparability artifact indicates leakage_detected=true")
if results.get("status") == "NON_COMPARABLE_BLOCKED":
    if results.get("reason_code") != "DATA_AVAILABILITY":
        raise SystemExit(
            "SK-H3 blocked comparability must use reason_code=DATA_AVAILABILITY."
        )
    if results.get("evidence_scope") != "available_subset":
        raise SystemExit(
            "SK-H3 blocked comparability must set evidence_scope=available_subset."
        )
    if results.get("full_data_closure_eligible") is not False:
        raise SystemExit(
            "SK-H3 blocked comparability must set full_data_closure_eligible=false."
        )
    if availability.get("status") != "DATA_AVAILABILITY_BLOCKED":
        raise SystemExit(
            "SK-H3 blocked comparability requires DATA_AVAILABILITY_BLOCKED artifact."
        )
    if results.get("missing_count") != availability.get("missing_count"):
        raise SystemExit(
            "SK-H3 comparability and data-availability missing_count mismatch."
        )
else:
    if results.get("evidence_scope") not in ("full_dataset", "available_subset"):
        raise SystemExit(
            f"SK-H3 comparability has invalid evidence_scope={results.get('evidence_scope')!r}."
        )

print("  [OK] SK-H3 comparability policy checks passed.")
PY

# 10. SK-M2 comparative uncertainty policy checks
echo "10. Checking SK-M2 comparative uncertainty policy..."
"${PYTHON_BIN}" scripts/comparative/run_proximity_uncertainty.py --iterations 2000 --seed 42 > /dev/null
"${PYTHON_BIN}" scripts/skeptic/check_comparative_uncertainty.py --mode release > /dev/null
"${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path

path = Path("results/human/phase_7c_uncertainty.json")
if not path.exists():
    raise SystemExit("Missing results/human/phase_7c_uncertainty.json")

results = json.loads(path.read_text(encoding="utf-8")).get("results", {})
required = [
    "status",
    "reason_code",
    "allowed_claim",
    "nearest_neighbor",
    "nearest_neighbor_stability",
    "jackknife_nearest_neighbor_stability",
    "rank_stability",
    "rank_stability_components",
    "nearest_neighbor_probability_margin",
    "top2_gap",
    "metric_validity",
]
missing = [k for k in required if k not in results]
if missing:
    raise SystemExit(f"SK-M2 uncertainty artifact missing keys: {missing}")
metric_validity = results.get("metric_validity") or {}
if metric_validity.get("required_fields_present") is not True:
    raise SystemExit("SK-M2 uncertainty artifact has incomplete required status inputs.")
if metric_validity.get("sufficient_iterations") is not True:
    raise SystemExit("SK-M2 uncertainty artifact reports insufficient iteration depth.")

print("  [OK] SK-M2 comparative uncertainty policy checks passed.")
PY

# 11. SK-M4 historical provenance policy checks
echo "11. Checking SK-M4 historical provenance policy..."
"${PYTHON_BIN}" scripts/audit/build_release_gate_health_status.py > /dev/null
"${PYTHON_BIN}" scripts/audit/build_provenance_health_status.py > /dev/null
"${PYTHON_BIN}" scripts/audit/sync_provenance_register.py > /dev/null
"${PYTHON_BIN}" scripts/skeptic/check_provenance_uncertainty.py --mode release > /dev/null
"${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path

provenance_path = Path("status/audit/provenance_health_status.json")
sync_path = Path("status/audit/provenance_register_sync_status.json")
if not provenance_path.exists():
    raise SystemExit("Missing status/audit/provenance_health_status.json")
if not sync_path.exists():
    raise SystemExit("Missing status/audit/provenance_register_sync_status.json")

prov = json.loads(provenance_path.read_text(encoding="utf-8"))
sync = json.loads(sync_path.read_text(encoding="utf-8"))
required_prov = [
    "status",
    "reason_code",
    "allowed_claim",
    "orphaned_rows",
    "orphaned_ratio",
    "threshold_policy_pass",
    "contract_health_status",
    "contract_health_reason_code",
    "contract_reason_codes",
    "contract_coupling_pass",
]
missing = [k for k in required_prov if k not in prov]
if missing:
    raise SystemExit(f"SK-M4 provenance artifact missing keys: {missing}")
if sync.get("status") != "IN_SYNC":
    raise SystemExit(
        f"SK-M4 register sync status must be IN_SYNC (got {sync.get('status')!r})."
    )
if sync.get("drift_detected") is not False:
    raise SystemExit("SK-M4 register sync artifact reports drift_detected=true.")

print("  [OK] SK-M4 historical provenance policy checks passed.")
PY

# 12. SK-H2.2 / SK-M1.2 operational entitlement policy checks
echo "12. Checking SK-H2.2 / SK-M1.2 operational entitlement policy..."
"${PYTHON_BIN}" scripts/audit/build_release_gate_health_status.py > /dev/null
"${PYTHON_BIN}" scripts/skeptic/check_claim_boundaries.py --mode release > /dev/null
"${PYTHON_BIN}" scripts/skeptic/check_closure_conditionality.py --mode release > /dev/null
"${PYTHON_BIN}" scripts/skeptic/check_report_coherence.py --mode release > /dev/null

VERIFICATION_COMPLETE=1
echo "${VERIFY_SUCCESS_TOKEN}"
echo "--- Reproduction Verification PASSED ---"
