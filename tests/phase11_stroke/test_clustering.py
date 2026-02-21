import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

pytestmark = pytest.mark.unit

from phase11_stroke.clustering import ClusteringAnalyzer  # noqa: E402
from phase11_stroke.schema import StrokeSchema  # noqa: E402


def _build_extracted(line_tokens: list[list[str]], counts: dict[str, int]) -> dict:
    token_type_features = {
        token: {
            "count": int(count),
            "mean_profile": [0.0] * 6,
            "boundary_profile": [0.0] * 12,
            "aggregate_profile": [0.0] * 6,
            "recognized_char_count_mean": float(len(token)),
            "skipped_char_count_mean": 0.0,
        }
        for token, count in counts.items()
    }
    line_features = [
        {
            "page_id": "f1r",
            "line_id": f"f1r:{idx + 1}",
            "line_index": idx + 1,
            "tokens": tokens,
            "token_count": len(tokens),
            "unique_token_count": len(set(tokens)),
            "mean_profile": [0.0] * 6,
            "aggregate_profile": [0.0] * 6,
        }
        for idx, tokens in enumerate(line_tokens)
    ]
    return {"token_type_features": token_type_features, "line_features": line_features}


def test_clustering_detects_positive_structure_on_synthetic_data() -> None:
    # Similar morphology pairs co-occur in the same lines.
    lines = []
    lines.extend([["da", "ea"] for _ in range(25)])
    lines.extend([["ky", "ty"] for _ in range(25)])
    counts = {"da": 25, "ea": 25, "ky": 25, "ty": 25}
    extracted = _build_extracted(lines, counts)

    analyzer = ClusteringAnalyzer(schema=StrokeSchema(), min_occurrence=1)
    result = analyzer.run(
        extracted_data=extracted,
        n_permutations=100,
        rng=np.random.default_rng(42),
    )

    assert result["observed_raw_rho"] > 0.1
    assert result["observed_partial_rho"] > 0.05


def test_clustering_returns_near_zero_when_cooccurrence_is_uniform() -> None:
    # Every line contains all tokens, so pairwise co-occurrence does not vary.
    lines = [["da", "ea", "ky", "ty"] for _ in range(40)]
    counts = {"da": 40, "ea": 40, "ky": 40, "ty": 40}
    extracted = _build_extracted(lines, counts)

    analyzer = ClusteringAnalyzer(schema=StrokeSchema(), min_occurrence=1)
    result = analyzer.run(
        extracted_data=extracted,
        n_permutations=50,
        rng=np.random.default_rng(7),
    )

    assert abs(result["observed_raw_rho"]) < 1e-9
    assert abs(result["observed_partial_rho"]) < 1e-9


def test_frequency_control_reduces_spurious_frequency_association() -> None:
    # High-frequency tokens are much more likely to co-occur, independent of morphology.
    lines = []
    lines.extend([["da", "ky"] for _ in range(40)])
    lines.extend([["da"] for _ in range(20)])
    lines.extend([["ky"] for _ in range(20)])
    lines.extend([["ea", "ty"] for _ in range(4)])
    counts = {"da": 60, "ky": 60, "ea": 4, "ty": 4}
    extracted = _build_extracted(lines, counts)

    analyzer = ClusteringAnalyzer(schema=StrokeSchema(), min_occurrence=1)
    result = analyzer.run(
        extracted_data=extracted,
        n_permutations=50,
        rng=np.random.default_rng(17),
    )

    assert abs(result["observed_partial_rho"]) <= abs(result["observed_raw_rho"]) + 1e-6
