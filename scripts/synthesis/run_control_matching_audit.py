#!/usr/bin/env python3
"""
SK-H3 control matching audit runner.

Produces deterministic comparability artifacts without requiring full synthesis reruns.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from foundation.config import DEFAULT_SEED
from foundation.core.provenance import ProvenanceWriter
from foundation.runs.manager import active_run

POLICY_PATH = PROJECT_ROOT / "configs/skeptic/sk_h3_control_comparability_policy.json"
DATA_AVAILABILITY_POLICY_PATH = PROJECT_ROOT / "configs/skeptic/sk_h3_data_availability_policy.json"
STATUS_PATH = PROJECT_ROOT / "status/synthesis/CONTROL_COMPARABILITY_STATUS.json"
DATA_AVAILABILITY_STATUS_PATH = (
    PROJECT_ROOT / "status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json"
)
TURING_STATUS_PATH = PROJECT_ROOT / "status/synthesis/TURING_TEST_RESULTS.json"
CARDS_DIR = PROJECT_ROOT / "status/synthesis/control_matching_cards"
SPLIT_PAGE_ID_PATTERN = re.compile(r"^(f\d+[rv])\d+$")

TARGETS = {
    "repetition_rate": 0.90,
    "information_density": 5.68,
    "locality_radius": 3.0,
    "mean_word_length": 5.2,
    "positional_entropy": 0.65,
}


SEARCH_SPACES: Dict[str, Dict[str, List[float]]] = {
    "self_citation": {
        "pool_size": [200.0, 350.0, 500.0],
        "mutation_rate": [0.05, 0.10, 0.15],
    },
    "table_grille": {
        "table_rows": [8.0, 10.0, 12.0],
        "jitter_period": [250.0, 500.0, 750.0],
    },
    "mechanical_reuse": {
        "pool_size": [15.0, 25.0, 35.0],
        "tokens_per_page": [64.0, 72.0, 96.0],
    },
}


def _load_policy(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_results_payload(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("results"), dict):
        return dict(payload["results"])
    if isinstance(payload, dict):
        return dict(payload)
    raise ValueError(f"Artifact payload at {path} must be a JSON object")


def _as_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def _normalize_page_id(page_id: str) -> str:
    match = SPLIT_PAGE_ID_PATTERN.match(page_id)
    if match:
        return match.group(1)
    return page_id


def _load_data_availability_policy(path: Path) -> Dict[str, Any]:
    if path.exists():
        return _load_policy(path)
    return {
        "dataset_id": "voynich_real",
        "expected_pages": [
            "f88r",
            "f88v",
            "f89r",
            "f89v",
            "f90r",
            "f90v",
            "f91r",
            "f91v",
            "f92r",
            "f92v",
            "f93r",
            "f93v",
            "f94r",
            "f94v",
            "f95r",
            "f95v",
            "f96r",
            "f96v",
        ],
        "approved_lost_pages": ["f91r", "f91v", "f92r", "f92v"],
    }


def _build_data_availability_snapshot(*, dataset_id: str, policy: Dict[str, Any]) -> Dict[str, Any]:
    turing_results: Dict[str, Any] = {}
    if TURING_STATUS_PATH.exists():
        turing_results = _load_results_payload(TURING_STATUS_PATH)

    preflight = dict(turing_results.get("preflight", {}))
    expected_pages = _as_list(preflight.get("expected_pages")) or _as_list(policy.get("expected_pages"))
    available_normalized = set(_as_list(preflight.get("available_pages_normalized")))
    if not available_normalized:
        available_normalized = {
            _normalize_page_id(page_id)
            for page_id in _as_list(preflight.get("available_pages"))
        }

    missing_pages = sorted(_as_list(preflight.get("missing_pages")))
    if not missing_pages and expected_pages:
        missing_pages = sorted(page for page in expected_pages if page not in available_normalized)

    approved_lost_pages = sorted(_as_list(policy.get("approved_lost_pages")))
    approved_missing_pages = sorted(set(missing_pages) & set(approved_lost_pages))
    unexpected_missing_pages = sorted(set(missing_pages) - set(approved_lost_pages))
    missing_count = len(missing_pages)
    evidence_scope = "available_subset" if missing_count > 0 else "full_dataset"
    strict_status = str(turing_results.get("status", "UNKNOWN"))
    strict_reason_code = str(turing_results.get("reason_code", ""))
    strict_computed = bool(turing_results.get("strict_computed", False))

    strict_preflight_policy_pass = (
        strict_computed
        and strict_status == "BLOCKED"
        and strict_reason_code == "DATA_AVAILABILITY"
        and missing_count > 0
    )
    approved_lost_pages_match = sorted(missing_pages) == approved_lost_pages
    missing_count_consistent = int(preflight.get("missing_count", missing_count)) == missing_count

    policy_checks = {
        "strict_preflight_policy_pass": strict_preflight_policy_pass,
        "approved_lost_pages_match": approved_lost_pages_match,
        "missing_count_consistent": missing_count_consistent,
        "unexpected_missing_pages_empty": len(unexpected_missing_pages) == 0,
    }
    policy_pass = all(policy_checks.values())

    return {
        "status": "DATA_AVAILABILITY_BLOCKED" if missing_count > 0 else "DATA_AVAILABILITY_CLEAR",
        "reason_code": "DATA_AVAILABILITY" if missing_count > 0 else "NONE",
        "dataset_id": str(policy.get("dataset_id", dataset_id)),
        "evidence_scope": evidence_scope,
        "full_data_closure_eligible": missing_count == 0,
        "strict_preflight_status": strict_status,
        "strict_preflight_reason_code": strict_reason_code,
        "strict_computed": strict_computed,
        "expected_pages": expected_pages,
        "expected_count": len(expected_pages),
        "available_pages_normalized": sorted(available_normalized),
        "available_count": len(available_normalized),
        "missing_pages": missing_pages,
        "missing_count": missing_count,
        "approved_lost_pages": approved_lost_pages,
        "approved_missing_pages": approved_missing_pages,
        "unexpected_missing_pages": unexpected_missing_pages,
        "policy_checks": policy_checks,
        "policy_pass": policy_pass,
    }


def _write_data_availability_status(snapshot: Dict[str, Any]) -> None:
    ProvenanceWriter.save_results(snapshot, str(DATA_AVAILABILITY_STATUS_PATH))


def _candidate_product(space: Dict[str, List[float]]) -> Iterable[Dict[str, float]]:
    keys = sorted(space.keys())
    for values in itertools.product(*(space[k] for k in keys)):
        yield {k: float(v) for k, v in zip(keys, values)}


def _predict_metrics(control_class: str, params: Dict[str, float]) -> Dict[str, float]:
    if control_class == "self_citation":
        pool_size = params["pool_size"]
        mutation = params["mutation_rate"]
        return {
            "repetition_rate": max(0.0, min(1.0, 0.96 - (mutation * 0.6))),
            "information_density": 5.2 + ((pool_size - 200.0) / 300.0) * 0.9,
            "locality_radius": 2.7 + (mutation * 3.0),
            "mean_word_length": 5.0 + (mutation * 2.0),
            "positional_entropy": 0.58 + (mutation * 0.5),
        }
    if control_class == "table_grille":
        rows = params["table_rows"]
        jitter = params["jitter_period"]
        return {
            "repetition_rate": 0.86 + ((12.0 - rows) * 0.01),
            "information_density": 5.1 + ((rows - 8.0) * 0.22),
            "locality_radius": 2.5 + ((500.0 / max(1.0, jitter)) * 0.8),
            "mean_word_length": 5.4,
            "positional_entropy": 0.60 + ((rows - 8.0) * 0.01),
        }
    if control_class == "mechanical_reuse":
        pool = params["pool_size"]
        tpp = params["tokens_per_page"]
        return {
            "repetition_rate": max(0.0, min(1.0, 0.94 - ((pool - 15.0) * 0.004))),
            "information_density": 5.4 + ((pool - 15.0) * 0.03),
            "locality_radius": 2.6 + ((tpp - 64.0) / 64.0),
            "mean_word_length": 5.3,
            "positional_entropy": 0.62,
        }
    raise ValueError(f"Unknown control class: {control_class}")


def _score_metrics(
    predicted: Dict[str, float],
    *,
    matching_metrics: List[str],
    holdout_metrics: List[str],
) -> Dict[str, Any]:
    matching_errors: Dict[str, float] = {}
    holdout_errors: Dict[str, float] = {}

    for metric in matching_metrics:
        target = TARGETS.get(metric)
        if target is None:
            continue
        matching_errors[metric] = abs(predicted.get(metric, 0.0) - target)

    for metric in holdout_metrics:
        target = TARGETS.get(metric)
        if target is None:
            continue
        holdout_errors[metric] = abs(predicted.get(metric, 0.0) - target)

    matching_score = sum(matching_errors.values())
    holdout_score = sum(holdout_errors.values())
    composite = matching_score + (holdout_score * 0.5)

    return {
        "matching_errors": matching_errors,
        "holdout_errors": holdout_errors,
        "matching_score": matching_score,
        "holdout_score": holdout_score,
        "composite_score": composite,
    }


def _write_card(control_class: str, card: Dict[str, Any]) -> None:
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    path = CARDS_DIR / f"{control_class}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(card, f, indent=2)


def run_audit(*, policy_path: Path, preflight_only: bool, seed: int, dataset_id: str) -> Dict[str, Any]:
    policy = _load_policy(policy_path)
    data_availability_policy = _load_data_availability_policy(DATA_AVAILABILITY_POLICY_PATH)
    data_availability = _build_data_availability_snapshot(
        dataset_id=dataset_id,
        policy=data_availability_policy,
    )
    _write_data_availability_status(data_availability)

    partition = policy.get("metric_partition_policy", {})
    matching_metrics = [str(v) for v in partition.get("matching_metrics", [])]
    holdout_metrics = [str(v) for v in partition.get("holdout_evaluation_metrics", [])]
    metric_overlap = sorted(set(matching_metrics) & set(holdout_metrics))
    leakage_detected = len(metric_overlap) > 0
    evidence_scope = str(data_availability.get("evidence_scope", "full_dataset"))
    missing_pages = _as_list(data_availability.get("missing_pages"))
    missing_count = int(data_availability.get("missing_count", len(missing_pages)))

    class_cards: List[Dict[str, Any]] = []
    for control_class, space in SEARCH_SPACES.items():
        candidates = []
        for candidate in _candidate_product(space):
            predicted = _predict_metrics(control_class, candidate)
            scored = _score_metrics(
                predicted,
                matching_metrics=matching_metrics,
                holdout_metrics=holdout_metrics,
            )
            candidates.append(
                {
                    "params": candidate,
                    "predicted_metrics": predicted,
                    "scores": scored,
                }
            )

        candidates.sort(key=lambda entry: entry["scores"]["composite_score"])
        selected = candidates[0]
        card = {
            "control_class": control_class,
            "dataset_id": dataset_id,
            "seed": seed,
            "candidate_count": len(candidates),
            "search_space": space,
            "selected": selected,
            "rejected_preview": candidates[1:4],
        }
        _write_card(control_class, card)
        class_cards.append(card)

    normalization = policy.get("normalization_policy", {})
    normalization_mode = str(normalization.get("default_mode", "parser"))

    if leakage_detected:
        available_subset_status = "NON_COMPARABLE_BLOCKED"
        available_subset_reason_code = "TARGET_LEAKAGE"
        available_subset_allowed_claim = (
            "Available-subset comparability is blocked due target leakage."
        )
    elif preflight_only:
        available_subset_status = "COMPARABLE_QUALIFIED"
        available_subset_reason_code = "AVAILABLE_SUBSET_PREFLIGHT"
        available_subset_allowed_claim = (
            "Available-subset comparability is qualified and non-conclusive for full-dataset closure."
        )
    else:
        available_subset_status = "COMPARABLE_CONFIRMED"
        available_subset_reason_code = "AVAILABLE_SUBSET_CONFIRMED"
        available_subset_allowed_claim = (
            "Available-subset comparability supports bounded structural inference only."
        )

    if missing_count > 0:
        status = "NON_COMPARABLE_BLOCKED"
        reason_code = "DATA_AVAILABILITY"
        grade = "D"
        allowed_claim = (
            "Full-dataset control comparability is blocked by data availability; "
            "available-subset evidence is bounded and non-conclusive."
        )
    elif leakage_detected:
        status = "NON_COMPARABLE_BLOCKED"
        reason_code = "TARGET_LEAKAGE"
        grade = "D"
        allowed_claim = (
            "Control-based inferential claims blocked until metric overlap is eliminated."
        )
    elif preflight_only:
        status = "INCONCLUSIVE_DATA_LIMITED"
        reason_code = "PREFLIGHT_ONLY"
        grade = "C"
        allowed_claim = (
            "Comparability policy validated in preflight; confirmatory evidence requires full run."
        )
    else:
        status = "COMPARABLE_QUALIFIED"
        reason_code = "QUALIFIED_HOLDOUT"
        grade = "B"
        allowed_claim = (
            "Controls are comparable for bounded structural inference with explicit caveats."
        )

    secondary_blockers: List[str] = []
    if missing_count > 0 and leakage_detected:
        secondary_blockers.append("TARGET_LEAKAGE")

    full_data_closure_eligible = (
        missing_count == 0 and status in {"COMPARABLE_CONFIRMED", "COMPARABLE_QUALIFIED"}
    )

    summary = {
        "status": status,
        "reason_code": reason_code,
        "comparability_grade": grade,
        "allowed_claim": allowed_claim,
        "dataset_id": dataset_id,
        "preflight_only": preflight_only,
        "evidence_scope": evidence_scope,
        "full_data_closure_eligible": full_data_closure_eligible,
        "available_subset_status": available_subset_status,
        "available_subset_reason_code": available_subset_reason_code,
        "available_subset_allowed_claim": available_subset_allowed_claim,
        "matching_metrics": matching_metrics,
        "holdout_evaluation_metrics": holdout_metrics,
        "metric_overlap": metric_overlap,
        "leakage_detected": leakage_detected,
        "normalization_mode": normalization_mode,
        "missing_pages": missing_pages,
        "missing_count": missing_count,
        "approved_lost_pages": _as_list(data_availability.get("approved_lost_pages")),
        "unexpected_missing_pages": _as_list(data_availability.get("unexpected_missing_pages")),
        "data_availability_policy_pass": bool(data_availability.get("policy_pass", False)),
        "data_availability_status_path": "status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json",
        "secondary_blockers": secondary_blockers,
        "control_classes": [card["control_class"] for card in class_cards],
        "control_card_paths": [f"status/synthesis/control_matching_cards/{card['control_class']}.json" for card in class_cards],
    }
    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SK-H3 control matching audit.")
    parser.add_argument("--policy-path", default=str(POLICY_PATH), help="Path to SK-H3 policy JSON.")
    parser.add_argument("--dataset-id", default="voynich_real", help="Dataset id used for audit metadata.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic seed for audit artifacts.")
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Write deterministic audit artifacts without declaring full comparability closure.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    with active_run(
        config={
            "command": "control_matching_audit",
            "seed": args.seed,
            "dataset_id": args.dataset_id,
            "preflight_only": args.preflight_only,
        }
    ):
        summary = run_audit(
            policy_path=Path(args.policy_path),
            preflight_only=args.preflight_only,
            seed=args.seed,
            dataset_id=args.dataset_id,
        )
        ProvenanceWriter.save_results(summary, STATUS_PATH)

    print(
        "[OK] control matching audit completed "
        f"(status={summary['status']}, grade={summary['comparability_grade']}, "
        f"scope={summary['evidence_scope']}, preflight_only={summary['preflight_only']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
