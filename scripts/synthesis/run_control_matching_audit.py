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


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _derive_h3_5_closure_lane(
    *,
    status: str,
    reason_code: str,
    evidence_scope: str,
    full_data_closure_eligible: bool,
    full_data_feasibility: str,
    missing_count: int,
    policy: Dict[str, Any],
) -> str:
    aligned_lane = str(policy.get("aligned_lane", "H3_5_ALIGNED"))
    terminal_lane = str(
        policy.get("terminal_qualified_lane", "H3_5_TERMINAL_QUALIFIED")
    )
    blocked_lane = str(policy.get("blocked_lane", "H3_5_BLOCKED"))
    inconclusive_lane = str(policy.get("inconclusive_lane", "H3_5_INCONCLUSIVE"))

    if (
        full_data_feasibility == "feasible"
        and missing_count == 0
        and evidence_scope == "full_dataset"
        and full_data_closure_eligible is True
        and status in {"COMPARABLE_CONFIRMED", "COMPARABLE_QUALIFIED", "DATA_AVAILABILITY_CLEAR"}
    ):
        return aligned_lane

    if (
        full_data_feasibility == "irrecoverable"
        and missing_count > 0
        and reason_code == "DATA_AVAILABILITY"
        and evidence_scope == "available_subset"
        and full_data_closure_eligible is False
    ):
        return terminal_lane

    if status == "INCONCLUSIVE_DATA_LIMITED":
        return inconclusive_lane

    return blocked_lane


def _resolve_h3_5_contract(
    *,
    lane: str,
    policy: Dict[str, Any],
    full_data_terminal_reason: str,
    full_data_reopen_conditions: List[str],
) -> Dict[str, Any]:
    aligned_lane = str(policy.get("aligned_lane", "H3_5_ALIGNED"))
    terminal_lane = str(
        policy.get("terminal_qualified_lane", "H3_5_TERMINAL_QUALIFIED")
    )
    blocked_lane = str(policy.get("blocked_lane", "H3_5_BLOCKED"))
    inconclusive_lane = str(policy.get("inconclusive_lane", "H3_5_INCONCLUSIVE"))

    if lane == aligned_lane:
        residual_reason = str(
            policy.get("aligned_residual_reason", "full_data_closure_aligned")
        )
        reopen_conditions = _as_list(
            policy.get("aligned_reopen_conditions")
        ) or ["none_required_full_data_available"]
    elif lane == terminal_lane:
        residual_reason = str(
            policy.get(
                "terminal_qualified_residual_reason",
                full_data_terminal_reason or "approved_lost_pages_not_in_source_corpus",
            )
        )
        reopen_conditions = _as_list(
            policy.get("terminal_qualified_reopen_conditions")
        ) or list(full_data_reopen_conditions)
    elif lane == inconclusive_lane:
        residual_reason = str(
            policy.get(
                "inconclusive_residual_reason",
                "evidence_incomplete_for_deterministic_lane",
            )
        )
        reopen_conditions = _as_list(
            policy.get("inconclusive_reopen_conditions")
        ) or [
            "complete_evidence_bundle_for_lane_classification",
            "rerun_control_matching_with_full_contract_coverage",
        ]
    elif lane == blocked_lane:
        residual_reason = str(
            policy.get(
                "blocked_residual_reason",
                "artifact_or_policy_contract_incoherence_detected",
            )
        )
        reopen_conditions = _as_list(policy.get("blocked_reopen_conditions")) or [
            "repair_artifact_parity_and_freshness_contracts",
            "rerun_control_matching_and_data_availability_checks",
        ]
    else:
        residual_reason = str(
            policy.get(
                "fallback_residual_reason",
                "h3_5_lane_unrecognized_contract_review_required",
            )
        )
        reopen_conditions = _as_list(policy.get("fallback_reopen_conditions")) or [
            "review_h3_5_lane_contract_configuration"
        ]

    return {
        "h3_5_residual_reason": residual_reason,
        "h3_5_reopen_conditions": reopen_conditions,
    }


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

    if missing_count > 0:
        strict_preflight_policy_pass = (
            strict_computed
            and strict_status == "BLOCKED"
            and strict_reason_code == "DATA_AVAILABILITY"
        )
    else:
        strict_preflight_policy_pass = strict_computed and strict_status == "PREFLIGHT_OK"

    approved_lost_pages_match = (
        sorted(missing_pages) == approved_lost_pages if missing_count > 0 else True
    )
    missing_count_consistent = _to_int(preflight.get("missing_count"), missing_count) == missing_count
    approved_lost_pages_policy_version = str(policy.get("version", "unknown"))
    approved_lost_pages_source_note_path = str(
        policy.get("approved_lost_pages_source_note_path", "")
    )

    has_unexpected_missing = len(unexpected_missing_pages) > 0
    has_approved_lost_only = missing_count > 0 and not has_unexpected_missing
    feasibility_policy = _as_dict(policy.get("feasibility_policy"))
    feasible_terminal_reason = str(
        feasibility_policy.get("feasible_terminal_reason", "full_data_pages_available")
    )
    irrecoverable_terminal_reason = str(
        feasibility_policy.get(
            "irrecoverable_terminal_reason",
            "approved_lost_pages_not_in_source_corpus",
        )
    )
    review_required_terminal_reason = str(
        feasibility_policy.get(
            "review_required_terminal_reason",
            "unexpected_missing_pages_require_recovery",
        )
    )
    aligned_lane = str(feasibility_policy.get("aligned_lane", "H3_4_ALIGNED"))
    qualified_lane = str(feasibility_policy.get("qualified_lane", "H3_4_QUALIFIED"))
    blocked_lane = str(feasibility_policy.get("blocked_lane", "H3_4_BLOCKED"))
    h3_5_policy = _as_dict(policy.get("h3_5_policy"))

    if missing_count == 0:
        irrecoverability_classification = "FULL_DATA_AVAILABLE"
        full_data_feasibility = "feasible"
        full_data_closure_terminal_reason = feasible_terminal_reason
        h3_4_closure_lane = aligned_lane
    elif has_unexpected_missing:
        irrecoverability_classification = "UNEXPECTED_MISSING_REVIEW_REQUIRED"
        full_data_feasibility = "feasible"
        full_data_closure_terminal_reason = review_required_terminal_reason
        h3_4_closure_lane = blocked_lane
    else:
        irrecoverability_classification = "APPROVED_LOST_IRRECOVERABLE"
        full_data_feasibility = "irrecoverable"
        full_data_closure_terminal_reason = irrecoverable_terminal_reason
        h3_4_closure_lane = qualified_lane

    full_data_closure_reopen_conditions = (
        [
            "new_primary_source_pages_added_to_dataset",
            "approved_lost_pages_policy_updated_with_new_evidence",
        ]
        if missing_count > 0
        else ["none_required_full_data_available"]
    )

    irrecoverability = {
        "recoverable": missing_count == 0 or has_unexpected_missing,
        "approved_lost": has_approved_lost_only,
        "unexpected_missing": has_unexpected_missing,
        "classification": irrecoverability_classification,
    }

    policy_checks = {
        "strict_preflight_policy_pass": strict_preflight_policy_pass,
        "approved_lost_pages_match": approved_lost_pages_match,
        "missing_count_consistent": missing_count_consistent,
        "unexpected_missing_pages_empty": not has_unexpected_missing,
        "irrecoverability_metadata_complete": all(
            key in irrecoverability
            for key in ("recoverable", "approved_lost", "unexpected_missing", "classification")
        ),
        "source_reference_pinned": bool(approved_lost_pages_policy_version)
        and bool(approved_lost_pages_source_note_path),
        "full_data_feasibility_declared": full_data_feasibility in {"feasible", "irrecoverable"},
        "closure_lane_declared": bool(h3_4_closure_lane),
    }
    h3_5_closure_lane = _derive_h3_5_closure_lane(
        status="DATA_AVAILABILITY_BLOCKED" if missing_count > 0 else "DATA_AVAILABILITY_CLEAR",
        reason_code="DATA_AVAILABILITY" if missing_count > 0 else "NONE",
        evidence_scope=evidence_scope,
        full_data_closure_eligible=missing_count == 0,
        full_data_feasibility=full_data_feasibility,
        missing_count=missing_count,
        policy=h3_5_policy,
    )
    h3_5_contract = _resolve_h3_5_contract(
        lane=h3_5_closure_lane,
        policy=h3_5_policy,
        full_data_terminal_reason=full_data_closure_terminal_reason,
        full_data_reopen_conditions=full_data_closure_reopen_conditions,
    )
    policy_checks["h3_5_closure_lane_declared"] = bool(h3_5_closure_lane)
    policy_checks["h3_5_reopen_conditions_declared"] = bool(
        h3_5_contract.get("h3_5_reopen_conditions")
    )
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
        "approved_lost_pages_policy_version": approved_lost_pages_policy_version,
        "approved_lost_pages_source_note_path": approved_lost_pages_source_note_path,
        "approved_missing_pages": approved_missing_pages,
        "unexpected_missing_pages": unexpected_missing_pages,
        "full_data_feasibility": full_data_feasibility,
        "full_data_closure_terminal_reason": full_data_closure_terminal_reason,
        "full_data_closure_reopen_conditions": full_data_closure_reopen_conditions,
        "h3_4_closure_lane": h3_4_closure_lane,
        "h3_5_closure_lane": h3_5_closure_lane,
        "h3_5_residual_reason": h3_5_contract.get("h3_5_residual_reason"),
        "h3_5_reopen_conditions": h3_5_contract.get("h3_5_reopen_conditions", []),
        "irrecoverability": irrecoverability,
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
    available_subset_policy = dict(policy.get("available_subset_policy", {}))
    thresholds = dict(available_subset_policy.get("thresholds", {}))

    control_card_paths = [
        f"status/synthesis/control_matching_cards/{card['control_class']}.json"
        for card in class_cards
    ]
    selected_composite_scores = [
        float(card.get("selected", {}).get("scores", {}).get("composite_score", 0.0))
        for card in class_cards
    ]
    stability_margins = []
    for card in class_cards:
        selected_score = float(card.get("selected", {}).get("scores", {}).get("composite_score", 0.0))
        rejected = list(card.get("rejected_preview", []))
        if rejected:
            alt_score = float(rejected[0].get("scores", {}).get("composite_score", selected_score))
            stability_margins.append(max(0.0, alt_score - selected_score))

    control_card_count = len(class_cards)
    expected_control_class_count = len(SEARCH_SPACES)
    control_class_coverage_ratio = (
        control_card_count / expected_control_class_count
        if expected_control_class_count > 0
        else 0.0
    )
    mean_selected_score = (
        sum(selected_composite_scores) / len(selected_composite_scores)
        if selected_composite_scores
        else 0.0
    )
    max_selected_score = max(selected_composite_scores) if selected_composite_scores else 0.0
    stability_margin_min = min(stability_margins) if stability_margins else 0.0
    stability_margin_mean = (
        sum(stability_margins) / len(stability_margins) if stability_margins else 0.0
    )

    min_control_card_count = _to_int(
        thresholds.get("min_control_card_count"), expected_control_class_count
    )
    min_control_class_coverage_ratio = _to_float(
        thresholds.get("min_control_class_coverage_ratio"), 1.0
    )
    max_mean_selected_composite_score = _to_float(
        thresholds.get("max_mean_selected_composite_score"), 0.5
    )
    min_stability_margin = _to_float(thresholds.get("min_stability_margin"), 0.05)

    available_subset_thresholds = {
        "min_control_card_count": min_control_card_count,
        "min_control_class_coverage_ratio": min_control_class_coverage_ratio,
        "max_mean_selected_composite_score": max_mean_selected_composite_score,
        "min_stability_margin": min_stability_margin,
    }
    available_subset_passes_thresholds = (
        control_card_count >= min_control_card_count
        and control_class_coverage_ratio >= min_control_class_coverage_ratio
        and mean_selected_score <= max_mean_selected_composite_score
        and stability_margin_min >= min_stability_margin
    )
    available_subset_diagnostics = {
        "control_card_count": control_card_count,
        "expected_control_class_count": expected_control_class_count,
        "control_class_coverage_ratio": control_class_coverage_ratio,
        "mean_selected_composite_score": mean_selected_score,
        "max_selected_composite_score": max_selected_score,
        "stability_margin_min": stability_margin_min,
        "stability_margin_mean": stability_margin_mean,
        "stability_envelope": {
            "min_selected_composite_score": min(selected_composite_scores)
            if selected_composite_scores
            else 0.0,
            "max_selected_composite_score": max_selected_score,
            "range_selected_composite_score": (
                (max_selected_score - min(selected_composite_scores))
                if selected_composite_scores
                else 0.0
            ),
        },
        "power_indicator": (
            "ADEQUATE" if control_card_count >= min_control_card_count else "UNDERPOWERED"
        ),
        "coverage_indicator": (
            "SUFFICIENT"
            if control_class_coverage_ratio >= min_control_class_coverage_ratio
            else "INSUFFICIENT"
        ),
        "thresholds": available_subset_thresholds,
        "passes_thresholds": available_subset_passes_thresholds,
    }
    available_subset_reproducibility = {
        "preflight_only": preflight_only,
        "dataset_id": dataset_id,
        "seed": seed,
        "control_card_paths": control_card_paths,
        "control_card_count": control_card_count,
    }
    available_subset_confidence_provenance = {
        "thresholds_passed": available_subset_passes_thresholds,
        "preflight_only": preflight_only,
        "evidence_scope": evidence_scope,
        "control_card_count": control_card_count,
        "control_class_coverage_ratio": control_class_coverage_ratio,
        "stability_margin_min": stability_margin_min,
        "mean_selected_composite_score": mean_selected_score,
        "source_artifacts": control_card_paths,
    }
    available_subset_confidence = (
        "UNDERPOWERED" if not available_subset_passes_thresholds else "QUALIFIED"
    )

    if leakage_detected:
        available_subset_status = "NON_COMPARABLE_BLOCKED"
        available_subset_reason_code = "TARGET_LEAKAGE"
        available_subset_confidence = "BLOCKED"
        available_subset_allowed_claim = (
            "Available-subset comparability is blocked due target leakage."
        )
    elif not available_subset_passes_thresholds:
        available_subset_status = "INCONCLUSIVE_DATA_LIMITED"
        available_subset_reason_code = "AVAILABLE_SUBSET_UNDERPOWERED"
        available_subset_allowed_claim = (
            "Available-subset comparability is underpowered; additional evidence is required."
        )
    elif preflight_only:
        available_subset_status = "COMPARABLE_QUALIFIED"
        available_subset_reason_code = "AVAILABLE_SUBSET_QUALIFIED"
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
    elif available_subset_status == "INCONCLUSIVE_DATA_LIMITED":
        status = "INCONCLUSIVE_DATA_LIMITED"
        reason_code = "AVAILABLE_SUBSET_UNDERPOWERED"
        grade = "C"
        allowed_claim = (
            "Comparability remains underpowered on available-subset evidence; "
            "full-dataset closure is not permitted."
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
    full_data_feasibility = str(data_availability.get("full_data_feasibility", "feasible"))
    h3_5_policy = _as_dict(data_availability_policy.get("h3_5_policy"))
    if (
        full_data_feasibility == "irrecoverable"
        and status == "NON_COMPARABLE_BLOCKED"
        and reason_code == "DATA_AVAILABILITY"
        and evidence_scope == "available_subset"
        and full_data_closure_eligible is False
    ):
        h3_4_closure_lane = "H3_4_QUALIFIED"
    elif full_data_closure_eligible:
        h3_4_closure_lane = "H3_4_ALIGNED"
    elif status == "INCONCLUSIVE_DATA_LIMITED":
        h3_4_closure_lane = "H3_4_INCONCLUSIVE"
    else:
        h3_4_closure_lane = "H3_4_BLOCKED"
    h3_5_closure_lane = _derive_h3_5_closure_lane(
        status=status,
        reason_code=reason_code,
        evidence_scope=evidence_scope,
        full_data_closure_eligible=full_data_closure_eligible,
        full_data_feasibility=full_data_feasibility,
        missing_count=missing_count,
        policy=h3_5_policy,
    )
    h3_5_contract = _resolve_h3_5_contract(
        lane=h3_5_closure_lane,
        policy=h3_5_policy,
        full_data_terminal_reason=str(
            data_availability.get("full_data_closure_terminal_reason", "")
        ),
        full_data_reopen_conditions=_as_list(
            data_availability.get("full_data_closure_reopen_conditions", [])
        ),
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
        "available_subset_confidence": available_subset_confidence,
        "available_subset_allowed_claim": available_subset_allowed_claim,
        "available_subset_diagnostics": available_subset_diagnostics,
        "available_subset_reproducibility": available_subset_reproducibility,
        "available_subset_confidence_provenance": available_subset_confidence_provenance,
        "matching_metrics": matching_metrics,
        "holdout_evaluation_metrics": holdout_metrics,
        "metric_overlap": metric_overlap,
        "leakage_detected": leakage_detected,
        "normalization_mode": normalization_mode,
        "missing_pages": missing_pages,
        "missing_count": missing_count,
        "full_data_feasibility": full_data_feasibility,
        "full_data_closure_terminal_reason": data_availability.get(
            "full_data_closure_terminal_reason"
        ),
        "full_data_closure_reopen_conditions": data_availability.get(
            "full_data_closure_reopen_conditions", []
        ),
        "h3_4_closure_lane": h3_4_closure_lane,
        "h3_5_closure_lane": h3_5_closure_lane,
        "h3_5_residual_reason": h3_5_contract.get("h3_5_residual_reason"),
        "h3_5_reopen_conditions": h3_5_contract.get("h3_5_reopen_conditions", []),
        "approved_lost_pages": _as_list(data_availability.get("approved_lost_pages")),
        "approved_lost_pages_policy_version": data_availability.get(
            "approved_lost_pages_policy_version"
        ),
        "approved_lost_pages_source_note_path": data_availability.get(
            "approved_lost_pages_source_note_path"
        ),
        "unexpected_missing_pages": _as_list(data_availability.get("unexpected_missing_pages")),
        "irrecoverability": data_availability.get("irrecoverability", {}),
        "data_availability_policy_pass": bool(data_availability.get("policy_pass", False)),
        "data_availability_status_path": "status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json",
        "secondary_blockers": secondary_blockers,
        "control_classes": [card["control_class"] for card in class_cards],
        "control_card_paths": control_card_paths,
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
