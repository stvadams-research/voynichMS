#!/bin/bash
set -euo pipefail

echo "--- Starting CI Check ---"
PYTHON_BIN="${PYTHON_BIN:-python3}"
SENSITIVITY_RELEASE_DATASET_ID="${SENSITIVITY_RELEASE_DATASET_ID:-voynich_real}"
SENSITIVITY_RELEASE_RUN_STATUS_PATH="${SENSITIVITY_RELEASE_RUN_STATUS_PATH:-core_status/core_audit/sensitivity_release_run_status.json}"

# 1. Environment Setup (Check dependencies)
echo "1. Checking environment..."
"${PYTHON_BIN}" --version

# 2. Linting
echo "2. Linting..."
# ruff check src tests # Commented out until ruff is configured/installed properly in this env, but intended for future.

# 2a. Release Gate-Health Artifact
echo "2a. Building release gate-health artifact..."
"${PYTHON_BIN}" scripts/core_audit/build_release_gate_health_status.py > /dev/null

# 2b. Claim-Boundary Policy
echo "2b. Checking claim boundaries..."
"${PYTHON_BIN}" scripts/core_skeptic/check_claim_boundaries.py --mode ci

# 2c. Control-Comparability Policy
echo "2c. Building control matching/data-availability artifacts..."
"${PYTHON_BIN}" scripts/phase3_synthesis/run_control_matching_audit.py --preflight-only > /dev/null
echo "2c. Checking control comparability policy..."
"${PYTHON_BIN}" scripts/core_skeptic/check_control_comparability.py --mode ci
echo "2c. Checking control data-availability policy..."
"${PYTHON_BIN}" scripts/core_skeptic/check_control_data_availability.py --mode ci
echo "2c. Verifying SK-H3 semantic parity..."
"${PYTHON_BIN}" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

status_path = Path("core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json")
availability_path = Path("core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json")
status_payload = json.loads(status_path.read_text(encoding="utf-8"))
availability_payload = json.loads(availability_path.read_text(encoding="utf-8"))
status = status_payload.get("results", {})
availability = availability_payload.get("results", {})

required_status = [
    "status",
    "reason_code",
    "evidence_scope",
    "full_data_closure_eligible",
    "missing_count",
    "available_subset_status",
    "available_subset_reason_code",
    "available_subset_confidence",
    "available_subset_diagnostics",
    "full_data_feasibility",
    "full_data_closure_terminal_reason",
    "full_data_closure_reopen_conditions",
    "h3_4_closure_lane",
    "h3_5_closure_lane",
    "h3_5_residual_reason",
    "h3_5_reopen_conditions",
    "approved_lost_pages_policy_version",
    "approved_lost_pages_source_note_path",
    "irrecoverability",
]
missing = [k for k in required_status if k not in status]
if missing:
    raise SystemExit(f"SK-H3 status artifact missing keys: {missing}")

if status.get("evidence_scope") != availability.get("evidence_scope"):
    raise SystemExit("SK-H3 evidence_scope mismatch across comparability/data-availability artifacts.")
if status.get("full_data_closure_eligible") != availability.get("full_data_closure_eligible"):
    raise SystemExit(
        "SK-H3 full_data_closure_eligible mismatch across comparability/data-availability artifacts."
    )
if status.get("missing_count") != availability.get("missing_count"):
    raise SystemExit("SK-H3 missing_count mismatch across comparability/data-availability artifacts.")
if status.get("approved_lost_pages_policy_version") != availability.get(
    "approved_lost_pages_policy_version"
):
    raise SystemExit(
        "SK-H3 approved_lost_pages_policy_version mismatch across comparability/data-availability artifacts."
    )
if status.get("approved_lost_pages_source_note_path") != availability.get(
    "approved_lost_pages_source_note_path"
):
    raise SystemExit(
        "SK-H3 approved_lost_pages_source_note_path mismatch across comparability/data-availability artifacts."
    )
if status.get("irrecoverability") != availability.get("irrecoverability"):
    raise SystemExit("SK-H3 irrecoverability metadata mismatch across artifacts.")
if status.get("full_data_feasibility") != availability.get("full_data_feasibility"):
    raise SystemExit("SK-H3 full_data_feasibility mismatch across artifacts.")
if status.get("full_data_closure_terminal_reason") != availability.get(
    "full_data_closure_terminal_reason"
):
    raise SystemExit(
        "SK-H3 full_data_closure_terminal_reason mismatch across artifacts."
    )
if status.get("full_data_closure_reopen_conditions") != availability.get(
    "full_data_closure_reopen_conditions"
):
    raise SystemExit(
        "SK-H3 full_data_closure_reopen_conditions mismatch across artifacts."
    )
if status.get("h3_4_closure_lane") != availability.get("h3_4_closure_lane"):
    raise SystemExit("SK-H3 h3_4_closure_lane mismatch across artifacts.")
if status.get("h3_5_closure_lane") != availability.get("h3_5_closure_lane"):
    raise SystemExit("SK-H3 h3_5_closure_lane mismatch across artifacts.")
if status.get("h3_5_residual_reason") != availability.get("h3_5_residual_reason"):
    raise SystemExit("SK-H3 h3_5_residual_reason mismatch across artifacts.")
if status.get("h3_5_reopen_conditions") != availability.get("h3_5_reopen_conditions"):
    raise SystemExit("SK-H3 h3_5_reopen_conditions mismatch across artifacts.")

h3_5_lane = status.get("h3_5_closure_lane")
h3_5_reason = status.get("h3_5_residual_reason")
h3_5_reopen_conditions = status.get("h3_5_reopen_conditions")
if h3_5_lane not in {"H3_5_ALIGNED", "H3_5_TERMINAL_QUALIFIED", "H3_5_BLOCKED", "H3_5_INCONCLUSIVE"}:
    raise SystemExit(f"SK-H3 invalid h3_5_closure_lane={h3_5_lane!r}.")
if not isinstance(h3_5_reason, str) or not h3_5_reason.strip():
    raise SystemExit("SK-H3 h3_5_residual_reason must be non-empty.")
if not isinstance(h3_5_reopen_conditions, list) or len(h3_5_reopen_conditions) == 0:
    raise SystemExit("SK-H3 h3_5_reopen_conditions must be a non-empty list.")

if (
    status.get("full_data_feasibility") == "irrecoverable"
    and status.get("status") == "NON_COMPARABLE_BLOCKED"
    and status.get("reason_code") == "DATA_AVAILABILITY"
    and status.get("evidence_scope") == "available_subset"
    and status.get("full_data_closure_eligible") is False
):
    expected_h3_5_lane = "H3_5_TERMINAL_QUALIFIED"
elif (
    status.get("full_data_feasibility") == "feasible"
    and status.get("status") in {"COMPARABLE_CONFIRMED", "COMPARABLE_QUALIFIED"}
    and status.get("evidence_scope") == "full_dataset"
    and status.get("full_data_closure_eligible") is True
    and status.get("missing_count") == 0
):
    expected_h3_5_lane = "H3_5_ALIGNED"
elif status.get("status") == "INCONCLUSIVE_DATA_LIMITED":
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
        raise SystemExit("SK-H3 terminal-qualified lane missing required reopen triggers.")

status_provenance = status_payload.get("provenance", {}) or {}
availability_provenance = availability_payload.get("provenance", {}) or {}
status_run_id = status_provenance.get("run_id")
availability_run_id = availability_provenance.get("run_id")
if not status_run_id or not availability_run_id:
    raise SystemExit("SK-H3 freshness check requires provenance.run_id in both artifacts.")
if status_run_id != availability_run_id:
    raise SystemExit(
        "SK-H3 freshness run_id mismatch across comparability/data-availability artifacts."
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
    raise SystemExit("SK-H3 freshness check requires valid provenance.timestamp in both artifacts.")
if abs((status_ts - availability_ts).total_seconds()) > 600:
    raise SystemExit("SK-H3 freshness timestamp skew exceeds 600 seconds.")

passes_thresholds = (status.get("available_subset_diagnostics") or {}).get("passes_thresholds")
if not isinstance(passes_thresholds, bool):
    raise SystemExit("SK-H3 available_subset_diagnostics.passes_thresholds must be boolean.")
if (not passes_thresholds) and status.get("available_subset_reason_code") != "AVAILABLE_SUBSET_UNDERPOWERED":
    raise SystemExit(
        "SK-H3 threshold failure requires available_subset_reason_code=AVAILABLE_SUBSET_UNDERPOWERED."
    )
if (
    status.get("evidence_scope") == "available_subset"
    and status.get("full_data_closure_eligible") is not False
):
    raise SystemExit(
        "SK-H3 available_subset evidence cannot set full_data_closure_eligible=true."
    )

print("  [OK] SK-H3 semantic parity checks passed.")
PY

# 2d. Closure-Conditionality Policy
echo "2d. Checking closure conditionality policy..."
"${PYTHON_BIN}" scripts/core_skeptic/check_closure_conditionality.py --mode ci

# 2d1. Claim-Entitlement Coherence
echo "2d1. Checking claim entitlement coherence..."
"${PYTHON_BIN}" scripts/core_skeptic/check_claim_entitlement_coherence.py --mode ci

# 2e. Comparative-Uncertainty Policy
echo "2e. Checking phase8_comparative uncertainty policy..."
"${PYTHON_BIN}" scripts/core_skeptic/check_comparative_uncertainty.py --mode ci
echo "2e. Verifying SK-M2.5 uncertainty lane semantics..."
"${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path

path = Path("results/phase7_human/phase_7c_uncertainty.json")
if not path.exists():
    raise SystemExit("SK-M2 artifact missing: results/phase7_human/phase_7c_uncertainty.json")

payload = json.loads(path.read_text(encoding="utf-8"))
results = payload.get("results", {})

if not str(results.get("m2_4_residual_reason", "")).strip():
    raise SystemExit("SK-M2 m2_4_residual_reason must be non-empty.")
if not str(results.get("m2_5_residual_reason", "")).strip():
    raise SystemExit("SK-M2 m2_5_residual_reason must be non-empty.")

lane = str(results.get("m2_5_closure_lane", ""))
if lane not in {
    "M2_5_ALIGNED",
    "M2_5_QUALIFIED",
    "M2_5_BOUNDED",
    "M2_5_BLOCKED",
    "M2_5_INCONCLUSIVE",
}:
    raise SystemExit(f"SK-M2 invalid m2_5_closure_lane={lane!r}.")

linkage = results.get("m2_5_data_availability_linkage")
if not isinstance(linkage, dict):
    raise SystemExit("SK-M2 m2_5_data_availability_linkage must be object.")
if (
    linkage.get("missing_folio_blocking_claimed") is True
    and linkage.get("objective_comparative_validity_failure") is not True
):
    raise SystemExit(
        "SK-M2 missing-folio blocking claim requires objective phase8_comparative validity failure."
    )
if lane == "M2_5_BLOCKED" and linkage.get("objective_comparative_validity_failure") is not True:
    raise SystemExit(
        "SK-M2 M2_5_BLOCKED lane requires objective phase8_comparative validity linkage."
    )

print("  [OK] SK-M2.5 uncertainty lane checks passed.")
PY

# 2f. Report-Coherence Policy
echo "2f. Checking report coherence policy..."
"${PYTHON_BIN}" scripts/core_skeptic/check_report_coherence.py --mode ci

# 2g. Provenance-Uncertainty Policy
echo "2g. Building provenance health artifact..."
"${PYTHON_BIN}" scripts/core_audit/build_provenance_health_status.py > /dev/null
echo "2g. Synchronizing provenance register..."
"${PYTHON_BIN}" scripts/core_audit/sync_provenance_register.py > /dev/null
echo "2g. Checking provenance uncertainty policy..."
"${PYTHON_BIN}" scripts/core_skeptic/check_provenance_uncertainty.py --mode ci
echo "2g. Verifying SK-M4.5 provenance lane semantics..."
"${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path

provenance_path = Path("core_status/core_audit/provenance_health_status.json")
sync_path = Path("core_status/core_audit/provenance_register_sync_status.json")
if not provenance_path.exists():
    raise SystemExit("SK-M4 artifact missing: core_status/core_audit/provenance_health_status.json")
if not sync_path.exists():
    raise SystemExit("SK-M4 artifact missing: core_status/core_audit/provenance_register_sync_status.json")

provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
sync = json.loads(sync_path.read_text(encoding="utf-8"))
lane = provenance.get("m4_5_historical_lane")
if lane not in {"M4_5_ALIGNED", "M4_5_QUALIFIED", "M4_5_BOUNDED", "M4_5_BLOCKED", "M4_5_INCONCLUSIVE"}:
    raise SystemExit(f"SK-M4 invalid m4_5_historical_lane={lane!r}.")
if not str(provenance.get("m4_5_residual_reason", "")).strip():
    raise SystemExit("SK-M4 m4_5_residual_reason must be non-empty.")
if not isinstance(provenance.get("m4_5_reopen_conditions"), list) or len(
    provenance.get("m4_5_reopen_conditions")
) == 0:
    raise SystemExit("SK-M4 m4_5_reopen_conditions must be a non-empty list.")

linkage = provenance.get("m4_5_data_availability_linkage")
if not isinstance(linkage, dict):
    raise SystemExit("SK-M4 m4_5_data_availability_linkage must be object.")
for key in (
    "missing_folio_blocking_claimed",
    "objective_provenance_contract_incompleteness",
    "approved_irrecoverable_loss_classification",
):
    if not isinstance(linkage.get(key), bool):
        raise SystemExit(f"SK-M4 {key} must be boolean.")
if linkage.get("missing_folio_blocking_claimed") and not linkage.get(
    "objective_provenance_contract_incompleteness"
):
    raise SystemExit(
        "SK-M4 missing-folio blocking claim requires objective_provenance_contract_incompleteness=true."
    )
if (
    linkage.get("approved_irrecoverable_loss_classification")
    and linkage.get("missing_folio_blocking_claimed")
    and not linkage.get("objective_provenance_contract_incompleteness")
):
    raise SystemExit(
        "SK-M4 approved irrecoverable-loss classification cannot block without objective linkage."
    )

if sync.get("provenance_health_lane") != lane:
    raise SystemExit("SK-M4 provenance_health_lane parity mismatch.")
if sync.get("provenance_health_m4_5_lane") != lane:
    raise SystemExit("SK-M4 provenance_health_m4_5_lane parity mismatch.")
if sync.get("provenance_health_m4_5_residual_reason") != provenance.get("m4_5_residual_reason"):
    raise SystemExit("SK-M4 provenance_health_m4_5_residual_reason parity mismatch.")

print("  [OK] SK-M4.5 provenance lane checks passed.")
PY

# 2h. Provenance Runner Contract
echo "2h. Checking provenance runner contract..."
"${PYTHON_BIN}" scripts/core_audit/check_provenance_runner_contract.py --mode ci

# 2i. Sensitivity artifact/report contract
echo "2i. Checking sensitivity artifact contract..."
"${PYTHON_BIN}" scripts/core_audit/check_sensitivity_artifact_contract.py --mode ci
echo "2i. Running release sensitivity preflight..."
"${PYTHON_BIN}" scripts/phase2_analysis/run_sensitivity_sweep.py \
  --mode release \
  --dataset-id "${SENSITIVITY_RELEASE_DATASET_ID}" \
  --preflight-only > /dev/null
echo "2i. Checking release-candidate sensitivity contract..."
"${PYTHON_BIN}" scripts/core_audit/check_sensitivity_artifact_contract.py --mode release

# 2j. Multimodal coupling status contract
echo "2j. Checking multimodal coupling policy..."
"${PYTHON_BIN}" scripts/core_skeptic/check_multimodal_coupling.py --mode ci
echo "2j. Verifying SK-H1.4/SK-H1.5 multimodal robustness parity..."
"${PYTHON_BIN}" - <<'PY'
import json
from pathlib import Path

path = Path("results/phase5_mechanism/anchor_coupling_confirmatory.json")
if not path.exists():
    raise SystemExit("SK-H1 artifact missing: results/phase5_mechanism/anchor_coupling_confirmatory.json")

payload = json.loads(path.read_text(encoding="utf-8"))
results = payload.get("results", {})
status = results.get("status")
h1_4_lane = results.get("h1_4_closure_lane")
h1_5_lane = results.get("h1_5_closure_lane")
robustness = results.get("robustness") or {}
robustness_class = robustness.get("robustness_class")
entitlement_robustness_class = robustness.get("entitlement_robustness_class")
robust_closure_reachable = robustness.get("robust_closure_reachable")
diagnostic_non_conclusive = int(robustness.get("diagnostic_non_conclusive_lane_count", 0) or 0)
diagnostic_total = int(robustness.get("observed_diagnostic_lane_count", 0) or 0) + int(
    robustness.get("observed_stress_lane_count", 0) or 0
)

if h1_4_lane not in {"H1_4_ALIGNED", "H1_4_QUALIFIED", "H1_4_BLOCKED", "H1_4_INCONCLUSIVE"}:
    raise SystemExit(f"SK-H1.4 invalid h1_4_closure_lane: {h1_4_lane!r}")
if h1_5_lane not in {"H1_5_ALIGNED", "H1_5_BOUNDED", "H1_5_QUALIFIED", "H1_5_BLOCKED", "H1_5_INCONCLUSIVE"}:
    raise SystemExit(f"SK-H1.5 invalid h1_5_closure_lane: {h1_5_lane!r}")
if robustness_class not in {"ROBUST", "MIXED", "FRAGILE"}:
    raise SystemExit(f"SK-H1.4 invalid robustness_class: {robustness_class!r}")
if entitlement_robustness_class not in {"ROBUST", "MIXED", "FRAGILE"}:
    raise SystemExit(
        "SK-H1.5 invalid entitlement_robustness_class: "
        f"{entitlement_robustness_class!r}"
    )
if not isinstance(robust_closure_reachable, bool):
    raise SystemExit("SK-H1.5 robust_closure_reachable must be boolean.")
if not isinstance(results.get("h1_4_reopen_conditions"), list) or len(results.get("h1_4_reopen_conditions")) == 0:
    raise SystemExit("SK-H1.4 h1_4_reopen_conditions must be a non-empty list.")
if not isinstance(results.get("h1_5_reopen_conditions"), list) or len(results.get("h1_5_reopen_conditions")) == 0:
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

print("  [OK] SK-H1.4/SK-H1.5 multimodal robustness checks passed.")
PY

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
CI_COVERAGE_JSON="${CI_COVERAGE_JSON:-core_status/ci_coverage.json}"
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
    "src/phase1_foundation/cli/main.py",
    "src/phase2_analysis/admissibility/manager.py",
    "src/phase1_foundation/core/queries.py",
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
