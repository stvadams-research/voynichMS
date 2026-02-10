import importlib.util
from pathlib import Path

from synthesis.interface import SectionProfile, SyntheticPage
from synthesis.refinement.interface import EquivalenceOutcome, EquivalenceTest


class _FakeResult:
    def __init__(self, real_vs_scrambled_separation, real_vs_synthetic_separation):
        self.real_vs_scrambled_separation = real_vs_scrambled_separation
        self.real_vs_synthetic_separation = real_vs_synthetic_separation


class _FakeTester:
    def __init__(self, _section_profile):
        self.synthetic_pages = []

    def load_real_pages(self):
        return None

    def load_synthetic_pages(self, pages):
        self.synthetic_pages = pages

    def generate_scrambled_controls(self, count=0):
        return count

    def run_test(self, label):
        if "phase31" in label or label.endswith("_p31"):
            return _FakeResult(real_vs_scrambled_separation=0.80, real_vs_synthetic_separation=0.28)
        return _FakeResult(real_vs_scrambled_separation=0.82, real_vs_synthetic_separation=0.42)


def _load_equivalence_module():
    module_path = Path("src/synthesis/refinement/equivalence_testing.py")
    spec = importlib.util.spec_from_file_location("equivalence_testing", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_page(page_id: str) -> SyntheticPage:
    page = SyntheticPage(page_id=page_id, gap_id="gap_a", jar_count=1, text_blocks=[["a", "b"]])
    page.compute_hash()
    return page


def test_equivalence_retest_uses_phase31_result_for_outcome(monkeypatch):
    module = _load_equivalence_module()
    monkeypatch.setattr(module, "IndistinguishabilityTester", _FakeTester)

    retest = module.EquivalenceReTest(SectionProfile())
    result = retest.run_comparison(
        phase3_pages={"gap_a": [_make_page("p3")]},
        phase31_pages={"gap_a": [_make_page("p31")]},
    )

    assert isinstance(result, EquivalenceTest)
    assert result.real_vs_synthetic_phase3 == 0.42
    assert result.real_vs_synthetic_phase31 == 0.28
    assert result.outcome == EquivalenceOutcome.STRUCTURAL_EQUIVALENCE


def test_termination_decision_handles_divergence_and_equivalence():
    module = _load_equivalence_module()

    eq = EquivalenceTest(
        real_vs_synthetic_phase3=0.45,
        real_vs_synthetic_phase31=0.25,
    )
    eq.determine_outcome()
    decision = module.TerminationDecision(eq, constraints_validated=2, constraints_rejected=0)
    should_terminate, reason = decision.should_terminate()
    assert should_terminate is True
    assert "Structural equivalence achieved" in reason

    div = EquivalenceTest(
        real_vs_synthetic_phase3=0.30,
        real_vs_synthetic_phase31=0.50,
    )
    div.determine_outcome()
    divergence_decision = module.TerminationDecision(div, constraints_validated=1, constraints_rejected=3)
    should_terminate_div, reason_div = divergence_decision.should_terminate()
    assert should_terminate_div is True
    assert "Separation increased" in reason_div
