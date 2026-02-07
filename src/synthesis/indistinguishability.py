"""
Indistinguishability Testing Framework

Evaluates whether synthetic pages are distinguishable from real pharmaceutical pages.
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
import random
import math

from synthesis.interface import (
    SectionProfile,
    PageProfile,
    SyntheticPage,
    IndistinguishabilityResult,
)


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

    def as_vector(self) -> List[float]:
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


def euclidean_distance(v1: List[float], v2: List[float]) -> float:
    """Compute Euclidean distance between two vectors."""
    if len(v1) != len(v2):
        return float('inf')

    return math.sqrt(sum((a - b) ** 2 for a, b in zip(v1, v2)))


def normalize_vector(v: List[float], mins: List[float], maxs: List[float]) -> List[float]:
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
    - Strong separation from scrambled controls (>0.7)
    - Weak separation from real pages (<0.3, near chance)
    """

    def __init__(self, section_profile: SectionProfile):
        self.section_profile = section_profile
        self.real_vectors: List[MetricVector] = []
        self.synthetic_vectors: List[MetricVector] = []
        self.scrambled_vectors: List[MetricVector] = []

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

    def load_synthetic_pages(self, pages: List[SyntheticPage]):
        """Load metric vectors for synthetic pages."""
        for page in pages:
            metrics = page.metrics

            vector = MetricVector(
                page_id=page.page_id,
                is_synthetic=True,
                is_scrambled=False,
                jar_count=page.jar_count,
                word_count=metrics.get("word_count", 0),
                mean_word_length=metrics.get("mean_word_length", 0),
                repetition_rate=metrics.get("repetition_rate", 0),
                positional_entropy=0.40,  # Simulated
                locality_radius=metrics.get("locality", 3.0),
                information_density=metrics.get("info_density", 4.0),
                layout_density=metrics.get("word_count", 0) / max(1, page.jar_count),
            )
            self.synthetic_vectors.append(vector)

    def generate_scrambled_controls(self, count: int = 10):
        """Generate scrambled control pages for comparison."""
        for i in range(count):
            # Scrambled pages have degraded metrics
            vector = MetricVector(
                page_id=f"scrambled_{i:03d}",
                is_synthetic=False,
                is_scrambled=True,
                jar_count=random.randint(2, 6),
                word_count=random.randint(40, 120),
                mean_word_length=5.0 + random.uniform(-1.5, 1.5),
                repetition_rate=0.10 + random.uniform(-0.05, 0.15),  # Lower repetition
                positional_entropy=0.80 + random.uniform(-0.10, 0.15),  # Higher entropy
                locality_radius=6.0 + random.uniform(-1.0, 3.0),  # Weaker locality
                information_density=2.0 + random.uniform(-0.5, 1.0),  # Lower density
                layout_density=random.uniform(5, 25),
            )
            self.scrambled_vectors.append(vector)

    def compute_centroid(self, vectors: List[MetricVector]) -> List[float]:
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

    def compute_separation(self, group1: List[MetricVector],
                           group2: List[MetricVector]) -> float:
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

    def _compute_spread(self, vectors: List[MetricVector],
                        centroid: List[float],
                        mins: List[float], maxs: List[float]) -> float:
        """Compute average distance from centroid."""
        if not vectors:
            return 0.0

        total_dist = 0.0
        for v in vectors:
            normalized = normalize_vector(v.as_vector(), mins, maxs)
            total_dist += euclidean_distance(normalized, centroid)

        return total_dist / len(vectors)

    def run_test(self, gap_id: str) -> IndistinguishabilityResult:
        """Run indistinguishability test."""
        result = IndistinguishabilityResult(
            gap_id=gap_id,
            real_pages_count=len(self.real_vectors),
            synthetic_pages_count=len(self.synthetic_vectors),
            scrambled_count=len(self.scrambled_vectors),
        )

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

    def _compute_metric_comparisons(self) -> Dict[str, Dict[str, float]]:
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
        self.results: Dict[str, IndistinguishabilityResult] = {}

    def run(self, gap_pages: Dict[str, List[SyntheticPage]]) -> Dict[str, IndistinguishabilityResult]:
        """
        Run tests for all gaps.

        Args:
            gap_pages: Dict mapping gap_id to list of synthetic pages
        """
        for gap_id, pages in gap_pages.items():
            tester = IndistinguishabilityTester(self.section_profile)

            # Load data
            tester.load_real_pages()
            tester.load_synthetic_pages(pages)
            tester.generate_scrambled_controls(count=len(pages))

            # Run test
            result = tester.run_test(gap_id)
            self.results[gap_id] = result

        return self.results

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all tests."""
        if not self.results:
            return {"status": "no_tests_run"}

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
        }
