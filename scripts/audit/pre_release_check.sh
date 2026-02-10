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

if mode != "release":
    raise SystemExit(f"[FAIL] Sensitivity execution_mode must be 'release' (got {mode!r})")
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
