import random

from phase3_synthesis.interface import SyntheticPage
from phase3_synthesis.refinement.interface import ConstraintStatus, StructuralConstraint
from phase3_synthesis.refinement.resynthesis import RefinedGenerator


def _make_generator_stub() -> RefinedGenerator:
    generator = RefinedGenerator.__new__(RefinedGenerator)
    generator.rng = random.Random(42)
    generator.refinement_constraints = []
    return generator


def test_compute_constraint_value_similarity_and_spacing_branches():
    generator = _make_generator_stub()
    page = SyntheticPage(
        page_id="SYNTHETIC_gap_a_00001",
        gap_id="gap_a",
        jar_count=2,
        text_blocks=[["a", "b", "a"], ["a", "c", "d"]],
    )

    similarity_constraint = StructuralConstraint(
        constraint_id="jar_similarity",
        source_feature="f1",
        name="similarity",
        description="",
        constraint_type="hard_bound",
        measure="similarity",
        enforcement="none",
        violation="none",
    )
    spacing_constraint = StructuralConstraint(
        constraint_id="repetition_spacing",
        source_feature="f2",
        name="spacing",
        description="",
        constraint_type="hard_bound",
        measure="spacing",
        enforcement="none",
        violation="none",
    )

    similarity = generator._compute_constraint_value(similarity_constraint, page)
    spacing = generator._compute_constraint_value(spacing_constraint, page)

    assert 0.0 <= similarity <= 1.0
    assert spacing >= 1.0


def test_check_constraints_marks_violations_with_bounds(monkeypatch):
    generator = _make_generator_stub()
    page = SyntheticPage(page_id="SYNTHETIC_gap_a_00002", gap_id="gap_a", jar_count=1, text_blocks=[["a"]])

    constraint = StructuralConstraint(
        constraint_id="variance_locality",
        source_feature="f3",
        name="variance",
        description="",
        constraint_type="hard_bound",
        measure="variance",
        enforcement="none",
        violation="none",
        lower_bound=0.0,
        upper_bound=0.2,
        target_mean=0.1,
        status=ConstraintStatus.PROPOSED,
    )
    generator.refinement_constraints = [constraint]
    monkeypatch.setattr(generator, "_compute_constraint_value", lambda *_args, **_kwargs: 0.5)

    checks = generator.check_constraints(page)

    assert len(checks) == 1
    assert checks[0].satisfied is False
    assert checks[0].constraint_id == "variance_locality"
    assert checks[0].deviation > 0
