import importlib.util
from pathlib import Path


def _load_7b_module():
    module_path = Path("scripts/human/run_7b_codicology.py")
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
