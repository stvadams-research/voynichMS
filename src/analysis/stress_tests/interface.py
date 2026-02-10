"""
Stress Test Interface

Defines the base class and result structure for all Phase 2.2 stress tests.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import logging
logger = logging.getLogger(__name__)


class StressTestOutcome(Enum):
    """Possible outcomes of a stress test."""
    STABLE = "stable"                    # Mapping survives perturbation
    FRAGILE = "fragile"                  # Mapping degrades but doesn't collapse
    COLLAPSED = "collapsed"              # Mapping fails under perturbation
    INDISTINGUISHABLE = "indistinguishable"  # No better than controls
    INCONCLUSIVE = "inconclusive"        # Insufficient evidence


@dataclass
class StressTestResult:
    """Result of a stress test execution."""
    test_id: str
    explanation_class: str
    outcome: StressTestOutcome

    # Provenance
    run_id: Optional[str] = None
    timestamp: Optional[str] = None
    dataset_id: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Quantitative results
    stability_score: float = 0.0             # 0.0 (collapsed) to 1.0 (perfectly stable)
    control_differential: float = 0.0        # How much better than controls
    collapse_threshold: Optional[float] = None  # Perturbation level at which collapse occurs

    # Detailed findings
    metrics: Dict[str, float] = field(default_factory=dict)
    failure_cases: List[Dict[str, Any]] = field(default_factory=list)

    # Implications
    tightens_constraints: bool = False
    rules_out_class: bool = False
    constraint_implications: List[str] = field(default_factory=list)

    # Evidence chain
    evidence_refs: List[str] = field(default_factory=list)
    summary: str = ""


class StressTest(ABC):
    """
    Base class for all Phase 2.2 stress tests.

    Stress tests evaluate whether translation-like operations are
    structurally coherent for a given explanation class.
    """

    def __init__(self, store):
        """
        Initialize with metadata store.

        Args:
            store: MetadataStore instance for accessing Phase 1 data
        """
        self.store = store

    @property
    @abstractmethod
    def test_id(self) -> str:
        """Unique identifier for this test."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this test evaluates."""
        pass

    @property
    @abstractmethod
    def applicable_classes(self) -> List[str]:
        """Explanation classes this test applies to."""
        pass

    @abstractmethod
    def run(self, explanation_class: str, dataset_id: str,
            control_ids: List[str]) -> StressTestResult:
        """
        Execute the stress test.

        Args:
            explanation_class: The explanation class being tested
            dataset_id: Real dataset to test against
            control_ids: Control datasets for comparison

        Returns:
            StressTestResult with findings
        """
        pass

    def applies_to(self, explanation_class: str) -> bool:
        """Check if this test applies to the given explanation class."""
        return explanation_class in self.applicable_classes
