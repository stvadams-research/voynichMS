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
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "status/audit/release_gate_health_status.json"
DEFAULT_BY_RUN_DIR = PROJECT_ROOT / "status/audit/by_run"
DEFAULT_SENSITIVITY_PATH = PROJECT_ROOT / "status/audit/sensitivity_sweep.json"


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


def _check_reason_code(check_id: str, passed: bool) -> str:
    if passed:
        return "PASS"
    mapping = {
        "sensitivity_contract_ci": "SENSITIVITY_CONTRACT_BLOCKED",
        "sensitivity_contract_release": "SENSITIVITY_RELEASE_CONTRACT_BLOCKED",
        "provenance_runner_contract_ci": "PROVENANCE_RUNNER_CONTRACT_BLOCKED",
        "provenance_runner_contract_release": "PROVENANCE_RUNNER_RELEASE_CONTRACT_BLOCKED",
        "multimodal_coupling_release": "MULTIMODAL_POLICY_BLOCKED",
    }
    return mapping.get(check_id, f"{check_id.upper()}_FAILED")


def _gate_status(
    gate_name: str, check_results: List[Dict[str, Any]], sensitivity_summary: Dict[str, Any]
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

    # Include direct sensitivity summary signals as dependency context.
    if sensitivity_summary:
        if sensitivity_summary.get("dataset_policy_pass") is not True:
            reason_codes.append("SENSITIVITY_DATASET_POLICY_FAILED")
        if sensitivity_summary.get("warning_policy_pass") is not True:
            reason_codes.append("SENSITIVITY_WARNING_POLICY_FAILED")
        if gate_name in ("pre_release_check", "verify_reproduction"):
            if sensitivity_summary.get("release_evidence_ready") is not True:
                reason_codes.append("SENSITIVITY_RELEASE_EVIDENCE_NOT_READY")

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
) -> Dict[str, Any]:
    run_id = str(uuid.uuid4())
    generated_utc = _utc_now_iso()
    sensitivity_summary = _load_sensitivity_summary(sensitivity_path)

    checks_by_gate: Dict[str, List[Tuple[str, List[str]]]] = {
        "ci_check": [
            (
                "sensitivity_contract_ci",
                [
                    "__PYTHON__",
                    "scripts/audit/check_sensitivity_artifact_contract.py",
                    "--mode",
                    "ci",
                ],
            ),
            (
                "provenance_runner_contract_ci",
                [
                    "__PYTHON__",
                    "scripts/audit/check_provenance_runner_contract.py",
                    "--mode",
                    "ci",
                ],
            ),
        ],
        "pre_release_check": [
            (
                "sensitivity_contract_release",
                [
                    "__PYTHON__",
                    "scripts/audit/check_sensitivity_artifact_contract.py",
                    "--mode",
                    "release",
                ],
            ),
            (
                "provenance_runner_contract_release",
                [
                    "__PYTHON__",
                    "scripts/audit/check_provenance_runner_contract.py",
                    "--mode",
                    "release",
                ],
            ),
        ],
        "verify_reproduction": [
            (
                "sensitivity_contract_release",
                [
                    "__PYTHON__",
                    "scripts/audit/check_sensitivity_artifact_contract.py",
                    "--mode",
                    "release",
                ],
            ),
            (
                "provenance_runner_contract_release",
                [
                    "__PYTHON__",
                    "scripts/audit/check_provenance_runner_contract.py",
                    "--mode",
                    "release",
                ],
            ),
            (
                "multimodal_coupling_release",
                [
                    "__PYTHON__",
                    "scripts/skeptic/check_multimodal_coupling.py",
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
        gates[gate_name] = _gate_status(gate_name, check_rows, sensitivity_summary)

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

    results: Dict[str, Any] = {
        "version": "2026-02-10-h2m1.2",
        "generated_utc": generated_utc,
        "status": status,
        "reason_code": reason_code,
        "entitlement_class": entitlement_class,
        "allowed_claim_class": allowed_claim_class,
        "allowed_closure_class": allowed_closure_class,
        "allowed_claim": allowed_claim,
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
        },
        "status_source": [
            "scripts/audit/check_sensitivity_artifact_contract.py",
            "scripts/audit/check_provenance_runner_contract.py",
            "scripts/skeptic/check_multimodal_coupling.py",
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
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    payload = build_release_gate_health_status(
        output_path=Path(args.output).resolve(),
        by_run_dir=Path(args.by_run_dir).resolve(),
        python_bin=args.python_bin,
        sensitivity_path=Path(args.sensitivity_path).resolve(),
    )
    results = payload.get("results", {})
    print(
        "status={status} reason_code={reason_code} "
        "allowed_claim_class={allowed_claim_class} allowed_closure_class={allowed_closure_class}".format(
            **results
        )
    )
