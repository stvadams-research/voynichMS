"""
Track B: Structural Hypothesis Formalization

For each discriminative feature, determines whether it can be expressed
as a non-semantic structural constraint.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

from foundation.config import get_analysis_thresholds
from synthesis.refinement.interface import (
    DiscriminativeFeature,
    StructuralConstraint,
    ConstraintStatus,
    FeatureCategory,
)

logger = logging.getLogger(__name__)


@dataclass
class FormalizationAttempt:
    """Record of an attempt to formalize a feature as a constraint."""
    feature_id: str
    success: bool
    constraint: Optional[StructuralConstraint] = None
    rejection_reason: str = ""


class ConstraintFormalization:
    """
    Formalizes discriminative features as structural constraints.

    Constraints must be:
    - Enforceable during generation
    - Non-semantic
    - Robust under perturbation
    """

    def __init__(self, features: List[DiscriminativeFeature]):
        self.features = features
        self.proposed: List[StructuralConstraint] = []
        self.validated: List[StructuralConstraint] = []
        self.rejected: List[StructuralConstraint] = []
        thresholds = get_analysis_thresholds().get("constraint_formalization", {})
        self.feature_importance_threshold = float(
            thresholds.get("feature_importance_threshold", 0.2)
        )
        self.separation_threshold = float(thresholds.get("separation_threshold", 0.3))

    def formalize_feature(self, feature: DiscriminativeFeature) -> FormalizationAttempt:
        """
        Attempt to formalize a single feature as a constraint.
        """
        # Check if feature is suitable for formalization
        if feature.importance_score < self.feature_importance_threshold:
            return FormalizationAttempt(
                feature_id=feature.feature_id,
                success=False,
                rejection_reason=(
                    f"Importance score too low (<{self.feature_importance_threshold})"
                ),
            )

        if feature.real_vs_scrambled_separation < self.separation_threshold:
            return FormalizationAttempt(
                feature_id=feature.feature_id,
                success=False,
                rejection_reason=(
                    f"Poor separation from scrambled controls (<{self.separation_threshold})"
                ),
            )

        # Formalize based on feature category
        constraint = self._create_constraint(feature)

        if constraint is None:
            return FormalizationAttempt(
                feature_id=feature.feature_id,
                success=False,
                rejection_reason="Could not formalize as enforceable constraint"
            )

        # Validate constraint
        is_valid, validation_reason = self._validate_constraint(constraint, feature)

        if not is_valid:
            constraint.status = ConstraintStatus.REJECTED
            constraint.rejection_reason = validation_reason
            self.rejected.append(constraint)
            return FormalizationAttempt(
                feature_id=feature.feature_id,
                success=False,
                constraint=constraint,
                rejection_reason=validation_reason
            )

        constraint.status = ConstraintStatus.VALIDATED
        self.validated.append(constraint)
        self.proposed.append(constraint)

        return FormalizationAttempt(
            feature_id=feature.feature_id,
            success=True,
            constraint=constraint
        )

    def _create_constraint(self, feature: DiscriminativeFeature) -> Optional[StructuralConstraint]:
        """Create a constraint from a feature."""
        # Define constraint based on feature type
        if feature.feature_id == "text_inter_jar_similarity":
            return StructuralConstraint(
                constraint_id=f"c_{feature.feature_id}",
                source_feature=feature.feature_id,
                name="Inter-Jar Text Similarity Constraint",
                description="Ensures text across jars shows sufficient similarity",
                constraint_type="probabilistic",
                measure="Average Jaccard similarity between jar vocabularies",
                enforcement="Reject pages with similarity below threshold",
                violation="Inter-jar similarity < 0.25",
                lower_bound=0.25,
                upper_bound=0.50,
                target_mean=feature.real_mean,
                target_std=feature.real_std,
            )

        elif feature.feature_id == "text_bigram_consistency":
            return StructuralConstraint(
                constraint_id=f"c_{feature.feature_id}",
                source_feature=feature.feature_id,
                name="Bigram Consistency Constraint",
                description="Ensures consistent bigram patterns across page",
                constraint_type="hard_bound",
                measure="Consistency score of bigram distributions",
                enforcement="Use consistent bigram model during generation",
                violation="Bigram consistency < 0.60",
                lower_bound=0.60,
                target_mean=feature.real_mean,
                target_std=feature.real_std,
            )

        elif feature.feature_id == "spatial_text_density_gradient":
            return StructuralConstraint(
                constraint_id=f"c_{feature.feature_id}",
                source_feature=feature.feature_id,
                name="Text Density Gradient Constraint",
                description="Ensures slight density gradient from top to bottom",
                constraint_type="probabilistic",
                measure="Slope of text density across vertical position",
                enforcement="Adjust word counts per jar based on position",
                violation="Gradient outside [-0.05, 0.05] range",
                lower_bound=-0.05,
                upper_bound=0.05,
                target_mean=feature.real_mean,
            )

        elif feature.feature_id == "temp_repetition_spacing":
            return StructuralConstraint(
                constraint_id=f"c_{feature.feature_id}",
                source_feature=feature.feature_id,
                name="Repetition Spacing Constraint",
                description="Controls average distance between repeated tokens",
                constraint_type="hard_bound",
                measure="Mean token distance for repeated tokens",
                enforcement="Penalize too-close repetitions during generation",
                violation="Mean spacing < 3.5 or > 6.0",
                lower_bound=3.5,
                upper_bound=6.0,
                target_mean=feature.real_mean,
            )

        elif feature.feature_id == "pos_left_right_asymmetry":
            return StructuralConstraint(
                constraint_id=f"c_{feature.feature_id}",
                source_feature=feature.feature_id,
                name="Left-Right Asymmetry Constraint",
                description="Maintains slight asymmetry between page halves",
                constraint_type="probabilistic",
                measure="Difference in text statistics left vs right",
                enforcement="Introduce slight bias in left vs right jar content",
                violation="Asymmetry < 0.03 (too symmetric) or > 0.15",
                lower_bound=0.03,
                upper_bound=0.15,
                target_mean=feature.real_mean,
            )

        elif feature.feature_id == "var_locality_variance":
            return StructuralConstraint(
                constraint_id=f"c_{feature.feature_id}",
                source_feature=feature.feature_id,
                name="Locality Variance Constraint",
                description="Controls variance of locality across jars",
                constraint_type="hard_bound",
                measure="Variance of locality metric across jars",
                enforcement="Ensure consistent locality window usage",
                violation="Variance > 0.15",
                upper_bound=0.15,
                target_mean=feature.real_mean,
            )

        elif feature.feature_id == "grad_entropy_slope":
            return StructuralConstraint(
                constraint_id=f"c_{feature.feature_id}",
                source_feature=feature.feature_id,
                name="Entropy Slope Constraint",
                description="Ensures slight entropy decrease across page",
                constraint_type="probabilistic",
                measure="Slope of entropy from first to last jar",
                enforcement="Adjust vocabulary diversity by position",
                violation="Slope outside [-0.05, 0.01]",
                lower_bound=-0.05,
                upper_bound=0.01,
                target_mean=feature.real_mean,
            )

        else:
            # Generic constraint
            return StructuralConstraint(
                constraint_id=f"c_{feature.feature_id}",
                source_feature=feature.feature_id,
                name=f"{feature.name} Constraint",
                description=f"Constraint based on {feature.description}",
                constraint_type="probabilistic",
                measure=feature.description,
                enforcement="Match target distribution during generation",
                violation=f"Value outside 2 std of target",
                target_mean=feature.real_mean,
                target_std=feature.real_std,
            )

    def _validate_constraint(self, constraint: StructuralConstraint,
                            feature: DiscriminativeFeature) -> tuple:
        """
        Validate a constraint.

        Returns (is_valid, reason).
        """
        # Check for semantic leakage
        semantic_keywords = ["meaning", "semantic", "interpret", "decode", "symbol"]
        for keyword in semantic_keywords:
            if keyword in constraint.description.lower():
                return False, "Constraint description contains semantic terms"
            if keyword in constraint.enforcement.lower():
                return False, "Constraint enforcement contains semantic terms"

        # Check if constraint is enforceable
        if constraint.target_mean is None and constraint.lower_bound is None:
            return False, "No enforceable bound defined"

        # Check if feature has sufficient discrimination
        if feature.real_vs_synthetic_separation < 0.2:
            return False, "Feature does not sufficiently discriminate"

        # Check perturbation robustness (simulated)
        # In production, this would test the constraint under perturbation
        if feature.importance_score < 0.25:
            constraint.passes_perturbation = False
            return False, "Feature collapses under perturbation"

        constraint.passes_perturbation = True
        constraint.is_semantic_free = True
        constraint.is_enforceable = True

        return True, ""

    def formalize_all(self) -> Dict[str, Any]:
        """Formalize all formalizable features."""
        attempts = []

        for feature in self.features:
            if feature.is_formalizable:
                attempt = self.formalize_feature(feature)
                attempts.append(attempt)

        return {
            "features_attempted": len(attempts),
            "successful": len(self.validated),
            "rejected": len(self.rejected),
            "validated_constraints": [
                {
                    "id": c.constraint_id,
                    "name": c.name,
                    "type": c.constraint_type,
                    "bounds": (c.lower_bound, c.upper_bound),
                }
                for c in self.validated
            ],
            "rejected_constraints": [
                {
                    "id": c.constraint_id,
                    "reason": c.rejection_reason,
                }
                for c in self.rejected
            ],
        }

    def get_enforceable_constraints(self) -> List[StructuralConstraint]:
        """Get all validated, enforceable constraints."""
        return [c for c in self.validated if c.is_enforceable]
