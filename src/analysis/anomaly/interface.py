"""
Phase 2.4 Interface and Data Structures

Defines the core structures for anomaly characterization and constraint closure.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, Tuple
from enum import Enum


class ConstraintSource(Enum):
    """Source phase of a constraint."""
    PHASE_1 = "phase_1"
    PHASE_2_1 = "phase_2_1"
    PHASE_2_2 = "phase_2_2"
    PHASE_2_3 = "phase_2_3"


class ConstraintType(Enum):
    """Type of constraint."""
    STRUCTURAL = "structural"
    STATISTICAL = "statistical"
    BEHAVIORAL = "behavioral"
    RELATIONAL = "relational"


@dataclass
class AnomalyDefinition:
    """
    Formal definition of the Phase 2.3 anomaly.

    This is fixed for Phase 2.4 analysis.
    """
    information_density_z: float = 4.0
    locality_radius: Tuple[int, int] = (2, 4)
    robustness_under_perturbation: bool = True
    all_nonsemantic_models_failed: bool = True

    description: str = (
        "High information density (z≈4.0) combined with strong locality "
        "(2-4 units) and universal failure of non-semantic explicit models."
    )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "information_density_z": self.information_density_z,
            "locality_radius": self.locality_radius,
            "robustness_under_perturbation": self.robustness_under_perturbation,
            "all_nonsemantic_models_failed": self.all_nonsemantic_models_failed,
            "description": self.description,
        }


@dataclass
class ConstraintRecord:
    """A constraint from any phase."""
    constraint_id: str
    source: ConstraintSource
    constraint_type: ConstraintType
    description: str

    # Which models this constraint excludes
    excludes_models: List[str] = field(default_factory=list)

    # Quantitative measure if available
    threshold: Optional[float] = None
    observed_value: Optional[float] = None

    # Whether this constraint is active
    active: bool = True

    def violated_by(self, value: float) -> bool:
        """Check if a value violates this constraint."""
        if self.threshold is None:
            return False
        return value > self.threshold


@dataclass
class ConstraintIntersection:
    """
    Result of intersecting multiple constraints.

    Used in Track D1 to find minimal impossibility sets.
    """
    constraints: List[str]  # constraint IDs
    excluded_models: Set[str]
    is_minimal: bool = False  # True if no subset has same exclusion power

    # Metrics
    constraint_count: int = 0
    exclusion_power: float = 0.0  # fraction of models excluded

    def __post_init__(self):
        self.constraint_count = len(self.constraints)


@dataclass
class StabilityEnvelope:
    """
    Stability analysis result for the anomaly.

    Used in Track D2 to verify anomaly is not an artifact.
    """
    metric_name: str
    baseline_value: float

    # Values under different representations
    values_by_representation: Dict[str, float] = field(default_factory=dict)

    # Stability measures
    mean_value: float = 0.0
    std_dev: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0

    # Comparison to controls
    control_mean: float = 0.0
    control_std: float = 0.0
    separation_z: float = 0.0  # z-score of separation from controls

    # Assessment
    is_stable: bool = False
    stability_confidence: float = 0.0

    def compute_stability(self):
        """Compute stability metrics from values."""
        if not self.values_by_representation:
            return

        values = list(self.values_by_representation.values())
        self.mean_value = sum(values) / len(values)

        if len(values) > 1:
            variance = sum((v - self.mean_value) ** 2 for v in values) / len(values)
            self.std_dev = variance ** 0.5

        self.min_value = min(values)
        self.max_value = max(values)

        # Compute separation from controls
        if self.control_std > 0:
            self.separation_z = abs(self.mean_value - self.control_mean) / self.control_std

        # Stability assessment: stable if std_dev < 20% of mean
        # and separation from controls remains significant
        self.is_stable = (
            self.std_dev < 0.2 * abs(self.mean_value) and
            self.separation_z > 2.0
        )
        self.stability_confidence = max(0, 1 - self.std_dev / max(0.01, abs(self.mean_value)))


@dataclass
class CapacityBound:
    """
    Structural capacity bound for Track D3.

    Defines lower/upper bounds on system properties.
    """
    property_name: str
    bound_type: str  # "lower" or "upper"
    bound_value: float

    # Derivation
    derived_from: List[str] = field(default_factory=list)
    derivation_method: str = ""

    # Comparison to known systems
    comparable_systems: Dict[str, float] = field(default_factory=dict)

    # Assessment
    is_feasible: bool = True
    notes: str = ""


@dataclass
class StructuralFeasibilityRegion:
    """
    The region of structural properties that could explain the anomaly.

    Combines all capacity bounds from Track D3.
    """
    bounds: List[CapacityBound] = field(default_factory=list)

    # Excluded system classes
    excluded_classes: List[str] = field(default_factory=list)

    # Required properties (non-semantic)
    required_properties: List[str] = field(default_factory=list)

    # Feasibility assessment
    is_feasible: bool = True
    feasibility_notes: str = ""

    def add_bound(self, bound: CapacityBound):
        self.bounds.append(bound)

    def check_feasibility(self):
        """Check if all bounds are mutually consistent."""
        # Check for contradictions (lower > upper for same property)
        by_property = {}
        for b in self.bounds:
            if b.property_name not in by_property:
                by_property[b.property_name] = {"lower": None, "upper": None}
            by_property[b.property_name][b.bound_type] = b.bound_value

        for prop, bounds in by_property.items():
            if bounds["lower"] is not None and bounds["upper"] is not None:
                if bounds["lower"] > bounds["upper"]:
                    self.is_feasible = False
                    self.feasibility_notes = f"Contradiction: {prop} lower bound exceeds upper bound"
                    return


class SemanticNecessity(Enum):
    """Result of semantic necessity test."""
    NOT_NECESSARY = "not_necessary"  # Anomaly explainable without semantics
    POSSIBLY_NECESSARY = "possibly_necessary"  # Evidence inconclusive
    LIKELY_NECESSARY = "likely_necessary"  # Strong evidence for semantics
    DEFINITELY_NECESSARY = "definitely_necessary"  # No alternative


@dataclass
class SemanticNecessityResult:
    """
    Result of Track D4 semantic necessity test.

    Determines whether Phase 3 is justified.
    """
    assessment: SemanticNecessity

    # Non-semantic systems tested
    systems_tested: List[str] = field(default_factory=list)
    systems_failed: List[str] = field(default_factory=list)
    systems_passed: List[str] = field(default_factory=list)

    # Evidence
    evidence_for_semantics: List[str] = field(default_factory=list)
    evidence_against_semantics: List[str] = field(default_factory=list)

    # Confidence
    confidence: float = 0.0

    # Phase 3 justification
    phase_3_justified: bool = False
    justification: str = ""

    # Conditions under which semantics might be required
    semantic_conditions: List[str] = field(default_factory=list)

    def generate_decision(self):
        """Generate Phase 3 decision based on assessment."""
        if self.assessment == SemanticNecessity.DEFINITELY_NECESSARY:
            self.phase_3_justified = True
            self.justification = (
                "All non-semantic systems fail to explain the anomaly. "
                "Semantic content is structurally required."
            )
        elif self.assessment == SemanticNecessity.LIKELY_NECESSARY:
            self.phase_3_justified = True
            self.justification = (
                "Strong evidence that non-semantic systems are insufficient. "
                "Phase 3 semantic investigation is warranted."
            )
        elif self.assessment == SemanticNecessity.POSSIBLY_NECESSARY:
            self.phase_3_justified = False
            self.justification = (
                "Evidence is inconclusive. Additional structural analysis "
                "recommended before proceeding to Phase 3."
            )
        else:
            self.phase_3_justified = False
            self.justification = (
                "Anomaly is explainable without semantics. "
                "Phase 3 is not justified."
            )


@dataclass
class Phase24Findings:
    """
    Complete findings from Phase 2.4.
    """
    # Anomaly definition
    anomaly: AnomalyDefinition = field(default_factory=AnomalyDefinition)

    # Track D1: Constraint intersection
    constraints: List[ConstraintRecord] = field(default_factory=list)
    intersections: List[ConstraintIntersection] = field(default_factory=list)
    minimal_impossibility_sets: List[ConstraintIntersection] = field(default_factory=list)

    # Track D2: Stability analysis
    stability_envelopes: List[StabilityEnvelope] = field(default_factory=list)
    anomaly_confirmed: bool = False

    # Track D3: Structural capacity
    feasibility_region: StructuralFeasibilityRegion = field(
        default_factory=StructuralFeasibilityRegion
    )

    # Track D4: Semantic necessity
    semantic_necessity: SemanticNecessityResult = field(
        default_factory=lambda: SemanticNecessityResult(
            assessment=SemanticNecessity.POSSIBLY_NECESSARY
        )
    )

    # Overall conclusions
    phase_3_decision: bool = False
    termination_reason: str = ""

    def generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of all findings."""
        return {
            "anomaly": self.anomaly.as_dict(),
            "constraints_analyzed": len(self.constraints),
            "minimal_impossibility_sets": len(self.minimal_impossibility_sets),
            "anomaly_confirmed": self.anomaly_confirmed,
            "stability_metrics": len(self.stability_envelopes),
            "feasibility_region": {
                "bounds": len(self.feasibility_region.bounds),
                "is_feasible": self.feasibility_region.is_feasible,
                "excluded_classes": self.feasibility_region.excluded_classes,
            },
            "semantic_necessity": {
                "assessment": self.semantic_necessity.assessment.value,
                "confidence": self.semantic_necessity.confidence,
                "phase_3_justified": self.semantic_necessity.phase_3_justified,
            },
            "phase_3_decision": self.phase_3_decision,
            "termination_reason": self.termination_reason,
        }
