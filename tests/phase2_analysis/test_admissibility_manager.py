import pytest

pytestmark = pytest.mark.unit

from phase1_foundation.storage.metadata import MetadataStore
from phase2_analysis.admissibility.manager import (
    AdmissibilityManager,
    AdmissibilityStatus,
    ConstraintType,
    SupportLevel,
)


def _new_store(tmp_path):
    return MetadataStore(f"sqlite:///{tmp_path}/admissibility.db")


def test_admissibility_manager_marks_class_admissible_with_supported_requirements(tmp_path):
    store = _new_store(tmp_path)
    manager = AdmissibilityManager(store)

    class_id = manager.register_class("c1", "Class One", "desc")
    req_id = manager.add_constraint(class_id, ConstraintType.REQUIRED, "must have local structure")
    manager.map_evidence(
        class_id=class_id,
        constraint_id=req_id,
        support_level=SupportLevel.SUPPORTS,
        reasoning="observed local structure",
    )

    result = manager.evaluate_status(class_id)
    assert result.status == AdmissibilityStatus.ADMISSIBLE
    assert result.violations == []
    assert result.unmet_requirements == []


def test_admissibility_manager_marks_class_inadmissible_when_forbidden_supported(tmp_path):
    store = _new_store(tmp_path)
    manager = AdmissibilityManager(store)

    class_id = manager.register_class("c2", "Class Two", "desc")
    forb_id = manager.add_constraint(class_id, ConstraintType.FORBIDDEN, "cannot be random")
    manager.map_evidence(
        class_id=class_id,
        constraint_id=forb_id,
        support_level=SupportLevel.SUPPORTS,
        reasoning="randomness signal present",
    )

    result = manager.evaluate_status(class_id)
    assert result.status == AdmissibilityStatus.INADMISSIBLE
    assert len(result.violations) == 1


def test_admissibility_manager_marks_underconstrained_without_required_evidence(tmp_path):
    store = _new_store(tmp_path)
    manager = AdmissibilityManager(store)

    class_id = manager.register_class("c3", "Class Three", "desc")
    manager.add_constraint(class_id, ConstraintType.REQUIRED, "needs anchor consistency")

    result = manager.evaluate_status(class_id)
    assert result.status == AdmissibilityStatus.UNDERCONSTRAINED
    assert len(result.unmet_requirements) == 1
