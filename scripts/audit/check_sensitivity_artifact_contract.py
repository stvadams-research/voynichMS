#!/usr/bin/env python3
"""
Check sensitivity artifact/report coherence contract (SK-C1.2).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_POLICY_PATH = PROJECT_ROOT / "configs/audit/sensitivity_artifact_contract.json"


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON payload must be an object: {path}")
    return payload


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _extract_results_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    results = payload.get("results")
    if isinstance(results, dict):
        return results
    return payload


def _extract_report_value_map(report_text: str) -> Dict[str, str]:
    value_map: Dict[str, str] = {}
    pattern = re.compile(r"^-\s*(?P<label>[^:]+):\s*`(?P<value>.*)`\s*$")
    for line in report_text.splitlines():
        match = pattern.match(line.strip())
        if match:
            label = match.group("label").strip()
            value = match.group("value").strip()
            value_map[label] = value
    return value_map


def _render_expected_value(summary: Dict[str, Any], spec: Dict[str, Any]) -> str:
    fmt = str(spec.get("format", "str"))
    key = str(spec.get("summary_key", "")).strip()

    if fmt == "scenario_fraction":
        return f"{summary.get('scenario_count_executed')}/{summary.get('scenario_count_expected')}"

    value = summary.get(key)
    if fmt == "bool":
        return str(value)
    if fmt == "int":
        return str(int(value))
    if fmt == "float2":
        return f"{float(value):.2f}"
    return str(value)


def _check_summary_fields(summary: Dict[str, Any], policy: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    for field in _as_list(policy.get("required_summary_fields")):
        if field not in summary:
            errors.append(f"[missing-summary-field] summary missing `{field}`")

    for field in _as_list(policy.get("required_summary_bool_fields")):
        if field in summary and not isinstance(summary.get(field), bool):
            errors.append(f"[invalid-summary-type] `{field}` must be bool")

    for field in _as_list(policy.get("required_summary_list_fields")):
        if field in summary and not isinstance(summary.get(field), list):
            errors.append(f"[invalid-summary-type] `{field}` must be list")

    return errors


def _check_release_readiness_invariants(summary: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    release_ready = summary.get("release_evidence_ready")
    failures = summary.get("release_readiness_failures")

    if isinstance(failures, list):
        if release_ready is True and failures:
            errors.append(
                "[release-readiness] release_evidence_ready=true requires empty release_readiness_failures"
            )
        if release_ready is False and len(failures) == 0:
            errors.append(
                "[release-readiness] release_evidence_ready=false requires non-empty release_readiness_failures"
            )

    if release_ready is True:
        required_true = (
            "dataset_policy_pass",
            "warning_policy_pass",
            "quality_gate_passed",
            "robustness_conclusive",
        )
        for key in required_true:
            if summary.get(key) is not True:
                errors.append(
                    f"[release-readiness] release_evidence_ready=true requires `{key}`=true"
                )
        if summary.get("execution_mode") != "release":
            errors.append(
                "[release-readiness] release_evidence_ready=true requires execution_mode='release'"
            )
        if summary.get("scenario_count_expected") != summary.get("scenario_count_executed"):
            errors.append(
                "[release-readiness] release_evidence_ready=true requires full scenario execution"
            )

    return errors


def _check_warning_caveat_invariants(
    summary: Dict[str, Any], report_text: str, policy: Dict[str, Any]
) -> List[str]:
    errors: List[str] = []
    caveat_policy = policy.get("caveat_policy", {}) if isinstance(policy.get("caveat_policy"), dict) else {}

    total_warnings = int(summary.get("total_warning_count", 0) or 0)
    caveats = summary.get("caveats")
    none_phrase = str(caveat_policy.get("none_phrase_pattern", "Caveat: none"))

    if total_warnings > 0:
        if caveat_policy.get("require_nonempty_caveat_list_when_warnings_present", True):
            if not isinstance(caveats, list) or len(caveats) == 0:
                errors.append(
                    "[caveat-contract] warnings are present but summary.caveats is empty"
                )
        if caveat_policy.get("forbid_none_phrase_when_warnings_present", True):
            if none_phrase in report_text:
                errors.append(
                    f"[caveat-contract] report contains `{none_phrase}` while warnings are present"
                )

    return errors


def _check_report_coherence(summary: Dict[str, Any], report_text: str, policy: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    value_map = _extract_report_value_map(report_text)

    for raw_spec in _as_list(policy.get("report_field_contract")):
        if not isinstance(raw_spec, dict):
            continue
        label = str(raw_spec.get("label", "")).strip()
        if not label:
            errors.append("[policy] report_field_contract entry missing label")
            continue

        if label not in value_map:
            errors.append(f"[report-missing-field] missing report field `{label}`")
            continue

        try:
            expected = _render_expected_value(summary, raw_spec)
        except Exception as exc:
            errors.append(f"[policy] could not render expected value for `{label}`: {exc}")
            continue

        actual = value_map[label]
        if actual != expected:
            errors.append(
                f"[report-mismatch] `{label}` report=`{actual}` expected=`{expected}`"
            )

    return errors


def _check_release_mode_requirements(summary: Dict[str, Any], policy: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    req = policy.get("release_mode_requirements")
    if not isinstance(req, dict):
        return errors

    execution_mode = req.get("execution_mode")
    if execution_mode is not None and summary.get("execution_mode") != execution_mode:
        errors.append(
            f"[release-mode] execution_mode must be `{execution_mode}` (got `{summary.get('execution_mode')}`)"
        )

    for key in (
        "release_evidence_ready",
        "dataset_policy_pass",
        "warning_policy_pass",
        "quality_gate_passed",
        "robustness_conclusive",
    ):
        if key in req and summary.get(key) is not req.get(key):
            errors.append(
                f"[release-mode] `{key}` must be `{req.get(key)}` (got `{summary.get(key)}`)"
            )

    if req.get("scenario_counts_must_match") is True:
        if summary.get("scenario_count_expected") != summary.get("scenario_count_executed"):
            errors.append("[release-mode] scenario_count_expected must match scenario_count_executed")

    if req.get("release_readiness_failures_must_be_empty") is True:
        failures = summary.get("release_readiness_failures")
        if not isinstance(failures, list) or failures:
            errors.append("[release-mode] release_readiness_failures must be an empty list")

    return errors


def run_checks(policy: Dict[str, Any], *, root: Path, mode: str) -> Tuple[List[str], Dict[str, Any]]:
    errors: List[str] = []

    artifact_rel = str(policy.get("artifact_path", "status/audit/sensitivity_sweep.json"))
    report_rel = str(policy.get("report_path", "reports/audit/SENSITIVITY_RESULTS.md"))
    artifact_path = root / artifact_rel
    report_path = root / report_rel

    if not artifact_path.exists():
        errors.append(f"[missing-artifact] {artifact_rel}")
        return errors, {}
    if not report_path.exists():
        errors.append(f"[missing-report] {report_rel}")
        return errors, {}

    artifact_payload = _read_json(artifact_path)
    results_payload = _extract_results_payload(artifact_payload)
    summary = results_payload.get("summary") if isinstance(results_payload, dict) else None
    if not isinstance(summary, dict):
        errors.append("[missing-summary] sensitivity artifact missing results.summary")
        return errors, {}

    report_text = report_path.read_text(encoding="utf-8")

    errors.extend(_check_summary_fields(summary, policy))
    errors.extend(_check_release_readiness_invariants(summary))
    errors.extend(_check_warning_caveat_invariants(summary, report_text, policy))
    errors.extend(_check_report_coherence(summary, report_text, policy))

    if mode == "release":
        errors.extend(_check_release_mode_requirements(summary, policy))

    return errors, summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check sensitivity artifact/report contract.")
    parser.add_argument(
        "--policy-path",
        default=str(DEFAULT_POLICY_PATH),
        help="Path to sensitivity artifact contract JSON.",
    )
    parser.add_argument(
        "--root",
        default=str(PROJECT_ROOT),
        help="Repository root for resolving policy paths.",
    )
    parser.add_argument(
        "--mode",
        choices=["ci", "release"],
        default="ci",
        help="Contract enforcement mode.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    policy_path = Path(args.policy_path)
    root = Path(args.root)

    try:
        policy = _read_json(policy_path)
    except Exception as exc:
        print(f"[FAIL] could not read sensitivity contract policy: {exc}")
        return 1

    errors, summary = run_checks(policy, root=root, mode=args.mode)
    if errors:
        print(f"[FAIL] sensitivity artifact contract violations (mode={args.mode}):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(
        "[OK] sensitivity artifact contract checks passed "
        f"(mode={args.mode}, dataset_id={summary.get('dataset_id')}, "
        f"release_evidence_ready={summary.get('release_evidence_ready')})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
