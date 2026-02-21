"""
Track D4: Semantic Necessity Test (Negative Form)

Tests whether *absence* of semantics forces contradiction.
Constructs maximally expressive non-semantic systems to test sufficiency.

IMPORTANT: This test should NOT pre-determine outcomes with hardcoded values.
Non-semantic systems are tested against actual stress test results.
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from phase2_analysis.anomaly.interface import (
    SemanticNecessity,
    SemanticNecessityResult,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from phase1_foundation.storage.metadata import MetadataStore


@dataclass
class NonSemanticSystem:
    """A maximally expressive non-semantic system for testing."""
    name: str
    description: str

    # System properties
    uses_meaning: bool = False
    uses_reference: bool = False
    uses_syntax: bool = True  # Structural rules only

    # Theoretical bounds - these are upper limits on what the system CAN achieve,
    # NOT predictions of what it WILL achieve. Actual performance is measured.
    max_info_density: float | None = None  # Upper bound on achievable density
    min_locality: float | None = None  # Lower bound on dependency radius
    max_robustness: float | None = None  # Upper bound on perturbation survival

    # Measured results (filled by actual testing)
    measured_info_density: float | None = None
    measured_locality: float | None = None
    measured_robustness: float | None = None

    # Test results
    passes_all_constraints: bool = False
    failure_reason: str = ""


class SemanticNecessityAnalyzer:
    """
    Tests whether semantics are necessary to explain the observed anomaly.

    This is a negative test: we construct the most powerful non-semantic
    systems possible and check if they can still fail to explain the data.

    IMPORTANT: This analyzer now uses actual measured thresholds from Phase 2.2
    stress tests, NOT hardcoded constants. This prevents circular reasoning.
    """

    def __init__(self, store: Optional["MetadataStore"] = None):
        """
        Initialize analyzer.

        Args:
            store: MetadataStore for running actual stress tests. If None,
                   uses theoretical bounds only (less rigorous).
        """
        self.store = store
        self.systems: list[NonSemanticSystem] = []
        self.result: SemanticNecessityResult = SemanticNecessityResult(
            assessment=SemanticNecessity.POSSIBLY_NECESSARY
        )

        # Thresholds are derived from Phase 2.2 measurements, not hardcoded
        # These will be populated by _load_measured_thresholds()
        self._observed_info_density: float | None = None
        self._observed_locality_radius: tuple[int, int] | None = None
        self._observed_robustness: float | None = None

    def _load_measured_thresholds(self, dataset_id: str) -> dict[str, float]:
        """
        Load actual measured thresholds from Phase 2.2 stress test results.

        These are the observed values from the real manuscript, which
        non-semantic systems must match or exceed to pass.
        """
        thresholds = {}

        if self.store is None:
            # Fallback: use default thresholds from AnomalyDefinition
            # These should be updated to match actual Phase 2.2 results
            thresholds["info_density"] = 4.0
            thresholds["locality_max"] = 4.0
            thresholds["robustness_min"] = 0.60
            return thresholds

        # Query actual Phase 2.2 results from the database
        session = self.store.Session()
        try:
            from phase1_foundation.storage.metadata import MetricResultRecord

            # Get information density z-score from Phase 2.2
            info_result = (
                session.query(MetricResultRecord)
                .filter_by(dataset_id=dataset_id, metric_name="information_density")
                .order_by(MetricResultRecord.created_at.desc())
                .first()
            )
            if info_result and info_result.details:
                thresholds["info_density"] = info_result.details.get("z_score", 4.0)
            else:
                thresholds["info_density"] = 4.0

            # Get locality radius from Phase 2.2
            locality_result = (
                session.query(MetricResultRecord)
                .filter_by(dataset_id=dataset_id, metric_name="locality_radius")
                .order_by(MetricResultRecord.created_at.desc())
                .first()
            )
            if locality_result and locality_result.value is not None:
                thresholds["locality_max"] = locality_result.value
            else:
                thresholds["locality_max"] = 4.0

            # Get robustness from Phase 2.2
            robustness_result = (
                session.query(MetricResultRecord)
                .filter_by(dataset_id=dataset_id, metric_name="mapping_stability")
                .order_by(MetricResultRecord.created_at.desc())
                .first()
            )
            if robustness_result and robustness_result.value is not None:
                thresholds["robustness_min"] = robustness_result.value
            else:
                thresholds["robustness_min"] = 0.60

        finally:
            session.close()

        self._observed_info_density = thresholds.get("info_density")
        self._observed_locality_radius = (2, int(thresholds.get("locality_max", 4)))
        self._observed_robustness = thresholds.get("robustness_min")

        return thresholds

    def construct_maximal_nonsemantic_systems(self) -> list[NonSemanticSystem]:
        """
        Construct maximally expressive non-semantic systems.

        These are the strongest possible systems that don't invoke meaning.
        Theoretical bounds are specified, but actual performance will be measured.
        """
        systems = [
            # High-order Markov chain
            NonSemanticSystem(
                name="high_order_markov",
                description="Markov chain with order 4+ to capture long-range correlations",
                uses_meaning=False,
                uses_reference=False,
                uses_syntax=True,
                # Theoretical bounds only - actual testing needed
                max_info_density=4.5,  # Can be high with enough context
                min_locality=3.0,  # Locality limited by Markov order
                max_robustness=0.70,  # Moderate robustness
            ),

            # Positionally constrained generator
            NonSemanticSystem(
                name="positional_constraint_generator",
                description="Generator with strict positional rules and no semantics",
                uses_meaning=False,
                uses_reference=False,
                uses_syntax=True,
                max_info_density=4.0,
                min_locality=2.0,  # Strong locality from positional constraints
                max_robustness=0.75,
            ),

            # Context-free non-semantic grammar
            NonSemanticSystem(
                name="context_free_nonsemantic",
                description="Context-free grammar without semantic attachment",
                uses_meaning=False,
                uses_reference=False,
                uses_syntax=True,
                max_info_density=4.2,
                min_locality=6.0,  # CFGs can have longer dependencies
                max_robustness=0.60,
            ),

            # Procedural table-based system
            NonSemanticSystem(
                name="procedural_table",
                description="Table-driven generation with positional lookup",
                uses_meaning=False,
                uses_reference=False,
                uses_syntax=True,
                max_info_density=5.0,  # Tables can encode anything
                min_locality=2.0,  # Very local lookups
                max_robustness=0.45,  # Fragile under perturbation
            ),

            # Hybrid statistical-structural
            NonSemanticSystem(
                name="hybrid_statistical_structural",
                description="Combines statistical generation with structural constraints",
                uses_meaning=False,
                uses_reference=False,
                uses_syntax=True,
                max_info_density=4.5,
                min_locality=3.0,
                max_robustness=0.65,
            ),

            # Visual-spatial encoding (no semantics)
            NonSemanticSystem(
                name="visual_spatial_encoding",
                description="Pure spatial/geometric encoding without meaning",
                uses_meaning=False,
                uses_reference=True,  # References visual elements but no meaning
                uses_syntax=True,
                max_info_density=4.0,
                min_locality=2.5,  # Good locality from spatial constraints
                max_robustness=0.55,  # Sensitive to anchor disruption
            ),
        ]

        return systems

    def _run_stress_tests_for_system(
        self, system: NonSemanticSystem, dataset_id: str, control_ids: list[str]
    ) -> dict[str, float]:
        """
        Run actual stress tests to measure system performance.

        This replaces hardcoded achievable values with real measurements.
        """
        if self.store is None:
            # No store available - use theoretical bounds as estimates
            return {
                "info_density": system.max_info_density or 3.0,
                "locality": system.min_locality or 5.0,
                "robustness": system.max_robustness or 0.5,
            }

        # Import stress tests
        from phase2_analysis.stress_tests.information_preservation import (
            InformationPreservationTest,
        )
        from phase2_analysis.stress_tests.locality import LocalityTest
        from phase2_analysis.stress_tests.mapping_stability import MappingStabilityTest

        results = {}

        # Run information preservation test
        info_test = InformationPreservationTest(self.store)
        info_result = info_test.run(
            explanation_class=system.name,
            dataset_id=dataset_id,
            control_ids=control_ids
        )
        results["info_density"] = info_result.metrics.get("z_score", 0)
        system.measured_info_density = results["info_density"]

        # Run locality test
        locality_test = LocalityTest(self.store)
        locality_result = locality_test.run(
            explanation_class=system.name,
            dataset_id=dataset_id,
            control_ids=control_ids
        )
        results["locality"] = locality_result.metrics.get("locality_radius", 5)
        system.measured_locality = results["locality"]

        # Run mapping stability test
        stability_test = MappingStabilityTest(self.store)
        stability_result = stability_test.run(
            explanation_class=system.name,
            dataset_id=dataset_id,
            control_ids=control_ids
        )
        results["robustness"] = stability_result.stability_score
        system.measured_robustness = results["robustness"]

        return results

    def test_system(
        self, system: NonSemanticSystem, thresholds: dict[str, float],
        dataset_id: str = "", control_ids: list[str] | None = None
    ) -> bool:
        """
        Test if a non-semantic system can satisfy all constraints.

        Now uses measured values from actual stress tests when available,
        falling back to theoretical bounds comparison otherwise.

        Returns True if system passes all constraints.
        """
        failures = []

        # Get required thresholds
        required_info_density = thresholds.get("info_density", 4.0)
        required_locality_max = thresholds.get("locality_max", 4.0)
        required_robustness = thresholds.get("robustness_min", 0.60)

        # Run actual stress tests if store is available
        if self.store and dataset_id:
            measured = self._run_stress_tests_for_system(
                system, dataset_id, control_ids or []
            )
            info_density = measured["info_density"]
            locality = measured["locality"]
            robustness = measured["robustness"]
        else:
            # Use theoretical bounds as upper limits
            info_density = system.max_info_density or 3.0
            locality = system.min_locality or 5.0
            robustness = system.max_robustness or 0.5

        # Tolerance margins for comparison
        info_density_margin = 0.5
        locality_margin = 1.0
        robustness_margin = 0.1

        # Check info density
        if info_density < required_info_density - info_density_margin:
            failures.append(
                f"info density ({info_density:.1f}) "
                f"below required ({required_info_density})"
            )

        # Check locality (lower is better - more local)
        if locality > required_locality_max + locality_margin:
            failures.append(
                f"locality ({locality:.1f}) "
                f"exceeds maximum ({required_locality_max})"
            )

        # Check robustness
        if robustness < required_robustness - robustness_margin:
            failures.append(
                f"robustness ({robustness:.2f}) "
                f"below required ({required_robustness})"
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

    def compile_evidence(self) -> tuple[list[str], list[str]]:
        """
        Compile evidence for and against semantic necessity.

        Uses measured values when available, theoretical bounds otherwise.
        """
        evidence_for = []
        evidence_against = []

        # Evidence FOR semantics
        if all(not s.passes_all_constraints for s in self.systems):
            evidence_for.append("No non-semantic system satisfies all constraints")

        # Check measured or theoretical info density
        for s in self.systems:
            if not s.passes_all_constraints:
                density = s.measured_info_density or s.max_info_density or 3.0
                if density < 3.5:
                    evidence_for.append(
                        f"{s.name}: cannot achieve observed info density "
                        f"(measured/max: {density:.1f}, required: ~4.0)"
                    )
                    break  # Only add once

        # Robustness failures - check measured or theoretical
        fragile_systems = []
        for s in self.systems:
            robustness = s.measured_robustness or s.max_robustness or 0.5
            if robustness < 0.5:
                fragile_systems.append(s)

        if len(fragile_systems) > len(self.systems) / 2:
            evidence_for.append("Most non-semantic systems are fragile under perturbation")

        # Only add Phase 2.3 finding if we have actual measured data
        if self._observed_info_density and self._observed_info_density > 3.5:
            evidence_for.append(
                f"Phase 2.2: Observed info density z={self._observed_info_density:.1f} "
                "exceeds what most non-semantic systems can achieve"
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

    def derive_semantic_conditions(self) -> list[str]:
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

    def analyze(
        self, dataset_id: str = "", control_ids: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Run full semantic necessity phase2_analysis.

        Args:
            dataset_id: Dataset to test against (uses measured thresholds).
            control_ids: Control datasets for comparison.
        """
        # Load measured thresholds from Phase 2.2 results
        thresholds = self._load_measured_thresholds(dataset_id)

        # Construct systems
        self.systems = self.construct_maximal_nonsemantic_systems()

        # Test each system against actual measured constraints
        for system in self.systems:
            self.test_system(system, thresholds, dataset_id, control_ids)

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

        # Compute confidence based on how decisively systems failed/passed
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
            "thresholds_used": thresholds,
            "system_details": [
                {
                    "name": s.name,
                    "passes": s.passes_all_constraints,
                    "failure_reason": s.failure_reason,
                    "theoretical_bounds": {
                        "max_info_density": s.max_info_density,
                        "min_locality": s.min_locality,
                        "max_robustness": s.max_robustness,
                    },
                    "measured_values": {
                        "info_density": s.measured_info_density,
                        "locality": s.measured_locality,
                        "robustness": s.measured_robustness,
                    },
                }
                for s in self.systems
            ],
        }

    def get_phase_3_decision(self) -> tuple[bool, str]:
        """
        Get the final decision on whether Phase 3 is justified.
        """
        return self.result.phase_3_justified, self.result.justification
