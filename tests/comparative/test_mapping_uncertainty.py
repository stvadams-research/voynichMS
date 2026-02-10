import importlib.util
import json
import sys
from pathlib import Path


def _load_mapping_module():
    src_path = Path("src").resolve()
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    module_path = Path("src/comparative/mapping.py")
    spec = importlib.util.spec_from_file_location("comparative_mapping", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_compute_distance_uncertainty_returns_expected_keys() -> None:
    mapping = _load_mapping_module()
    matrix = {
        "Voynich": mapping.np.array([4.0, 5.0, 4.0, 4.0]),
        "Lullian": mapping.np.array([4.0, 4.5, 4.5, 4.0]),
        "Latin": mapping.np.array([1.0, 1.5, 1.0, 1.0]),
    }

    result = mapping.compute_distance_uncertainty(
        matrix,
        target="Voynich",
        seed=7,
        iterations=300,
    )

    assert result["nearest_neighbor"] == "Lullian"
    assert result["status"] in {
        "STABILITY_CONFIRMED",
        "DISTANCE_QUALIFIED",
        "INCONCLUSIVE_UNCERTAINTY",
    }
    assert 0.0 <= result["nearest_neighbor_stability"] <= 1.0
    assert 0.0 <= result["rank_stability"] <= 1.0
    assert "rank_stability_components" in result
    assert "nearest_neighbor_probability_margin" in result
    assert "metric_validity" in result
    assert result["metric_validity"]["required_fields_present"] is True
    assert "distance_summary" in result
    assert "Lullian" in result["distance_summary"]
    assert "ci95_lower" in result["distance_summary"]["Lullian"]


def test_run_analysis_writes_report_and_uncertainty_artifact(tmp_path) -> None:
    mapping = _load_mapping_module()

    matrix_path = tmp_path / "matrix.csv"
    matrix_path.write_text(
        "\n".join(
            [
                "Artifact,D1,D2,D3,D4",
                "Voynich,4,5,4,4",
                "Lullian,5,4,5,4",
                "Latin,2,2,1,2",
            ]
        ),
        encoding="utf-8",
    )

    report_path = tmp_path / "PROXIMITY_ANALYSIS.md"
    artifact_path = tmp_path / "phase_7c_uncertainty.json"
    summary = mapping.run_analysis(
        matrix_path=matrix_path,
        report_path=report_path,
        uncertainty_output_path=artifact_path,
        iterations=300,
        seed=42,
        target="Voynich",
    )

    assert summary["status"] in {
        "STABILITY_CONFIRMED",
        "DISTANCE_QUALIFIED",
        "INCONCLUSIVE_UNCERTAINTY",
    }
    assert "reason_code" in summary
    assert "rank_stability" in summary
    assert report_path.exists()
    report_text = report_path.read_text(encoding="utf-8")
    assert "95% CI" in report_text
    assert "Nearest-Neighbor Stability" in report_text
    assert "Rank Stability" in report_text

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert "results" in payload
    assert "distance_summary" in payload["results"]
    assert "rank_stability" in payload["results"]
