"""
Phase 3: Pharmaceutical Section Continuation Synthesis

Gap-Constrained Structural Indistinguishability Study

This module tests whether structurally admissible pages can be generated
to fill physically plausible missing gaps in the pharmaceutical (jar) section
using only constraints derived from surviving pages.

All outputs are explicitly labeled SYNTHETIC.
No semantic assumptions are permitted.
Multiple non-unique continuations are required.
"""

from phase3_synthesis.interface import (
    SectionProfile,
    PageProfile,
    JarProfile,
    GapDefinition,
    GapStrength,
    ContinuationConstraints,
    SyntheticPage,
    ContinuationResult,
    IndistinguishabilityResult,
    Phase3Findings,
    GeneratorType,
)
from phase3_synthesis.profile_extractor import PharmaceuticalProfileExtractor
from phase3_synthesis.text_generator import TextContinuationGenerator, ConstrainedMarkovGenerator
from phase3_synthesis.gap_continuation import GapConditionedContinuation, MultiGapContinuation
from phase3_synthesis.indistinguishability import (
    IndistinguishabilityTester,
    FullIndistinguishabilityTest,
)

__all__ = [
    # Data structures
    "SectionProfile",
    "PageProfile",
    "JarProfile",
    "GapDefinition",
    "GapStrength",
    "ContinuationConstraints",
    "SyntheticPage",
    "ContinuationResult",
    "IndistinguishabilityResult",
    "Phase3Findings",
    "GeneratorType",
    # Profile extraction
    "PharmaceuticalProfileExtractor",
    # Text generation
    "TextContinuationGenerator",
    "ConstrainedMarkovGenerator",
    # Gap continuation
    "GapConditionedContinuation",
    "MultiGapContinuation",
    # Indistinguishability testing
    "IndistinguishabilityTester",
    "FullIndistinguishabilityTest",
]
