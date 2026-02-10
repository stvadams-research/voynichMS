"""
Anchor-coupling analysis utilities for SK-H1 multimodal evidence hardening.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Sequence

from mechanism.large_object.collision_testing import PathCollisionTester

STATUS_CONCLUSIVE_NO_COUPLING = "CONCLUSIVE_NO_COUPLING"
STATUS_CONCLUSIVE_COUPLING_PRESENT = "CONCLUSIVE_COUPLING_PRESENT"
STATUS_INCONCLUSIVE_UNDERPOWERED = "INCONCLUSIVE_UNDERPOWERED"
STATUS_INCONCLUSIVE_INFERENTIAL_AMBIGUITY = "INCONCLUSIVE_INFERENTIAL_AMBIGUITY"
STATUS_BLOCKED_DATA_GEOMETRY = "BLOCKED_DATA_GEOMETRY"
ROBUSTNESS_CLASS_ROBUST = "ROBUST"
ROBUSTNESS_CLASS_MIXED = "MIXED"
ROBUSTNESS_CLASS_FRAGILE = "FRAGILE"
H1_4_LANE_ALIGNED = "H1_4_ALIGNED"
H1_4_LANE_QUALIFIED = "H1_4_QUALIFIED"
H1_4_LANE_BLOCKED = "H1_4_BLOCKED"
H1_4_LANE_INCONCLUSIVE = "H1_4_INCONCLUSIVE"
H1_5_LANE_ALIGNED = "H1_5_ALIGNED"
H1_5_LANE_BOUNDED = "H1_5_BOUNDED"
H1_5_LANE_QUALIFIED = "H1_5_QUALIFIED"
H1_5_LANE_BLOCKED = "H1_5_BLOCKED"
H1_5_LANE_INCONCLUSIVE = "H1_5_INCONCLUSIVE"


DEFAULT_MULTIMODAL_POLICY: Dict[str, Any] = {
    "dataset_id": "voynich_real",
    "transcription_source_id": "zandbergen_landini",
    "anchor_method_name": "geometric_v1",
    "anchor_relation_types": ["inside", "overlaps", "near"],
    "near_score_min": 0.90,
    "line_anchor_ratio_min": 0.50,
    "line_unanchored_ratio_max": 0.10,
    "sampling": {
        "matched_sampling": True,
        "max_lines_per_cohort": 400,
        "seed": 42,
    },
    "adequacy": {
        "min_lines_per_cohort": 40,
        "min_pages_per_cohort": 8,
        "min_recurring_contexts_per_cohort": 80,
        "min_balance_ratio": 0.20,
    },
    "inference": {
        "bootstrap_iterations": 250,
        "permutation_iterations": 500,
        "alpha": 0.05,
        "coupling_delta_abs_min": 0.030,
        "no_coupling_delta_abs_max": 0.015,
    },
    "robustness_matrix": {
        "matrix_id": "SK_H1_5_MATRIX_2026-02-10",
        "version": "2026-02-10-h1.5",
        "lane_taxonomy_version": "2026-02-10-h1.5",
        "publication_lane_id": "publication-default",
        "allowed_robustness_classes": [
            ROBUSTNESS_CLASS_ROBUST,
            ROBUSTNESS_CLASS_MIXED,
            ROBUSTNESS_CLASS_FRAGILE,
        ],
        "required_conclusive_agreement_ratio_for_robust": 1.0,
        "max_ambiguity_lane_count_for_robust": 0,
        "max_underpowered_lane_count_for_robust": 0,
        "max_blocked_lane_count_for_robust": 0,
        "required_conclusive_agreement_ratio_for_entitlement_robust": 1.0,
        "max_ambiguity_lane_count_for_entitlement_robust": 0,
        "max_underpowered_lane_count_for_entitlement_robust": 0,
        "max_blocked_lane_count_for_entitlement_robust": 0,
        "lane_registry": [
            {
                "lane_id": "publication-default",
                "purpose": "canonical publication lane",
                "lane_class": "entitlement",
                "seed": 42,
                "max_lines_per_cohort": 1600,
                "method_name": "geometric_v1_t001",
            },
            {
                "lane_id": "stability-probe-seed-2718",
                "purpose": "seed robustness probe",
                "lane_class": "diagnostic",
                "seed": 2718,
                "max_lines_per_cohort": 1600,
                "method_name": "geometric_v1_t001",
            },
            {
                "lane_id": "adequacy-floor",
                "purpose": "adequacy floor probe",
                "lane_class": "stress",
                "seed": 42,
                "max_lines_per_cohort": 20,
                "method_name": "geometric_v1_t001",
            },
        ],
        "reopen_conditions": [
            "registered lane matrix reaches robust class without inferential ambiguity",
            "policy thresholds are revised with documented rationale and rerun evidence",
        ],
        "h1_5_reopen_conditions": [
            "entitlement lanes lose conclusive alignment under registered matrix",
            "diagnostic/stress lanes introduce policy-incoherent contradiction",
            "lane taxonomy or thresholds are revised with documented rationale and rerun evidence",
        ],
    },
}


def classify_line_cohort(
    anchored_flags: Sequence[bool],
    *,
    anchored_ratio_min: float,
    unanchored_ratio_max: float,
) -> str:
    """Classify a line as anchored/unanchored/ambiguous based on token anchor ratio."""
    if not anchored_flags:
        return "ambiguous"
    anchored_ratio = sum(1 for flag in anchored_flags if flag) / len(anchored_flags)
    if anchored_ratio >= anchored_ratio_min:
        return "anchored"
    if anchored_ratio <= unanchored_ratio_max:
        return "unanchored"
    return "ambiguous"


def _percentile(values: Sequence[float], q: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return float(values[0])
    ordered = sorted(float(v) for v in values)
    idx = (len(ordered) - 1) * q
    low = int(idx)
    high = min(low + 1, len(ordered) - 1)
    frac = idx - low
    return ordered[low] * (1.0 - frac) + ordered[high] * frac


def compute_consistency_summary(
    lines: Sequence[Sequence[str]],
    *,
    context_len: int = 2,
) -> Dict[str, Any]:
    tester = PathCollisionTester(context_len=context_len)
    result = tester.calculate_successor_consistency([list(line) for line in lines])
    if "num_recurring_contexts" not in result:
        result["num_recurring_contexts"] = int(result.get("sample_size", 0))
    result["line_count"] = len(lines)
    result["token_count"] = int(sum(len(line) for line in lines))
    return result


def bootstrap_delta_ci(
    anchored_lines: Sequence[Sequence[str]],
    unanchored_lines: Sequence[Sequence[str]],
    *,
    iterations: int,
    seed: int,
    context_len: int = 2,
) -> Dict[str, Any]:
    if not anchored_lines or not unanchored_lines or iterations <= 0:
        return {"delta_ci_low": 0.0, "delta_ci_high": 0.0, "samples": []}
    rng = random.Random(seed)
    deltas: List[float] = []
    for _ in range(iterations):
        sampled_anchor = [
            anchored_lines[rng.randrange(len(anchored_lines))]
            for _ in range(len(anchored_lines))
        ]
        sampled_unanchored = [
            unanchored_lines[rng.randrange(len(unanchored_lines))]
            for _ in range(len(unanchored_lines))
        ]
        anchor_mean = compute_consistency_summary(
            sampled_anchor, context_len=context_len
        ).get("mean_consistency", 0.0)
        unanchored_mean = compute_consistency_summary(
            sampled_unanchored, context_len=context_len
        ).get("mean_consistency", 0.0)
        deltas.append(float(anchor_mean) - float(unanchored_mean))
    return {
        "delta_ci_low": _percentile(deltas, 0.025),
        "delta_ci_high": _percentile(deltas, 0.975),
        "samples": deltas,
    }


def permutation_p_value(
    anchored_lines: Sequence[Sequence[str]],
    unanchored_lines: Sequence[Sequence[str]],
    *,
    iterations: int,
    seed: int,
    observed_delta: float,
    context_len: int = 2,
) -> float:
    if not anchored_lines or not unanchored_lines or iterations <= 0:
        return 1.0

    rng = random.Random(seed)
    combined = [list(line) for line in anchored_lines] + [list(line) for line in unanchored_lines]
    n_anchor = len(anchored_lines)
    observed_abs = abs(float(observed_delta))
    extreme = 0

    for _ in range(iterations):
        permuted = combined[:]
        rng.shuffle(permuted)
        perm_anchor = permuted[:n_anchor]
        perm_unanchored = permuted[n_anchor:]
        anchor_mean = compute_consistency_summary(
            perm_anchor, context_len=context_len
        ).get("mean_consistency", 0.0)
        unanchored_mean = compute_consistency_summary(
            perm_unanchored, context_len=context_len
        ).get("mean_consistency", 0.0)
        if abs(float(anchor_mean) - float(unanchored_mean)) >= observed_abs:
            extreme += 1
    return float((extreme + 1) / (iterations + 1))


def evaluate_adequacy(
    *,
    available_anchor_line_count: int,
    available_unanchored_line_count: int,
    anchored_page_count: int,
    unanchored_page_count: int,
    anchored_recurring_contexts: int,
    unanchored_recurring_contexts: int,
    policy: Dict[str, Any],
) -> Dict[str, Any]:
    min_lines = int(policy.get("min_lines_per_cohort", 0))
    min_pages = int(policy.get("min_pages_per_cohort", 0))
    min_contexts = int(policy.get("min_recurring_contexts_per_cohort", 0))
    min_balance_ratio = float(policy.get("min_balance_ratio", 0.0))

    reasons: List[str] = []
    blocked_reasons: List[str] = []

    if available_anchor_line_count <= 0:
        blocked_reasons.append("no_anchored_lines")
    if available_unanchored_line_count <= 0:
        blocked_reasons.append("no_unanchored_lines")
    if anchored_page_count <= 0:
        blocked_reasons.append("no_anchored_pages")
    if unanchored_page_count <= 0:
        blocked_reasons.append("no_unanchored_pages")

    if blocked_reasons:
        return {
            "pass": False,
            "blocked": True,
            "reasons": blocked_reasons,
            "metrics": {
                "available_anchor_line_count": available_anchor_line_count,
                "available_unanchored_line_count": available_unanchored_line_count,
                "anchored_page_count": anchored_page_count,
                "unanchored_page_count": unanchored_page_count,
                "anchored_recurring_contexts": anchored_recurring_contexts,
                "unanchored_recurring_contexts": unanchored_recurring_contexts,
                "balance_ratio": 0.0,
            },
        }

    max_lines = max(available_anchor_line_count, available_unanchored_line_count)
    min_lines_observed = min(available_anchor_line_count, available_unanchored_line_count)
    balance_ratio = (min_lines_observed / max_lines) if max_lines > 0 else 0.0

    if min_lines_observed < min_lines:
        reasons.append(
            f"line_count_below_min: observed={min_lines_observed} required={min_lines}"
        )
    if min(anchored_page_count, unanchored_page_count) < min_pages:
        reasons.append(
            "page_count_below_min: observed="
            f"{min(anchored_page_count, unanchored_page_count)} required={min_pages}"
        )
    if min(anchored_recurring_contexts, unanchored_recurring_contexts) < min_contexts:
        reasons.append(
            "recurring_contexts_below_min: observed="
            f"{min(anchored_recurring_contexts, unanchored_recurring_contexts)} "
            f"required={min_contexts}"
        )
    if balance_ratio < min_balance_ratio:
        reasons.append(
            f"balance_ratio_below_min: observed={balance_ratio:.3f} required={min_balance_ratio:.3f}"
        )

    return {
        "pass": len(reasons) == 0,
        "blocked": False,
        "reasons": reasons,
        "metrics": {
            "available_anchor_line_count": available_anchor_line_count,
            "available_unanchored_line_count": available_unanchored_line_count,
            "anchored_page_count": anchored_page_count,
            "unanchored_page_count": unanchored_page_count,
            "anchored_recurring_contexts": anchored_recurring_contexts,
            "unanchored_recurring_contexts": unanchored_recurring_contexts,
            "balance_ratio": balance_ratio,
        },
    }


def evaluate_inference(
    *,
    delta_mean_consistency: float,
    delta_ci_low: float,
    delta_ci_high: float,
    p_value: float,
    policy: Dict[str, Any],
) -> Dict[str, Any]:
    alpha = float(policy.get("alpha", 0.05))
    coupling_delta_abs_min = float(policy.get("coupling_delta_abs_min", 0.03))
    no_coupling_delta_abs_max = float(policy.get("no_coupling_delta_abs_max", 0.015))

    ci_crosses_zero = delta_ci_low <= 0.0 <= delta_ci_high
    abs_delta = abs(float(delta_mean_consistency))

    if (
        p_value < alpha
        and abs_delta >= coupling_delta_abs_min
        and not ci_crosses_zero
    ):
        decision = "COUPLING_PRESENT"
    elif (
        p_value >= alpha
        and abs_delta <= no_coupling_delta_abs_max
        and ci_crosses_zero
    ):
        decision = "NO_COUPLING"
    else:
        decision = "INCONCLUSIVE"

    return {
        "decision": decision,
        "alpha": alpha,
        "coupling_delta_abs_min": coupling_delta_abs_min,
        "no_coupling_delta_abs_max": no_coupling_delta_abs_max,
        "ci_crosses_zero": ci_crosses_zero,
        "abs_delta": abs_delta,
    }


def allowed_claim_for_status(status: str) -> str:
    if status == STATUS_CONCLUSIVE_NO_COUPLING:
        return (
            "No robust image/layout coupling signal was detected under the configured "
            "adequacy and inference criteria."
        )
    if status == STATUS_CONCLUSIVE_COUPLING_PRESENT:
        return (
            "A coupling signal was detected under the configured adequacy and "
            "inference criteria."
        )
    if status == STATUS_BLOCKED_DATA_GEOMETRY:
        return (
            "Coupling assessment is blocked by cohort-geometry/data-availability "
            "constraints; no conclusive claim is allowed."
        )
    if status == STATUS_INCONCLUSIVE_INFERENTIAL_AMBIGUITY:
        return (
            "Adequacy thresholds are satisfied, but inferential evidence remains "
            "ambiguous; no conclusive coupling claim is allowed."
        )
    return (
        "Current evidence is underpowered or ambiguous; no conclusive coupling claim "
        "is allowed."
    )


def decide_status(
    *,
    adequacy: Dict[str, Any],
    inference: Dict[str, Any],
) -> Dict[str, Any]:
    if adequacy.get("blocked"):
        status = STATUS_BLOCKED_DATA_GEOMETRY
        reason = "geometry_or_data_block"
    elif not adequacy.get("pass"):
        status = STATUS_INCONCLUSIVE_UNDERPOWERED
        reason = "adequacy_thresholds_not_met"
    else:
        decision = inference.get("decision")
        if decision == "NO_COUPLING":
            status = STATUS_CONCLUSIVE_NO_COUPLING
            reason = "adequacy_and_inference_support_no_coupling"
        elif decision == "COUPLING_PRESENT":
            status = STATUS_CONCLUSIVE_COUPLING_PRESENT
            reason = "adequacy_and_inference_support_coupling"
        else:
            status = STATUS_INCONCLUSIVE_INFERENTIAL_AMBIGUITY
            reason = "inferential_ambiguity"

    return {
        "status": status,
        "status_reason": reason,
        "allowed_claim": allowed_claim_for_status(status),
    }


def derive_h1_4_closure_lane(*, status: str, robustness_class: str) -> str:
    conclusive_statuses = {
        STATUS_CONCLUSIVE_NO_COUPLING,
        STATUS_CONCLUSIVE_COUPLING_PRESENT,
    }
    inconclusive_statuses = {
        STATUS_INCONCLUSIVE_UNDERPOWERED,
        STATUS_INCONCLUSIVE_INFERENTIAL_AMBIGUITY,
    }

    if status in conclusive_statuses:
        if robustness_class == ROBUSTNESS_CLASS_ROBUST:
            return H1_4_LANE_ALIGNED
        if robustness_class in {ROBUSTNESS_CLASS_MIXED, ROBUSTNESS_CLASS_FRAGILE}:
            return H1_4_LANE_QUALIFIED
    if status in inconclusive_statuses:
        return H1_4_LANE_INCONCLUSIVE
    if status == STATUS_BLOCKED_DATA_GEOMETRY:
        return H1_4_LANE_BLOCKED
    return H1_4_LANE_INCONCLUSIVE


def derive_h1_5_closure_lane(
    *,
    status: str,
    entitlement_robustness_class: str,
    diagnostic_lane_count: int,
    diagnostic_non_conclusive_count: int,
    robust_closure_reachable: bool,
) -> str:
    conclusive_statuses = {
        STATUS_CONCLUSIVE_NO_COUPLING,
        STATUS_CONCLUSIVE_COUPLING_PRESENT,
    }
    inconclusive_statuses = {
        STATUS_INCONCLUSIVE_UNDERPOWERED,
        STATUS_INCONCLUSIVE_INFERENTIAL_AMBIGUITY,
    }

    if not robust_closure_reachable:
        return H1_5_LANE_BLOCKED
    if status in conclusive_statuses:
        if entitlement_robustness_class == ROBUSTNESS_CLASS_ROBUST:
            if diagnostic_lane_count > 0 and diagnostic_non_conclusive_count > 0:
                return H1_5_LANE_BOUNDED
            return H1_5_LANE_ALIGNED
        if entitlement_robustness_class in {
            ROBUSTNESS_CLASS_MIXED,
            ROBUSTNESS_CLASS_FRAGILE,
        }:
            return H1_5_LANE_QUALIFIED
    if status in inconclusive_statuses:
        return H1_5_LANE_INCONCLUSIVE
    if status == STATUS_BLOCKED_DATA_GEOMETRY:
        return H1_5_LANE_BLOCKED
    return H1_5_LANE_INCONCLUSIVE
