from __future__ import annotations

import csv
import logging
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

import numpy as np

from foundation.core.provenance import ProvenanceWriter

logger = logging.getLogger(__name__)

DEFAULT_RANDOM_SEED = 42
DEFAULT_ITERATIONS = 2000
DEFAULT_TARGET = "Voynich"
DEFAULT_STATUS_THRESHOLDS: Dict[str, float] = {
    "min_nearest_neighbor_stability_for_confirmed": 0.75,
    "min_jackknife_stability_for_confirmed": 0.75,
    "min_rank_stability_for_confirmed": 0.65,
    "min_probability_margin_for_confirmed": 0.10,
    "min_top2_gap_ci_lower_for_confirmed": 0.05,
    "min_nearest_neighbor_stability_for_qualified": 0.50,
    "min_jackknife_stability_for_qualified": 0.70,
    "min_rank_stability_for_qualified": 0.55,
    "min_probability_margin_for_qualified": 0.03,
}


def load_matrix(csv_path: Path | str) -> Dict[str, np.ndarray]:
    matrix: Dict[str, np.ndarray] = {}
    with open(csv_path, "r", encoding="utf-8") as handle:
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
) -> Dict[str, float]:
    target_vector = matrix[target]
    distances: Dict[str, float] = {}
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


def _to_ci95(values: np.ndarray) -> Dict[str, float]:
    lower, upper = np.percentile(values, [2.5, 97.5])
    return {
        "mean": float(np.mean(values)),
        "std": float(np.std(values)),
        "ci95_lower": float(lower),
        "ci95_upper": float(upper),
    }


def _merge_status_thresholds(
    overrides: Mapping[str, Any] | None,
) -> Dict[str, float]:
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


def compute_distance_uncertainty(
    matrix: Mapping[str, np.ndarray],
    *,
    target: str = DEFAULT_TARGET,
    seed: int = DEFAULT_RANDOM_SEED,
    iterations: int = DEFAULT_ITERATIONS,
    status_thresholds: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
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

    distance_samples: Dict[str, list[float]] = {name: [] for name in candidates}
    nearest_counter: Counter[str] = Counter()
    top3_counter: Counter[str] = Counter()
    rank_position_counts: Dict[str, Counter[int]] = {name: Counter() for name in candidates}
    top2_gap_samples: list[float] = []
    top2_set_match_count = 0
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

    summary: Dict[str, Any] = {}
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
        if top2_gap_fragile:
            reason_code = "TOP2_GAP_FRAGILE"
        elif rank_stability < thresholds["min_rank_stability_for_qualified"]:
            reason_code = "RANK_UNSTABLE_UNDER_PERTURBATION"
        else:
            reason_code = "CONFIDENCE_BELOW_POLICY"
        allowed_claim = (
            "Comparative claim remains provisional pending uncertainty-complete evidence."
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
    metric_validity = {
        "required_fields_present": len(missing_required_fields) == 0,
        "missing_required_fields": missing_required_fields,
        "sufficient_iterations": bool(iterations >= 100),
        "status_inputs": status_inputs,
    }

    return {
        "target_artifact": target,
        "parameters": {
            "seed": seed,
            "iterations": iterations,
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
        "metric_validity": metric_validity,
    }


def write_proximity_report(
    distances: Mapping[str, float],
    uncertainty: Mapping[str, Any],
    *,
    report_path: Path | str,
) -> None:
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
        handle.write(f"- **Comparative Uncertainty Status:** `{status}`\n")
        handle.write(f"- **Reason Code:** `{reason_code}`\n")
        handle.write(f"- **Allowed Claim:** {allowed_claim}\n")
        handle.write(
            "- **Uncertainty Artifact:** `results/human/phase_7c_uncertainty.json`\n"
        )


def run_analysis(
    *,
    matrix_path: Path | str | None = None,
    report_path: Path | str | None = None,
    uncertainty_output_path: Path | str | None = None,
    seed: int = DEFAULT_RANDOM_SEED,
    iterations: int = DEFAULT_ITERATIONS,
    target: str = DEFAULT_TARGET,
    status_thresholds: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    csv_path = _resolve_existing_path(
        matrix_path or Path("reports/comparative/COMPARATIVE_MATRIX.csv"),
        "reports/comparative/COMPARATIVE_MATRIX.csv",
    )
    output_report = Path(report_path or "reports/comparative/PROXIMITY_ANALYSIS.md")
    output_uncertainty = Path(uncertainty_output_path or "results/human/phase_7c_uncertainty.json")

    matrix = load_matrix(csv_path)
    distances = calculate_distances(matrix, target=target)
    uncertainty = compute_distance_uncertainty(
        matrix,
        target=target,
        seed=seed,
        iterations=iterations,
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
        "nearest_neighbor": str(uncertainty.get("nearest_neighbor")),
        "nearest_neighbor_stability": float(
            uncertainty.get("nearest_neighbor_stability", 0.0)
        ),
        "rank_stability": float(uncertainty.get("rank_stability", 0.0)),
    }


if __name__ == "__main__":
    run_analysis()
