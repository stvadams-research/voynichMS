#!/usr/bin/env python3
"""
Cross-check SK-H2/SK-M1 claim entitlement coherence against gate-health status.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_GATE_HEALTH_PATH = PROJECT_ROOT / "core_status/core_audit/release_gate_health_status.json"
DEFAULT_H2_POLICY_PATH = PROJECT_ROOT / "configs/core_skeptic/sk_h2_claim_language_policy.json"
DEFAULT_M1_POLICY_PATH = PROJECT_ROOT / "configs/core_skeptic/sk_m1_closure_policy.json"


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return data


def _as_results(payload: dict[str, Any]) -> dict[str, Any]:
    results = payload.get("results")
    if isinstance(results, dict):
        return results
    return payload


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _derive_expected_lane(status: str, h2_policy: dict[str, Any]) -> str:
    h2_4_policy = _as_dict(h2_policy.get("h2_4_policy"))
    lane_by_status = _as_dict(h2_4_policy.get("lane_by_gate_status"))
    lane = lane_by_status.get(status)
    return str(lane).strip() if lane is not None else ""


def _required_by_lane(policy: dict[str, Any], lane: str, key: str) -> str:
    h2_4_policy = _as_dict(policy.get("h2_4_policy"))
    mapping = _as_dict(h2_4_policy.get(key))
    value = mapping.get(lane)
    return str(value).strip() if value is not None else ""


def run_checks(
    *,
    root: Path,
    gate_health_path: Path,
    h2_policy_path: Path,
    m1_policy_path: Path,
    mode: str,
) -> list[str]:
    errors: list[str] = []
    gate_payload = _load_json(gate_health_path)
    gate_results = _as_results(gate_payload)
    h2_policy = _load_json(h2_policy_path)
    m1_policy = _load_json(m1_policy_path)

    status = str(gate_results.get("status", "")).strip()
    declared_lane = str(gate_results.get("h2_4_closure_lane", "")).strip()
    expected_lane = _derive_expected_lane(status, h2_policy)
    if expected_lane and declared_lane != expected_lane:
        errors.append(
            "[h2_4-lane] gate-health lane mismatch: "
            f"status `{status}` expects `{expected_lane}` but found `{declared_lane}`"
        )

    lane = declared_lane or expected_lane
    if lane:
        required_claim_class = _required_by_lane(
            h2_policy, lane, "required_claim_class_by_lane"
        )
        if required_claim_class:
            actual_claim_class = str(gate_results.get("allowed_claim_class", "")).strip()
            if actual_claim_class != required_claim_class:
                errors.append(
                    "[h2_4-entitlement] allowed_claim_class mismatch: "
                    f"lane `{lane}` requires `{required_claim_class}` but found `{actual_claim_class}`"
                )

        required_closure_class = _required_by_lane(
            m1_policy, lane, "required_closure_class_by_lane"
        )
        if required_closure_class:
            actual_closure_class = str(
                gate_results.get("allowed_closure_class", "")
            ).strip()
            if actual_closure_class != required_closure_class:
                errors.append(
                    "[h2_4-entitlement] allowed_closure_class mismatch: "
                    f"lane `{lane}` requires `{required_closure_class}` but found `{actual_closure_class}`"
                )

    claim_checker = _load_module(
        PROJECT_ROOT / "scripts/core_skeptic/check_claim_boundaries.py",
        "check_claim_boundaries",
    )
    closure_checker = _load_module(
        PROJECT_ROOT / "scripts/core_skeptic/check_closure_conditionality.py",
        "check_closure_conditionality",
    )

    claim_errors = claim_checker.run_checks(h2_policy, root=root, mode=mode)
    closure_errors = closure_checker.run_checks(m1_policy, root=root, mode=mode)
    errors.extend(claim_errors)
    errors.extend(closure_errors)
    return errors


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check SK-H2/SK-M1 claim entitlement coherence."
    )
    parser.add_argument("--mode", choices=["ci", "release"], default="ci")
    parser.add_argument("--root", default=str(PROJECT_ROOT))
    parser.add_argument("--gate-health-path", default=str(DEFAULT_GATE_HEALTH_PATH))
    parser.add_argument("--h2-policy-path", default=str(DEFAULT_H2_POLICY_PATH))
    parser.add_argument("--m1-policy-path", default=str(DEFAULT_M1_POLICY_PATH))
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        errors = run_checks(
            root=Path(args.root),
            gate_health_path=Path(args.gate_health_path),
            h2_policy_path=Path(args.h2_policy_path),
            m1_policy_path=Path(args.m1_policy_path),
            mode=args.mode,
        )
    except Exception as exc:
        print(f"[FAIL] entitlement coherence check error: {exc}")
        return 1

    if errors:
        print(f"[FAIL] claim entitlement coherence violations (mode={args.mode}):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"[OK] claim entitlement coherence checks passed (mode={args.mode}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
