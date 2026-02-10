"""
Track D: Equivalence Re-Testing and Termination

Re-runs the full Phase 3 indistinguishability suite with refined synthetic pages
and determines the outcome.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import logging

from synthesis.interface import SectionProfile, SyntheticPage
from synthesis.indistinguishability import (
    IndistinguishabilityTester,
    FullIndistinguishabilityTest,
)
from synthesis.refinement.interface import (
    EquivalenceTest,
    EquivalenceOutcome,
)

logger = logging.getLogger(__name__)


class EquivalenceReTest:
    """
    Re-tests equivalence between real and refined synthetic pages.

    Compares:
    - Real vs Scrambled (should remain separable)
    - Real vs Phase 3 Synthetic (baseline)
    - Real vs Phase 3.1 Synthetic (refined)
    """

    def __init__(self, section_profile: SectionProfile):
        self.section_profile = section_profile
        self.equivalence_test = EquivalenceTest()

    def run_comparison(self,
                       phase3_pages: Dict[str, List[SyntheticPage]],
                       phase31_pages: Dict[str, List[SyntheticPage]]) -> EquivalenceTest:
        """
        Run full comparison suite.

        Args:
            phase3_pages: Original Phase 3 synthetic pages by gap
            phase31_pages: Refined Phase 3.1 synthetic pages by gap
        """
        # Flatten page lists
        phase3_all = []
        for pages in phase3_pages.values():
            phase3_all.extend(pages)

        phase31_all = []
        for pages in phase31_pages.values():
            phase31_all.extend(pages)

        # Run Phase 3 test
        tester_p3 = IndistinguishabilityTester(self.section_profile)
        tester_p3.load_real_pages()
        tester_p3.load_synthetic_pages(phase3_all)
        tester_p3.generate_scrambled_controls(count=len(phase3_all))

        result_p3 = tester_p3.run_test("phase3_comparison")

        # Run Phase 3.1 test
        tester_p31 = IndistinguishabilityTester(self.section_profile)
        tester_p31.load_real_pages()
        tester_p31.load_synthetic_pages(phase31_all)
        tester_p31.generate_scrambled_controls(count=len(phase31_all))

        result_p31 = tester_p31.run_test("phase31_comparison")

        # Compile results
        self.equivalence_test.real_vs_scrambled = result_p31.real_vs_scrambled_separation
        self.equivalence_test.real_vs_synthetic_phase3 = result_p3.real_vs_synthetic_separation
        self.equivalence_test.real_vs_synthetic_phase31 = result_p31.real_vs_synthetic_separation

        # Determine outcome
        self.equivalence_test.determine_outcome()

        return self.equivalence_test

    def get_detailed_comparison(self,
                                phase3_pages: Dict[str, List[SyntheticPage]],
                                phase31_pages: Dict[str, List[SyntheticPage]]) -> Dict[str, Any]:
        """Get detailed per-gap comparison."""
        comparisons = {}

        for gap_id in set(phase3_pages.keys()) | set(phase31_pages.keys()):
            p3_pages = phase3_pages.get(gap_id, [])
            p31_pages = phase31_pages.get(gap_id, [])

            # Test Phase 3 for this gap
            tester_p3 = IndistinguishabilityTester(self.section_profile)
            tester_p3.load_real_pages()
            tester_p3.load_synthetic_pages(p3_pages)
            tester_p3.generate_scrambled_controls(count=max(5, len(p3_pages)))
            result_p3 = tester_p3.run_test(f"{gap_id}_p3")

            # Test Phase 3.1 for this gap
            tester_p31 = IndistinguishabilityTester(self.section_profile)
            tester_p31.load_real_pages()
            tester_p31.load_synthetic_pages(p31_pages)
            tester_p31.generate_scrambled_controls(count=max(5, len(p31_pages)))
            result_p31 = tester_p31.run_test(f"{gap_id}_p31")

            comparisons[gap_id] = {
                "phase3_pages": len(p3_pages),
                "phase31_pages": len(p31_pages),
                "phase3_separation": result_p3.real_vs_synthetic_separation,
                "phase31_separation": result_p31.real_vs_synthetic_separation,
                "improvement": result_p3.real_vs_synthetic_separation - result_p31.real_vs_synthetic_separation,
            }

        return comparisons


class TerminationDecision:
    """
    Makes the termination decision for Phase 3.1.
    """

    def __init__(self, equivalence_test: EquivalenceTest,
                 constraints_validated: int,
                 constraints_rejected: int):
        self.equivalence_test = equivalence_test
        self.constraints_validated = constraints_validated
        self.constraints_rejected = constraints_rejected

    def should_terminate(self) -> tuple:
        """
        Determine if Phase 3.1 should terminate.

        Returns (should_terminate, reason).
        """
        outcome = self.equivalence_test.outcome

        if outcome == EquivalenceOutcome.STRUCTURAL_EQUIVALENCE:
            return True, (
                "Structural equivalence achieved. Real vs synthetic separation "
                f"reduced to {self.equivalence_test.real_vs_synthetic_phase31:.3f}, "
                "below threshold of 0.30. Non-semantic structural constraints "
                "fully capture manuscript properties."
            )

        if outcome == EquivalenceOutcome.SEPARATION_REDUCED:
            delta = self.equivalence_test.phase3_to_phase31_delta
            if delta > 0.20:
                return False, (
                    f"Significant improvement achieved (delta = {delta:.3f}). "
                    "Additional constraint refinement may close remaining gap."
                )
            else:
                return True, (
                    f"Separation reduced but diminishing returns (delta = {delta:.3f}). "
                    "Additional refinement unlikely to achieve equivalence. "
                    "Remaining gap may require more complex structural modeling."
                )

        if outcome == EquivalenceOutcome.NO_CHANGE:
            if self.constraints_rejected > self.constraints_validated:
                return True, (
                    "Most constraint formalizations were rejected. "
                    "Discriminative features cannot be expressed as enforceable "
                    "non-semantic constraints. Structural refinement exhausted."
                )
            else:
                return True, (
                    "Constraints integrated but no improvement in separation. "
                    "Identified features do not explain the real-synthetic gap. "
                    "Additional structural exploration may be needed."
                )

        if outcome == EquivalenceOutcome.DIVERGENCE:
            return True, (
                "Separation increased after refinement (unexpected). "
                "Constraints may be incorrectly specified. "
                "Review constraint formalization before continuing."
            )

        return True, "Unknown outcome - terminating for safety."

    def get_final_statement(self) -> str:
        """Generate the final termination statement."""
        should_term, reason = self.should_terminate()

        if self.equivalence_test.outcome == EquivalenceOutcome.STRUCTURAL_EQUIVALENCE:
            return (
                "We have achieved structural equivalence between real and synthetic pages. "
                "The manuscript's distinguishing properties can be captured entirely through "
                "non-semantic structural constraints."
            )
        else:
            return (
                "We have exhausted reasonable non-semantic structural refinement. "
                f"Final separation: {self.equivalence_test.real_vs_synthetic_phase31:.3f}. "
                f"Improvement from Phase 3: {self.equivalence_test.phase3_to_phase31_delta:.3f}. "
                "Any remaining gap may require either more complex structural modeling "
                "or, if proven necessary, semantic investigation."
            )
