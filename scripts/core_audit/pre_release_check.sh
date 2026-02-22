#!/bin/bash
set -euo pipefail

echo "--- Pre-Release Baseline Check ---"

if [ ! -f "AUDIT_LOG.md" ]; then
  echo "[FAIL] Missing AUDIT_LOG.md"
  exit 1
fi

echo "[OK] AUDIT_LOG.md present"

SENSITIVITY_RELEASE_STATUS_PATH="${SENSITIVITY_RELEASE_STATUS_PATH:-core_status/core_audit/sensitivity_sweep_release.json}"
SENSITIVITY_RELEASE_REPORT_PATH="${SENSITIVITY_RELEASE_REPORT_PATH:-results/reports/core_audit/SENSITIVITY_RESULTS_RELEASE.md}"
SENSITIVITY_RELEASE_PREFLIGHT_PATH="${SENSITIVITY_RELEASE_PREFLIGHT_PATH:-core_status/core_audit/sensitivity_release_preflight.json}"
SENSITIVITY_RELEASE_RUN_STATUS_PATH="${SENSITIVITY_RELEASE_RUN_STATUS_PATH:-core_status/core_audit/sensitivity_release_run_status.json}"
SENSITIVITY_RELEASE_DATASET_ID="${SENSITIVITY_RELEASE_DATASET_ID:-voynich_real}"
export SENSITIVITY_RELEASE_STATUS_PATH
export SENSITIVITY_RELEASE_REPORT_PATH
export SENSITIVITY_RELEASE_PREFLIGHT_PATH
export SENSITIVITY_RELEASE_RUN_STATUS_PATH
export SENSITIVITY_RELEASE_DATASET_ID

echo "[P0] Runtime dependency preflight..."
python3 scripts/core_audit/check_runtime_dependencies.py --mode release

echo "[SK-C1.4] Running release sensitivity preflight..."
python3 scripts/phase2_analysis/run_sensitivity_sweep.py \
  --mode release \
  --dataset-id "${SENSITIVITY_RELEASE_DATASET_ID}" \
  --preflight-only > /dev/null

python3 - <<'PY'
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
        "[FAIL] Missing sensitivity release preflight artifact "
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
        "[FAIL] Sensitivity release preflight is not PREFLIGHT_OK "
        f"(status={status!r}, reason_codes={reason_codes!r})."
    )

print("[OK] Sensitivity release preflight passed.")
PY

if [ ! -f "${SENSITIVITY_RELEASE_STATUS_PATH}" ]; then
  echo "[FAIL] Missing ${SENSITIVITY_RELEASE_STATUS_PATH}"
  echo "       Generate release-candidate sensitivity evidence with:"
  echo "       python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real"
  exit 1
fi

if [ ! -f "${SENSITIVITY_RELEASE_REPORT_PATH}" ]; then
  echo "[FAIL] Missing ${SENSITIVITY_RELEASE_REPORT_PATH}"
  echo "       Generate release-candidate sensitivity report with:"
  echo "       python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real"
  exit 1
fi

echo "[SK-C1.2] Validating sensitivity artifact/report contract (release mode)..."
python3 scripts/core_audit/check_sensitivity_artifact_contract.py --mode release

echo "[SK-C2.2] Validating provenance runner contract (release mode)..."
python3 scripts/core_audit/check_provenance_runner_contract.py --mode release

echo "[SK-H1.2] Validating multimodal coupling policy (release mode)..."
python3 scripts/core_skeptic/check_multimodal_coupling.py --mode release

python3 - <<'PY'
import json
from pathlib import Path

path = Path("results/data/phase5_mechanism/anchor_coupling_confirmatory.json")
if not path.exists():
    raise SystemExit(
        "[FAIL] Missing results/data/phase5_mechanism/anchor_coupling_confirmatory.json for SK-H1 checks."
    )
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
lane_id = robustness.get("lane_id")
publication_lane_id = robustness.get("publication_lane_id")
agreement_ratio = robustness.get("agreement_ratio")

if not isinstance(robustness, dict) or not robustness:
    raise SystemExit("[FAIL] SK-H1 artifact is missing robustness metadata.")
if h1_4_lane not in {"H1_4_ALIGNED", "H1_4_QUALIFIED", "H1_4_BLOCKED", "H1_4_INCONCLUSIVE"}:
    raise SystemExit(f"[FAIL] SK-H1.4 invalid h1_4_closure_lane={h1_4_lane!r}.")
if h1_5_lane not in {"H1_5_ALIGNED", "H1_5_BOUNDED", "H1_5_QUALIFIED", "H1_5_BLOCKED", "H1_5_INCONCLUSIVE"}:
    raise SystemExit(f"[FAIL] SK-H1.5 invalid h1_5_closure_lane={h1_5_lane!r}.")
if not isinstance(h1_4_reason, str) or not h1_4_reason.strip():
    raise SystemExit("[FAIL] SK-H1.4 h1_4_residual_reason is missing.")
if not isinstance(h1_5_reason, str) or not h1_5_reason.strip():
    raise SystemExit("[FAIL] SK-H1.5 h1_5_residual_reason is missing.")
if not isinstance(h1_4_reopen_conditions, list) or len(h1_4_reopen_conditions) == 0:
    raise SystemExit("[FAIL] SK-H1.4 h1_4_reopen_conditions must be a non-empty list.")
if not isinstance(h1_5_reopen_conditions, list) or len(h1_5_reopen_conditions) == 0:
    raise SystemExit("[FAIL] SK-H1.5 h1_5_reopen_conditions must be a non-empty list.")
if robustness_class not in {"ROBUST", "MIXED", "FRAGILE"}:
    raise SystemExit(f"[FAIL] SK-H1.4 invalid robustness_class={robustness_class!r}.")
if entitlement_robustness_class not in {"ROBUST", "MIXED", "FRAGILE"}:
    raise SystemExit(
        "[FAIL] SK-H1.5 invalid entitlement_robustness_class="
        f"{entitlement_robustness_class!r}."
    )
if not isinstance(robust_closure_reachable, bool):
    raise SystemExit("[FAIL] SK-H1.5 robust_closure_reachable must be boolean.")
if lane_id is None or publication_lane_id is None:
    raise SystemExit("[FAIL] SK-H1.4 robustness lane_id/publication_lane_id are required.")
if not isinstance(agreement_ratio, (int, float)):
    raise SystemExit("[FAIL] SK-H1.4 robustness agreement_ratio must be numeric.")

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
        "[FAIL] SK-H1.4 core_status/robustness mismatch: "
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
        "[FAIL] SK-H1.5 core_status/entitlement mismatch: "
        f"status={status!r} entitlement_robustness_class={entitlement_robustness_class!r} "
        f"reachable={robust_closure_reachable!r} "
        f"declared_lane={h1_5_lane!r} expected_lane={expected_h1_5_lane!r}"
    )

print(
    "[OK] SK-H1.4/SK-H1.5 multimodal robustness contract passed "
    f"(status={status}, robustness_class={robustness_class}, "
    f"h1_4_closure_lane={h1_4_lane}, h1_5_closure_lane={h1_5_lane})."
)
PY

python3 - <<'PY'
import json
import os
from pathlib import Path

path = Path(
    os.environ.get(
        "SENSITIVITY_RELEASE_STATUS_PATH",
        "core_status/core_audit/sensitivity_sweep_release.json",
    )
)
data = json.loads(path.read_text(encoding="utf-8"))
summary = data.get("results", {}).get("summary", {})
mode = summary.get("execution_mode")
release_ready = summary.get("release_evidence_ready")
expected = summary.get("scenario_count_expected")
executed = summary.get("scenario_count_executed")
decision = summary.get("robustness_decision")
quality_gate_passed = summary.get("quality_gate_passed")
robustness_conclusive = summary.get("robustness_conclusive")
dataset_policy_pass = summary.get("dataset_policy_pass")
warning_policy_pass = summary.get("warning_policy_pass")
warning_density = summary.get("warning_density_per_scenario")
total_warning_count = summary.get("total_warning_count")
caveats = summary.get("caveats")

if mode != "release":
    raise SystemExit(f"[FAIL] Sensitivity execution_mode must be 'release' (got {mode!r})")
if dataset_policy_pass is not True:
    raise SystemExit(
        "[FAIL] Sensitivity dataset policy is not satisfied "
        "(dataset_policy_pass=true required for release evidence)."
    )
if warning_policy_pass is not True:
    raise SystemExit(
        "[FAIL] Sensitivity warning policy is not satisfied "
        "(warning_policy_pass=true required for release evidence)."
    )
if release_ready is not True:
    raise SystemExit(
        "[FAIL] release sensitivity artifact is not marked release_evidence_ready=true "
        "(full sweep + conclusive robustness + quality gate)"
    )
if expected != executed:
    raise SystemExit(f"[FAIL] Sensitivity scenarios incomplete: {executed}/{expected}")
if decision == "INCONCLUSIVE":
    raise SystemExit(
        "[FAIL] Sensitivity robustness_decision is INCONCLUSIVE; "
        "release baseline requires conclusive PASS/FAIL evidence."
    )
if robustness_conclusive is not True:
    raise SystemExit(
        "[FAIL] Sensitivity summary missing robustness_conclusive=true; "
        "regenerate artifact with updated sweep runner."
    )
if quality_gate_passed is not True:
    raise SystemExit(
        "[FAIL] Sensitivity quality gate failed; "
        "release baseline requires sufficient valid scenarios and non-collapse."
    )
if warning_density is None:
    raise SystemExit(
        "[FAIL] Sensitivity summary missing warning_density_per_scenario field."
    )
if total_warning_count is None:
    raise SystemExit(
        "[FAIL] Sensitivity summary missing total_warning_count field."
    )
if total_warning_count > 0 and (not isinstance(caveats, list) or len(caveats) == 0):
    raise SystemExit(
        "[FAIL] Sensitivity warnings are present but caveats list is empty. "
        "Warning-bearing release evidence must include explicit caveats."
    )

print(f"[OK] Sensitivity artifact release-ready ({executed}/{expected})")
PY

python3 - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

path = Path("core_status/phase3_synthesis/TURING_TEST_RESULTS.json")
if not path.exists():
    raise SystemExit(
        "[FAIL] Missing core_status/phase3_synthesis/TURING_TEST_RESULTS.json. "
        "Run strict preflight: REQUIRE_COMPUTED=1 python3 scripts/phase3_synthesis/run_indistinguishability_test.py --preflight-only"
    )

payload = json.loads(path.read_text(encoding="utf-8"))
results = payload.get("results", {})
status = results.get("status")
strict = results.get("strict_computed")
reason_code = results.get("reason_code")
preflight = results.get("preflight") or {}
missing_count = preflight.get("missing_count")

if strict is not True:
    raise SystemExit(
        "[FAIL] TURING_TEST_RESULTS must be generated from strict preflight "
        "(strict_computed=true)."
    )

if status == "PREFLIGHT_OK":
    if missing_count not in (0, None):
        raise SystemExit(
            "[FAIL] Strict preflight marked PREFLIGHT_OK but missing_count is non-zero."
        )
elif status == "BLOCKED":
    if reason_code != "DATA_AVAILABILITY":
        raise SystemExit(
            "[FAIL] Strict preflight BLOCKED without approved reason_code=DATA_AVAILABILITY."
        )
    if missing_count is None:
        raise SystemExit(
            "[FAIL] Strict preflight BLOCKED but preflight missing_count is absent."
        )
else:
    raise SystemExit(f"[FAIL] Unexpected TURING_TEST_RESULTS status: {status!r}")

print(
    "[OK] Strict indistinguishability preflight artifact is policy-compliant "
    f"(status={status}, reason_code={reason_code}, missing_count={missing_count})."
)
PY

echo "[SK-H3] Generating control matching core_audit artifact..."
python3 scripts/phase3_synthesis/run_control_matching_audit.py --preflight-only > /dev/null

echo "[SK-H3] Validating control comparability policy (release mode)..."
python3 scripts/core_skeptic/check_control_comparability.py --mode release

echo "[SK-H3] Validating control data-availability policy (release mode)..."
python3 scripts/core_skeptic/check_control_data_availability.py --mode release

python3 - <<'PY'
import json
from pathlib import Path

status_path = Path("core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json")
availability_path = Path("core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json")
if not status_path.exists():
    raise SystemExit(
        "[FAIL] Missing core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json after SK-H3 core_audit."
    )
if not availability_path.exists():
    raise SystemExit(
        "[FAIL] Missing core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json after SK-H3 core_audit."
    )

status_payload = json.loads(status_path.read_text(encoding="utf-8"))
availability_payload = json.loads(availability_path.read_text(encoding="utf-8"))
results = status_payload.get("results", {})
availability = availability_payload.get("results", {})
status = results.get("status")
reason_code = results.get("reason_code")
leakage_detected = results.get("leakage_detected")
evidence_scope = results.get("evidence_scope")
full_data_closure_eligible = results.get("full_data_closure_eligible")
missing_count = results.get("missing_count")
approved_policy_version = results.get("approved_lost_pages_policy_version")
approved_source_note = results.get("approved_lost_pages_source_note_path")
irrecoverability = results.get("irrecoverability")
available_subset_status = results.get("available_subset_status")
available_subset_reason_code = results.get("available_subset_reason_code")
available_subset_confidence = results.get("available_subset_confidence")
available_subset_diagnostics = results.get("available_subset_diagnostics") or {}
availability_status = availability.get("status")
availability_reason_code = availability.get("reason_code")
availability_scope = availability.get("evidence_scope")
availability_full_closure_eligible = availability.get("full_data_closure_eligible")
availability_missing_count = availability.get("missing_count")
availability_policy_version = availability.get("approved_lost_pages_policy_version")
availability_source_note = availability.get("approved_lost_pages_source_note_path")
availability_irrecoverability = availability.get("irrecoverability")
full_data_feasibility = results.get("full_data_feasibility")
full_data_terminal_reason = results.get("full_data_closure_terminal_reason")
full_data_reopen_conditions = results.get("full_data_closure_reopen_conditions")
h3_4_closure_lane = results.get("h3_4_closure_lane")
h3_5_closure_lane = results.get("h3_5_closure_lane")
h3_5_residual_reason = results.get("h3_5_residual_reason")
h3_5_reopen_conditions = results.get("h3_5_reopen_conditions")
availability_feasibility = availability.get("full_data_feasibility")
availability_terminal_reason = availability.get("full_data_closure_terminal_reason")
availability_reopen_conditions = availability.get("full_data_closure_reopen_conditions")
availability_h3_4_closure_lane = availability.get("h3_4_closure_lane")
availability_h3_5_closure_lane = availability.get("h3_5_closure_lane")
availability_h3_5_residual_reason = availability.get("h3_5_residual_reason")
availability_h3_5_reopen_conditions = availability.get("h3_5_reopen_conditions")

status_provenance = status_payload.get("provenance", {}) or {}
availability_provenance = availability_payload.get("provenance", {}) or {}
status_run_id = status_provenance.get("run_id")
availability_run_id = availability_provenance.get("run_id")
if not status_run_id or not availability_run_id:
    raise SystemExit(
        "[FAIL] SK-H3 freshness check requires provenance.run_id in both artifacts."
    )
if status_run_id != availability_run_id:
    raise SystemExit(
        "[FAIL] SK-H3 freshness run_id mismatch across artifacts "
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
        "[FAIL] SK-H3 freshness check requires valid provenance.timestamp in both artifacts."
    )
ts_skew = abs((status_ts - availability_ts).total_seconds())
if ts_skew > 600:
    raise SystemExit(
        "[FAIL] SK-H3 freshness timestamp skew exceeds 600s "
        f"(skew_seconds={ts_skew:.1f})."
    )

if evidence_scope != availability_scope:
    raise SystemExit(
        "[FAIL] SK-H3 comparability/data-availability evidence_scope mismatch."
    )
if full_data_closure_eligible != availability_full_closure_eligible:
    raise SystemExit(
        "[FAIL] SK-H3 comparability/data-availability full_data_closure_eligible mismatch."
    )
if approved_policy_version != availability_policy_version:
    raise SystemExit(
        "[FAIL] SK-H3 comparability/data-availability approved_lost_pages_policy_version mismatch."
    )
if approved_source_note != availability_source_note:
    raise SystemExit(
        "[FAIL] SK-H3 comparability/data-availability approved_lost_pages_source_note_path mismatch."
    )
if irrecoverability != availability_irrecoverability:
    raise SystemExit(
        "[FAIL] SK-H3 comparability/data-availability irrecoverability metadata mismatch."
    )
if full_data_feasibility != availability_feasibility:
    raise SystemExit(
        "[FAIL] SK-H3 comparability/data-availability full_data_feasibility mismatch."
    )
if full_data_terminal_reason != availability_terminal_reason:
    raise SystemExit(
        "[FAIL] SK-H3 comparability/data-availability full_data_closure_terminal_reason mismatch."
    )
if full_data_reopen_conditions != availability_reopen_conditions:
    raise SystemExit(
        "[FAIL] SK-H3 comparability/data-availability full_data_closure_reopen_conditions mismatch."
    )
if h3_4_closure_lane != availability_h3_4_closure_lane:
    raise SystemExit(
        "[FAIL] SK-H3 comparability/data-availability h3_4_closure_lane mismatch."
    )
if h3_5_closure_lane != availability_h3_5_closure_lane:
    raise SystemExit(
        "[FAIL] SK-H3 comparability/data-availability h3_5_closure_lane mismatch."
    )
if h3_5_residual_reason != availability_h3_5_residual_reason:
    raise SystemExit(
        "[FAIL] SK-H3 comparability/data-availability h3_5_residual_reason mismatch."
    )
if h3_5_reopen_conditions != availability_h3_5_reopen_conditions:
    raise SystemExit(
        "[FAIL] SK-H3 comparability/data-availability h3_5_reopen_conditions mismatch."
    )

h3_5_allowed_lanes = {
    "H3_5_ALIGNED",
    "H3_5_TERMINAL_QUALIFIED",
    "H3_5_BLOCKED",
    "H3_5_INCONCLUSIVE",
}
if h3_5_closure_lane not in h3_5_allowed_lanes:
    raise SystemExit(
        f"[FAIL] SK-H3 invalid h3_5_closure_lane={h3_5_closure_lane!r}."
    )
if not isinstance(h3_5_residual_reason, str) or not h3_5_residual_reason.strip():
    raise SystemExit("[FAIL] SK-H3 h3_5_residual_reason must be non-empty.")
if not isinstance(h3_5_reopen_conditions, list) or len(h3_5_reopen_conditions) == 0:
    raise SystemExit("[FAIL] SK-H3 h3_5_reopen_conditions must be a non-empty list.")

if (
    full_data_feasibility == "irrecoverable"
    and status == "NON_COMPARABLE_BLOCKED"
    and reason_code == "DATA_AVAILABILITY"
    and evidence_scope == "available_subset"
    and full_data_closure_eligible is False
):
    expected_h3_5_lane = "H3_5_TERMINAL_QUALIFIED"
elif (
    full_data_feasibility == "feasible"
    and status in {"COMPARABLE_CONFIRMED", "COMPARABLE_QUALIFIED"}
    and evidence_scope == "full_dataset"
    and full_data_closure_eligible is True
    and missing_count == 0
):
    expected_h3_5_lane = "H3_5_ALIGNED"
elif status == "INCONCLUSIVE_DATA_LIMITED":
    expected_h3_5_lane = "H3_5_INCONCLUSIVE"
else:
    expected_h3_5_lane = "H3_5_BLOCKED"

if h3_5_closure_lane != expected_h3_5_lane:
    raise SystemExit(
        "[FAIL] SK-H3 h3_5_closure_lane does not match core_status/feasibility semantics "
        f"(declared={h3_5_closure_lane!r}, expected={expected_h3_5_lane!r})."
    )

if h3_5_closure_lane == "H3_5_TERMINAL_QUALIFIED":
    required_terminal_reopen = {
        "new_primary_source_pages_added_to_dataset",
        "approved_lost_pages_policy_updated_with_new_evidence",
        "artifact_parity_or_freshness_contract_failed",
        "claim_boundaries_exceeded_terminal_qualified_scope",
    }
    if not required_terminal_reopen.issubset(set(h3_5_reopen_conditions)):
        raise SystemExit(
            "[FAIL] SK-H3 terminal-qualified lane missing required reopen triggers."
        )

if status == "NON_COMPARABLE_BLOCKED":
    if reason_code != "DATA_AVAILABILITY":
        raise SystemExit(
            "[FAIL] SK-H3 comparability is blocked for non-approved reason "
            f"(reason_code={reason_code!r})."
        )
    if availability_reason_code != "DATA_AVAILABILITY":
        raise SystemExit(
            "[FAIL] SK-H3 blocked comparability requires availability reason_code=DATA_AVAILABILITY."
        )
    if evidence_scope != "available_subset":
        raise SystemExit(
            "[FAIL] SK-H3 blocked comparability must declare evidence_scope=available_subset."
        )
    if full_data_closure_eligible is not False:
        raise SystemExit(
            "[FAIL] SK-H3 blocked comparability must set full_data_closure_eligible=false."
        )
    if availability_status != "DATA_AVAILABILITY_BLOCKED":
        raise SystemExit(
            "[FAIL] SK-H3 blocked comparability requires DATA_AVAILABILITY_BLOCKED artifact state."
        )
    if missing_count != availability_missing_count:
        raise SystemExit(
            "[FAIL] SK-H3 blocked comparability missing_count mismatch across artifacts."
        )
    if available_subset_confidence not in {"QUALIFIED", "UNDERPOWERED", "BLOCKED"}:
        raise SystemExit(
            "[FAIL] SK-H3 blocked comparability has invalid available_subset_confidence."
        )
    passes_thresholds = available_subset_diagnostics.get("passes_thresholds")
    if passes_thresholds is False and available_subset_reason_code != "AVAILABLE_SUBSET_UNDERPOWERED":
        raise SystemExit(
            "[FAIL] SK-H3 subset thresholds failed but reason_code is not AVAILABLE_SUBSET_UNDERPOWERED."
        )
    print(
        "[OK] SK-H3 comparability is blocked by approved data-availability "
        "constraint with bounded available-subset scope."
    )
elif leakage_detected is True:
    raise SystemExit(
        "[FAIL] SK-H3 comparability artifact reports leakage_detected=true."
    )
else:
    if evidence_scope not in ("full_dataset", "available_subset"):
        raise SystemExit(
            f"[FAIL] SK-H3 comparability has invalid evidence_scope: {evidence_scope!r}."
        )
    if evidence_scope == "available_subset" and full_data_closure_eligible is not False:
        raise SystemExit(
            "[FAIL] SK-H3 available_subset evidence cannot set full_data_closure_eligible=true."
        )
    if available_subset_status == "INCONCLUSIVE_DATA_LIMITED":
        if available_subset_reason_code != "AVAILABLE_SUBSET_UNDERPOWERED":
            raise SystemExit(
                "[FAIL] SK-H3 underpowered subset status must use reason_code=AVAILABLE_SUBSET_UNDERPOWERED."
            )
    if available_subset_confidence not in {"QUALIFIED", "UNDERPOWERED", "BLOCKED"}:
        raise SystemExit(
            "[FAIL] SK-H3 comparability has invalid available_subset_confidence."
        )
    print(
        "[OK] SK-H3 comparability artifact is policy-compliant "
        f"(status={status}, reason_code={reason_code}, evidence_scope={evidence_scope})."
    )
PY

echo "[SK-H2.2/SK-M1.2] Building release gate-health artifact..."
python3 scripts/core_audit/build_release_gate_health_status.py > /dev/null

echo "[SK-H2] Validating claim-boundary policy (release mode)..."
python3 scripts/core_skeptic/check_claim_boundaries.py --mode release

echo "[SK-M1] Validating closure conditionality policy (release mode)..."
python3 scripts/core_skeptic/check_closure_conditionality.py --mode release

echo "[SK-H2.4] Validating claim entitlement coherence (release mode)..."
python3 scripts/core_skeptic/check_claim_entitlement_coherence.py --mode release

echo "[SK-M2] Regenerating phase8_comparative uncertainty artifact..."
python3 scripts/phase8_comparative/run_proximity_uncertainty.py --iterations 2000 --seed 42 > /dev/null

echo "[SK-M2] Validating phase8_comparative uncertainty policy (release mode)..."
python3 scripts/core_skeptic/check_comparative_uncertainty.py --mode release

python3 - <<'PY'
import json
from pathlib import Path

path = Path("results/data/phase7_human/phase_7c_uncertainty.json")
if not path.exists():
    raise SystemExit("[FAIL] Missing SK-M2 artifact: results/data/phase7_human/phase_7c_uncertainty.json")

payload = json.loads(path.read_text(encoding="utf-8"))
results = payload.get("results", {})
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
    raise SystemExit(f"[FAIL] SK-M2 uncertainty artifact missing keys: {missing}")

metric_validity = results.get("metric_validity") or {}
if metric_validity.get("required_fields_present") is not True:
    raise SystemExit("[FAIL] SK-M2 metric_validity.required_fields_present must be true.")
if metric_validity.get("sufficient_iterations") is not True:
    raise SystemExit("[FAIL] SK-M2 metric_validity.sufficient_iterations must be true.")

if not str(results.get("m2_4_residual_reason", "")).strip():
    raise SystemExit("[FAIL] SK-M2 m2_4_residual_reason is missing.")
if not isinstance(results.get("m2_4_reopen_triggers"), list) or len(
    results.get("m2_4_reopen_triggers")
) == 0:
    raise SystemExit("[FAIL] SK-M2 m2_4_reopen_triggers must be non-empty list.")

m2_5_lane = str(results.get("m2_5_closure_lane", "")).strip()
if m2_5_lane not in {
    "M2_5_ALIGNED",
    "M2_5_QUALIFIED",
    "M2_5_BOUNDED",
    "M2_5_BLOCKED",
    "M2_5_INCONCLUSIVE",
}:
    raise SystemExit(f"[FAIL] SK-M2 invalid m2_5_closure_lane={m2_5_lane!r}.")
if not str(results.get("m2_5_residual_reason", "")).strip():
    raise SystemExit("[FAIL] SK-M2 m2_5_residual_reason is missing.")
if not isinstance(results.get("m2_5_reopen_triggers"), list) or len(
    results.get("m2_5_reopen_triggers")
) == 0:
    raise SystemExit("[FAIL] SK-M2 m2_5_reopen_triggers must be non-empty list.")

linkage = results.get("m2_5_data_availability_linkage")
if not isinstance(linkage, dict):
    raise SystemExit("[FAIL] SK-M2 m2_5_data_availability_linkage must be object.")
if not isinstance(linkage.get("missing_folio_blocking_claimed"), bool):
    raise SystemExit(
        "[FAIL] SK-M2 linkage missing_folio_blocking_claimed must be boolean."
    )
if not isinstance(linkage.get("objective_comparative_validity_failure"), bool):
    raise SystemExit(
        "[FAIL] SK-M2 linkage objective_comparative_validity_failure must be boolean."
    )
if (
    linkage.get("missing_folio_blocking_claimed") is True
    and linkage.get("objective_comparative_validity_failure") is not True
):
    raise SystemExit(
        "[FAIL] SK-M2 missing-folio blocking claim requires objective phase8_comparative validity failure."
    )
if m2_5_lane == "M2_5_BLOCKED" and linkage.get("objective_comparative_validity_failure") is not True:
    raise SystemExit(
        "[FAIL] SK-M2 M2_5_BLOCKED lane requires objective phase8_comparative validity failure linkage."
    )

print("[OK] SK-M2 release contract checks passed.")
PY

echo "[SK-M3] Validating report coherence policy (release mode)..."
python3 scripts/core_skeptic/check_report_coherence.py --mode release

echo "[SK-M4] Building provenance health artifact..."
python3 scripts/core_audit/build_provenance_health_status.py > /dev/null

echo "[SK-M4] Synchronizing provenance register..."
python3 scripts/core_audit/sync_provenance_register.py > /dev/null

echo "[SK-M4] Validating provenance uncertainty policy (release mode)..."
python3 scripts/core_skeptic/check_provenance_uncertainty.py --mode release

python3 - <<'PY'
import json
from pathlib import Path

provenance_path = Path("core_status/core_audit/provenance_health_status.json")
sync_path = Path("core_status/core_audit/provenance_register_sync_status.json")
if not provenance_path.exists():
    raise SystemExit("[FAIL] Missing core_status/core_audit/provenance_health_status.json")
if not sync_path.exists():
    raise SystemExit("[FAIL] Missing core_status/core_audit/provenance_register_sync_status.json")

provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
sync = json.loads(sync_path.read_text(encoding="utf-8"))
lane = provenance.get("m4_5_historical_lane")
if lane not in {"M4_5_ALIGNED", "M4_5_QUALIFIED", "M4_5_BOUNDED", "M4_5_BLOCKED", "M4_5_INCONCLUSIVE"}:
    raise SystemExit(f"[FAIL] SK-M4 invalid m4_5_historical_lane={lane!r}.")
if not str(provenance.get("m4_5_residual_reason", "")).strip():
    raise SystemExit("[FAIL] SK-M4 m4_5_residual_reason must be non-empty.")
if not isinstance(provenance.get("m4_5_reopen_conditions"), list) or len(
    provenance.get("m4_5_reopen_conditions")
) == 0:
    raise SystemExit("[FAIL] SK-M4 m4_5_reopen_conditions must be non-empty list.")

linkage = provenance.get("m4_5_data_availability_linkage")
if not isinstance(linkage, dict):
    raise SystemExit("[FAIL] SK-M4 m4_5_data_availability_linkage must be object.")
missing_folio_blocking_claimed = linkage.get("missing_folio_blocking_claimed")
objective_incompleteness = linkage.get("objective_provenance_contract_incompleteness")
approved_irrecoverable = linkage.get("approved_irrecoverable_loss_classification")
if not isinstance(missing_folio_blocking_claimed, bool):
    raise SystemExit("[FAIL] SK-M4 linkage missing_folio_blocking_claimed must be boolean.")
if not isinstance(objective_incompleteness, bool):
    raise SystemExit(
        "[FAIL] SK-M4 linkage objective_provenance_contract_incompleteness must be boolean."
    )
if not isinstance(approved_irrecoverable, bool):
    raise SystemExit(
        "[FAIL] SK-M4 linkage approved_irrecoverable_loss_classification must be boolean."
    )
if missing_folio_blocking_claimed and not objective_incompleteness:
    raise SystemExit(
        "[FAIL] SK-M4 missing-folio blocking claim requires objective_provenance_contract_incompleteness=true."
    )
if approved_irrecoverable and missing_folio_blocking_claimed and not objective_incompleteness:
    raise SystemExit(
        "[FAIL] SK-M4 approved irrecoverable-loss folio claims cannot block without objective linkage."
    )

if sync.get("provenance_health_lane") != lane:
    raise SystemExit("[FAIL] SK-M4 provenance_health_lane parity mismatch.")
if sync.get("provenance_health_m4_5_lane") != lane:
    raise SystemExit("[FAIL] SK-M4 provenance_health_m4_5_lane parity mismatch.")
if sync.get("provenance_health_m4_5_residual_reason") != provenance.get("m4_5_residual_reason"):
    raise SystemExit("[FAIL] SK-M4 provenance_health_m4_5_residual_reason parity mismatch.")

print(
    "[OK] SK-M4.5 contract checks passed "
    f"(lane={lane}, residual={provenance.get('m4_5_residual_reason')})."
)
PY

python3 - <<'PY'
import json
from pathlib import Path

by_run_dir = Path("core_status/by_run")
legacy = []
if by_run_dir.exists():
    for artifact in by_run_dir.glob("verify_*.json"):
        try:
            payload = json.loads(artifact.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if payload.get("provenance", {}).get("status") is not None:
            legacy.append(str(artifact))

if legacy:
    preview = ", ".join(sorted(legacy)[:3])
    raise SystemExit(
        "[FAIL] Legacy verification artifacts still contain provenance.status "
        f"fields ({preview}). Run scripts/core_audit/cleanup_status_artifacts.sh clean."
    )

print("[OK] Legacy verification artifact check passed")
PY

dirty_count="$(git status --short | wc -l | tr -d ' ')"
if [ "${dirty_count}" -gt 0 ]; then
  if [ "${ALLOW_DIRTY_RELEASE:-0}" != "1" ]; then
    echo "[FAIL] Working tree has ${dirty_count} changes."
    echo "       Review with: git status --short"
    echo "       If this diff is intentional for a release cut, rerun with:"
    echo "       ALLOW_DIRTY_RELEASE=1 DIRTY_RELEASE_REASON='<ticket-or-rationale>' bash scripts/core_audit/pre_release_check.sh"
    exit 1
  fi
  if [ -z "${DIRTY_RELEASE_REASON:-}" ]; then
    echo "[FAIL] ALLOW_DIRTY_RELEASE=1 requires DIRTY_RELEASE_REASON to be set."
    exit 1
  fi
  if [ "${#DIRTY_RELEASE_REASON}" -lt 12 ]; then
    echo "[FAIL] DIRTY_RELEASE_REASON must be at least 12 characters."
    echo "       Use structured format: '<ticket-or-context>: <why dirty release is acceptable>'"
    exit 1
  fi
  if [[ "${DIRTY_RELEASE_REASON}" != *:* ]]; then
    echo "[FAIL] DIRTY_RELEASE_REASON must include ':' separating context and rationale."
    echo "       Example: 'AUDIT-10: expected fixture refresh in progress'"
    exit 1
  fi
fi

echo "[OK] Working tree gate passed (dirty_count=${dirty_count}, ALLOW_DIRTY_RELEASE=${ALLOW_DIRTY_RELEASE:-0}, DIRTY_RELEASE_REASON='${DIRTY_RELEASE_REASON:-}')"

echo "--- Pre-Release Baseline Check PASSED ---"
