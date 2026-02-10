"""
Track D3: Structural Capacity Bounding

Derives bounds on what kinds of systems could theoretically satisfy the constraints.
Compares against known system classes.

Methodological note on circularity:
- ``OBSERVED_*`` constants are Phase 2.2/2.3 measurements used as INPUTS.
- This module asks whether non-semantic systems could produce those values.
- It does not re-test whether those observed values are themselves anomalous.
- See docs/METHODS_REFERENCE.md for the full cross-phase data-flow disclosure.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from analysis.anomaly.interface import CapacityBound, StructuralFeasibilityRegion
import logging
logger = logging.getLogger(__name__)


@dataclass
class SystemClass:
    """A known class of systems for comparison."""
    name: str
    description: str

    # Typical property ranges for this class
    memory_range: tuple = (0, 0)  # (min, max) in bits
    state_range: tuple = (0, 0)
    dependency_depth: tuple = (0, 0)
    locality_range: tuple = (0, 0)
    info_density_range: tuple = (0, 0)

    # Whether this class is consistent with observed constraints
    consistent: bool = False
    inconsistency_reason: str = ""


class CapacityBoundingAnalyzer:
    """
    Derives structural capacity bounds from observed constraints.
    """

    # Observed values from Phase 2.2/2.3
    OBSERVED_INFO_DENSITY_Z = 4.0
    OBSERVED_LOCALITY_MIN = 2
    OBSERVED_LOCALITY_MAX = 4
    OBSERVED_REPETITION_RATE = 0.20
    OBSERVED_VOCABULARY_SIZE = 8000  # approximate unique tokens

    def __init__(self):
        self.bounds: List[CapacityBound] = []
        self.system_classes: List[SystemClass] = []
        self.feasibility_region: StructuralFeasibilityRegion = StructuralFeasibilityRegion()

    def derive_bounds(self) -> List[CapacityBound]:
        """
        Derive capacity bounds from observed constraints.
        """
        bounds = []

        # === LOWER BOUNDS ===

        # Memory lower bound: must store enough states for observed info density
        # High info density (z=4.0) suggests significant state complexity
        memory_lower = CapacityBound(
            property_name="memory",
            bound_type="lower",
            bound_value=12.0,  # bits - log2(vocabulary_size) ~ 13 bits
            derived_from=["P22_C1 (info density)", "P22_C4 (vocabulary size)"],
            derivation_method="log2(vocabulary_size) = log2(8000) ≈ 13 bits",
            comparable_systems={
                "random_markov": 8.0,
                "natural_language": 15.0,
                "simple_cipher": 5.0,
            },
        )
        bounds.append(memory_lower)

        # State lower bound: locality implies local state dependencies
        state_lower = CapacityBound(
            property_name="state_complexity",
            bound_type="lower",
            bound_value=16.0,  # distinct states
            derived_from=["P22_C2 (locality)", "P22_C3 (compositional pattern)"],
            derivation_method="Locality radius 2-4 implies at least 4^2 = 16 distinguishable local states",
            comparable_systems={
                "markov_order_1": 8.0,
                "markov_order_2": 64.0,
                "natural_language": 1000.0,
            },
        )
        bounds.append(state_lower)

        # Dependency depth lower bound: compositional structure requires depth
        dependency_lower = CapacityBound(
            property_name="dependency_depth",
            bound_type="lower",
            bound_value=2.0,  # minimum depth
            derived_from=["P22_C3 (LOCAL_COMPOSITIONAL)"],
            derivation_method="Compositional pattern requires at least 2 levels of structure",
            comparable_systems={
                "flat_encoding": 1.0,
                "hierarchical_grammar": 4.0,
                "natural_language": 6.0,
            },
        )
        bounds.append(dependency_lower)

        # === UPPER BOUNDS ===

        # Locality upper bound: observed locality constrains global dependencies
        locality_upper = CapacityBound(
            property_name="locality_radius",
            bound_type="upper",
            bound_value=4.0,
            derived_from=["P22_C2 (locality radius 2-4)"],
            derivation_method="Direct observation from Phase 2.2",
            comparable_systems={
                "random_sequence": 0.0,  # no locality
                "natural_language": 8.0,  # longer range
                "local_grammar": 3.0,
            },
        )
        bounds.append(locality_upper)

        # Compositional complexity upper bound: patterns are local, not global
        complexity_upper = CapacityBound(
            property_name="compositional_complexity",
            bound_type="upper",
            bound_value=3.0,  # levels of nesting
            derived_from=["P22_C3 (LOCAL pattern)", "P23_C1 (anchor sensitivity)"],
            derivation_method="Local compositional pattern with anchor sensitivity suggests limited depth",
            comparable_systems={
                "flat_labels": 1.0,
                "simple_grammar": 2.0,
                "context_free_grammar": 5.0,
            },
        )
        bounds.append(complexity_upper)

        # Semantic dependency upper bound: non-semantic models still partially work
        semantic_upper = CapacityBound(
            property_name="semantic_dependency",
            bound_type="upper",
            bound_value=0.5,  # scale 0-1
            derived_from=["P23_C4 (procedural generation partial success)"],
            derivation_method="Procedural generation survives perturbation, suggesting semantics not fully required",
            comparable_systems={
                "random_nonsense": 0.0,
                "meaningful_text": 1.0,
                "glossolalia": 0.2,
            },
        )
        bounds.append(semantic_upper)

        return bounds

    def define_system_classes(self) -> List[SystemClass]:
        """
        Define known system classes for comparison.
        """
        classes = [
            SystemClass(
                name="random_markov_order_1",
                description="First-order Markov chain with random transitions",
                memory_range=(3, 8),
                state_range=(8, 64),
                dependency_depth=(1, 1),
                locality_range=(1, 1),
                info_density_range=(0.5, 1.5),
            ),
            SystemClass(
                name="random_markov_order_2",
                description="Second-order Markov chain",
                memory_range=(6, 12),
                state_range=(64, 256),
                dependency_depth=(1, 2),
                locality_range=(1, 2),
                info_density_range=(1.0, 2.5),
            ),
            SystemClass(
                name="constrained_markov",
                description="Markov chain with positional constraints",
                memory_range=(8, 14),
                state_range=(32, 128),
                dependency_depth=(1, 2),
                locality_range=(2, 4),
                info_density_range=(2.0, 3.5),
            ),
            SystemClass(
                name="glossolalia_human",
                description="Human-produced glossolalia (speaking in tongues)",
                memory_range=(10, 15),
                state_range=(50, 200),
                dependency_depth=(1, 3),
                locality_range=(2, 5),
                info_density_range=(2.5, 4.0),
            ),
            SystemClass(
                name="local_notation_system",
                description="Personal notation or indexing system",
                memory_range=(10, 16),
                state_range=(100, 500),
                dependency_depth=(2, 4),
                locality_range=(2, 6),
                info_density_range=(3.0, 5.0),
            ),
            SystemClass(
                name="simple_substitution_cipher",
                description="Monoalphabetic substitution cipher",
                memory_range=(4, 6),
                state_range=(26, 30),
                dependency_depth=(0, 0),
                locality_range=(0, 0),
                info_density_range=(4.0, 5.0),
            ),
            SystemClass(
                name="natural_language",
                description="Natural human language",
                memory_range=(12, 20),
                state_range=(500, 5000),
                dependency_depth=(3, 8),
                locality_range=(4, 15),
                info_density_range=(4.0, 6.0),
            ),
            SystemClass(
                name="diagram_label_system",
                description="Labels and annotations for diagrams",
                memory_range=(8, 14),
                state_range=(50, 500),
                dependency_depth=(1, 2),
                locality_range=(1, 3),
                info_density_range=(2.5, 4.5),
            ),
        ]

        return classes

    def evaluate_system_classes(self) -> List[SystemClass]:
        """
        Evaluate which system classes are consistent with observed bounds.
        """
        for sc in self.system_classes:
            consistent = True
            reasons = []

            # Check memory
            memory_lower = next(
                (b for b in self.bounds
                 if b.property_name == "memory" and b.bound_type == "lower"),
                None
            )
            if memory_lower and sc.memory_range[1] < memory_lower.bound_value:
                consistent = False
                reasons.append(f"memory too low ({sc.memory_range[1]} < {memory_lower.bound_value})")

            # Check locality
            locality_upper = next(
                (b for b in self.bounds
                 if b.property_name == "locality_radius" and b.bound_type == "upper"),
                None
            )
            if locality_upper and sc.locality_range[0] > locality_upper.bound_value:
                consistent = False
                reasons.append(f"locality too high ({sc.locality_range[0]} > {locality_upper.bound_value})")

            # Check info density (must overlap with observed z=4.0)
            if sc.info_density_range[1] < 3.5 or sc.info_density_range[0] > 5.0:
                consistent = False
                reasons.append(f"info density range {sc.info_density_range} doesn't match z=4.0")

            # Check dependency depth
            depth_lower = next(
                (b for b in self.bounds
                 if b.property_name == "dependency_depth" and b.bound_type == "lower"),
                None
            )
            if depth_lower and sc.dependency_depth[1] < depth_lower.bound_value:
                consistent = False
                reasons.append(f"dependency depth too shallow")

            sc.consistent = consistent
            sc.inconsistency_reason = "; ".join(reasons) if reasons else ""

        return self.system_classes

    def build_feasibility_region(self) -> StructuralFeasibilityRegion:
        """
        Build the structural feasibility region from bounds.
        """
        region = StructuralFeasibilityRegion()

        for b in self.bounds:
            region.add_bound(b)

        # Check feasibility
        region.check_feasibility()

        # Identify excluded classes
        for sc in self.system_classes:
            if not sc.consistent:
                region.excluded_classes.append(sc.name)

        # Derive required properties
        region.required_properties = [
            "Memory capacity ≥ 12 bits",
            "State complexity ≥ 16 states",
            "Dependency depth ≥ 2 levels",
            "Locality radius ≤ 4 units",
            "Compositional complexity ≤ 3 levels",
            "Local compositional structure",
            "Bounded vocabulary with moderate repetition",
        ]

        return region

    def analyze(self) -> Dict[str, Any]:
        """Run full capacity bounding analysis."""
        # Derive bounds
        self.bounds = self.derive_bounds()

        # Define and evaluate system classes
        self.system_classes = self.define_system_classes()
        self.evaluate_system_classes()

        # Build feasibility region
        self.feasibility_region = self.build_feasibility_region()

        # Summarize consistent vs excluded classes
        consistent_classes = [sc for sc in self.system_classes if sc.consistent]
        excluded_classes = [sc for sc in self.system_classes if not sc.consistent]

        return {
            "total_bounds": len(self.bounds),
            "lower_bounds": len([b for b in self.bounds if b.bound_type == "lower"]),
            "upper_bounds": len([b for b in self.bounds if b.bound_type == "upper"]),
            "system_classes_evaluated": len(self.system_classes),
            "consistent_classes": [sc.name for sc in consistent_classes],
            "excluded_classes": [
                {"name": sc.name, "reason": sc.inconsistency_reason}
                for sc in excluded_classes
            ],
            "feasibility_region": {
                "is_feasible": self.feasibility_region.is_feasible,
                "required_properties": self.feasibility_region.required_properties,
                "notes": self.feasibility_region.feasibility_notes,
            },
            "bounds_detail": [
                {
                    "property": b.property_name,
                    "type": b.bound_type,
                    "value": b.bound_value,
                    "derived_from": b.derived_from,
                }
                for b in self.bounds
            ],
        }

    def get_candidate_systems(self) -> List[str]:
        """Get list of system classes that remain viable."""
        return [sc.name for sc in self.system_classes if sc.consistent]
