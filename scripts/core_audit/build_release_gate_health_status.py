#!/usr/bin/env python3
"""
Build canonical release gate-health status artifact for SK-H2.2 / SK-M1.2.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "core_status/core_audit/release_gate_health_status.json"
DEFAULT_BY_RUN_DIR = PROJECT_ROOT / "core_status/core_audit/by_run"
DEFAULT_SENSITIVITY_PATH = PROJECT_ROOT / "core_status/core_audit/sensitivity_sweep_release.json"
DEFAULT_SENSITIVITY_PREFLIGHT_PATH = (
    PROJECT_ROOT / "core_status/core_audit/sensitivity_release_preflight.json"
)
DEFAULT_SENSITIVITY_RUN_STATUS_PATH = (
    PROJECT_ROOT / "core_status/core_audit/sensitivity_release_run_status.json"
)
DEFAULT_CONTROL_COMPARABILITY_PATH = (
    PROJECT_ROOT / "core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json"
)
DEFAULT_CONTROL_DATA_AVAILABILITY_PATH = (
    PROJECT_ROOT / "core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json"
)
DEFAULT_MULTIMODAL_STATUS_PATH = (
    PROJECT_ROOT / "results/data/phase5_mechanism/anchor_coupling_confirmatory.json"
)
DEFAULT_COMPARATIVE_UNCERTAINTY_PATH = (
    PROJECT_ROOT / "results/data/phase7_human/phase_7c_uncertainty.json"
)
DEFAULT_PROVENANCE_HEALTH_PATH = PROJECT_ROOT / "core_status/core_audit/provenance_health_status.json"
DEFAULT_PROVENANCE_SYNC_PATH = PROJECT_ROOT / "core_status/core_audit/provenance_register_sync_status.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run_check(
    *, check_id: str, command: List[str], python_bin: str, root: Path
) -> Dict[str, Any]:
    expanded = [python_bin if arg == "__PYTHON__" else arg for arg in command]
    proc = subprocess.run(
        expanded,
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )
    passed = proc.returncode == 0
    reason_code = "PASS" if passed else f"{check_id.upper()}_FAILED"
    log_tail = "\n".join((proc.stderr or proc.stdout or "").strip().splitlines()[-5:])
    return {
        "check_id": check_id,
        "passed": passed,
        "returncode": proc.returncode,
        "reason_code": reason_code,
        "command": " ".join(expanded),
        "log_tail": log_tail,
    }


def _load_sensitivity_summary(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    results = payload.get("results", {})
    if not isinstance(results, dict):
        return {}
    summary = results.get("summary", {})
    return summary if isinstance(summary, dict) else {}


def _load_results_payload(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    results = payload.get("results") if isinstance(payload, dict) else None
    if isinstance(results, dict):
        return results
    if isinstance(payload, dict):
        return payload
    return {}


def _load_artifact_bundle(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"results": {}, "provenance": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"results": {}, "provenance": {}}
    if not isinstance(payload, dict):
        return {"results": {}, "provenance": {}}
    results = payload.get("results")
    if not isinstance(results, dict):
        results = payload
    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        provenance = {}
    return {"results": results, "provenance": provenance}


def _load_sensitivity_preflight(path: Path) -> Dict[str, Any]:
    payload = _load_results_payload(path)
    return payload if isinstance(payload, dict) else {}


def _collect_sensitivity_subreasons(log_tail: str) -> List[str]:
    subreasons: List[str] = []
    text = log_tail or ""
    if "[missing-artifact]" in text and "sensitivity_sweep_release.json" in text:
        subreasons.append("SENSITIVITY_RELEASE_ARTIFACT_MISSING")
    if "[missing-artifact]" in text and "sensitivity_release_preflight.json" in text:
        subreasons.append("SENSITIVITY_RELEASE_PREFLIGHT_MISSING")
    if "[missing-report]" in text and "SENSITIVITY_RESULTS_RELEASE.md" in text:
        subreasons.append("SENSITIVITY_RELEASE_REPORT_MISSING")
    if "[release-readiness]" in text:
        subreasons.append("SENSITIVITY_RELEASE_READINESS_INVARIANT_FAILED")
    if "[release-mode]" in text:
        subreasons.append("SENSITIVITY_RELEASE_MODE_REQUIREMENT_FAILED")
    if "[preflight-ok-but-release-artifact-missing]" in text:
        subreasons.append("SENSITIVITY_PREFLIGHT_OK_ARTIFACT_MISSING")
    if "[release-run-status] missing run status artifact" in text:
        subreasons.append("SENSITIVITY_RELEASE_RUN_STATUS_MISSING")
    if "[release-run-status] stale-heartbeat" in text:
        subreasons.append("SENSITIVITY_RELEASE_RUN_STALE")
    if "[release-run-status]" in text and "status='FAILED'" in text:
        subreasons.append("SENSITIVITY_RELEASE_RUN_FAILED")
    return sorted(set(subreasons))


def _collect_control_subreasons(log_tail: str) -> List[str]:
    subreasons: List[str] = []
    text = log_tail or ""
    if "[freshness]" in text:
        subreasons.append("CONTROL_ARTIFACT_FRESHNESS_FAILED")
    if "[cross-artifact]" in text:
        subreasons.append("CONTROL_ARTIFACT_PARITY_FAILED")
    if "[availability-feasibility]" in text or "[artifact-feasibility]" in text:
        subreasons.append("CONTROL_FEASIBILITY_CONTRACT_FAILED")
    if "h3_4_closure_lane" in text:
        subreasons.append("CONTROL_CLOSURE_LANE_MISMATCH")
    if "h3_5_closure_lane" in text or "h3_5_residual_reason" in text:
        subreasons.append("CONTROL_H3_5_CLOSURE_CONTRACT_FAILED")
    return sorted(set(subreasons))


def _collect_multimodal_subreasons(log_tail: str) -> List[str]:
    subreasons: List[str] = []
    text = log_tail or ""
    if "[artifact-h1_4]" in text:
        subreasons.append("MULTIMODAL_H1_4_CONTRACT_FAILED")
    if "[artifact-coherence]" in text:
        subreasons.append("MULTIMODAL_STATUS_COHERENCE_FAILED")
    if "[missing-marker]" in text:
        subreasons.append("MULTIMODAL_CLAIM_BOUNDARY_MARKERS_MISSING")
    if "[banned-pattern]" in text:
        subreasons.append("MULTIMODAL_CLAIM_OVERREACH_DETECTED")
    return sorted(set(subreasons))


def _parse_iso_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _derive_h3_closure_lane(
    control_comparability: Dict[str, Any], control_data_availability: Dict[str, Any]
) -> str:
    status = str(control_comparability.get("status", ""))
    reason_code = str(control_comparability.get("reason_code", ""))
    evidence_scope = str(control_comparability.get("evidence_scope", ""))
    full_data_closure_eligible = control_comparability.get("full_data_closure_eligible")
    feasibility = str(control_comparability.get("full_data_feasibility", ""))
    availability_feasibility = str(control_data_availability.get("full_data_feasibility", ""))
    missing_count = control_comparability.get("missing_count")

    if (
        feasibility == "feasible"
        and availability_feasibility == "feasible"
        and missing_count == 0
        and status in {"COMPARABLE_CONFIRMED", "COMPARABLE_QUALIFIED"}
        and full_data_closure_eligible is True
        and evidence_scope == "full_dataset"
    ):
        return "H3_4_ALIGNED"

    if (
        feasibility == "irrecoverable"
        and availability_feasibility == "irrecoverable"
        and status == "NON_COMPARABLE_BLOCKED"
        and reason_code == "DATA_AVAILABILITY"
        and evidence_scope == "available_subset"
        and full_data_closure_eligible is False
    ):
        return "H3_4_QUALIFIED"

    if status == "INCONCLUSIVE_DATA_LIMITED":
        return "H3_4_INCONCLUSIVE"
    return "H3_4_BLOCKED"


def _derive_h3_5_closure_lane(
    control_comparability: Dict[str, Any], control_data_availability: Dict[str, Any]
) -> str:
    declared = str(control_comparability.get("h3_5_closure_lane", "")).strip()
    if declared:
        return declared

    status = str(control_comparability.get("status", ""))
    reason_code = str(control_comparability.get("reason_code", ""))
    evidence_scope = str(control_comparability.get("evidence_scope", ""))
    full_data_closure_eligible = control_comparability.get("full_data_closure_eligible")
    feasibility = str(control_comparability.get("full_data_feasibility", ""))
    availability_feasibility = str(control_data_availability.get("full_data_feasibility", ""))
    missing_count = control_comparability.get("missing_count")

    if (
        feasibility == "feasible"
        and availability_feasibility == "feasible"
        and missing_count == 0
        and status in {"COMPARABLE_CONFIRMED", "COMPARABLE_QUALIFIED"}
        and full_data_closure_eligible is True
        and evidence_scope == "full_dataset"
    ):
        return "H3_5_ALIGNED"

    if (
        feasibility == "irrecoverable"
        and availability_feasibility == "irrecoverable"
        and status == "NON_COMPARABLE_BLOCKED"
        and reason_code == "DATA_AVAILABILITY"
        and evidence_scope == "available_subset"
        and full_data_closure_eligible is False
    ):
        return "H3_5_TERMINAL_QUALIFIED"

    if status == "INCONCLUSIVE_DATA_LIMITED":
        return "H3_5_INCONCLUSIVE"
    return "H3_5_BLOCKED"


def _derive_h1_4_closure_lane(multimodal_results: Dict[str, Any]) -> str:
    status = str(multimodal_results.get("status", ""))
    robustness = multimodal_results.get("robustness")
    robustness_class = ""
    if isinstance(robustness, dict):
        robustness_class = str(robustness.get("robustness_class", ""))
    declared_lane = str(multimodal_results.get("h1_4_closure_lane", ""))
    if declared_lane:
        return declared_lane
    if status in {"CONCLUSIVE_NO_COUPLING", "CONCLUSIVE_COUPLING_PRESENT"}:
        if robustness_class == "ROBUST":
            return "H1_4_ALIGNED"
        return "H1_4_QUALIFIED"
    if status in {"INCONCLUSIVE_UNDERPOWERED", "INCONCLUSIVE_INFERENTIAL_AMBIGUITY"}:
        return "H1_4_INCONCLUSIVE"
    if status == "BLOCKED_DATA_GEOMETRY":
        return "H1_4_BLOCKED"
    return "H1_4_INCONCLUSIVE"


def _derive_h1_5_closure_lane(multimodal_results: Dict[str, Any]) -> str:
    status = str(multimodal_results.get("status", ""))
    declared_lane = str(multimodal_results.get("h1_5_closure_lane", ""))
    if declared_lane:
        return declared_lane

    robustness = multimodal_results.get("robustness")
    if not isinstance(robustness, dict):
        robustness = {}
    entitlement_class = str(robustness.get("entitlement_robustness_class", ""))
    reachable = bool(robustness.get("robust_closure_reachable", False))
    diagnostic_non_conclusive = int(robustness.get("diagnostic_non_conclusive_lane_count", 0) or 0)
    diagnostic_total = int(robustness.get("observed_diagnostic_lane_count", 0) or 0) + int(
        robustness.get("observed_stress_lane_count", 0) or 0
    )

    if not reachable:
        return "H1_5_BLOCKED"
    if status in {"CONCLUSIVE_NO_COUPLING", "CONCLUSIVE_COUPLING_PRESENT"}:
        if entitlement_class == "ROBUST":
            if diagnostic_total > 0 and diagnostic_non_conclusive > 0:
                return "H1_5_BOUNDED"
            return "H1_5_ALIGNED"
        return "H1_5_QUALIFIED"
    if status in {"INCONCLUSIVE_UNDERPOWERED", "INCONCLUSIVE_INFERENTIAL_AMBIGUITY"}:
        return "H1_5_INCONCLUSIVE"
    if status == "BLOCKED_DATA_GEOMETRY":
        return "H1_5_BLOCKED"
    return "H1_5_INCONCLUSIVE"


def _derive_h2_4_closure_lane(gate_health_status: str) -> str:
    if gate_health_status == "GATE_HEALTH_OK":
        return "H2_4_ALIGNED"
    if gate_health_status == "GATE_HEALTH_DEGRADED":
        return "H2_4_QUALIFIED"
    return "H2_4_INCONCLUSIVE"


def _derive_m2_5_closure_lane(comparative_results: Dict[str, Any]) -> str:
    declared_lane = str(comparative_results.get("m2_5_closure_lane", "")).strip()
    if declared_lane:
        return declared_lane

    status = str(comparative_results.get("status", ""))
    metric_validity = comparative_results.get("metric_validity")
    required_fields_present = False
    if isinstance(metric_validity, dict):
        required_fields_present = metric_validity.get("required_fields_present") is True
    if status == "STABILITY_CONFIRMED":
        return "M2_5_ALIGNED"
    if status == "DISTANCE_QUALIFIED":
        return "M2_5_QUALIFIED"
    if status == "INCONCLUSIVE_UNCERTAINTY":
        if required_fields_present:
            return "M2_5_BOUNDED"
        return "M2_5_BLOCKED"
    return "M2_5_INCONCLUSIVE"


def _check_reason_code(check_id: str, passed: bool) -> str:
    if passed:
        return "PASS"
    mapping = {
        "sensitivity_contract_ci": "SENSITIVITY_CONTRACT_BLOCKED",
        "sensitivity_contract_release": "SENSITIVITY_RELEASE_CONTRACT_BLOCKED",
        "provenance_runner_contract_ci": "PROVENANCE_RUNNER_CONTRACT_BLOCKED",
        "provenance_runner_contract_release": "PROVENANCE_RUNNER_RELEASE_CONTRACT_BLOCKED",
        "multimodal_coupling_release": "MULTIMODAL_POLICY_BLOCKED",
        "control_comparability_ci": "CONTROL_COMPARABILITY_POLICY_BLOCKED",
        "control_data_availability_ci": "CONTROL_DATA_AVAILABILITY_POLICY_BLOCKED",
        "control_comparability_release": "CONTROL_COMPARABILITY_RELEASE_BLOCKED",
        "control_data_availability_release": "CONTROL_DATA_AVAILABILITY_RELEASE_BLOCKED",
        "comparative_uncertainty_ci": "COMPARATIVE_UNCERTAINTY_POLICY_BLOCKED",
        "comparative_uncertainty_release": "COMPARATIVE_UNCERTAINTY_RELEASE_BLOCKED",
    }
    return mapping.get(check_id, f"{check_id.upper()}_FAILED")


def _gate_status(
    gate_name: str,
    check_results: List[Dict[str, Any]],
    sensitivity_summary: Dict[str, Any],
    sensitivity_preflight: Dict[str, Any],
    sensitivity_run_status: Dict[str, Any],
) -> Dict[str, Any]:
    checks = {}
    reason_codes: List[str] = []
    for row in check_results:
        reason_code = _check_reason_code(row["check_id"], row["passed"])
        checks[row["check_id"]] = {
            "passed": bool(row["passed"]),
            "returncode": int(row["returncode"]),
            "reason_code": reason_code,
            "command": row["command"],
            "log_tail": row["log_tail"],
        }
        if reason_code != "PASS":
            reason_codes.append(reason_code)
            if row["check_id"] == "sensitivity_contract_release":
                reason_codes.extend(_collect_sensitivity_subreasons(row["log_tail"]))
            if row["check_id"].startswith("control_"):
                reason_codes.extend(_collect_control_subreasons(row["log_tail"]))
            if row["check_id"].startswith("multimodal_"):
                reason_codes.extend(_collect_multimodal_subreasons(row["log_tail"]))

    # Include direct sensitivity summary signals as dependency context.
    if sensitivity_summary:
        if sensitivity_summary.get("dataset_policy_pass") is not True:
            reason_codes.append("SENSITIVITY_DATASET_POLICY_FAILED")
        if sensitivity_summary.get("warning_policy_pass") is not True:
            reason_codes.append("SENSITIVITY_WARNING_POLICY_FAILED")
        if gate_name in ("pre_release_check", "verify_reproduction"):
            if sensitivity_summary.get("release_evidence_ready") is not True:
                reason_codes.append("SENSITIVITY_RELEASE_EVIDENCE_NOT_READY")
    elif gate_name in ("pre_release_check", "verify_reproduction"):
        reason_codes.append("SENSITIVITY_RELEASE_SUMMARY_UNAVAILABLE")

    preflight_status = sensitivity_preflight.get("status")
    preflight_reason_codes = sensitivity_preflight.get("reason_codes")
    if gate_name in ("ci_check", "pre_release_check", "verify_reproduction"):
        if preflight_status == "BLOCKED":
            reason_codes.append("SENSITIVITY_RELEASE_PREFLIGHT_BLOCKED")
            if isinstance(preflight_reason_codes, list):
                for code in preflight_reason_codes:
                    reason_codes.append(f"SENSITIVITY_PREFLIGHT_{code}")
        elif preflight_status is None:
            reason_codes.append("SENSITIVITY_RELEASE_PREFLIGHT_UNKNOWN")

    run_status = sensitivity_run_status.get("status")
    run_status_reason_codes = sensitivity_run_status.get("reason_codes")
    if gate_name in ("ci_check", "pre_release_check", "verify_reproduction"):
        if run_status in {"STARTED", "RUNNING"}:
            reason_codes.append("SENSITIVITY_RELEASE_RUN_INCOMPLETE")
        elif run_status == "FAILED":
            reason_codes.append("SENSITIVITY_RELEASE_RUN_FAILED")
        elif run_status is None:
            reason_codes.append("SENSITIVITY_RELEASE_RUN_STATUS_UNAVAILABLE")
        if isinstance(run_status_reason_codes, list):
            for code in run_status_reason_codes:
                if isinstance(code, str) and code.strip():
                    reason_codes.append(f"SENSITIVITY_RUNSTATUS_{code}")

    reason_codes = sorted(set(reason_codes))
    passed = len(reason_codes) == 0
    return {
        "status": "PASS" if passed else "FAIL",
        "passed": passed,
        "reason_codes": reason_codes,
        "checks": checks,
    }


def build_release_gate_health_status(
    *,
    output_path: Path,
    by_run_dir: Path,
    python_bin: str,
    sensitivity_path: Path,
    sensitivity_preflight_path: Path = DEFAULT_SENSITIVITY_PREFLIGHT_PATH,
    sensitivity_run_status_path: Path = DEFAULT_SENSITIVITY_RUN_STATUS_PATH,
    control_comparability_path: Path = DEFAULT_CONTROL_COMPARABILITY_PATH,
    control_data_availability_path: Path = DEFAULT_CONTROL_DATA_AVAILABILITY_PATH,
    multimodal_status_path: Path = DEFAULT_MULTIMODAL_STATUS_PATH,
    comparative_uncertainty_path: Path = DEFAULT_COMPARATIVE_UNCERTAINTY_PATH,
    provenance_health_path: Path = DEFAULT_PROVENANCE_HEALTH_PATH,
    provenance_sync_path: Path = DEFAULT_PROVENANCE_SYNC_PATH,
) -> Dict[str, Any]:
    run_id = str(uuid.uuid4())
    generated_utc = _utc_now_iso()
    sensitivity_summary = _load_sensitivity_summary(sensitivity_path)
    sensitivity_preflight = _load_sensitivity_preflight(sensitivity_preflight_path)
    sensitivity_run_status = _load_results_payload(sensitivity_run_status_path)

    checks_by_gate: Dict[str, List[Tuple[str, List[str]]]] = {
        "ci_check": [
            (
                "control_comparability_ci",
                [
                    "__PYTHON__",
                    "scripts/core_skeptic/check_control_comparability.py",
                    "--mode",
                    "ci",
                ],
            ),
            (
                "control_data_availability_ci",
                [
                    "__PYTHON__",
                    "scripts/core_skeptic/check_control_data_availability.py",
                    "--mode",
                    "ci",
                ],
            ),
            (
                "sensitivity_contract_ci",
                [
                    "__PYTHON__",
                    "scripts/core_audit/check_sensitivity_artifact_contract.py",
                    "--mode",
                    "ci",
                ],
            ),
            (
                "provenance_runner_contract_ci",
                [
                    "__PYTHON__",
                    "scripts/core_audit/check_provenance_runner_contract.py",
                    "--mode",
                    "ci",
                ],
            ),
            (
                "comparative_uncertainty_ci",
                [
                    "__PYTHON__",
                    "scripts/core_skeptic/check_comparative_uncertainty.py",
                    "--mode",
                    "ci",
                ],
            ),
        ],
        "pre_release_check": [
            (
                "control_comparability_release",
                [
                    "__PYTHON__",
                    "scripts/core_skeptic/check_control_comparability.py",
                    "--mode",
                    "release",
                ],
            ),
            (
                "control_data_availability_release",
                [
                    "__PYTHON__",
                    "scripts/core_skeptic/check_control_data_availability.py",
                    "--mode",
                    "release",
                ],
            ),
            (
                "sensitivity_contract_release",
                [
                    "__PYTHON__",
                    "scripts/core_audit/check_sensitivity_artifact_contract.py",
                    "--mode",
                    "release",
                ],
            ),
            (
                "provenance_runner_contract_release",
                [
                    "__PYTHON__",
                    "scripts/core_audit/check_provenance_runner_contract.py",
                    "--mode",
                    "release",
                ],
            ),
            (
                "comparative_uncertainty_release",
                [
                    "__PYTHON__",
                    "scripts/core_skeptic/check_comparative_uncertainty.py",
                    "--mode",
                    "release",
                ],
            ),
        ],
        "verify_reproduction": [
            (
                "control_comparability_release",
                [
                    "__PYTHON__",
                    "scripts/core_skeptic/check_control_comparability.py",
                    "--mode",
                    "release",
                ],
            ),
            (
                "control_data_availability_release",
                [
                    "__PYTHON__",
                    "scripts/core_skeptic/check_control_data_availability.py",
                    "--mode",
                    "release",
                ],
            ),
            (
                "sensitivity_contract_release",
                [
                    "__PYTHON__",
                    "scripts/core_audit/check_sensitivity_artifact_contract.py",
                    "--mode",
                    "release",
                ],
            ),
            (
                "provenance_runner_contract_release",
                [
                    "__PYTHON__",
                    "scripts/core_audit/check_provenance_runner_contract.py",
                    "--mode",
                    "release",
                ],
            ),
            (
                "multimodal_coupling_release",
                [
                    "__PYTHON__",
                    "scripts/core_skeptic/check_multimodal_coupling.py",
                    "--mode",
                    "release",
                ],
            ),
            (
                "comparative_uncertainty_release",
                [
                    "__PYTHON__",
                    "scripts/core_skeptic/check_comparative_uncertainty.py",
                    "--mode",
                    "release",
                ],
            ),
        ],
    }

    gates: Dict[str, Any] = {}
    for gate_name, specs in checks_by_gate.items():
        check_rows = [
            _run_check(
                check_id=check_id,
                command=command,
                python_bin=python_bin,
                root=PROJECT_ROOT,
            )
            for check_id, command in specs
        ]
        gates[gate_name] = _gate_status(
            gate_name,
            check_rows,
            sensitivity_summary,
            sensitivity_preflight,
            sensitivity_run_status,
        )

    gate_failures = sorted(
        {
            reason
            for gate_payload in gates.values()
            for reason in gate_payload.get("reason_codes", [])
            if reason != "PASS"
        }
    )
    all_pass = all(gate_payload.get("passed") is True for gate_payload in gates.values())
    status = "GATE_HEALTH_OK" if all_pass else "GATE_HEALTH_DEGRADED"
    reason_code = "ALL_GATES_PASS" if all_pass else "GATE_CONTRACT_BLOCKED"
    entitlement_class = "ENTITLEMENT_FULL" if all_pass else "ENTITLEMENT_DEGRADED"
    allowed_claim_class = "CONCLUSIVE_WITHIN_SCOPE" if all_pass else "QUALIFIED"
    allowed_closure_class = (
        "CONDITIONAL_CLOSURE_ALIGNED" if all_pass else "CONDITIONAL_CLOSURE_QUALIFIED"
    )
    allowed_claim = (
        "Closure and summary claims may use full framework-bounded confidence class."
        if all_pass
        else "Closure and summary claims must remain operationally contingent and qualified."
    )
    h2_4_closure_lane = _derive_h2_4_closure_lane(status)
    h2_4_residual_reason = (
        "none"
        if h2_4_closure_lane == "H2_4_ALIGNED"
        else "gate_contract_dependency_unresolved"
    )
    h2_4_reopen_conditions = [
        "release gate health transitions to GATE_HEALTH_OK with passing release sensitivity contract",
        "claim and closure entitlement policies are revised with documented rationale and checker parity",
    ]
    control_comparability_bundle = _load_artifact_bundle(control_comparability_path)
    control_data_availability_bundle = _load_artifact_bundle(control_data_availability_path)
    multimodal_bundle = _load_artifact_bundle(multimodal_status_path)
    comparative_uncertainty_bundle = _load_artifact_bundle(comparative_uncertainty_path)
    provenance_health = _load_results_payload(provenance_health_path)
    provenance_sync = _load_results_payload(provenance_sync_path)
    control_comparability = control_comparability_bundle.get("results", {})
    control_data_availability = control_data_availability_bundle.get("results", {})
    multimodal_results = multimodal_bundle.get("results", {})
    comparative_results = comparative_uncertainty_bundle.get("results", {})
    control_comp_provenance = control_comparability_bundle.get("provenance", {})
    control_avail_provenance = control_data_availability_bundle.get("provenance", {})
    multimodal_provenance = multimodal_bundle.get("provenance", {})
    comparative_provenance = comparative_uncertainty_bundle.get("provenance", {})
    control_comp_run_id = control_comp_provenance.get("run_id")
    control_avail_run_id = control_avail_provenance.get("run_id")
    control_run_id_match = (
        bool(control_comp_run_id)
        and bool(control_avail_run_id)
        and control_comp_run_id == control_avail_run_id
    )
    control_comp_ts = _parse_iso_timestamp(control_comp_provenance.get("timestamp"))
    control_avail_ts = _parse_iso_timestamp(control_avail_provenance.get("timestamp"))
    control_timestamp_skew_seconds = None
    if control_comp_ts is not None and control_avail_ts is not None:
        control_timestamp_skew_seconds = abs(
            (control_comp_ts - control_avail_ts).total_seconds()
        )
    h3_4_closure_lane = _derive_h3_closure_lane(
        control_comparability, control_data_availability
    )
    h3_5_closure_lane = _derive_h3_5_closure_lane(
        control_comparability, control_data_availability
    )
    h1_4_closure_lane = _derive_h1_4_closure_lane(multimodal_results)
    h1_5_closure_lane = _derive_h1_5_closure_lane(multimodal_results)
    m2_5_closure_lane = _derive_m2_5_closure_lane(comparative_results)
    provenance_m4_5_lane = provenance_health.get("m4_5_historical_lane") or provenance_health.get(
        "m4_4_historical_lane"
    )
    provenance_m4_5_residual_reason = provenance_health.get("m4_5_residual_reason") or provenance_health.get(
        "m4_4_residual_reason"
    )
    provenance_m4_5_reopen_conditions = provenance_health.get("m4_5_reopen_conditions") or provenance_health.get(
        "m4_4_reopen_conditions"
    )

    results: Dict[str, Any] = {
        "version": "2026-02-10-h2.4",
        "generated_utc": generated_utc,
        "generated_at": generated_utc,
        "status": status,
        "reason_code": reason_code,
        "entitlement_class": entitlement_class,
        "allowed_claim_class": allowed_claim_class,
        "allowed_closure_class": allowed_closure_class,
        "allowed_claim": allowed_claim,
        "h2_4_closure_lane": h2_4_closure_lane,
        "h2_4_residual_reason": h2_4_residual_reason,
        "h2_4_reopen_conditions": h2_4_reopen_conditions,
        "gate_failures": gate_failures,
        "gates": gates,
        "dependency_snapshot": {
            "sensitivity_summary_path": str(sensitivity_path.relative_to(PROJECT_ROOT)),
            "execution_mode": sensitivity_summary.get("execution_mode"),
            "release_evidence_ready": sensitivity_summary.get("release_evidence_ready"),
            "dataset_policy_pass": sensitivity_summary.get("dataset_policy_pass"),
            "warning_policy_pass": sensitivity_summary.get("warning_policy_pass"),
            "total_warning_count": sensitivity_summary.get("total_warning_count"),
            "warning_density_per_scenario": sensitivity_summary.get(
                "warning_density_per_scenario"
            ),
            "sensitivity_preflight_path": str(
                sensitivity_preflight_path.relative_to(PROJECT_ROOT)
            ),
            "sensitivity_preflight_status": sensitivity_preflight.get("status"),
            "sensitivity_preflight_reason_codes": sensitivity_preflight.get(
                "reason_codes"
            ),
            "sensitivity_preflight_generated_utc": sensitivity_preflight.get(
                "generated_utc"
            ),
            "sensitivity_run_status_path": str(
                sensitivity_run_status_path.relative_to(PROJECT_ROOT)
            ),
            "sensitivity_run_status": sensitivity_run_status.get("status"),
            "sensitivity_run_status_reason_codes": sensitivity_run_status.get(
                "reason_codes"
            ),
            "sensitivity_run_status_stage": sensitivity_run_status.get("stage"),
            "sensitivity_run_status_generated_utc": sensitivity_run_status.get(
                "generated_utc"
            ),
            "control_comparability_path": str(
                control_comparability_path.relative_to(PROJECT_ROOT)
            ),
            "control_comparability_status": control_comparability.get("status"),
            "control_comparability_reason_code": control_comparability.get("reason_code"),
            "control_comparability_evidence_scope": control_comparability.get("evidence_scope"),
            "control_comparability_full_data_closure_eligible": control_comparability.get(
                "full_data_closure_eligible"
            ),
            "control_comparability_missing_count": control_comparability.get("missing_count"),
            "control_comparability_full_data_feasibility": control_comparability.get(
                "full_data_feasibility"
            ),
            "control_comparability_terminal_reason": control_comparability.get(
                "full_data_closure_terminal_reason"
            ),
            "control_comparability_h3_4_closure_lane": control_comparability.get(
                "h3_4_closure_lane"
            ),
            "control_comparability_h3_5_closure_lane": control_comparability.get(
                "h3_5_closure_lane"
            ),
            "control_comparability_h3_5_residual_reason": control_comparability.get(
                "h3_5_residual_reason"
            ),
            "control_comparability_provenance_run_id": control_comp_run_id,
            "control_comparability_provenance_timestamp": control_comp_provenance.get(
                "timestamp"
            ),
            "control_data_availability_path": str(
                control_data_availability_path.relative_to(PROJECT_ROOT)
            ),
            "control_data_availability_status": control_data_availability.get("status"),
            "control_data_availability_reason_code": control_data_availability.get(
                "reason_code"
            ),
            "control_data_availability_evidence_scope": control_data_availability.get(
                "evidence_scope"
            ),
            "control_data_availability_full_data_closure_eligible": control_data_availability.get(
                "full_data_closure_eligible"
            ),
            "control_data_availability_missing_count": control_data_availability.get(
                "missing_count"
            ),
            "control_data_availability_full_data_feasibility": control_data_availability.get(
                "full_data_feasibility"
            ),
            "control_data_availability_terminal_reason": control_data_availability.get(
                "full_data_closure_terminal_reason"
            ),
            "control_data_availability_h3_4_closure_lane": control_data_availability.get(
                "h3_4_closure_lane"
            ),
            "control_data_availability_h3_5_closure_lane": control_data_availability.get(
                "h3_5_closure_lane"
            ),
            "control_data_availability_h3_5_residual_reason": control_data_availability.get(
                "h3_5_residual_reason"
            ),
            "control_data_availability_provenance_run_id": control_avail_run_id,
            "control_data_availability_provenance_timestamp": control_avail_provenance.get(
                "timestamp"
            ),
            "control_artifact_run_id_match": control_run_id_match,
            "control_artifact_timestamp_skew_seconds": control_timestamp_skew_seconds,
            "control_h3_4_closure_lane": h3_4_closure_lane,
            "control_h3_5_closure_lane": h3_5_closure_lane,
            "control_irrecoverability_classification": (
                control_data_availability.get("irrecoverability") or {}
            ).get("classification"),
            "multimodal_status_path": str(multimodal_status_path.relative_to(PROJECT_ROOT)),
            "multimodal_status": multimodal_results.get("status"),
            "multimodal_status_reason": multimodal_results.get("status_reason"),
            "multimodal_h1_4_closure_lane": multimodal_results.get("h1_4_closure_lane"),
            "multimodal_h1_4_derived_closure_lane": h1_4_closure_lane,
            "multimodal_h1_4_residual_reason": multimodal_results.get("h1_4_residual_reason"),
            "multimodal_h1_5_closure_lane": multimodal_results.get("h1_5_closure_lane"),
            "multimodal_h1_5_derived_closure_lane": h1_5_closure_lane,
            "multimodal_h1_5_residual_reason": multimodal_results.get("h1_5_residual_reason"),
            "multimodal_robustness_class": (multimodal_results.get("robustness") or {}).get(
                "robustness_class"
            ),
            "multimodal_entitlement_robustness_class": (
                multimodal_results.get("robustness") or {}
            ).get("entitlement_robustness_class"),
            "multimodal_robust_closure_reachable": (
                multimodal_results.get("robustness") or {}
            ).get("robust_closure_reachable"),
            "multimodal_robustness_lane_id": (multimodal_results.get("robustness") or {}).get(
                "lane_id"
            ),
            "multimodal_robustness_publication_lane_id": (
                multimodal_results.get("robustness") or {}
            ).get("publication_lane_id"),
            "multimodal_provenance_run_id": multimodal_provenance.get("run_id"),
            "multimodal_provenance_timestamp": multimodal_provenance.get("timestamp"),
            "comparative_uncertainty_path": str(
                comparative_uncertainty_path.relative_to(PROJECT_ROOT)
            ),
            "comparative_status": comparative_results.get("status"),
            "comparative_reason_code": comparative_results.get("reason_code"),
            "comparative_nearest_neighbor": comparative_results.get("nearest_neighbor"),
            "comparative_nearest_neighbor_stability": comparative_results.get(
                "nearest_neighbor_stability"
            ),
            "comparative_rank_stability": comparative_results.get("rank_stability"),
            "comparative_top2_gap_ci95_lower": (
                comparative_results.get("top2_gap") or {}
            ).get("ci95_lower"),
            "comparative_m2_4_closure_lane": comparative_results.get("m2_4_closure_lane"),
            "comparative_m2_4_residual_reason": comparative_results.get(
                "m2_4_residual_reason"
            ),
            "comparative_m2_5_closure_lane": comparative_results.get("m2_5_closure_lane"),
            "comparative_m2_5_derived_closure_lane": m2_5_closure_lane,
            "comparative_m2_5_residual_reason": comparative_results.get(
                "m2_5_residual_reason"
            ),
            "comparative_provenance_run_id": comparative_provenance.get("run_id"),
            "comparative_provenance_timestamp": comparative_provenance.get("timestamp"),
            "provenance_health_path": str(provenance_health_path.relative_to(PROJECT_ROOT)),
            "provenance_status": provenance_health.get("status"),
            "provenance_reason_code": provenance_health.get("reason_code"),
            "provenance_recoverability_class": provenance_health.get("recoverability_class"),
            "provenance_threshold_policy_pass": provenance_health.get("threshold_policy_pass"),
            "provenance_contract_coupling_pass": provenance_health.get("contract_coupling_pass"),
            "provenance_m4_5_historical_lane": provenance_m4_5_lane,
            "provenance_m4_5_residual_reason": provenance_m4_5_residual_reason,
            "provenance_m4_5_reopen_conditions": provenance_m4_5_reopen_conditions,
            "provenance_m4_5_data_availability_linkage": provenance_health.get(
                "m4_5_data_availability_linkage"
            ),
            "provenance_sync_path": str(provenance_sync_path.relative_to(PROJECT_ROOT)),
            "provenance_sync_status": provenance_sync.get("status"),
            "provenance_sync_drift_detected": provenance_sync.get("drift_detected"),
            "provenance_sync_health_lane": provenance_sync.get("provenance_health_lane"),
            "provenance_sync_health_m4_5_lane": provenance_sync.get("provenance_health_m4_5_lane"),
            "provenance_sync_health_m4_5_residual_reason": provenance_sync.get(
                "provenance_health_m4_5_residual_reason"
            ),
            "provenance_sync_contract_coupling_state": provenance_sync.get(
                "contract_coupling_state"
            ),
        },
        "status_source": [
            "scripts/core_skeptic/check_control_comparability.py",
            "scripts/core_skeptic/check_control_data_availability.py",
            "scripts/core_audit/check_sensitivity_artifact_contract.py",
            "scripts/core_audit/check_provenance_runner_contract.py",
            "scripts/core_skeptic/check_multimodal_coupling.py",
            "scripts/core_skeptic/check_comparative_uncertainty.py",
        ],
    }
    payload: Dict[str, Any] = {
        "provenance": {
            "run_id": run_id,
            "timestamp": generated_utc,
            "command": "build_release_gate_health_status",
        },
        "results": results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    by_run_dir.mkdir(parents=True, exist_ok=True)
    by_run_path = by_run_dir / f"release_gate_health_status.{run_id}.json"
    by_run_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build canonical release gate-health status artifact."
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Output path for release gate-health artifact.",
    )
    parser.add_argument(
        "--by-run-dir",
        default=str(DEFAULT_BY_RUN_DIR),
        help="Directory for run-scoped release gate-health artifacts.",
    )
    parser.add_argument(
        "--python-bin",
        default=sys.executable or "python3",
        help="Python interpreter used for subordinate policy checks.",
    )
    parser.add_argument(
        "--sensitivity-path",
        default=str(DEFAULT_SENSITIVITY_PATH),
        help="Path to canonical sensitivity artifact used for dependency snapshot.",
    )
    parser.add_argument(
        "--sensitivity-preflight-path",
        default=str(DEFAULT_SENSITIVITY_PREFLIGHT_PATH),
        help="Path to canonical sensitivity release-preflight artifact.",
    )
    parser.add_argument(
        "--sensitivity-run-status-path",
        default=str(DEFAULT_SENSITIVITY_RUN_STATUS_PATH),
        help="Path to canonical sensitivity release run-status artifact.",
    )
    parser.add_argument(
        "--control-comparability-path",
        default=str(DEFAULT_CONTROL_COMPARABILITY_PATH),
        help="Path to canonical SK-H3 control-comparability status artifact.",
    )
    parser.add_argument(
        "--control-data-availability-path",
        default=str(DEFAULT_CONTROL_DATA_AVAILABILITY_PATH),
        help="Path to canonical SK-H3 control data-availability artifact.",
    )
    parser.add_argument(
        "--multimodal-status-path",
        default=str(DEFAULT_MULTIMODAL_STATUS_PATH),
        help="Path to canonical SK-H1 multimodal confirmatory artifact.",
    )
    parser.add_argument(
        "--comparative-uncertainty-path",
        default=str(DEFAULT_COMPARATIVE_UNCERTAINTY_PATH),
        help="Path to canonical SK-M2 comparative uncertainty artifact.",
    )
    parser.add_argument(
        "--provenance-health-path",
        default=str(DEFAULT_PROVENANCE_HEALTH_PATH),
        help="Path to canonical SK-M4 provenance-health artifact.",
    )
    parser.add_argument(
        "--provenance-sync-path",
        default=str(DEFAULT_PROVENANCE_SYNC_PATH),
        help="Path to canonical SK-M4 provenance register sync artifact.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    payload = build_release_gate_health_status(
        output_path=Path(args.output).resolve(),
        by_run_dir=Path(args.by_run_dir).resolve(),
        python_bin=args.python_bin,
        sensitivity_path=Path(args.sensitivity_path).resolve(),
        sensitivity_preflight_path=Path(args.sensitivity_preflight_path).resolve(),
        sensitivity_run_status_path=Path(args.sensitivity_run_status_path).resolve(),
        control_comparability_path=Path(args.control_comparability_path).resolve(),
        control_data_availability_path=Path(args.control_data_availability_path).resolve(),
        multimodal_status_path=Path(args.multimodal_status_path).resolve(),
        comparative_uncertainty_path=Path(args.comparative_uncertainty_path).resolve(),
        provenance_health_path=Path(args.provenance_health_path).resolve(),
        provenance_sync_path=Path(args.provenance_sync_path).resolve(),
    )
    results = payload.get("results", {})
    print(
        "status={status} reason_code={reason_code} "
        "allowed_claim_class={allowed_claim_class} allowed_closure_class={allowed_closure_class}".format(
            **results
        )
    )
