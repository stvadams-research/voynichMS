import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def _load_7b_module():
    module_path = Path("scripts/phase7_human/run_7b_codicology.py")
    spec = importlib.util.spec_from_file_location("run_7b_codicology", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_phase7_guardrail_marks_missing_artifact_as_non_conclusive() -> None:
    mod = _load_7b_module()
    summary = mod.summarize_illustration_coupling({})
    assert summary["status"] == "MISSING_ARTIFACT"
    assert summary["conclusive"] is False
    assert "no coupling claim" in summary["statement"]


def test_phase7_guardrail_respects_conclusive_no_coupling_status() -> None:
    mod = _load_7b_module()
    summary = mod.summarize_illustration_coupling(
        {
            "status": "CONCLUSIVE_NO_COUPLING",
            "allowed_claim": "No robust image/layout coupling detected.",
        }
    )
    assert summary["status"] == "CONCLUSIVE_NO_COUPLING"
    assert summary["conclusive"] is True
    assert "did not detect" in summary["statement"]


def test_phase7_guardrail_blocks_categorical_language_when_inconclusive() -> None:
    mod = _load_7b_module()
    summary = mod.summarize_illustration_coupling(
        {
            "status": "INCONCLUSIVE_UNDERPOWERED",
            "allowed_claim": "No conclusive coupling claim is allowed.",
        }
    )
    assert summary["conclusive"] is False
    assert "no conclusive claim is allowed" in summary["statement"]


def test_phase7_guardrail_distinguishes_inferential_ambiguity_from_underpower() -> None:
    mod = _load_7b_module()
    summary = mod.summarize_illustration_coupling(
        {
            "status": "INCONCLUSIVE_INFERENTIAL_AMBIGUITY",
            "allowed_claim": "Adequacy thresholds pass but phase4_inference remains ambiguous.",
        }
    )
    assert summary["conclusive"] is False
    assert "inferentially ambiguous" in summary["statement"]


def test_phase7_guardrail_marks_h1_4_qualified_lane_as_non_conclusive() -> None:
    mod = _load_7b_module()
    summary = mod.summarize_illustration_coupling(
        {
            "status": "CONCLUSIVE_NO_COUPLING",
            "h1_4_closure_lane": "H1_4_QUALIFIED",
            "robustness": {"robustness_class": "MIXED"},
            "allowed_claim": "Canonical lane shows no robust coupling signal.",
        }
    )
    assert summary["conclusive"] is False
    assert summary["h1_4_closure_lane"] == "H1_4_QUALIFIED"
    assert summary["robustness_class"] == "MIXED"
    assert "robustness remains qualified across registered lanes" in summary["statement"]


def test_phase7_guardrail_marks_h1_5_bounded_lane_as_non_conclusive() -> None:
    mod = _load_7b_module()
    summary = mod.summarize_illustration_coupling(
        {
            "status": "CONCLUSIVE_NO_COUPLING",
            "h1_4_closure_lane": "H1_4_QUALIFIED",
            "h1_5_closure_lane": "H1_5_BOUNDED",
            "robustness": {
                "robustness_class": "MIXED",
                "entitlement_robustness_class": "ROBUST",
            },
            "allowed_claim": "Entitlement lane shows no robust coupling signal.",
        }
    )
    assert summary["conclusive"] is False
    assert summary["h1_5_closure_lane"] == "H1_5_BOUNDED"
    assert summary["entitlement_robustness_class"] == "ROBUST"
    assert "diagnostic lanes remain non-conclusive monitoring signals" in summary["statement"]
