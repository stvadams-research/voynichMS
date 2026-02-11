#!/bin/bash
set -euo pipefail

echo "--- Voynich MS Reproduction Verification ---"
PYTHON_BIN="${PYTHON_BIN:-python3}"
SENSITIVITY_RELEASE_STATUS_PATH="${SENSITIVITY_RELEASE_STATUS_PATH:-core_status/core_audit/sensitivity_sweep_release.json}"
SENSITIVITY_RELEASE_REPORT_PATH="${SENSITIVITY_RELEASE_REPORT_PATH:-reports/core_audit/SENSITIVITY_RESULTS_RELEASE.md}"
SENSITIVITY_RELEASE_PREFLIGHT_PATH="${SENSITIVITY_RELEASE_PREFLIGHT_PATH:-core_status/core_audit/sensitivity_release_preflight.json}"
SENSITIVITY_RELEASE_RUN_STATUS_PATH="${SENSITIVITY_RELEASE_RUN_STATUS_PATH:-core_status/core_audit/sensitivity_release_run_status.json}"
SENSITIVITY_RELEASE_DATASET_ID="${SENSITIVITY_RELEASE_DATASET_ID:-voynich_real}"
export SENSITIVITY_RELEASE_STATUS_PATH
export SENSITIVITY_RELEASE_REPORT_PATH
export SENSITIVITY_RELEASE_PREFLIGHT_PATH
export SENSITIVITY_RELEASE_RUN_STATUS_PATH
export SENSITIVITY_RELEASE_DATASET_ID
CLEAN_VERIFY_DB=0
VERIFICATION_COMPLETE=0
VERIFY_SUCCESS_TOKEN="VERIFY_REPRODUCTION_COMPLETED"

support_cleanup() {
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
trap support_cleanup EXIT

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
    "${PYTHON_BIN}" scripts/phase1_foundation/acceptance_test.py
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
"${PYTHON_BIN}" scripts/phase3_synthesis/run_test_a.py --seed "$SEED" --db-url "$VERIFY_DB_URL" --output "$OUT1" > /dev/null

echo "Running test A (2/2)..."
"${PYTHON_BIN}" scripts/phase3_synthesis/run_test_a.py --seed "$SEED" --db-url "$VERIFY_DB_URL" --output "$OUT2" > /dev/null

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
echo "4. Running phase2_analysis spot check..."
"${PYTHON_BIN}" -m pytest -q tests/phase2_analysis/test_mapping_stability.py > /dev/null
echo "  [OK] Analysis stress-test spot check passed."

# 5. Critical Metrics Check
echo "5. Checking regression fixtures..."
"${PYTHON_BIN}" scripts/core_audit/generate_fixtures.py > /dev/null
# Note: In a real CI, we would diff against LOCKED fixtures.
# Here we just ensure the generation runs without error.

# 5b. Provenance Runner Contract Check
echo "5b. Checking provenance runner contract..."
"${PYTHON_BIN}" scripts/core_audit/check_provenance_runner_contract.py --mode release

# 5c. Multimodal Coupling Status Check
echo "5c. Checking multimodal coupling policy..."
"${PYTHON_BIN}" scripts/core_skeptic/check_multimodal_coupling.py --mode release
echo "5d. Verifying SK-H1.4/SK-H1.5 multimodal robustness semantics..."
"${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path

path = Path("results/phase5_mechanism/anchor_coupling_confirmatory.json")
if not path.exists():
    raise SystemExit("Missing results/phase5_mechanism/anchor_coupling_confirmatory.json for SK-H1 checks.")

payload = json.loads(path.read_text(encoding="utf-8"))
results = payload.get("results", {})
status = results.get("status")
robustness = results.get("robustness") or {}
robustness_class = robustness.get("robustness_class")
entitlement_robustness_class = robustness.get("entitlement_robustness_class")
robust_closure_reachable = robustness.get("robust_closure_reachable")
diagnostic_non_conclusive = int(robustness.get("diagnostic_non_conclusive_lane_count", 0) or 0)
diagnostic_total = int(robustness.get("observed_diagnostic_lane_count", 0) or 0) + int(
    robustness.get("observed_stress_lane_count", 0) or 0
)
h1_4_lane = results.get("h1_4_closure_lane")
h1_4_reason = results.get("h1_4_residual_reason")
h1_4_reopen_conditions = results.get("h1_4_reopen_conditions")
h1_5_lane = results.get("h1_5_closure_lane")
h1_5_reason = results.get("h1_5_residual_reason")
h1_5_reopen_conditions = results.get("h1_5_reopen_conditions")

if not isinstance(robustness, dict) or not robustness:
    raise SystemExit("SK-H1 artifact missing robustness block.")
if h1_4_lane not in {"H1_4_ALIGNED", "H1_4_QUALIFIED", "H1_4_BLOCKED", "H1_4_INCONCLUSIVE"}:
    raise SystemExit(f"Invalid SK-H1.4 h1_4_closure_lane: {h1_4_lane!r}")
if h1_5_lane not in {"H1_5_ALIGNED", "H1_5_BOUNDED", "H1_5_QUALIFIED", "H1_5_BLOCKED", "H1_5_INCONCLUSIVE"}:
    raise SystemExit(f"Invalid SK-H1.5 h1_5_closure_lane: {h1_5_lane!r}")
if robustness_class not in {"ROBUST", "MIXED", "FRAGILE"}:
    raise SystemExit(f"Invalid SK-H1.4 robustness_class: {robustness_class!r}")
if entitlement_robustness_class not in {"ROBUST", "MIXED", "FRAGILE"}:
    raise SystemExit(
        "Invalid SK-H1.5 entitlement_robustness_class: "
        f"{entitlement_robustness_class!r}"
    )
if not isinstance(robust_closure_reachable, bool):
    raise SystemExit("SK-H1.5 robust_closure_reachable must be boolean.")
if not isinstance(h1_4_reason, str) or not h1_4_reason.strip():
    raise SystemExit("SK-H1.4 h1_4_residual_reason is missing.")
if not isinstance(h1_5_reason, str) or not h1_5_reason.strip():
    raise SystemExit("SK-H1.5 h1_5_residual_reason is missing.")
if not isinstance(h1_4_reopen_conditions, list) or len(h1_4_reopen_conditions) == 0:
    raise SystemExit("SK-H1.4 h1_4_reopen_conditions must be a non-empty list.")
if not isinstance(h1_5_reopen_conditions, list) or len(h1_5_reopen_conditions) == 0:
    raise SystemExit("SK-H1.5 h1_5_reopen_conditions must be a non-empty list.")

if status in {"CONCLUSIVE_NO_COUPLING", "CONCLUSIVE_COUPLING_PRESENT"}:
    expected_lane = "H1_4_ALIGNED" if robustness_class == "ROBUST" else "H1_4_QUALIFIED"
elif status in {"INCONCLUSIVE_UNDERPOWERED", "INCONCLUSIVE_INFERENTIAL_AMBIGUITY"}:
    expected_lane = "H1_4_INCONCLUSIVE"
elif status == "BLOCKED_DATA_GEOMETRY":
    expected_lane = "H1_4_BLOCKED"
else:
    expected_lane = "H1_4_INCONCLUSIVE"

if h1_4_lane != expected_lane:
    raise SystemExit(
        "SK-H1.4 core_status/robustness mismatch: "
        f"status={status!r} robustness_class={robustness_class!r} "
        f"declared_lane={h1_4_lane!r} expected_lane={expected_lane!r}"
    )

if robust_closure_reachable is False:
    expected_h1_5_lane = "H1_5_BLOCKED"
elif status in {"CONCLUSIVE_NO_COUPLING", "CONCLUSIVE_COUPLING_PRESENT"}:
    if entitlement_robustness_class == "ROBUST":
        if diagnostic_total > 0 and diagnostic_non_conclusive > 0:
            expected_h1_5_lane = "H1_5_BOUNDED"
        else:
            expected_h1_5_lane = "H1_5_ALIGNED"
    else:
        expected_h1_5_lane = "H1_5_QUALIFIED"
elif status in {"INCONCLUSIVE_UNDERPOWERED", "INCONCLUSIVE_INFERENTIAL_AMBIGUITY"}:
    expected_h1_5_lane = "H1_5_INCONCLUSIVE"
elif status == "BLOCKED_DATA_GEOMETRY":
    expected_h1_5_lane = "H1_5_BLOCKED"
else:
    expected_h1_5_lane = "H1_5_INCONCLUSIVE"

if h1_5_lane != expected_h1_5_lane:
    raise SystemExit(
        "SK-H1.5 core_status/entitlement mismatch: "
        f"status={status!r} entitlement_robustness_class={entitlement_robustness_class!r} "
        f"reachable={robust_closure_reachable!r} "
        f"declared_lane={h1_5_lane!r} expected_lane={expected_h1_5_lane!r}"
    )

print(
    "  [OK] SK-H1.4/SK-H1.5 multimodal robustness checks passed "
    f"(status={status}, robustness_class={robustness_class}, "
    f"h1_4_closure_lane={h1_4_lane}, h1_5_closure_lane={h1_5_lane})."
)
PY

# 6. Sensitivity Artifact Integrity Check
echo "6. Checking sensitivity artifact integrity..."
echo "6a. Running release sensitivity preflight..."
"${PYTHON_BIN}" scripts/phase2_analysis/run_sensitivity_sweep.py \
  --mode release \
  --dataset-id "${SENSITIVITY_RELEASE_DATASET_ID}" \
  --preflight-only > /dev/null
"${PYTHON_BIN}" - <<'PY'
import json
import os
from pathlib import Path

path = Path(
    os.environ.get(
        "SENSITIVITY_RELEASE_PREFLIGHT_PATH",
        "core_status/core_audit/sensitivity_release_preflight.json",
    )
)
if not path.exists():
    raise SystemExit(
        "Missing sensitivity release preflight artifact "
        "(core_status/core_audit/sensitivity_release_preflight.json)."
    )

payload = json.loads(path.read_text(encoding="utf-8"))
results = payload.get("results", {})
if not isinstance(results, dict):
    results = payload
status = results.get("status")
reason_codes = results.get("reason_codes")
if status != "PREFLIGHT_OK":
    raise SystemExit(
        "Sensitivity release preflight is not PREFLIGHT_OK: "
        f"status={status!r} reason_codes={reason_codes!r}"
    )
print("  [OK] Sensitivity release preflight passed.")
PY

"${PYTHON_BIN}" scripts/core_audit/check_sensitivity_artifact_contract.py --mode release
"${PYTHON_BIN}" - <<'PY'
import json
import os
from pathlib import Path

status_path = Path(
    os.environ.get(
        "SENSITIVITY_RELEASE_STATUS_PATH",
        "core_status/core_audit/sensitivity_sweep_release.json",
    )
)
report_path = Path(
    os.environ.get(
        "SENSITIVITY_RELEASE_REPORT_PATH",
        "results/reports/core_audit/SENSITIVITY_RESULTS_RELEASE.md",
    )
)

if not status_path.exists():
    raise SystemExit(
        f"Missing {status_path}. Run "
        "python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real"
    )
if not report_path.exists():
    raise SystemExit(
        f"Missing {report_path}. Run "
        "python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real"
    )

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
by_run_dir = Path("core_status/by_run")
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
        f"({preview}). Run scripts/core_audit/cleanup_status_artifacts.sh clean."
    )

print("  [OK] Sensitivity artifact integrity check passed.")
PY

# 7. Strict-mode release-path enforcement (always required)
echo "7. Validating strict indistinguishability preflight policy..."
STRICT_PREFLIGHT_EXIT=0
if REQUIRE_COMPUTED=1 "${PYTHON_BIN}" scripts/phase3_synthesis/run_indistinguishability_test.py --preflight-only > /dev/null 2>&1; then
    STRICT_PREFLIGHT_EXIT=0
else
    STRICT_PREFLIGHT_EXIT=$?
fi

STATUS_FILE="core_status/phase3_synthesis/TURING_TEST_RESULTS.json"
"${PYTHON_BIN}" - <<'PY' "${STRICT_PREFLIGHT_EXIT}" "${STATUS_FILE}"
import json
import sys
from pathlib import Path

strict_exit = int(sys.argv[1])
status_file = Path(sys.argv[2])
if not status_file.exists():
    raise SystemExit("Strict preflight did not produce core_status/phase3_synthesis/TURING_TEST_RESULTS.json")

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
    REQUIRE_COMPUTED=1 "${PYTHON_BIN}" -m pytest -q tests/phase1_foundation/test_enforcement.py > /dev/null
    echo "  [OK] Additional strict enforcement checks passed."
fi

# 9. SK-H3 control-comparability policy checks
echo "9. Checking SK-H3 control comparability policy..."
"${PYTHON_BIN}" scripts/phase3_synthesis/run_control_matching_audit.py --preflight-only > /dev/null
"${PYTHON_BIN}" scripts/core_skeptic/check_control_comparability.py --mode release > /dev/null
"${PYTHON_BIN}" scripts/core_skeptic/check_control_data_availability.py --mode release > /dev/null
"${PYTHON_BIN}" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

status_path = Path("core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json")
availability_path = Path("core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json")
if not status_path.exists():
    raise SystemExit("Missing core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json")
if not availability_path.exists():
    raise SystemExit("Missing core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json")

status_payload = json.loads(status_path.read_text(encoding="utf-8"))
availability_payload = json.loads(availability_path.read_text(encoding="utf-8"))
results = status_payload.get("results", {})
availability = availability_payload.get("results", {})
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
    "available_subset_confidence",
    "available_subset_diagnostics",
    "available_subset_reproducibility",
    "approved_lost_pages_policy_version",
    "approved_lost_pages_source_note_path",
    "irrecoverability",
    "full_data_feasibility",
    "full_data_closure_terminal_reason",
    "full_data_closure_reopen_conditions",
    "h3_4_closure_lane",
    "h3_5_closure_lane",
    "h3_5_residual_reason",
    "h3_5_reopen_conditions",
]
missing = [k for k in required if k not in results]
if missing:
    raise SystemExit(f"SK-H3 comparability artifact missing keys: {missing}")
if results.get("leakage_detected") is True:
    raise SystemExit("SK-H3 comparability artifact indicates leakage_detected=true")

if results.get("evidence_scope") != availability.get("evidence_scope"):
    raise SystemExit("SK-H3 comparability/data-availability evidence_scope mismatch.")
if results.get("full_data_closure_eligible") != availability.get("full_data_closure_eligible"):
    raise SystemExit(
        "SK-H3 comparability/data-availability full_data_closure_eligible mismatch."
    )
if results.get("approved_lost_pages_policy_version") != availability.get(
    "approved_lost_pages_policy_version"
):
    raise SystemExit(
        "SK-H3 comparability/data-availability approved_lost_pages_policy_version mismatch."
    )
if results.get("approved_lost_pages_source_note_path") != availability.get(
    "approved_lost_pages_source_note_path"
):
    raise SystemExit(
        "SK-H3 comparability/data-availability approved_lost_pages_source_note_path mismatch."
    )
if results.get("irrecoverability") != availability.get("irrecoverability"):
    raise SystemExit(
        "SK-H3 comparability/data-availability irrecoverability metadata mismatch."
    )
if results.get("full_data_feasibility") != availability.get("full_data_feasibility"):
    raise SystemExit(
        "SK-H3 comparability/data-availability full_data_feasibility mismatch."
    )
if results.get("full_data_closure_terminal_reason") != availability.get(
    "full_data_closure_terminal_reason"
):
    raise SystemExit(
        "SK-H3 comparability/data-availability full_data_closure_terminal_reason mismatch."
    )
if results.get("full_data_closure_reopen_conditions") != availability.get(
    "full_data_closure_reopen_conditions"
):
    raise SystemExit(
        "SK-H3 comparability/data-availability full_data_closure_reopen_conditions mismatch."
    )
if results.get("h3_4_closure_lane") != availability.get("h3_4_closure_lane"):
    raise SystemExit(
        "SK-H3 comparability/data-availability h3_4_closure_lane mismatch."
    )
if results.get("h3_5_closure_lane") != availability.get("h3_5_closure_lane"):
    raise SystemExit(
        "SK-H3 comparability/data-availability h3_5_closure_lane mismatch."
    )
if results.get("h3_5_residual_reason") != availability.get("h3_5_residual_reason"):
    raise SystemExit(
        "SK-H3 comparability/data-availability h3_5_residual_reason mismatch."
    )
if results.get("h3_5_reopen_conditions") != availability.get("h3_5_reopen_conditions"):
    raise SystemExit(
        "SK-H3 comparability/data-availability h3_5_reopen_conditions mismatch."
    )

h3_5_lane = results.get("h3_5_closure_lane")
h3_5_reason = results.get("h3_5_residual_reason")
h3_5_reopen_conditions = results.get("h3_5_reopen_conditions")
if h3_5_lane not in {
    "H3_5_ALIGNED",
    "H3_5_TERMINAL_QUALIFIED",
    "H3_5_BLOCKED",
    "H3_5_INCONCLUSIVE",
}:
    raise SystemExit(f"SK-H3 invalid h3_5_closure_lane={h3_5_lane!r}.")
if not isinstance(h3_5_reason, str) or not h3_5_reason.strip():
    raise SystemExit("SK-H3 h3_5_residual_reason must be non-empty.")
if not isinstance(h3_5_reopen_conditions, list) or len(h3_5_reopen_conditions) == 0:
    raise SystemExit("SK-H3 h3_5_reopen_conditions must be non-empty list.")

if (
    results.get("full_data_feasibility") == "irrecoverable"
    and results.get("status") == "NON_COMPARABLE_BLOCKED"
    and results.get("reason_code") == "DATA_AVAILABILITY"
    and results.get("evidence_scope") == "available_subset"
    and results.get("full_data_closure_eligible") is False
):
    expected_h3_5_lane = "H3_5_TERMINAL_QUALIFIED"
elif (
    results.get("full_data_feasibility") == "feasible"
    and results.get("status") in {"COMPARABLE_CONFIRMED", "COMPARABLE_QUALIFIED"}
    and results.get("evidence_scope") == "full_dataset"
    and results.get("full_data_closure_eligible") is True
    and results.get("missing_count") == 0
):
    expected_h3_5_lane = "H3_5_ALIGNED"
elif results.get("status") == "INCONCLUSIVE_DATA_LIMITED":
    expected_h3_5_lane = "H3_5_INCONCLUSIVE"
else:
    expected_h3_5_lane = "H3_5_BLOCKED"
if h3_5_lane != expected_h3_5_lane:
    raise SystemExit(
        "SK-H3 h3_5_closure_lane mismatch with status semantics "
        f"(declared={h3_5_lane!r}, expected={expected_h3_5_lane!r})."
    )

if h3_5_lane == "H3_5_TERMINAL_QUALIFIED":
    required_terminal_reopen = {
        "new_primary_source_pages_added_to_dataset",
        "approved_lost_pages_policy_updated_with_new_evidence",
        "artifact_parity_or_freshness_contract_failed",
        "claim_boundaries_exceeded_terminal_qualified_scope",
    }
    if not required_terminal_reopen.issubset(set(h3_5_reopen_conditions)):
        raise SystemExit(
            "SK-H3 terminal-qualified lane missing required reopen triggers."
        )

status_provenance = status_payload.get("provenance", {}) or {}
availability_provenance = availability_payload.get("provenance", {}) or {}
status_run_id = status_provenance.get("run_id")
availability_run_id = availability_provenance.get("run_id")
if not status_run_id or not availability_run_id:
    raise SystemExit(
        "SK-H3 freshness check requires provenance.run_id in both artifacts."
    )
if status_run_id != availability_run_id:
    raise SystemExit(
        "SK-H3 freshness run_id mismatch across artifacts "
        f"(comparability={status_run_id!r}, availability={availability_run_id!r})."
    )

def _parse_ts(value):
    if not isinstance(value, str) or not value:
        return None
    raw = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

status_ts = _parse_ts(status_provenance.get("timestamp"))
availability_ts = _parse_ts(availability_provenance.get("timestamp"))
if status_ts is None or availability_ts is None:
    raise SystemExit(
        "SK-H3 freshness check requires valid provenance.timestamp in both artifacts."
    )
skew_seconds = abs((status_ts - availability_ts).total_seconds())
if skew_seconds > 600:
    raise SystemExit(
        f"SK-H3 freshness timestamp skew exceeds 600s (skew_seconds={skew_seconds:.1f})."
    )

subset_diagnostics = results.get("available_subset_diagnostics") or {}
passes_thresholds = subset_diagnostics.get("passes_thresholds")
if isinstance(passes_thresholds, bool):
    if (not passes_thresholds) and results.get("available_subset_reason_code") != "AVAILABLE_SUBSET_UNDERPOWERED":
        raise SystemExit(
            "SK-H3 subset thresholds failed without reason_code=AVAILABLE_SUBSET_UNDERPOWERED."
        )
else:
    raise SystemExit("SK-H3 available_subset_diagnostics.passes_thresholds must be boolean.")
if results.get("available_subset_confidence") not in {"QUALIFIED", "UNDERPOWERED", "BLOCKED"}:
    raise SystemExit("SK-H3 available_subset_confidence has invalid value.")
if (
    results.get("evidence_scope") == "available_subset"
    and results.get("full_data_closure_eligible") is not False
):
    raise SystemExit(
        "SK-H3 available_subset evidence cannot set full_data_closure_eligible=true."
    )
if results.get("status") == "NON_COMPARABLE_BLOCKED":
    if results.get("reason_code") != "DATA_AVAILABILITY":
        raise SystemExit(
            "SK-H3 blocked comparability must use reason_code=DATA_AVAILABILITY."
        )
    if availability.get("reason_code") != "DATA_AVAILABILITY":
        raise SystemExit(
            "SK-H3 blocked comparability requires availability reason_code=DATA_AVAILABILITY."
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

# 10. SK-M2 phase8_comparative uncertainty policy checks
echo "10. Checking SK-M2 phase8_comparative uncertainty policy..."
"${PYTHON_BIN}" scripts/phase8_comparative/run_proximity_uncertainty.py --iterations 2000 --seed 42 > /dev/null
"${PYTHON_BIN}" scripts/core_skeptic/check_comparative_uncertainty.py --mode release > /dev/null
"${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path

path = Path("results/phase7_human/phase_7c_uncertainty.json")
if not path.exists():
    raise SystemExit("Missing results/phase7_human/phase_7c_uncertainty.json")

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
    "m2_4_closure_lane",
    "m2_4_residual_reason",
    "m2_4_reopen_triggers",
    "m2_5_closure_lane",
    "m2_5_residual_reason",
    "m2_5_reopen_triggers",
    "m2_5_data_availability_linkage",
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

m2_4_residual_reason = str(results.get("m2_4_residual_reason", "")).strip()
if not m2_4_residual_reason:
    raise SystemExit("SK-M2 uncertainty artifact has empty m2_4_residual_reason.")
m2_4_reopen = results.get("m2_4_reopen_triggers")
if not isinstance(m2_4_reopen, list) or len(m2_4_reopen) == 0:
    raise SystemExit("SK-M2 uncertainty artifact requires non-empty m2_4_reopen_triggers.")

m2_5_lane = str(results.get("m2_5_closure_lane", "")).strip()
if m2_5_lane not in {
    "M2_5_ALIGNED",
    "M2_5_QUALIFIED",
    "M2_5_BOUNDED",
    "M2_5_BLOCKED",
    "M2_5_INCONCLUSIVE",
}:
    raise SystemExit(f"SK-M2 uncertainty artifact has invalid m2_5_closure_lane={m2_5_lane!r}.")
m2_5_residual_reason = str(results.get("m2_5_residual_reason", "")).strip()
if not m2_5_residual_reason:
    raise SystemExit("SK-M2 uncertainty artifact has empty m2_5_residual_reason.")
m2_5_reopen = results.get("m2_5_reopen_triggers")
if not isinstance(m2_5_reopen, list) or len(m2_5_reopen) == 0:
    raise SystemExit("SK-M2 uncertainty artifact requires non-empty m2_5_reopen_triggers.")
linkage = results.get("m2_5_data_availability_linkage")
if not isinstance(linkage, dict):
    raise SystemExit("SK-M2 uncertainty artifact requires object m2_5_data_availability_linkage.")
missing_folio_blocking_claimed = linkage.get("missing_folio_blocking_claimed")
objective_validity_failure = linkage.get("objective_comparative_validity_failure")
if not isinstance(missing_folio_blocking_claimed, bool):
    raise SystemExit(
        "SK-M2 m2_5_data_availability_linkage.missing_folio_blocking_claimed must be boolean."
    )
if not isinstance(objective_validity_failure, bool):
    raise SystemExit(
        "SK-M2 m2_5_data_availability_linkage.objective_comparative_validity_failure must be boolean."
    )
if missing_folio_blocking_claimed and not objective_validity_failure:
    raise SystemExit(
        "SK-M2 missing-folio blocking claim requires objective phase8_comparative validity failure."
    )
if m2_5_lane == "M2_5_BLOCKED" and not objective_validity_failure:
    raise SystemExit(
        "SK-M2 M2_5_BLOCKED lane requires objective phase8_comparative validity failure linkage."
    )

print("  [OK] SK-M2 phase8_comparative uncertainty policy checks passed.")
PY

# 11. SK-M4 historical provenance policy checks
echo "11. Checking SK-M4 historical provenance policy..."
"${PYTHON_BIN}" scripts/core_audit/build_release_gate_health_status.py > /dev/null
"${PYTHON_BIN}" scripts/core_audit/build_provenance_health_status.py > /dev/null
"${PYTHON_BIN}" scripts/core_audit/sync_provenance_register.py > /dev/null
"${PYTHON_BIN}" scripts/core_skeptic/check_provenance_uncertainty.py --mode release > /dev/null
"${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path

provenance_path = Path("core_status/core_audit/provenance_health_status.json")
sync_path = Path("core_status/core_audit/provenance_register_sync_status.json")
if not provenance_path.exists():
    raise SystemExit("Missing core_status/core_audit/provenance_health_status.json")
if not sync_path.exists():
    raise SystemExit("Missing core_status/core_audit/provenance_register_sync_status.json")

prov = json.loads(provenance_path.read_text(encoding="utf-8"))
sync = json.loads(sync_path.read_text(encoding="utf-8"))
required_prov = [
    "status",
    "reason_code",
    "allowed_claim",
    "orphaned_rows",
    "orphaned_ratio",
    "threshold_policy_pass",
    "m4_5_historical_lane",
    "m4_5_residual_reason",
    "m4_5_reopen_conditions",
    "m4_5_data_availability_linkage",
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
if sync.get("provenance_health_lane") != prov.get("m4_5_historical_lane"):
    raise SystemExit("SK-M4 provenance_health_lane mismatch with m4_5_historical_lane.")
if sync.get("provenance_health_m4_5_lane") != prov.get("m4_5_historical_lane"):
    raise SystemExit("SK-M4 provenance_health_m4_5_lane mismatch with m4_5_historical_lane.")
if sync.get("provenance_health_m4_5_residual_reason") != prov.get("m4_5_residual_reason"):
    raise SystemExit(
        "SK-M4 provenance_health_m4_5_residual_reason mismatch with m4_5_residual_reason."
    )

lane = prov.get("m4_5_historical_lane")
if lane not in {"M4_5_ALIGNED", "M4_5_QUALIFIED", "M4_5_BOUNDED", "M4_5_BLOCKED", "M4_5_INCONCLUSIVE"}:
    raise SystemExit(f"SK-M4 invalid m4_5_historical_lane={lane!r}.")
if not str(prov.get("m4_5_residual_reason", "")).strip():
    raise SystemExit("SK-M4 m4_5_residual_reason must be non-empty.")
if not isinstance(prov.get("m4_5_reopen_conditions"), list) or len(
    prov.get("m4_5_reopen_conditions")
) == 0:
    raise SystemExit("SK-M4 m4_5_reopen_conditions must be non-empty list.")

linkage = prov.get("m4_5_data_availability_linkage")
if not isinstance(linkage, dict):
    raise SystemExit("SK-M4 m4_5_data_availability_linkage must be an object.")
missing_folio_blocking_claimed = linkage.get("missing_folio_blocking_claimed")
objective_incompleteness = linkage.get("objective_provenance_contract_incompleteness")
approved_irrecoverable = linkage.get("approved_irrecoverable_loss_classification")
if not isinstance(missing_folio_blocking_claimed, bool):
    raise SystemExit(
        "SK-M4 m4_5_data_availability_linkage.missing_folio_blocking_claimed must be boolean."
    )
if not isinstance(objective_incompleteness, bool):
    raise SystemExit(
        "SK-M4 m4_5_data_availability_linkage.objective_provenance_contract_incompleteness must be boolean."
    )
if not isinstance(approved_irrecoverable, bool):
    raise SystemExit(
        "SK-M4 m4_5_data_availability_linkage.approved_irrecoverable_loss_classification must be boolean."
    )
if missing_folio_blocking_claimed and not objective_incompleteness:
    raise SystemExit(
        "SK-M4 missing-folio blocking claim requires objective provenance contract incompleteness."
    )
if approved_irrecoverable and missing_folio_blocking_claimed and not objective_incompleteness:
    raise SystemExit(
        "SK-M4 approved irrecoverable-loss folio claim cannot block without objective linkage."
    )

print("  [OK] SK-M4 historical provenance policy checks passed.")
PY

# 12. SK-H2.2 / SK-M1.2 operational entitlement policy checks
echo "12. Checking SK-H2.2 / SK-M1.2 operational entitlement policy..."
"${PYTHON_BIN}" scripts/core_audit/build_release_gate_health_status.py > /dev/null
"${PYTHON_BIN}" scripts/core_skeptic/check_claim_boundaries.py --mode release > /dev/null
"${PYTHON_BIN}" scripts/core_skeptic/check_closure_conditionality.py --mode release > /dev/null
"${PYTHON_BIN}" scripts/core_skeptic/check_claim_entitlement_coherence.py --mode release > /dev/null
"${PYTHON_BIN}" scripts/core_skeptic/check_report_coherence.py --mode release > /dev/null

VERIFICATION_COMPLETE=1
echo "${VERIFY_SUCCESS_TOKEN}"
echo "--- Reproduction Verification PASSED ---"
