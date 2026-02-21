from __future__ import annotations

import csv
import logging
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from phase1_foundation.core.provenance import ProvenanceWriter

logger = logging.getLogger(__name__)

DEFAULT_RANDOM_SEED = 42
DEFAULT_ITERATIONS = 2000
DEFAULT_TARGET = "Voynich"
DEFAULT_STATUS_THRESHOLDS: dict[str, float] = {
    "min_nearest_neighbor_stability_for_confirmed": 0.75,
    "min_jackknife_stability_for_confirmed": 0.75,
    "min_rank_stability_for_confirmed": 0.65,
    "min_probability_margin_for_confirmed": 0.10,
    "min_top2_gap_ci_lower_for_confirmed": 0.05,
    "min_nearest_neighbor_stability_for_qualified": 0.50,
    "min_jackknife_stability_for_qualified": 0.70,
    "min_rank_stability_for_qualified": 0.55,
    "min_probability_margin_for_qualified": 0.03,
    "min_top2_set_stability_for_identity_flip_dominant": 0.60,
    "min_rank_entropy_for_high": 1.50,
}

M2_REASON_TO_RESIDUAL: dict[str, str] = {
    "ROBUST_NEAREST_NEIGHBOR": "none",
    "MODERATE_RANK_VOLATILITY": "directional_signal_requires_explicit_uncertainty_caveats",
    "TOP2_GAP_FRAGILE": "top2_gap_confidence_interval_remains_fragile",
    "TOP2_IDENTITY_FLIP_DOMINANT": "top2_identity_flip_rate_remains_dominant",
    "MARGIN_VOLATILITY_DOMINANT": "nearest_neighbor_margin_volatility_remains_dominant",
    "RANK_ENTROPY_HIGH": "rank_entropy_remains_high_under_registered_perturbations",
    "RANK_UNSTABLE_UNDER_PERTURBATION": "rank_stability_below_qualified_floor",
    "CONFIDENCE_BELOW_POLICY": "comparative_confidence_below_policy_thresholds",
    "FIELD_INCOMPLETE": "uncertainty_contract_fields_incomplete",
}

M2_4_REOPEN_TRIGGERS_BY_LANE: dict[str, list[str]] = {
    "M2_4_ALIGNED": [
        (
            "Reopen if any confirmed-threshold metric falls below policy floor in "
            "canonical reruns."
        ),
        "Reopen if checker/report entitlement coherence fails.",
    ],
    "M2_4_QUALIFIED": [
        (
            "Promote to M2_4_ALIGNED only when confirmed-threshold metrics clear "
            "simultaneously."
        ),
        "Reopen if uncertainty diagnostics become incomplete or coherence checks fail.",
    ],
    "M2_4_BOUNDED": [
        (
            "Promote only when nearest_neighbor_stability, "
            "jackknife_nearest_neighbor_stability, rank_stability, "
            "nearest_neighbor_probability_margin, and top2_gap.ci95_lower satisfy "
            "promotion thresholds."
        ),
        (
            "Reopen if dominant fragility signal or nearest-neighbor identity shifts "
            "under registered matrix reruns."
        ),
    ],
    "M2_4_INCONCLUSIVE": [
        "Restore required uncertainty fields and regenerate canonical artifact.",
        "Reopen after policy/checker/report parity is restored.",
    ],
}

M2_5_REOPEN_TRIGGERS_BY_LANE: dict[str, list[str]] = {
    "M2_5_ALIGNED": [
        "Reopen if confirmed-threshold support degrades in canonical reruns.",
        "Reopen if checker/policy/report parity fails.",
    ],
    "M2_5_QUALIFIED": [
        "Promote to M2_5_ALIGNED only when confirmed-threshold support is complete.",
        "Demote to M2_5_BOUNDED if fragility diagnostics regress.",
    ],
    "M2_5_BOUNDED": [
        "Promote only when qualified/confirmed stability predicates are satisfied.",
        (
            "Reopen if dominant fragility signal, nearest-neighbor identity, or "
            "artifact coherence materially changes."
        ),
    ],
    "M2_5_BLOCKED": [
        "Repair missing uncertainty contract fields before reclassification.",
        "Reopen when checker/policy/report parity is restored.",
    ],
    "M2_5_INCONCLUSIVE": [
        "Complete missing evidence required for deterministic lane classification.",
        "Re-run canonical matrix after evidence completion.",
    ],
}


def load_matrix(csv_path: Path | str) -> dict[str, np.ndarray]:
    """Load a comparative feature matrix from a CSV file.

    Reads a CSV where each row is an artifact. The 'Artifact' column supplies
    the key and the remaining numeric columns form the feature vector.

    Returns a dict mapping artifact names to numpy feature vectors.
    """
    matrix: dict[str, np.ndarray] = {}
    with open(csv_path, encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            name = str(row.pop("Artifact"))
            vector = np.array([float(v) for v in row.values()], dtype=float)
            matrix[name] = vector
    return matrix


def _resolve_existing_path(path: Path | str, fallback: str) -> Path:
    resolved = Path(path)
    if resolved.exists():
        return resolved
    fallback_path = Path(__file__).resolve().parent.parent.parent / fallback
    return fallback_path


def _distance(
    target_vector: np.ndarray,
    candidate_vector: np.ndarray,
    *,
    dimensions: np.ndarray | None = None,
    weights: np.ndarray | None = None,
) -> float:
    if dimensions is None:
        v_target = target_vector
        v_candidate = candidate_vector
    else:
        v_target = target_vector[dimensions]
        v_candidate = candidate_vector[dimensions]
    diff = v_target - v_candidate
    if weights is not None:
        diff = diff * weights
    return float(np.linalg.norm(diff))


def calculate_distances(
    matrix: Mapping[str, np.ndarray],
    *,
    target: str = DEFAULT_TARGET,
    dimensions: np.ndarray | None = None,
    weights: np.ndarray | None = None,
) -> dict[str, float]:
    """Compute weighted Euclidean distances from a target artifact to all others.

    Optionally restricts computation to a subset of dimensions and applies
    per-dimension weights. Returns a dict mapping each non-target artifact
    name to its distance from the target.
    """
    target_vector = matrix[target]
    distances: dict[str, float] = {}
    for name, vector in matrix.items():
        if name == target:
            continue
        distances[name] = _distance(
            target_vector,
            vector,
            dimensions=dimensions,
            weights=weights,
        )
    return distances


def _to_ci95(values: np.ndarray) -> dict[str, float]:
    lower, upper = np.percentile(values, [2.5, 97.5])
    return {
        "mean": float(np.mean(values)),
        "std": float(np.std(values)),
        "ci95_lower": float(lower),
        "ci95_upper": float(upper),
    }


def _merge_status_thresholds(
    overrides: Mapping[str, Any] | None,
) -> dict[str, float]:
    thresholds = dict(DEFAULT_STATUS_THRESHOLDS)
    if not isinstance(overrides, Mapping):
        return thresholds
    for key, default_value in DEFAULT_STATUS_THRESHOLDS.items():
        if key not in overrides:
            continue
        try:
            thresholds[key] = float(overrides[key])
        except (TypeError, ValueError):
            logger.warning(
                "Invalid SK-M2 threshold override for %s=%r; using default %.4f",
                key,
                overrides[key],
                default_value,
            )
    return thresholds


def _resolve_m2_residual_reason(
    *, status: str, reason_code: str, required_fields_present: bool
) -> str:
    if not required_fields_present:
        return M2_REASON_TO_RESIDUAL["FIELD_INCOMPLETE"]
    if status == "STABILITY_CONFIRMED":
        return "none"
    return M2_REASON_TO_RESIDUAL.get(
        reason_code, "comparative_confidence_below_policy_thresholds"
    )


def _derive_m2_4_closure_lane(*, status: str, required_fields_present: bool) -> str:
    if status == "STABILITY_CONFIRMED":
        return "M2_4_ALIGNED"
    if status == "DISTANCE_QUALIFIED":
        return "M2_4_QUALIFIED"
    if status == "INCONCLUSIVE_UNCERTAINTY":
        if required_fields_present:
            return "M2_4_BOUNDED"
        return "M2_4_INCONCLUSIVE"
    return "M2_4_INCONCLUSIVE"


def _derive_m2_5_closure_lane(*, status: str, required_fields_present: bool) -> str:
    if status == "STABILITY_CONFIRMED":
        return "M2_5_ALIGNED"
    if status == "DISTANCE_QUALIFIED":
        return "M2_5_QUALIFIED"
    if status == "INCONCLUSIVE_UNCERTAINTY":
        if required_fields_present:
            return "M2_5_BOUNDED"
        return "M2_5_BLOCKED"
    return "M2_5_INCONCLUSIVE"


def _lane_reopen_triggers(lane: str, *, m2_generation: str) -> list[str]:
    if m2_generation == "M2_4":
        return list(M2_4_REOPEN_TRIGGERS_BY_LANE.get(lane, []))
    return list(M2_5_REOPEN_TRIGGERS_BY_LANE.get(lane, []))


def compute_distance_uncertainty(
    matrix: Mapping[str, np.ndarray],
    *,
    target: str = DEFAULT_TARGET,
    seed: int = DEFAULT_RANDOM_SEED,
    iterations: int = DEFAULT_ITERATIONS,
    run_profile: str = "custom",
    status_thresholds: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Quantify uncertainty of comparative distances via bootstrap perturbation.

    Performs bootstrap resampling of feature dimensions with weight jitter and
    leave-one-dimension-out jackknife analysis. Produces stability metrics
    (nearest-neighbor stability, rank stability, top-2 gap robustness),
    fragility diagnostics, and M2.4/M2.5 closure-lane classifications.

    Returns a dict containing status, distance summaries, stability metrics,
    fragility diagnostics, and closure-lane assignments.
    """
    if target not in matrix:
        raise KeyError(f"Target artifact {target!r} not found in matrix")
    if iterations < 100:
        raise ValueError("iterations must be >= 100 for stable confidence estimates")

    target_vector = matrix[target]
    dims = len(target_vector)
    rng = np.random.default_rng(seed)
    candidates = [name for name in matrix.keys() if name != target]
    base_distances = calculate_distances(matrix, target=target)
    base_ranking = sorted(base_distances.items(), key=lambda pair: pair[1])
    point_ranking_names = [name for name, _ in base_ranking]
    point_top2_set = set(point_ranking_names[:2])
    point_top3_set = set(point_ranking_names[:3])
    thresholds = _merge_status_thresholds(status_thresholds)

    distance_samples: dict[str, list[float]] = {name: [] for name in candidates}
    nearest_counter: Counter[str] = Counter()
    top3_counter: Counter[str] = Counter()
    rank_position_counts: dict[str, Counter[int]] = {name: Counter() for name in candidates}
    top2_gap_samples: list[float] = []
    top2_set_match_count = 0
    top2_order_match_count = 0
    top3_set_match_count = 0
    full_ranking_match_count = 0

    for _ in range(iterations):
        sampled_dims = rng.integers(low=0, high=dims, size=dims, endpoint=False)
        weights = rng.uniform(0.85, 1.15, size=dims)
        sampled_distances = calculate_distances(
            matrix,
            target=target,
            dimensions=sampled_dims,
            weights=weights,
        )

        ranking = sorted(sampled_distances.items(), key=lambda pair: pair[1])
        ranking_names = [name for name, _ in ranking]
        nearest_counter[ranking[0][0]] += 1
        for name, _ in ranking[:3]:
            top3_counter[name] += 1
        for rank_index, (name, _dist) in enumerate(ranking, start=1):
            rank_position_counts[name][rank_index] += 1

        if set(ranking_names[:2]) == point_top2_set:
            top2_set_match_count += 1
        if ranking_names[:2] == point_ranking_names[:2]:
            top2_order_match_count += 1
        if set(ranking_names[:3]) == point_top3_set:
            top3_set_match_count += 1
        if ranking_names == point_ranking_names:
            full_ranking_match_count += 1

        if len(ranking) > 1:
            top2_gap_samples.append(float(ranking[1][1] - ranking[0][1]))

        for artifact_name, dist in sampled_distances.items():
            distance_samples[artifact_name].append(float(dist))

    # Leave-one-dimension-out jackknife stability.
    jackknife_nearest_counter: Counter[str] = Counter()
    for dim in range(dims):
        keep_dims = np.array([d for d in range(dims) if d != dim], dtype=int)
        jackknife_distances = calculate_distances(
            matrix,
            target=target,
            dimensions=keep_dims,
        )
        jackknife_rank = sorted(jackknife_distances.items(), key=lambda pair: pair[1])
        jackknife_nearest_counter[jackknife_rank[0][0]] += 1

    base_nearest = base_ranking[0][0]
    nearest_neighbor_stability = nearest_counter.get(base_nearest, 0) / iterations
    jackknife_stability = jackknife_nearest_counter.get(base_nearest, 0) / max(dims, 1)
    top2_set_stability = top2_set_match_count / iterations
    top2_order_match_rate = top2_order_match_count / iterations
    top3_set_stability = top3_set_match_count / iterations
    full_ranking_match_rate = full_ranking_match_count / iterations
    rank_stability = top3_set_stability

    nearest_probability_by_artifact = {
        name: float(nearest_counter.get(name, 0) / iterations) for name in candidates
    }
    nearest_probability_ranked = sorted(
        nearest_probability_by_artifact.items(),
        key=lambda pair: pair[1],
        reverse=True,
    )
    base_nearest_probability = float(nearest_probability_by_artifact.get(base_nearest, 0.0))
    if len(nearest_probability_ranked) > 1:
        second_name, second_probability = nearest_probability_ranked[1]
    else:
        second_name, second_probability = "", 0.0
    probability_margin = float(base_nearest_probability - second_probability)

    summary: dict[str, Any] = {}
    for artifact_name in candidates:
        samples = np.array(distance_samples[artifact_name], dtype=float)
        stats = _to_ci95(samples)
        stats["point_estimate"] = float(base_distances[artifact_name])
        stats["nearest_probability"] = float(nearest_counter.get(artifact_name, 0) / iterations)
        stats["top3_probability"] = float(top3_counter.get(artifact_name, 0) / iterations)
        rank_counts = rank_position_counts[artifact_name]
        rank_probabilities = {
            str(rank): float(count / iterations)
            for rank, count in sorted(rank_counts.items())
        }
        stats["rank_probability"] = rank_probabilities
        stats["expected_rank"] = float(
            sum(rank * count for rank, count in rank_counts.items()) / iterations
        )
        probs = np.array(list(rank_probabilities.values()), dtype=float)
        if probs.size > 0:
            stats["rank_entropy"] = float(-np.sum(probs * np.log2(probs + 1e-12)))
        else:
            stats["rank_entropy"] = 0.0
        summary[artifact_name] = stats

    top2_gap = _to_ci95(np.array(top2_gap_samples, dtype=float)) if top2_gap_samples else {
        "mean": 0.0,
        "std": 0.0,
        "ci95_lower": 0.0,
        "ci95_upper": 0.0,
    }
    top2_gap_fragile = bool(
        top2_gap["ci95_lower"]
        < thresholds["min_top2_gap_ci_lower_for_confirmed"]
    )
    top2_identity_flip_rate = float(1.0 - top2_set_stability)
    top2_order_flip_rate = float(1.0 - top2_order_match_rate)
    nearest_rank_entropy = float(summary.get(base_nearest, {}).get("rank_entropy", 0.0))
    runner_up_rank_entropy = float(summary.get(second_name, {}).get("rank_entropy", 0.0))
    top2_competition_ratio = float(
        second_probability / base_nearest_probability if base_nearest_probability > 0 else 0.0
    )

    status_inputs = {
        "nearest_neighbor_stability": float(nearest_neighbor_stability),
        "jackknife_nearest_neighbor_stability": float(jackknife_stability),
        "rank_stability": float(rank_stability),
        "nearest_neighbor_probability_margin": float(probability_margin),
        "top2_gap_ci95_lower": float(top2_gap["ci95_lower"]),
    }
    missing_required_fields = [
        key
        for key, value in status_inputs.items()
        if value is None or (isinstance(value, float) and np.isnan(value))
    ]
    required_fields_present = len(missing_required_fields) == 0

    if (
        nearest_neighbor_stability >= thresholds["min_nearest_neighbor_stability_for_confirmed"]
        and jackknife_stability >= thresholds["min_jackknife_stability_for_confirmed"]
        and rank_stability >= thresholds["min_rank_stability_for_confirmed"]
        and probability_margin >= thresholds["min_probability_margin_for_confirmed"]
        and not top2_gap_fragile
    ):
        status = "STABILITY_CONFIRMED"
        reason_code = "ROBUST_NEAREST_NEIGHBOR"
        allowed_claim = (
            "Comparative proximity is uncertainty-qualified and robust under tested perturbations."
        )
    elif (
        nearest_neighbor_stability >= thresholds["min_nearest_neighbor_stability_for_qualified"]
        and jackknife_stability >= thresholds["min_jackknife_stability_for_qualified"]
        and rank_stability >= thresholds["min_rank_stability_for_qualified"]
    ):
        status = "DISTANCE_QUALIFIED"
        reason_code = (
            "TOP2_GAP_FRAGILE"
            if probability_margin < thresholds["min_probability_margin_for_qualified"]
            else "MODERATE_RANK_VOLATILITY"
        )
        allowed_claim = "Comparative proximity is directional with explicit uncertainty caveats."
    else:
        status = "INCONCLUSIVE_UNCERTAINTY"
        if not required_fields_present:
            reason_code = "FIELD_INCOMPLETE"
        elif (
            top2_gap_fragile
            and top2_set_stability
            < thresholds["min_top2_set_stability_for_identity_flip_dominant"]
        ):
            reason_code = "TOP2_IDENTITY_FLIP_DOMINANT"
        elif (
            top2_gap_fragile
            and probability_margin < thresholds["min_probability_margin_for_qualified"]
        ):
            reason_code = "MARGIN_VOLATILITY_DOMINANT"
        elif (
            top2_gap_fragile
            and max(nearest_rank_entropy, runner_up_rank_entropy)
            >= thresholds["min_rank_entropy_for_high"]
        ):
            reason_code = "RANK_ENTROPY_HIGH"
        elif top2_gap_fragile:
            reason_code = "TOP2_GAP_FRAGILE"
        elif rank_stability < thresholds["min_rank_stability_for_qualified"]:
            reason_code = "RANK_UNSTABLE_UNDER_PERTURBATION"
        else:
            reason_code = "CONFIDENCE_BELOW_POLICY"
        allowed_claim = {
            "TOP2_IDENTITY_FLIP_DOMINANT": (
                "Comparative claim remains provisional; nearest-neighbor identity is unstable "
                "across perturbation lanes."
            ),
            "MARGIN_VOLATILITY_DOMINANT": (
                "Comparative claim remains provisional; nearest-neighbor margin volatility "
                "prevents stable phase8_comparative ranking."
            ),
            "RANK_ENTROPY_HIGH": (
                "Comparative claim remains provisional; rank entropy remains high under "
                "perturbation and prevents robust ordering claims."
            ),
            "TOP2_GAP_FRAGILE": (
                "Comparative claim remains provisional pending uncertainty-complete evidence."
            ),
            "RANK_UNSTABLE_UNDER_PERTURBATION": (
                "Comparative claim remains provisional; rank stability is below policy floor."
            ),
            "CONFIDENCE_BELOW_POLICY": (
                "Comparative claim remains provisional; confidence remains below policy thresholds."
            ),
            "FIELD_INCOMPLETE": (
                "Comparative claim remains provisional due incomplete uncertainty evidence fields."
            ),
        }.get(reason_code, "Comparative claim remains provisional pending uncertainty-complete evidence.")

    m2_residual_reason = _resolve_m2_residual_reason(
        status=status,
        reason_code=reason_code,
        required_fields_present=required_fields_present,
    )
    m2_4_closure_lane = _derive_m2_4_closure_lane(
        status=status,
        required_fields_present=required_fields_present,
    )
    m2_4_reopen_triggers = _lane_reopen_triggers(
        m2_4_closure_lane, m2_generation="M2_4"
    )
    m2_4_residual_reason = (
        "none" if m2_4_closure_lane == "M2_4_ALIGNED" else m2_residual_reason
    )

    m2_5_closure_lane = _derive_m2_5_closure_lane(
        status=status,
        required_fields_present=required_fields_present,
    )
    if m2_5_closure_lane == "M2_5_ALIGNED":
        m2_5_residual_reason = "none"
    elif m2_5_closure_lane == "M2_5_INCONCLUSIVE":
        m2_5_residual_reason = "insufficient_evidence_for_m2_5_lane_classification"
    else:
        m2_5_residual_reason = m2_residual_reason
    m2_5_reopen_triggers = _lane_reopen_triggers(
        m2_5_closure_lane, m2_generation="M2_5"
    )
    m2_5_data_availability_linkage = {
        "missing_folio_blocking_claimed": False,
        "objective_comparative_validity_failure": False,
        "blocking_evidence": "",
        "classification": "NON_BLOCKING_EXTERNAL_CONSTRAINT",
    }

    fragility_diagnostics = {
        "top2_set_stability": float(top2_set_stability),
        "top2_identity_flip_rate": float(top2_identity_flip_rate),
        "top2_order_match_rate": float(top2_order_match_rate),
        "top2_order_flip_rate": float(top2_order_flip_rate),
        "nearest_rank_entropy": float(nearest_rank_entropy),
        "runner_up_rank_entropy": float(runner_up_rank_entropy),
        "margin_volatility_std": float(top2_gap.get("std", 0.0)),
        "top2_competition_ratio": float(top2_competition_ratio),
        "identity_flip_dominant": bool(
            top2_set_stability
            < thresholds["min_top2_set_stability_for_identity_flip_dominant"]
        ),
        "margin_volatility_dominant": bool(
            probability_margin < thresholds["min_probability_margin_for_qualified"]
        ),
        "rank_entropy_high": bool(
            max(nearest_rank_entropy, runner_up_rank_entropy)
            >= thresholds["min_rank_entropy_for_high"]
        ),
        "dominant_fragility_signal": reason_code if status == "INCONCLUSIVE_UNCERTAINTY" else "",
    }

    metric_validity = {
        "required_fields_present": required_fields_present,
        "missing_required_fields": missing_required_fields,
        "sufficient_iterations": bool(iterations >= 100),
        "status_inputs": status_inputs,
    }

    return {
        "target_artifact": target,
        "parameters": {
            "seed": seed,
            "iterations": iterations,
            "run_profile": str(run_profile),
            "dimension_count": dims,
            "bootstrap_dimensions": True,
            "weight_jitter_range": [0.85, 1.15],
            "jackknife_dimensions": True,
            "status_thresholds": thresholds,
        },
        "status": status,
        "reason_code": reason_code,
        "allowed_claim": allowed_claim,
        "nearest_neighbor": base_nearest,
        "nearest_neighbor_distance": float(base_ranking[0][1]),
        "nearest_neighbor_stability": float(nearest_neighbor_stability),
        "jackknife_nearest_neighbor_stability": float(jackknife_stability),
        "rank_stability": float(rank_stability),
        "rank_stability_components": {
            "top2_set_stability": float(top2_set_stability),
            "top3_set_stability": float(top3_set_stability),
            "full_ranking_match_rate": float(full_ranking_match_rate),
        },
        "nearest_neighbor_alternative": str(second_name),
        "nearest_neighbor_alternative_probability": float(second_probability),
        "nearest_neighbor_probability_margin": float(probability_margin),
        "distance_summary": summary,
        "ranking_point_estimate": [name for name, _ in base_ranking],
        "top2_gap": top2_gap,
        "top2_gap_fragile": top2_gap_fragile,
        "fragility_diagnostics": fragility_diagnostics,
        "m2_4_closure_lane": m2_4_closure_lane,
        "m2_4_residual_reason": m2_4_residual_reason,
        "m2_4_reopen_triggers": m2_4_reopen_triggers,
        "m2_5_closure_lane": m2_5_closure_lane,
        "m2_5_residual_reason": m2_5_residual_reason,
        "m2_5_reopen_triggers": m2_5_reopen_triggers,
        "m2_5_data_availability_linkage": m2_5_data_availability_linkage,
        "metric_validity": metric_validity,
    }


def write_proximity_report(
    distances: Mapping[str, float],
    uncertainty: Mapping[str, Any],
    *,
    report_path: Path | str,
) -> None:
    """Write a Markdown proximity report summarizing comparative distances.

    Renders a table of point-estimate distances with 95% confidence intervals,
    nearest-neighbor stability metrics, fragility diagnostics, and M2.4/M2.5
    closure-lane assignments. The report is written to report_path.
    """
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sorted_dist = sorted(distances.items(), key=lambda x: x[1])

    status = str(uncertainty.get("status", "INCONCLUSIVE_UNCERTAINTY"))
    reason_code = str(uncertainty.get("reason_code", "UNKNOWN"))
    nearest_neighbor = str(uncertainty.get("nearest_neighbor", "unknown"))
    nearest_stability = float(uncertainty.get("nearest_neighbor_stability", 0.0))
    jackknife_stability = float(uncertainty.get("jackknife_nearest_neighbor_stability", 0.0))
    rank_stability = float(uncertainty.get("rank_stability", 0.0))
    nearest_margin = float(uncertainty.get("nearest_neighbor_probability_margin", 0.0))
    top2_gap = uncertainty.get("top2_gap", {})
    top2_gap_ci_low = float(top2_gap.get("ci95_lower", 0.0))
    distance_summary = dict(uncertainty.get("distance_summary", {}))
    allowed_claim = str(uncertainty.get("allowed_claim", ""))
    m2_4_lane = str(uncertainty.get("m2_4_closure_lane", "M2_4_INCONCLUSIVE"))
    m2_5_lane = str(uncertainty.get("m2_5_closure_lane", "M2_5_INCONCLUSIVE"))
    m2_5_residual_reason = str(uncertainty.get("m2_5_residual_reason", ""))
    data_linkage = dict(uncertainty.get("m2_5_data_availability_linkage", {}))
    missing_folio_blocking_claimed = bool(
        data_linkage.get("missing_folio_blocking_claimed", False)
    )
    objective_validity_failure = bool(
        data_linkage.get("objective_comparative_validity_failure", False)
    )
    fragility = dict(uncertainty.get("fragility_diagnostics", {}))
    top2_identity_flip_rate = float(fragility.get("top2_identity_flip_rate", 0.0))
    top2_order_flip_rate = float(fragility.get("top2_order_flip_rate", 0.0))
    nearest_rank_entropy = float(fragility.get("nearest_rank_entropy", 0.0))
    runner_up_rank_entropy = float(fragility.get("runner_up_rank_entropy", 0.0))
    dominant_fragility_signal = str(fragility.get("dominant_fragility_signal", ""))

    with open(path, "w", encoding="utf-8") as handle:
        handle.write("# PROXIMITY_ANALYSIS.md\n")
        handle.write("## Phase B: Comparative and Contextual Classification\n\n")
        handle.write(
            "### Euclidean Distances from Voynich Manuscript (Uncertainty-Qualified)\n\n"
        )
        handle.write("| Artifact | Distance (Point) | 95% CI | Proximity | Nearest P |\n")
        handle.write("| :--- | :---: | :---: | :--- | :---: |\n")

        for name, dist in sorted_dist:
            prox = "Close" if dist < 5 else "Moderate" if dist < 8 else "Distant"
            stats = distance_summary.get(name, {})
            ci_low = float(stats.get("ci95_lower", dist))
            ci_high = float(stats.get("ci95_upper", dist))
            nearest_p = float(stats.get("nearest_probability", 0.0))
            handle.write(
                f"| {name} | {dist:.4f} | [{ci_low:.4f}, {ci_high:.4f}] | {prox} | {nearest_p:.3f} |\n"
            )

        handle.write("\n### Clustering Insights\n\n")
        handle.write(f"- **Nearest Neighbor (Point Estimate):** {nearest_neighbor}\n")
        handle.write(
            f"- **Nearest-Neighbor Stability:** {nearest_stability:.3f} (bootstrap perturbation)\n"
        )
        handle.write(
            f"- **Jackknife Stability:** {jackknife_stability:.3f} (leave-one-dimension-out)\n"
        )
        handle.write(f"- **Rank Stability:** {rank_stability:.3f} (top-3 set stability)\n")
        handle.write(f"- **Nearest-Neighbor Margin (P1-P2):** {nearest_margin:.3f}\n")
        handle.write(f"- **Top-2 Gap Robustness (CI Lower):** {top2_gap_ci_low:.4f}\n")
        handle.write(f"- **M2.5 Closure Lane:** `{m2_5_lane}`\n")
        handle.write(f"- **M2.5 Residual Reason:** `{m2_5_residual_reason}`\n")
        handle.write(f"- **M2.4 Closure Lane (Compatibility):** `{m2_4_lane}`\n")
        handle.write(f"- **Top-2 Identity Flip Rate:** {top2_identity_flip_rate:.3f}\n")
        handle.write(f"- **Top-2 Order Flip Rate:** {top2_order_flip_rate:.3f}\n")
        handle.write(f"- **Nearest Rank Entropy:** {nearest_rank_entropy:.3f}\n")
        handle.write(f"- **Runner-up Rank Entropy:** {runner_up_rank_entropy:.3f}\n")
        handle.write(f"- **Dominant Fragility Signal:** `{dominant_fragility_signal}`\n")
        handle.write(f"- **Comparative Uncertainty Status:** `{status}`\n")
        handle.write(f"- **Reason Code:** `{reason_code}`\n")
        handle.write(f"- **Allowed Claim:** {allowed_claim}\n")
        handle.write(
            "- **Missing-Folio Blocking Claimed:** "
            f"`{missing_folio_blocking_claimed}`\n"
        )
        handle.write(
            "- **Objective Comparative Validity Failure:** "
            f"`{objective_validity_failure}`\n"
        )
        handle.write(
            "- **Uncertainty Artifact:** `results/data/phase7_human/phase_7c_uncertainty.json`\n"
        )


def run_analysis(
    *,
    matrix_path: Path | str | None = None,
    report_path: Path | str | None = None,
    uncertainty_output_path: Path | str | None = None,
    seed: int = DEFAULT_RANDOM_SEED,
    iterations: int = DEFAULT_ITERATIONS,
    run_profile: str = "custom",
    target: str = DEFAULT_TARGET,
    status_thresholds: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the full comparative mapping pipeline end-to-end.

    Loads the feature matrix, computes distances and uncertainty, writes the
    Markdown proximity report and JSON uncertainty artifact, and returns a
    summary dict with status, closure lanes, and key stability metrics.
    """
    csv_path = _resolve_existing_path(
        matrix_path or Path("results/reports/phase8_comparative/COMPARATIVE_MATRIX.csv"),
        "results/reports/phase8_comparative/COMPARATIVE_MATRIX.csv",
    )
    output_report = Path(report_path or "results/reports/phase8_comparative/PROXIMITY_ANALYSIS.md")
    output_uncertainty = Path(uncertainty_output_path or "results/data/phase7_human/phase_7c_uncertainty.json")

    matrix = load_matrix(csv_path)
    distances = calculate_distances(matrix, target=target)
    uncertainty = compute_distance_uncertainty(
        matrix,
        target=target,
        seed=seed,
        iterations=iterations,
        run_profile=run_profile,
        status_thresholds=status_thresholds,
    )

    write_proximity_report(distances, uncertainty, report_path=output_report)
    ProvenanceWriter.save_results(uncertainty, output_uncertainty)

    return {
        "matrix_path": str(csv_path),
        "report_path": str(output_report),
        "uncertainty_output_path": str(output_uncertainty),
        "status": str(uncertainty.get("status")),
        "reason_code": str(uncertainty.get("reason_code")),
        "m2_4_closure_lane": str(uncertainty.get("m2_4_closure_lane", "")),
        "m2_5_closure_lane": str(uncertainty.get("m2_5_closure_lane", "")),
        "nearest_neighbor": str(uncertainty.get("nearest_neighbor")),
        "nearest_neighbor_stability": float(
            uncertainty.get("nearest_neighbor_stability", 0.0)
        ),
        "rank_stability": float(uncertainty.get("rank_stability", 0.0)),
    }


if __name__ == "__main__":
    run_analysis()
