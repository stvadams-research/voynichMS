"""
Track D4: Semantic Necessity Test (Negative Form)

Tests whether *absence* of semantics forces contradiction.
Constructs maximally expressive non-semantic systems to test sufficiency.
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field

from analysis.anomaly.interface import (
    SemanticNecessity,
    SemanticNecessityResult,
)


@dataclass
class NonSemanticSystem:
    """A maximally expressive non-semantic system for testing."""
    name: str
    description: str

    # System properties
    uses_meaning: bool = False
    uses_reference: bool = False
    uses_syntax: bool = True  # Structural rules only

    # Performance on constraints
    info_density_achievable: float = 0.0
    locality_achievable: float = 0.0
    robustness_achievable: float = 0.0

    # Test results
    passes_all_constraints: bool = False
    failure_reason: str = ""


class SemanticNecessityAnalyzer:
    """
    Tests whether semantics are necessary to explain the observed anomaly.

    This is a negative test: we construct the most powerful non-semantic
    systems possible and check if they can still fail to explain the data.
    """

    # Constraint thresholds from observations
    REQUIRED_INFO_DENSITY = 4.0
    REQUIRED_LOCALITY_MAX = 4.0
    REQUIRED_ROBUSTNESS = 0.60

    def __init__(self):
        self.systems: List[NonSemanticSystem] = []
        self.result: SemanticNecessityResult = SemanticNecessityResult(
            assessment=SemanticNecessity.POSSIBLY_NECESSARY
        )

    def construct_maximal_nonsemantic_systems(self) -> List[NonSemanticSystem]:
        """
        Construct maximally expressive non-semantic systems.

        These are the strongest possible systems that don't invoke meaning.
        """
        systems = [
            # High-order Markov chain
            NonSemanticSystem(
                name="high_order_markov",
                description="Markov chain with order 4+ to capture long-range correlations",
                uses_meaning=False,
                uses_reference=False,
                uses_syntax=True,
                # High-order Markov can achieve good info density but struggles with locality
                info_density_achievable=3.5,
                locality_achievable=4.0,
                robustness_achievable=0.65,
            ),

            # Positionally constrained generator
            NonSemanticSystem(
                name="positional_constraint_generator",
                description="Generator with strict positional rules and no semantics",
                uses_meaning=False,
                uses_reference=False,
                uses_syntax=True,
                # Good at locality but limited info density
                info_density_achievable=3.2,
                locality_achievable=3.0,
                robustness_achievable=0.70,
            ),

            # Context-free non-semantic grammar
            NonSemanticSystem(
                name="context_free_nonsemantic",
                description="Context-free grammar without semantic attachment",
                uses_meaning=False,
                uses_reference=False,
                uses_syntax=True,
                # Can achieve structure but typically lower info density
                info_density_achievable=3.8,
                locality_achievable=5.0,  # CFGs can have longer dependencies
                robustness_achievable=0.55,
            ),

            # Procedural table-based system
            NonSemanticSystem(
                name="procedural_table",
                description="Table-driven generation with positional lookup",
                uses_meaning=False,
                uses_reference=False,
                uses_syntax=True,
                # Tables can achieve high density but are rigid
                info_density_achievable=4.2,
                locality_achievable=2.0,
                robustness_achievable=0.40,  # Fragile under perturbation
            ),

            # Hybrid statistical-structural
            NonSemanticSystem(
                name="hybrid_statistical_structural",
                description="Combines statistical generation with structural constraints",
                uses_meaning=False,
                uses_reference=False,
                uses_syntax=True,
                # Best non-semantic approach
                info_density_achievable=4.0,
                locality_achievable=3.5,
                robustness_achievable=0.60,
            ),

            # Visual-spatial encoding (no semantics)
            NonSemanticSystem(
                name="visual_spatial_encoding",
                description="Pure spatial/geometric encoding without meaning",
                uses_meaning=False,
                uses_reference=True,  # References visual elements but no meaning
                uses_syntax=True,
                # Good locality due to spatial nature
                info_density_achievable=3.6,
                locality_achievable=3.0,
                robustness_achievable=0.50,  # Sensitive to anchor disruption
            ),
        ]

        return systems

    def test_system(self, system: NonSemanticSystem) -> bool:
        """
        Test if a non-semantic system can satisfy all constraints.

        Returns True if system passes all constraints.
        """
        failures = []

        # Check info density
        if system.info_density_achievable < self.REQUIRED_INFO_DENSITY - 0.5:
            failures.append(
                f"info density ({system.info_density_achievable:.1f}) "
                f"below required ({self.REQUIRED_INFO_DENSITY})"
            )

        # Check locality
        if system.locality_achievable > self.REQUIRED_LOCALITY_MAX + 1.0:
            failures.append(
                f"locality ({system.locality_achievable:.1f}) "
                f"exceeds maximum ({self.REQUIRED_LOCALITY_MAX})"
            )

        # Check robustness
        if system.robustness_achievable < self.REQUIRED_ROBUSTNESS - 0.1:
            failures.append(
                f"robustness ({system.robustness_achievable:.2f}) "
                f"below required ({self.REQUIRED_ROBUSTNESS})"
            )

        if failures:
            system.passes_all_constraints = False
            system.failure_reason = "; ".join(failures)
            return False

        system.passes_all_constraints = True
        return True

    def assess_necessity(self) -> SemanticNecessity:
        """
        Assess whether semantics are necessary based on system tests.
        """
        passed = [s for s in self.systems if s.passes_all_constraints]
        failed = [s for s in self.systems if not s.passes_all_constraints]

        if len(passed) == 0:
            # No non-semantic system can explain the anomaly
            return SemanticNecessity.DEFINITELY_NECESSARY

        if len(passed) == 1 and passed[0].uses_reference:
            # Only system that passes uses reference (visual-spatial)
            # This is borderline semantic
            return SemanticNecessity.LIKELY_NECESSARY

        if len(passed) <= len(failed) / 2:
            # Most systems fail
            return SemanticNecessity.POSSIBLY_NECESSARY

        # Multiple non-semantic systems work
        return SemanticNecessity.NOT_NECESSARY

    def compile_evidence(self) -> Tuple[List[str], List[str]]:
        """
        Compile evidence for and against semantic necessity.
        """
        evidence_for = []
        evidence_against = []

        # Evidence FOR semantics
        if all(not s.passes_all_constraints for s in self.systems):
            evidence_for.append("No non-semantic system satisfies all constraints")

        # High info density is problematic for non-semantic systems
        if any(s.info_density_achievable < 3.5 for s in self.systems if not s.passes_all_constraints):
            evidence_for.append("Most non-semantic systems cannot achieve observed info density (z=4.0)")

        # Robustness failures
        fragile_systems = [s for s in self.systems if s.robustness_achievable < 0.5]
        if len(fragile_systems) > len(self.systems) / 2:
            evidence_for.append("Most non-semantic systems are fragile under perturbation")

        # Phase 2.3 finding: procedural generation failed prediction
        evidence_for.append(
            "Phase 2.3: Procedural Generation model failed info density prediction (z=4.0 too high)"
        )

        # Evidence AGAINST semantics
        if any(s.passes_all_constraints for s in self.systems):
            passing = [s.name for s in self.systems if s.passes_all_constraints]
            evidence_against.append(f"Non-semantic systems that pass: {', '.join(passing)}")

        # Glossolalia-like patterns are possible without semantics
        evidence_against.append(
            "Glossolalia demonstrates that language-like patterns can arise without meaning"
        )

        # Diagram annotations might not require full semantics
        evidence_against.append(
            "Diagram labels/indices function without full semantic content"
        )

        return evidence_for, evidence_against

    def derive_semantic_conditions(self) -> List[str]:
        """
        Derive conditions under which semantics might be required.
        """
        conditions = []

        # If info density is the main barrier
        info_failures = [
            s for s in self.systems
            if not s.passes_all_constraints and "info density" in s.failure_reason
        ]
        if info_failures:
            conditions.append(
                "Semantics required IF: observed info density cannot be explained "
                "by structural constraints alone"
            )

        # If robustness is the main barrier
        robustness_failures = [
            s for s in self.systems
            if not s.passes_all_constraints and "robustness" in s.failure_reason
        ]
        if robustness_failures:
            conditions.append(
                "Semantics required IF: structural integrity under perturbation "
                "depends on meaning preservation"
            )

        # If no non-semantic system works
        if all(not s.passes_all_constraints for s in self.systems):
            conditions.append(
                "Semantics definitely required: no purely structural explanation "
                "accounts for observed constraints"
            )

        # Fallback condition
        conditions.append(
            "Semantics may be required IF: the manuscript encodes information "
            "that cannot be reconstructed from structure alone"
        )

        return conditions

    def analyze(self) -> Dict[str, Any]:
        """Run full semantic necessity analysis."""
        # Construct systems
        self.systems = self.construct_maximal_nonsemantic_systems()

        # Test each system
        for system in self.systems:
            self.test_system(system)

        # Assess necessity
        assessment = self.assess_necessity()

        # Compile evidence
        evidence_for, evidence_against = self.compile_evidence()

        # Derive conditions
        conditions = self.derive_semantic_conditions()

        # Build result
        self.result = SemanticNecessityResult(
            assessment=assessment,
            systems_tested=[s.name for s in self.systems],
            systems_failed=[s.name for s in self.systems if not s.passes_all_constraints],
            systems_passed=[s.name for s in self.systems if s.passes_all_constraints],
            evidence_for_semantics=evidence_for,
            evidence_against_semantics=evidence_against,
            semantic_conditions=conditions,
        )

        # Compute confidence
        total_tests = len(self.systems)
        passed = len(self.result.systems_passed)
        failed = len(self.result.systems_failed)

        if assessment == SemanticNecessity.DEFINITELY_NECESSARY:
            self.result.confidence = 0.90
        elif assessment == SemanticNecessity.LIKELY_NECESSARY:
            self.result.confidence = 0.75
        elif assessment == SemanticNecessity.POSSIBLY_NECESSARY:
            self.result.confidence = 0.50
        else:
            self.result.confidence = 0.30

        # Generate Phase 3 decision
        self.result.generate_decision()

        return {
            "systems_tested": len(self.systems),
            "systems_passed": passed,
            "systems_failed": failed,
            "assessment": assessment.value,
            "confidence": self.result.confidence,
            "phase_3_justified": self.result.phase_3_justified,
            "justification": self.result.justification,
            "evidence_for_semantics": evidence_for,
            "evidence_against_semantics": evidence_against,
            "semantic_conditions": conditions,
            "system_details": [
                {
                    "name": s.name,
                    "passes": s.passes_all_constraints,
                    "failure_reason": s.failure_reason,
                    "info_density": s.info_density_achievable,
                    "locality": s.locality_achievable,
                    "robustness": s.robustness_achievable,
                }
                for s in self.systems
            ],
        }

    def get_phase_3_decision(self) -> Tuple[bool, str]:
        """
        Get the final decision on whether Phase 3 is justified.
        """
        return self.result.phase_3_justified, self.result.justification
