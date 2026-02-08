"""
Track D1: Constraint Intersection Analysis

Identifies which constraints jointly force model failure.
Computes minimal impossibility sets.
"""

from typing import Dict, List, Set, Any, Tuple
from itertools import combinations
from dataclasses import dataclass, field

from analysis.anomaly.interface import (
    ConstraintRecord,
    ConstraintIntersection,
    ConstraintSource,
    ConstraintType,
)


@dataclass
class ConstraintInteractionGraph:
    """
    Graph showing how constraints interact to exclude models.
    """
    constraints: List[ConstraintRecord]
    models: List[str]

    # Edges: which constraints exclude which models
    exclusions: Dict[str, Set[str]] = field(default_factory=dict)

    # Redundancy: constraints that add no exclusion power
    redundant_constraints: List[str] = field(default_factory=list)

    def build(self):
        """Build the interaction graph."""
        for c in self.constraints:
            self.exclusions[c.constraint_id] = set(c.excludes_models)

        # Find redundant constraints (whose exclusions are subsets of others)
        for c in self.constraints:
            c_exclusions = self.exclusions[c.constraint_id]
            for other in self.constraints:
                if other.constraint_id != c.constraint_id:
                    other_exclusions = self.exclusions[other.constraint_id]
                    if c_exclusions <= other_exclusions and c_exclusions != other_exclusions:
                        if c.constraint_id not in self.redundant_constraints:
                            self.redundant_constraints.append(c.constraint_id)


class ConstraintIntersectionAnalyzer:
    """
    Analyzes constraint intersections to find minimal impossibility sets.
    """

    def __init__(self):
        self.constraints: List[ConstraintRecord] = []
        self.models: List[str] = []
        self.all_intersections: List[ConstraintIntersection] = []
        self.minimal_sets: List[ConstraintIntersection] = []

    def load_constraints_from_phases(self) -> List[ConstraintRecord]:
        """
        Load all constraints from Phases 1-3.

        These are based on the findings from previous phases.
        """
        constraints = []

        # Phase 1 Constraints (from destructive audit)
        constraints.extend([
            ConstraintRecord(
                constraint_id="P1_C1",
                source=ConstraintSource.PHASE_1,
                constraint_type=ConstraintType.STRUCTURAL,
                description="Glyph identity is segmentation-dependent (37.5% collapse on shift)",
                excludes_models=["natural_language_fixed_alphabet"],
                threshold=0.20,
                observed_value=0.375,
            ),
            ConstraintRecord(
                constraint_id="P1_C2",
                source=ConstraintSource.PHASE_1,
                constraint_type=ConstraintType.STATISTICAL,
                description="Strong positional constraints (entropy 0.40)",
                excludes_models=["random_generation", "uniform_distribution"],
                threshold=0.60,
                observed_value=0.40,
            ),
            ConstraintRecord(
                constraint_id="P1_C3",
                source=ConstraintSource.PHASE_1,
                constraint_type=ConstraintType.BEHAVIORAL,
                description="Scrambled data shows >80% anchor degradation",
                excludes_models=["position_independent_encoding"],
                threshold=0.50,
                observed_value=0.80,
            ),
        ])

        # Phase 2.1 Constraints (from admissibility mapping)
        # Note: These are EXCLUSION_DECISION constraints, not STRUCTURAL constraints.
        # They represent Phase 2.1 decisions based on structural test failures,
        # not direct structural measurements.
        constraints.extend([
            ConstraintRecord(
                constraint_id="P21_C1",
                source=ConstraintSource.PHASE_2_1,
                constraint_type=ConstraintType.EXCLUSION_DECISION,
                description="Natural language models excluded based on structural test failures in Phase 2.1",
                excludes_models=[
                    "natural_language_latin",
                    "natural_language_germanic",
                    "natural_language_romance",
                    "natural_language_unknown",
                ],
            ),
            ConstraintRecord(
                constraint_id="P21_C2",
                source=ConstraintSource.PHASE_2_1,
                constraint_type=ConstraintType.EXCLUSION_DECISION,
                description="Enciphered language models excluded based on structural test failures in Phase 2.1",
                excludes_models=[
                    "simple_substitution_cipher",
                    "polyalphabetic_cipher",
                    "nomenclator",
                ],
            ),
        ])

        # Phase 2.2 Constraints (from stress tests)
        constraints.extend([
            ConstraintRecord(
                constraint_id="P22_C1",
                source=ConstraintSource.PHASE_2_2,
                constraint_type=ConstraintType.STATISTICAL,
                description="High information density (z=4.0)",
                excludes_models=[
                    "random_generation",
                    "cs_procedural_generation",  # Note: problematic but survived
                ],
                threshold=2.0,
                observed_value=4.0,
            ),
            ConstraintRecord(
                constraint_id="P22_C2",
                source=ConstraintSource.PHASE_2_2,
                constraint_type=ConstraintType.STRUCTURAL,
                description="Strong locality (radius 2-4)",
                excludes_models=["global_pattern_only", "no_locality"],
            ),
            ConstraintRecord(
                constraint_id="P22_C3",
                source=ConstraintSource.PHASE_2_2,
                constraint_type=ConstraintType.BEHAVIORAL,
                description="LOCAL_COMPOSITIONAL pattern detected",
                excludes_models=["pure_random", "pure_global"],
            ),
            ConstraintRecord(
                constraint_id="P22_C4",
                source=ConstraintSource.PHASE_2_2,
                constraint_type=ConstraintType.STATISTICAL,
                description="20% repetition rate with bounded vocabulary",
                excludes_models=["unbounded_vocabulary", "zero_repetition"],
            ),
        ])

        # Phase 2.3 Constraints (from model disconfirmation)
        constraints.extend([
            ConstraintRecord(
                constraint_id="P23_C1",
                source=ConstraintSource.PHASE_2_3,
                constraint_type=ConstraintType.BEHAVIORAL,
                description="Visual grammar models fail at anchor disruption (0.10 strength)",
                excludes_models=[
                    "vg_adjacency_grammar",
                    "vg_containment_grammar",
                    "vg_diagram_annotation",
                ],
                threshold=0.50,
                observed_value=0.84,
            ),
            ConstraintRecord(
                constraint_id="P23_C2",
                source=ConstraintSource.PHASE_2_3,
                constraint_type=ConstraintType.BEHAVIORAL,
                description="Glossolalia model fails at ordering perturbation",
                excludes_models=["cs_glossolalia"],
                threshold=0.60,
                observed_value=0.64,
            ),
            ConstraintRecord(
                constraint_id="P23_C3",
                source=ConstraintSource.PHASE_2_3,
                constraint_type=ConstraintType.BEHAVIORAL,
                description="Meaningful construct fails at omission/anchor tests",
                excludes_models=["cs_meaningful_construct"],
            ),
            ConstraintRecord(
                constraint_id="P23_C4",
                source=ConstraintSource.PHASE_2_3,
                constraint_type=ConstraintType.STATISTICAL,
                description="Procedural generation fails info density prediction",
                excludes_models=[],  # Survived but with caveat
                threshold=2.0,
                observed_value=4.0,
            ),
        ])

        return constraints

    def load_models(self) -> List[str]:
        """Load all models that were tested."""
        return [
            # Phase 2.3 explicit models
            "vg_adjacency_grammar",
            "vg_containment_grammar",
            "vg_diagram_annotation",
            "cs_procedural_generation",
            "cs_glossolalia",
            "cs_meaningful_construct",
            # Implicit models ruled out by Phase 2.1
            "natural_language_latin",
            "natural_language_germanic",
            "natural_language_romance",
            "natural_language_unknown",
            "simple_substitution_cipher",
            "polyalphabetic_cipher",
            "nomenclator",
            # Null models
            "random_generation",
            "uniform_distribution",
        ]

    def compute_intersection(self, constraint_ids: List[str]) -> ConstraintIntersection:
        """Compute the intersection of a set of constraints."""
        excluded = set()

        for cid in constraint_ids:
            for c in self.constraints:
                if c.constraint_id == cid:
                    excluded.update(c.excludes_models)
                    break

        return ConstraintIntersection(
            constraints=constraint_ids,
            excluded_models=excluded,
            exclusion_power=len(excluded) / max(1, len(self.models)),
        )

    def find_all_intersections(self) -> List[ConstraintIntersection]:
        """Find all constraint intersections."""
        results = []
        constraint_ids = [c.constraint_id for c in self.constraints]

        # Single constraints
        for cid in constraint_ids:
            results.append(self.compute_intersection([cid]))

        # Pairs
        for pair in combinations(constraint_ids, 2):
            results.append(self.compute_intersection(list(pair)))

        # Triples (limit to prevent explosion)
        for triple in combinations(constraint_ids, 3):
            results.append(self.compute_intersection(list(triple)))

        return results

    def find_minimal_impossibility_sets(self) -> List[ConstraintIntersection]:
        """
        Find minimal sets of constraints that exclude each model.

        A set is minimal if no proper subset has the same exclusion power.
        """
        minimal_sets = []

        # For each excluded model, find the smallest constraint set that excludes it
        all_excluded = set()
        for c in self.constraints:
            all_excluded.update(c.excludes_models)

        for model in all_excluded:
            # Find constraints that exclude this model
            excluding_constraints = [
                c.constraint_id for c in self.constraints
                if model in c.excludes_models
            ]

            if excluding_constraints:
                # The minimal set is just one constraint (any that excludes the model)
                minimal = ConstraintIntersection(
                    constraints=[excluding_constraints[0]],
                    excluded_models={model},
                    is_minimal=True,
                )
                minimal_sets.append(minimal)

        # Also find constraint combinations that together exclude all Phase 2.3 models
        phase23_models = {
            "vg_adjacency_grammar",
            "vg_containment_grammar",
            "vg_diagram_annotation",
            "cs_glossolalia",
            "cs_meaningful_construct",
        }

        # Find minimal set that excludes all Phase 2.3 failures
        for size in range(1, len(self.constraints) + 1):
            for combo in combinations([c.constraint_id for c in self.constraints], size):
                intersection = self.compute_intersection(list(combo))
                if phase23_models <= intersection.excluded_models:
                    intersection.is_minimal = True
                    minimal_sets.append(intersection)
                    break
            else:
                continue
            break

        return minimal_sets

    def analyze(self) -> Dict[str, Any]:
        """Run full constraint intersection analysis."""
        self.constraints = self.load_constraints_from_phases()
        self.models = self.load_models()

        # Build interaction graph
        graph = ConstraintInteractionGraph(
            constraints=self.constraints,
            models=self.models,
        )
        graph.build()

        # Find all intersections
        self.all_intersections = self.find_all_intersections()

        # Find minimal impossibility sets
        self.minimal_sets = self.find_minimal_impossibility_sets()

        # Compute constraint redundancy
        redundant = []
        for c in self.constraints:
            if not c.excludes_models:
                redundant.append(c.constraint_id)

        return {
            "total_constraints": len(self.constraints),
            "total_models": len(self.models),
            "total_intersections": len(self.all_intersections),
            "minimal_impossibility_sets": len(self.minimal_sets),
            "redundant_constraints": redundant,
            "graph_redundant": graph.redundant_constraints,
            "constraints_by_source": self._count_by_source(),
            "constraints_by_type": self._count_by_type(),
            "exclusion_summary": self._summarize_exclusions(),
        }

    def _count_by_source(self) -> Dict[str, int]:
        counts = {}
        for c in self.constraints:
            source = c.source.value
            counts[source] = counts.get(source, 0) + 1
        return counts

    def _count_by_type(self) -> Dict[str, int]:
        counts = {}
        for c in self.constraints:
            ctype = c.constraint_type.value
            counts[ctype] = counts.get(ctype, 0) + 1
        return counts

    def _summarize_exclusions(self) -> Dict[str, List[str]]:
        """Summarize which constraints exclude which models."""
        summary = {}
        for c in self.constraints:
            if c.excludes_models:
                summary[c.constraint_id] = c.excludes_models
        return summary
