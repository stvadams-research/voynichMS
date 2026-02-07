"""
Phase 3.1 Interface and Data Structures

Defines structures for discriminative feature discovery, constraint formalization,
and equivalence testing.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Callable
from enum import Enum


class FeatureCategory(Enum):
    """Categories of discriminative features."""
    SPATIAL = "spatial"  # Higher-order spatial correlations
    TEXTUAL = "textual"  # Inter-jar text similarity
    POSITIONAL = "positional"  # Positional asymmetries
    VARIANCE = "variance"  # Variance of locality/metrics
    TEMPORAL = "temporal"  # Cross-jar repetition timing
    GRADIENT = "gradient"  # Entropy gradients


class ConstraintStatus(Enum):
    """Status of a formalized constraint."""
    PROPOSED = "proposed"
    VALIDATED = "validated"
    REJECTED = "rejected"
    INTEGRATED = "integrated"


class EquivalenceOutcome(Enum):
    """Possible outcomes of equivalence testing."""
    STRUCTURAL_EQUIVALENCE = "structural_equivalence"  # Gap closed
    SEPARATION_REDUCED = "separation_reduced"  # Gap narrowed
    NO_CHANGE = "no_change"  # Gap persists
    DIVERGENCE = "divergence"  # Gap widened (unexpected)


@dataclass
class DiscriminativeFeature:
    """A feature that discriminates real from synthetic pages."""
    feature_id: str
    name: str
    category: FeatureCategory
    description: str

    # Computation
    compute_fn: Optional[Callable] = None

    # Discrimination power
    importance_score: float = 0.0
    stability_score: float = 0.0  # Stability under resampling

    # Values
    real_mean: float = 0.0
    real_std: float = 0.0
    synthetic_mean: float = 0.0
    synthetic_std: float = 0.0
    scrambled_mean: float = 0.0
    scrambled_std: float = 0.0

    # Separation
    real_vs_synthetic_separation: float = 0.0
    real_vs_scrambled_separation: float = 0.0

    # Formalizable as constraint?
    is_formalizable: bool = False
    formalization_notes: str = ""


@dataclass
class FeatureImportance:
    """Feature importance from discriminator."""
    feature_id: str
    importance: float
    rank: int
    stable_across_folds: bool = False
    correlated_with: List[str] = field(default_factory=list)


@dataclass
class StructuralConstraint:
    """A formalized structural constraint from discriminative features."""
    constraint_id: str
    source_feature: str
    name: str
    description: str

    # Specification
    constraint_type: str  # "hard_bound", "probabilistic", "relational", etc.
    measure: str  # What it measures
    enforcement: str  # How enforced during generation
    violation: str  # How violation is detected

    # Bounds
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    target_mean: Optional[float] = None
    target_std: Optional[float] = None

    # Status
    status: ConstraintStatus = ConstraintStatus.PROPOSED

    # Validation
    passes_perturbation: bool = False
    is_semantic_free: bool = True
    is_enforceable: bool = True

    # Rejection reason if applicable
    rejection_reason: str = ""


@dataclass
class RefinementResult:
    """Result of constraint integration and re-synthesis."""
    gap_id: str

    # Before refinement (Phase 3)
    phase3_separation: float = 0.0
    phase3_pages_count: int = 0

    # After refinement (Phase 3.1)
    phase31_separation: float = 0.0
    phase31_pages_count: int = 0

    # Improvement
    separation_delta: float = 0.0
    improvement_percent: float = 0.0

    # Constraint satisfaction
    constraints_applied: List[str] = field(default_factory=list)
    constraints_satisfied: int = 0
    constraints_violated: int = 0

    # Non-uniqueness preserved?
    unique_pages: int = 0
    non_uniqueness_preserved: bool = False


@dataclass
class EquivalenceTest:
    """Result of equivalence re-testing."""
    # Separation scores
    real_vs_scrambled: float = 0.0
    real_vs_synthetic_phase3: float = 0.0
    real_vs_synthetic_phase31: float = 0.0

    # Improvement
    phase3_to_phase31_delta: float = 0.0

    # Outcome determination
    outcome: EquivalenceOutcome = EquivalenceOutcome.NO_CHANGE

    # Thresholds
    equivalence_threshold: float = 0.30  # Below this = equivalence
    improvement_threshold: float = 0.10  # Improvement > this = meaningful

    def determine_outcome(self):
        """Determine the outcome based on separation scores."""
        self.phase3_to_phase31_delta = (
            self.real_vs_synthetic_phase3 - self.real_vs_synthetic_phase31
        )

        if self.real_vs_synthetic_phase31 < self.equivalence_threshold:
            self.outcome = EquivalenceOutcome.STRUCTURAL_EQUIVALENCE
        elif self.phase3_to_phase31_delta > self.improvement_threshold:
            self.outcome = EquivalenceOutcome.SEPARATION_REDUCED
        elif self.phase3_to_phase31_delta < -self.improvement_threshold:
            self.outcome = EquivalenceOutcome.DIVERGENCE
        else:
            self.outcome = EquivalenceOutcome.NO_CHANGE


@dataclass
class Phase31Findings:
    """Complete findings from Phase 3.1."""
    # Track A: Discriminative features
    features_discovered: List[DiscriminativeFeature] = field(default_factory=list)
    feature_importances: List[FeatureImportance] = field(default_factory=list)

    # Track B: Constraint formalization
    constraints_proposed: List[StructuralConstraint] = field(default_factory=list)
    constraints_validated: List[StructuralConstraint] = field(default_factory=list)
    constraints_rejected: List[StructuralConstraint] = field(default_factory=list)

    # Track C: Re-synthesis results
    refinement_results: Dict[str, RefinementResult] = field(default_factory=dict)

    # Track D: Equivalence testing
    equivalence_test: EquivalenceTest = field(default_factory=EquivalenceTest)

    # Termination
    structural_refinement_exhausted: bool = False
    termination_reason: str = ""

    # Success criteria
    discriminative_features_identified: bool = False
    formalization_documented: bool = False
    limits_demonstrated: bool = False
    principled_termination: bool = False

    def evaluate_success(self):
        """Evaluate Phase 3.1 success criteria."""
        self.discriminative_features_identified = len(self.features_discovered) > 0
        self.formalization_documented = (
            len(self.constraints_proposed) > 0 or
            len(self.constraints_rejected) > 0
        )
        self.limits_demonstrated = (
            self.equivalence_test.outcome != EquivalenceOutcome.STRUCTURAL_EQUIVALENCE or
            len(self.constraints_rejected) > 0
        )
        self.principled_termination = (
            self.structural_refinement_exhausted or
            self.equivalence_test.outcome == EquivalenceOutcome.STRUCTURAL_EQUIVALENCE
        )

    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary of findings."""
        return {
            "features_discovered": len(self.features_discovered),
            "top_features": [
                {"id": f.feature_id, "importance": f.importance_score}
                for f in sorted(
                    self.features_discovered,
                    key=lambda x: x.importance_score,
                    reverse=True
                )[:5]
            ],
            "constraints_proposed": len(self.constraints_proposed),
            "constraints_validated": len(self.constraints_validated),
            "constraints_rejected": len(self.constraints_rejected),
            "equivalence_outcome": self.equivalence_test.outcome.value,
            "phase3_separation": self.equivalence_test.real_vs_synthetic_phase3,
            "phase31_separation": self.equivalence_test.real_vs_synthetic_phase31,
            "improvement": self.equivalence_test.phase3_to_phase31_delta,
            "structural_refinement_exhausted": self.structural_refinement_exhausted,
            "termination_reason": self.termination_reason,
        }
