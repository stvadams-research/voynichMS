"""
Admissibility Manager

Provides logic for registering explanation classes, defining constraints,
mapping evidence from Phase 1, and evaluating admissibility status.

Per Phase 2 Principles:
- Admissibility Before Truth: We evaluate whether an explanation is permitted,
  not whether it is correct.
- Explicit Assumptions: Every phase2_analysis must declare what it assumes.
- Controls Are First-Class Citizens: All analyses must reference Phase 1 controls.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
from phase1_foundation.storage.metadata import (
    MetadataStore,
    ExplanationClassRecord,
    AdmissibilityConstraintRecord,
    AdmissibilityEvidenceRecord,
    StructureRecord,
    HypothesisRecord,
)

logger = logging.getLogger(__name__)


class ConstraintType(Enum):
    REQUIRED = "REQUIRED"      # Must be satisfied for admissibility
    FORBIDDEN = "FORBIDDEN"    # If true, class is inadmissible
    OPTIONAL = "OPTIONAL"      # Relevant but not decisive


class SupportLevel(Enum):
    SUPPORTS = "SUPPORTS"          # Evidence supports the constraint
    CONTRADICTS = "CONTRADICTS"    # Evidence contradicts the constraint
    IRRELEVANT = "IRRELEVANT"      # Evidence doesn't bear on constraint


class AdmissibilityStatus(Enum):
    ADMISSIBLE = "admissible"              # All requirements met, no forbiddens triggered
    INADMISSIBLE = "inadmissible"          # A forbidden is triggered or a required is contradicted
    UNDERCONSTRAINED = "underconstrained"  # Insufficient evidence to decide


@dataclass
class EvaluationResult:
    """Result of evaluating an explanation class."""
    class_id: str
    status: AdmissibilityStatus
    violations: List[Dict[str, Any]]      # Constraints that caused inadmissibility
    unmet_requirements: List[Dict[str, Any]]  # Required constraints without supporting evidence
    supporting_evidence: List[Dict[str, Any]]  # Evidence that supports admissibility
    reversal_conditions: List[str]         # What would change the status


class AdmissibilityManager:
    """
    Manages the admissibility mapping process for Phase 2.1.

    Workflow:
    1. Register explanation classes (e.g., natural_language, enciphered)
    2. Define constraints for each class (REQUIRED, FORBIDDEN, OPTIONAL)
    3. Map evidence from Phase 1 structures/hypotheses to constraints
    4. Evaluate status based on evidence mapping
    """

    def __init__(self, store: MetadataStore):
        self.store = store

    def register_class(self, id: str, name: str, description: str) -> str:
        """
        Register a new explanation class.

        Args:
            id: Unique identifier (e.g., "natural_language")
            name: Human-readable name
            description: Full description of the explanation class

        Returns:
            The class id
        """
        self.store.add_explanation_class(
            id=id,
            name=name,
            description=description,
            status=AdmissibilityStatus.UNDERCONSTRAINED.value
        )
        return id

    def add_constraint(
        self,
        class_id: str,
        constraint_type: ConstraintType,
        description: str
    ) -> int:
        """
        Add a constraint to an explanation class.

        Args:
            class_id: The explanation class to constrain
            constraint_type: REQUIRED, FORBIDDEN, or OPTIONAL
            description: What the constraint means

        Returns:
            The constraint id
        """
        return self.store.add_admissibility_constraint(
            explanation_class_id=class_id,
            constraint_type=constraint_type.value,
            description=description
        )

    def map_evidence(
        self,
        class_id: str,
        constraint_id: int,
        support_level: SupportLevel,
        reasoning: str,
        structure_id: Optional[str] = None,
        hypothesis_id: Optional[str] = None
    ):
        """
        Map Phase 1 evidence to a constraint.

        Args:
            class_id: The explanation class
            constraint_id: The constraint being evidenced
            support_level: SUPPORTS, CONTRADICTS, or IRRELEVANT
            reasoning: Explanation of how the evidence relates
            structure_id: Optional Phase 1 structure providing evidence
            hypothesis_id: Optional Phase 1 hypothesis providing evidence
        """
        session = self.store.Session()
        try:
            from phase1_foundation.storage.metadata import AdmissibilityEvidenceRecord
            record = AdmissibilityEvidenceRecord(
                explanation_class_id=class_id,
                constraint_id=constraint_id,
                structure_id=structure_id,
                hypothesis_id=hypothesis_id,
                support_level=support_level.value,
                reasoning=reasoning
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

    def evaluate_status(self, class_id: str) -> EvaluationResult:
        """
        Evaluate the admissibility status of an explanation class.

        Logic:
        - If any FORBIDDEN constraint is SUPPORTED -> INADMISSIBLE
        - If any REQUIRED constraint is CONTRADICTED -> INADMISSIBLE
        - If REQUIRED constraints lack SUPPORTING evidence -> UNDERCONSTRAINED
        - Otherwise -> ADMISSIBLE

        Returns:
            EvaluationResult with status and details
        """
        session = self.store.Session()
        try:
            # Get all constraints for this class
            constraints = session.query(AdmissibilityConstraintRecord).filter_by(
                explanation_class_id=class_id
            ).all()

            violations = []
            unmet_requirements = []
            supporting_evidence = []
            reversal_conditions = []

            required_constraints = [c for c in constraints if c.constraint_type == "REQUIRED"]
            forbidden_constraints = [c for c in constraints if c.constraint_type == "FORBIDDEN"]

            # Check FORBIDDEN constraints
            for constraint in forbidden_constraints:
                evidence = session.query(AdmissibilityEvidenceRecord).filter_by(
                    constraint_id=constraint.id
                ).all()

                for ev in evidence:
                    if ev.support_level == "SUPPORTS":
                        # FORBIDDEN constraint is supported = inadmissible
                        violations.append({
                            "constraint_id": constraint.id,
                            "constraint_type": "FORBIDDEN",
                            "constraint_description": constraint.description,
                            "evidence_reasoning": ev.reasoning,
                            "structure_id": ev.structure_id,
                            "hypothesis_id": ev.hypothesis_id,
                        })

            # Check REQUIRED constraints
            for constraint in required_constraints:
                evidence = session.query(AdmissibilityEvidenceRecord).filter_by(
                    constraint_id=constraint.id
                ).all()

                has_support = any(ev.support_level == "SUPPORTS" for ev in evidence)
                has_contradiction = any(ev.support_level == "CONTRADICTS" for ev in evidence)

                if has_contradiction:
                    # REQUIRED constraint is contradicted = inadmissible
                    for ev in evidence:
                        if ev.support_level == "CONTRADICTS":
                            violations.append({
                                "constraint_id": constraint.id,
                                "constraint_type": "REQUIRED",
                                "constraint_description": constraint.description,
                                "evidence_reasoning": ev.reasoning,
                                "structure_id": ev.structure_id,
                                "hypothesis_id": ev.hypothesis_id,
                            })
                elif has_support:
                    # REQUIRED constraint is supported = good
                    for ev in evidence:
                        if ev.support_level == "SUPPORTS":
                            supporting_evidence.append({
                                "constraint_id": constraint.id,
                                "constraint_description": constraint.description,
                                "evidence_reasoning": ev.reasoning,
                                "structure_id": ev.structure_id,
                                "hypothesis_id": ev.hypothesis_id,
                            })
                else:
                    # REQUIRED constraint lacks evidence = underconstrained
                    unmet_requirements.append({
                        "constraint_id": constraint.id,
                        "constraint_description": constraint.description,
                    })

            # Determine status
            if violations:
                status = AdmissibilityStatus.INADMISSIBLE
                reversal_conditions = [
                    f"Remove or invalidate evidence for: {v['constraint_description']}"
                    for v in violations
                ]
            elif unmet_requirements:
                status = AdmissibilityStatus.UNDERCONSTRAINED
                reversal_conditions = [
                    f"Provide evidence for: {u['constraint_description']}"
                    for u in unmet_requirements
                ]
            else:
                status = AdmissibilityStatus.ADMISSIBLE
                # For admissible, reversal conditions are what would make it inadmissible
                reversal_conditions = [
                    f"If FORBIDDEN triggered: {c.description}"
                    for c in forbidden_constraints
                ] + [
                    f"If REQUIRED contradicted: {c.description}"
                    for c in required_constraints
                ]

            # Update status in database
            self.store.update_explanation_class_status(class_id, status.value)

            return EvaluationResult(
                class_id=class_id,
                status=status,
                violations=violations,
                unmet_requirements=unmet_requirements,
                supporting_evidence=supporting_evidence,
                reversal_conditions=reversal_conditions
            )

        finally:
            session.close()

    def evaluate_all(self) -> Dict[str, EvaluationResult]:
        """
        Evaluate all registered explanation classes.

        Returns:
            Dictionary mapping class_id to EvaluationResult
        """
        classes = self.store.get_all_explanation_classes()
        return {c.id: self.evaluate_status(c.id) for c in classes}

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate the Admissibility Matrix report.

        Returns:
            Structured report data suitable for display or export
        """
        results = self.evaluate_all()

        report = {
            "summary": {
                "total_classes": len(results),
                "admissible": sum(1 for r in results.values() if r.status == AdmissibilityStatus.ADMISSIBLE),
                "inadmissible": sum(1 for r in results.values() if r.status == AdmissibilityStatus.INADMISSIBLE),
                "underconstrained": sum(1 for r in results.values() if r.status == AdmissibilityStatus.UNDERCONSTRAINED),
            },
            "classes": {}
        }

        for class_id, result in results.items():
            cls = self.store.get_explanation_class(class_id)
            report["classes"][class_id] = {
                "name": cls.name if cls else class_id,
                "description": cls.description if cls else "",
                "status": result.status.value,
                "violations": result.violations,
                "unmet_requirements": result.unmet_requirements,
                "supporting_evidence": result.supporting_evidence,
                "reversal_conditions": result.reversal_conditions,
            }

        return report
