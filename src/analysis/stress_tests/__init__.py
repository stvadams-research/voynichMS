"""
Phase 2.2: Stress Tests for Constraint Tightening

This module provides infrastructure for testing whether translation-like
or mapping-based operations are structurally coherent for admissible
explanation classes.

Three tracks:
- B1: Mapping Stability Tests
- B2: Information Preservation Tests
- B3: Locality and Compositionality Tests
"""

from analysis.stress_tests.interface import StressTest, StressTestResult
from analysis.stress_tests.mapping_stability import MappingStabilityTest
from analysis.stress_tests.information_preservation import InformationPreservationTest
from analysis.stress_tests.locality import LocalityTest

__all__ = [
    "StressTest",
    "StressTestResult",
    "MappingStabilityTest",
    "InformationPreservationTest",
    "LocalityTest",
]
