#!/bin/bash
set -euo pipefail

echo "--- Pre-Release Baseline Check ---"

if [ ! -f "AUDIT_LOG.md" ]; then
  echo "[FAIL] Missing AUDIT_LOG.md"
  exit 1
fi

echo "[OK] AUDIT_LOG.md present"

if [ ! -f "status/audit/sensitivity_sweep.json" ]; then
  echo "[FAIL] Missing status/audit/sensitivity_sweep.json"
  exit 1
fi

echo "[SK-C1.2] Validating sensitivity artifact/report contract (release mode)..."
python3 scripts/audit/check_sensitivity_artifact_contract.py --mode release

echo "[SK-C2.2] Validating provenance runner contract (release mode)..."
python3 scripts/audit/check_provenance_runner_contract.py --mode release

echo "[SK-H1.2] Validating multimodal coupling policy (release mode)..."
python3 scripts/skeptic/check_multimodal_coupling.py --mode release

python3 - <<'PY'
import json
from pathlib import Path

path = Path("status/audit/sensitivity_sweep.json")
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
        "[FAIL] sensitivity_sweep.json is not marked release_evidence_ready=true "
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
from pathlib import Path

path = Path("status/synthesis/TURING_TEST_RESULTS.json")
if not path.exists():
    raise SystemExit(
        "[FAIL] Missing status/synthesis/TURING_TEST_RESULTS.json. "
        "Run strict preflight: REQUIRE_COMPUTED=1 python3 scripts/synthesis/run_indistinguishability_test.py --preflight-only"
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

echo "[SK-H3] Generating control matching audit artifact..."
python3 scripts/synthesis/run_control_matching_audit.py --preflight-only > /dev/null

echo "[SK-H3] Validating control comparability policy (release mode)..."
python3 scripts/skeptic/check_control_comparability.py --mode release

echo "[SK-H3] Validating control data-availability policy (release mode)..."
python3 scripts/skeptic/check_control_data_availability.py --mode release

python3 - <<'PY'
import json
from pathlib import Path

status_path = Path("status/synthesis/CONTROL_COMPARABILITY_STATUS.json")
availability_path = Path("status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json")
if not status_path.exists():
    raise SystemExit(
        "[FAIL] Missing status/synthesis/CONTROL_COMPARABILITY_STATUS.json after SK-H3 audit."
    )
if not availability_path.exists():
    raise SystemExit(
        "[FAIL] Missing status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json after SK-H3 audit."
    )

results = json.loads(status_path.read_text(encoding="utf-8")).get("results", {})
availability = json.loads(availability_path.read_text(encoding="utf-8")).get("results", {})
status = results.get("status")
reason_code = results.get("reason_code")
leakage_detected = results.get("leakage_detected")
evidence_scope = results.get("evidence_scope")
full_data_closure_eligible = results.get("full_data_closure_eligible")
missing_count = results.get("missing_count")
availability_status = availability.get("status")
availability_missing_count = availability.get("missing_count")

if status == "NON_COMPARABLE_BLOCKED":
    if reason_code != "DATA_AVAILABILITY":
        raise SystemExit(
            "[FAIL] SK-H3 comparability is blocked for non-approved reason "
            f"(reason_code={reason_code!r})."
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
    print(
        "[OK] SK-H3 comparability artifact is policy-compliant "
        f"(status={status}, reason_code={reason_code}, evidence_scope={evidence_scope})."
    )
PY

echo "[SK-H2.2/SK-M1.2] Building release gate-health artifact..."
python3 scripts/audit/build_release_gate_health_status.py > /dev/null

echo "[SK-H2] Validating claim-boundary policy (release mode)..."
python3 scripts/skeptic/check_claim_boundaries.py --mode release

echo "[SK-M1] Validating closure conditionality policy (release mode)..."
python3 scripts/skeptic/check_closure_conditionality.py --mode release

echo "[SK-M2] Regenerating comparative uncertainty artifact..."
python3 scripts/comparative/run_proximity_uncertainty.py --iterations 2000 --seed 42 > /dev/null

echo "[SK-M2] Validating comparative uncertainty policy (release mode)..."
python3 scripts/skeptic/check_comparative_uncertainty.py --mode release

echo "[SK-M3] Validating report coherence policy (release mode)..."
python3 scripts/skeptic/check_report_coherence.py --mode release

echo "[SK-M4] Building provenance health artifact..."
python3 scripts/audit/build_provenance_health_status.py > /dev/null

echo "[SK-M4] Synchronizing provenance register..."
python3 scripts/audit/sync_provenance_register.py > /dev/null

echo "[SK-M4] Validating provenance uncertainty policy (release mode)..."
python3 scripts/skeptic/check_provenance_uncertainty.py --mode release

python3 - <<'PY'
import json
from pathlib import Path

by_run_dir = Path("status/by_run")
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
        f"fields ({preview}). Run scripts/audit/cleanup_status_artifacts.sh clean."
    )

print("[OK] Legacy verification artifact check passed")
PY

dirty_count="$(git status --short | wc -l | tr -d ' ')"
if [ "${dirty_count}" -gt 0 ]; then
  if [ "${ALLOW_DIRTY_RELEASE:-0}" != "1" ]; then
    echo "[FAIL] Working tree has ${dirty_count} changes."
    echo "       Review with: git status --short"
    echo "       If this diff is intentional for a release cut, rerun with:"
    echo "       ALLOW_DIRTY_RELEASE=1 DIRTY_RELEASE_REASON='<ticket-or-rationale>' bash scripts/audit/pre_release_check.sh"
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
