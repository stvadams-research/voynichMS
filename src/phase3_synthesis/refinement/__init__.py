"""
Phase 3.1: Residual Structural Constraint Extraction

Closes the synthetic-real gap by:
1. Identifying discriminative features
2. Formalizing them as non-semantic constraints
3. Integrating into generators
4. Re-testing for equivalence

Goal: Exhaust reasonable structural explanations before any interpretive escalation.
"""

from phase3_synthesis.refinement.interface import (
    DiscriminativeFeature,
    FeatureImportance,
    StructuralConstraint,
    ConstraintStatus,
    RefinementResult,
    EquivalenceOutcome,
    EquivalenceTest,
    Phase31Findings,
)
from phase3_synthesis.refinement.feature_discovery import DiscriminativeFeatureDiscovery
from phase3_synthesis.refinement.constraint_formalization import ConstraintFormalization
from phase3_synthesis.refinement.resynthesis import RefinedGenerator, RefinedSynthesis
from phase3_synthesis.refinement.equivalence_testing import EquivalenceReTest, TerminationDecision

__all__ = [
    # Data structures
    "DiscriminativeFeature",
    "FeatureImportance",
    "StructuralConstraint",
    "ConstraintStatus",
    "RefinementResult",
    "EquivalenceOutcome",
    "EquivalenceTest",
    "Phase31Findings",
    # Analyzers
    "DiscriminativeFeatureDiscovery",
    "ConstraintFormalization",
    "RefinedGenerator",
    "RefinedSynthesis",
    "EquivalenceReTest",
    "TerminationDecision",
]
