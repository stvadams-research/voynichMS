"""
Indistinguishability Testing Framework

Evaluates whether synthetic pages are distinguishable from real pharmaceutical pages.
"""

import logging
import math
import os
import random
from dataclasses import dataclass
from typing import Any

from phase1_foundation.config import SCRAMBLED_CONTROL_PARAMS, get_analysis_thresholds
from phase3_synthesis.interface import (
    IndistinguishabilityResult,
    SectionProfile,
    SyntheticPage,
)

logger = logging.getLogger(__name__)

DEFAULT_MATCHING_METRICS = [
    "repetition_rate",
    "information_density",
    "locality_radius",
]
DEFAULT_HOLDOUT_EVALUATION_METRICS = [
    "mean_word_length",
    "positional_entropy",
]


@dataclass
class MetricVector:
    """Vector of structural metrics for a page."""
    page_id: str
    is_synthetic: bool
    is_scrambled: bool = False

    # Metrics
    jar_count: int = 0
    word_count: int = 0
    mean_word_length: float = 0.0
    repetition_rate: float = 0.0
    positional_entropy: float = 0.0
    locality_radius: float = 0.0
    information_density: float = 0.0
    layout_density: float = 0.0

    def as_vector(self) -> list[float]:
        """Return metrics as a numeric vector."""
        return [
            float(self.jar_count),
            float(self.word_count),
            self.mean_word_length,
            self.repetition_rate,
            self.positional_entropy,
            self.locality_radius,
            self.information_density,
            self.layout_density,
        ]


def euclidean_distance(v1: list[float], v2: list[float]) -> float:
    """Compute Euclidean distance between two vectors."""
    if len(v1) != len(v2):
        return float('inf')

    return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))


def normalize_vector(v: list[float], mins: list[float], maxs: list[float]) -> list[float]:
    """Normalize vector to 0-1 range."""
    normalized = []
    for i, val in enumerate(v):
        range_val = maxs[i] - mins[i]
        if range_val > 0:
            normalized.append((val - mins[i]) / range_val)
        else:
            normalized.append(0.5)
    return normalized


class IndistinguishabilityTester:
    """
    Tests whether synthetic pages are distinguishable from real pages.

    Success criteria:
    - Strong separation from scrambled controls (configurable threshold)
    - Weak separation from real pages (configurable threshold)
    """

    def __init__(self, section_profile: SectionProfile):
        self.section_profile = section_profile
        self.real_vectors: list[MetricVector] = []
        self.synthetic_vectors: list[MetricVector] = []
        self.scrambled_vectors: list[MetricVector] = []
        self.matching_metrics: list[str] = list(DEFAULT_MATCHING_METRICS)
        self.holdout_evaluation_metrics: list[str] = list(DEFAULT_HOLDOUT_EVALUATION_METRICS)
        thresholds = get_analysis_thresholds().get("indistinguishability", {})
        self.success_threshold = float(thresholds.get("separation_success", 0.7))
        self.failure_threshold = float(thresholds.get("separation_failure", 0.3))
        self.require_computed = os.environ.get("REQUIRE_COMPUTED", "0") == "1"

    def set_metric_partitions(
        self, *, matching_metrics: list[str], holdout_evaluation_metrics: list[str]
    ) -> None:
        """Set metric partitions used for anti-leakage reporting."""
        self.matching_metrics = list(matching_metrics)
        self.holdout_evaluation_metrics = list(holdout_evaluation_metrics)

    def metric_overlap(self) -> list[str]:
        """Return metric overlap between matching and holdout sets."""
        return sorted(set(self.matching_metrics) & set(self.holdout_evaluation_metrics))

    def _compute_positional_entropy(self, text_blocks: list[list[str]]) -> float:
        """
        Compute positional entropy from generated token character positions.
        """
        from collections import Counter

        counts = {"start": Counter(), "mid": Counter(), "end": Counter()}
        tokens = [token for block in text_blocks for token in block]
        if not tokens:
            return 0.0

        for token in tokens:
            if not token:
                continue
            counts["start"][token[0]] += 1
            counts["end"][token[-1]] += 1
            for char in token[1:-1]:
                counts["mid"][char] += 1

        entropies = []
        for counter in counts.values():
            if not counter:
                continue
            total = sum(counter.values())
            entropy = 0.0
            for count in counter.values():
                p = count / total
                if p > 0:
                    entropy -= p * math.log2(p)
            max_entropy = math.log2(len(counter)) if len(counter) > 1 else 1.0
            entropies.append(entropy / max_entropy if max_entropy > 0 else 0.0)
        return sum(entropies) / len(entropies) if entropies else 0.0

    def load_real_pages(self):
        """Load metric vectors for real pharmaceutical pages."""
        for page in self.section_profile.pages:
            vector = MetricVector(
                page_id=page.page_id,
                is_synthetic=False,
                is_scrambled=False,
                jar_count=page.jar_count,
                word_count=page.total_words,
                mean_word_length=page.mean_word_length,
                repetition_rate=page.token_repetition_rate,
                positional_entropy=page.positional_entropy,
                locality_radius=page.locality_radius,
                information_density=page.information_density,
                layout_density=page.layout_density,
            )
            self.real_vectors.append(vector)

    def load_synthetic_pages(self, pages: list[SyntheticPage]):
        """Load metric vectors for synthetic pages."""
        for page in pages:
            metrics = page.metrics

            positional_entropy = metrics.get("positional_entropy")
            if positional_entropy is None:
                positional_entropy = self._compute_positional_entropy(page.text_blocks)
                logger.warning(
                    "Synthetic page %s missing positional entropy metric; computed from generated tokens.",
                    page.page_id,
                )

            locality_radius = metrics.get("locality")
            if locality_radius is None:
                if self.require_computed:
                    raise NotImplementedError(
                        f"Missing computed locality for synthetic page {page.page_id} while REQUIRE_COMPUTED=1"
                    )
                logger.warning("Synthetic page %s missing locality; using 0.0 fallback.", page.page_id)
                locality_radius = 0.0

            information_density = metrics.get("info_density")
            if information_density is None:
                if self.require_computed:
                    raise NotImplementedError(
                        f"Missing computed information density for synthetic page {page.page_id} while REQUIRE_COMPUTED=1"
                    )
                logger.warning("Synthetic page %s missing info_density; using 0.0 fallback.", page.page_id)
                information_density = 0.0

            vector = MetricVector(
                page_id=page.page_id,
                is_synthetic=True,
                is_scrambled=False,
                jar_count=page.jar_count,
                word_count=metrics.get("word_count", 0),
                mean_word_length=metrics.get("mean_word_length", 0),
                repetition_rate=metrics.get("repetition_rate", 0),
                positional_entropy=positional_entropy,
                locality_radius=locality_radius,
                information_density=information_density,
                layout_density=metrics.get("word_count", 0) / max(1, page.jar_count),
            )
            self.synthetic_vectors.append(vector)

    def generate_scrambled_controls(self, count: int = 10, seed: int | None = None):
        """Generate scrambled control pages for comparison."""
        from phase1_foundation.core.randomness import get_randomness_controller
        controller = get_randomness_controller()

        for i in range(count):
            page_seed = seed + i if seed is not None else i
            controller.register_seed(f"scrambled_{i}", page_seed, "indistinguishability_control")
            rng = random.Random(page_seed)

            # Scrambled pages have degraded metrics
            p = SCRAMBLED_CONTROL_PARAMS
            vector = MetricVector(
                page_id=f"scrambled_{i:03d}",
                is_synthetic=False,
                is_scrambled=True,
                jar_count=rng.randint(*p["jar_count_range"]),
                word_count=rng.randint(*p["word_count_range"]),
                mean_word_length=p["mean_word_length"]["baseline"] + rng.uniform(-p["mean_word_length"]["spread"], p["mean_word_length"]["spread"]),
                repetition_rate=p["repetition_rate"]["baseline"] + rng.uniform(p["repetition_rate"]["offset_min"], p["repetition_rate"]["offset_max"]),
                positional_entropy=p["positional_entropy"]["baseline"] + rng.uniform(p["positional_entropy"]["offset_min"], p["positional_entropy"]["offset_max"]),
                locality_radius=p["locality_radius"]["baseline"] + rng.uniform(p["locality_radius"]["offset_min"], p["locality_radius"]["offset_max"]),
                information_density=p["information_density"]["baseline"] + rng.uniform(p["information_density"]["offset_min"], p["information_density"]["offset_max"]),
                layout_density=rng.uniform(*p["layout_density_range"]),
            )
            self.scrambled_vectors.append(vector)

    def compute_centroid(self, vectors: list[MetricVector]) -> list[float]:
        """Compute centroid of a set of metric vectors."""
        if not vectors:
            return [0.0] * 8

        n = len(vectors)
        centroid = [0.0] * 8

        for v in vectors:
            vec = v.as_vector()
            for i, val in enumerate(vec):
                centroid[i] += val / n

        return centroid

    def compute_separation(self, group1: list[MetricVector],
                           group2: list[MetricVector]) -> float:
        """
        Compute separation between two groups of vectors.

        Returns value in [0, 1] where:
        - 0 = completely overlapping
        - 1 = completely separated
        """
        if not group1 or not group2:
            return 0.0

        # Get all vectors for normalization
        all_vectors = [v.as_vector() for v in group1 + group2]

        # Compute mins/maxs for normalization
        mins = [min(v[i] for v in all_vectors) for i in range(8)]
        maxs = [max(v[i] for v in all_vectors) for i in range(8)]

        # Compute normalized centroids
        c1 = normalize_vector(self.compute_centroid(group1), mins, maxs)
        c2 = normalize_vector(self.compute_centroid(group2), mins, maxs)

        # Compute inter-centroid distance
        inter_dist = euclidean_distance(c1, c2)

        # Compute intra-group spread
        spread1 = self._compute_spread(group1, c1, mins, maxs)
        spread2 = self._compute_spread(group2, c2, mins, maxs)
        avg_spread = (spread1 + spread2) / 2

        # Separation = inter-distance / (inter-distance + avg_spread)
        if inter_dist + avg_spread == 0:
            return 0.0

        separation = inter_dist / (inter_dist + avg_spread)

        return min(1.0, max(0.0, separation))

    def _compute_spread(self, vectors: list[MetricVector],
                        centroid: list[float],
                        mins: list[float], maxs: list[float]) -> float:
        """Compute average distance from centroid."""
        if not vectors:
            return 0.0

        total_dist = 0.0
        for v in vectors:
            normalized = normalize_vector(v.as_vector(), mins, maxs)
            total_dist += euclidean_distance(normalized, centroid)

        return total_dist / len(vectors) if len(vectors) > 0 else 0.0

    def run_test(self, gap_id: str) -> IndistinguishabilityResult:
        """Run indistinguishability test."""
        result = IndistinguishabilityResult(
            gap_id=gap_id,
            real_pages_count=len(self.real_vectors),
            synthetic_pages_count=len(self.synthetic_vectors),
            scrambled_count=len(self.scrambled_vectors),
        )
        result.separation_success_threshold = self.success_threshold
        result.separation_failure_threshold = self.failure_threshold

        # Compute separations
        result.real_vs_scrambled_separation = self.compute_separation(
            self.real_vectors, self.scrambled_vectors
        )

        result.synthetic_vs_scrambled_separation = self.compute_separation(
            self.synthetic_vectors, self.scrambled_vectors
        )

        result.real_vs_synthetic_separation = self.compute_separation(
            self.real_vectors, self.synthetic_vectors
        )

        # Store detailed metric comparisons
        result.metric_comparisons = self._compute_metric_comparisons()

        # Evaluate success
        result.evaluate_success()

        return result

    def _compute_metric_comparisons(self) -> dict[str, dict[str, float]]:
        """Compute per-metric comparisons."""
        metrics = [
            "jar_count", "word_count", "mean_word_length", "repetition_rate",
            "positional_entropy", "locality_radius", "information_density", "layout_density"
        ]

        comparisons = {}
        for i, metric in enumerate(metrics):
            real_vals = [v.as_vector()[i] for v in self.real_vectors]
            synth_vals = [v.as_vector()[i] for v in self.synthetic_vectors]
            scrambled_vals = [v.as_vector()[i] for v in self.scrambled_vectors]

            comparisons[metric] = {
                "real_mean": sum(real_vals) / max(1, len(real_vals)),
                "synthetic_mean": sum(synth_vals) / max(1, len(synth_vals)),
                "scrambled_mean": sum(scrambled_vals) / max(1, len(scrambled_vals)),
            }

        return comparisons


class FullIndistinguishabilityTest:
    """
    Runs full indistinguishability test across all gaps.
    """

    def __init__(self, section_profile: SectionProfile):
        self.section_profile = section_profile
        self.results: dict[str, IndistinguishabilityResult] = {}

    def run(self, gap_pages: dict[str, list[SyntheticPage]], seed: int | None = None) -> dict[str, IndistinguishabilityResult]:
        """
        Run tests for all gaps.

        Args:
            gap_pages: Dict mapping gap_id to list of synthetic pages
            seed: Optional seed for reproducibility
        """
        for i, (gap_id, pages) in enumerate(gap_pages.items()):
            tester = IndistinguishabilityTester(self.section_profile)

            # Load data
            tester.load_real_pages()
            tester.load_synthetic_pages(pages)
            
            # Derive seed for this gap
            gap_seed = seed + i * 1000 if seed is not None else None
            tester.generate_scrambled_controls(count=len(pages), seed=gap_seed)

            # Run test
            result = tester.run_test(gap_id)
            self.results[gap_id] = result

        return self.results

    def get_summary(self) -> dict[str, Any]:
        """Get summary of all tests."""
        if not self.results:
            return {
                "status": "no_tests_run",
                "matching_metrics": list(self.matching_metrics),
                "holdout_evaluation_metrics": list(self.holdout_evaluation_metrics),
                "metric_overlap": self.metric_overlap(),
                "leakage_detected": bool(self.metric_overlap()),
            }

        return {
            "gaps_tested": len(self.results),
            "scrambled_separated": sum(
                1 for r in self.results.values() if r.scrambled_clearly_separated
            ),
            "synthetic_indistinguishable": sum(
                1 for r in self.results.values() if r.synthetic_indistinguishable
            ),
            "overall_success": all(
                r.scrambled_clearly_separated and r.synthetic_indistinguishable
                for r in self.results.values()
            ),
            "per_gap": {
                gap_id: {
                    "real_vs_scrambled": r.real_vs_scrambled_separation,
                    "synthetic_vs_scrambled": r.synthetic_vs_scrambled_separation,
                    "real_vs_synthetic": r.real_vs_synthetic_separation,
                    "success": r.scrambled_clearly_separated and r.synthetic_indistinguishable,
                }
                for gap_id, r in self.results.items()
            },
            "matching_metrics": list(self.matching_metrics),
            "holdout_evaluation_metrics": list(self.holdout_evaluation_metrics),
            "metric_overlap": self.metric_overlap(),
            "leakage_detected": bool(self.metric_overlap()),
        }
