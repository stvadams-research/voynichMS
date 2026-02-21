"""
Track D3: Structural Capacity Bounding

Derives bounds on what kinds of systems could theoretically satisfy the constraints.
Compares against known system classes.

Methodological note on circularity:
- Observed values are loaded from ``configs/phase2_analysis/anomaly_observed.json``.
- This module asks whether non-semantic systems could produce those values.
- It does not re-test whether those observed values are themselves anomalous.
- See governance/governance/METHODS_REFERENCE.md for the full cross-phase data-flow disclosure.
"""

import logging
import math
from dataclasses import dataclass
from typing import Any

from phase1_foundation.config import get_anomaly_observed_values
from phase2_analysis.anomaly.interface import CapacityBound, StructuralFeasibilityRegion

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

    def __init__(self):
        observed = get_anomaly_observed_values().get("capacity_bounding", {})
        self.observed_info_density_z = float(observed.get("info_density_z", 4.0))
        self.observed_locality_min = int(observed.get("locality_min", 2))
        self.observed_locality_max = int(observed.get("locality_max", 4))
        self.observed_repetition_rate = float(observed.get("repetition_rate", 0.20))
        self.observed_vocabulary_size = int(observed.get("vocabulary_size", 8000))
        self.bounds: list[CapacityBound] = []
        self.system_classes: list[SystemClass] = []
        self.feasibility_region: StructuralFeasibilityRegion = StructuralFeasibilityRegion()

    def derive_bounds(self) -> list[CapacityBound]:
        """
        Derive capacity bounds from observed constraints.
        """
        bounds = []

        # === LOWER BOUNDS ===

        # Memory lower bound: must store enough states for observed vocabulary.
        memory_bits = math.log2(max(2, self.observed_vocabulary_size))
        memory_lower = CapacityBound(
            property_name="memory",
            bound_type="lower",
            bound_value=round(memory_bits, 2),
            derived_from=["P22_C1 (info density)", "P22_C4 (vocabulary size)"],
            derivation_method=(
                f"log2(vocabulary_size={self.observed_vocabulary_size}) ≈ {memory_bits:.2f} bits"
            ),
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
            bound_value=float(self.observed_locality_max),
            derived_from=[f"P22_C2 (locality radius {self.observed_locality_min}-{self.observed_locality_max})"],
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

    def define_system_classes(self) -> list[SystemClass]:
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
                description="Natural phase7_human language",
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

    def evaluate_system_classes(self) -> list[SystemClass]:
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

            # Check info density overlap around observed anomaly value.
            lower_band = self.observed_info_density_z - 0.5
            upper_band = self.observed_info_density_z + 1.0
            if sc.info_density_range[1] < lower_band or sc.info_density_range[0] > upper_band:
                consistent = False
                reasons.append(
                    f"info density range {sc.info_density_range} doesn't match z={self.observed_info_density_z:.1f}"
                )

            # Check dependency depth
            depth_lower = next(
                (b for b in self.bounds
                 if b.property_name == "dependency_depth" and b.bound_type == "lower"),
                None
            )
            if depth_lower and sc.dependency_depth[1] < depth_lower.bound_value:
                consistent = False
                reasons.append("dependency depth too shallow")

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
            f"Memory capacity ≥ {math.log2(max(2, self.observed_vocabulary_size)):.1f} bits",
            "State complexity ≥ 16 states",
            "Dependency depth ≥ 2 levels",
            f"Locality radius ≤ {self.observed_locality_max} units",
            "Compositional complexity ≤ 3 levels",
            "Local compositional structure",
            f"Bounded vocabulary with moderate repetition (≈{self.observed_repetition_rate:.2f})",
        ]

        return region

    def analyze(self) -> dict[str, Any]:
        """Run full capacity bounding phase2_analysis."""
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

    def get_candidate_systems(self) -> list[str]:
        """Get list of system classes that remain viable."""
        return [sc.name for sc in self.system_classes if sc.consistent]
