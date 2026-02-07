"""
Model Interface for Phase 2.3

Defines the base class and structures for explicit, falsifiable models.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class ModelStatus(Enum):
    """Status of a model after testing."""
    UNTESTED = "untested"
    SURVIVING = "surviving"      # Passed all tests so far
    FRAGILE = "fragile"          # Passed but with warnings
    FALSIFIED = "falsified"      # Failed disconfirmation
    DISCONTINUED = "discontinued"  # Removed from consideration


class PredictionType(Enum):
    """Types of predictions a model can make."""
    STRUCTURAL = "structural"    # About structure/organization
    STATISTICAL = "statistical"  # About distributions/frequencies
    RELATIONAL = "relational"    # About relationships between elements
    BEHAVIORAL = "behavioral"    # About behavior under perturbation


@dataclass
class ModelPrediction:
    """A testable prediction made by a model."""
    prediction_id: str
    prediction_type: PredictionType
    description: str
    test_method: str              # How to test this prediction
    success_criterion: str        # What constitutes success
    failure_criterion: str        # What constitutes failure

    # Results (filled after testing)
    tested: bool = False
    passed: bool = False
    actual_result: Optional[str] = None
    confidence: float = 0.0


@dataclass
class DisconfirmationResult:
    """Result of attempting to disconfirm a model."""
    model_id: str
    test_id: str
    perturbation_type: str

    # Outcome
    survived: bool
    failure_mode: Optional[str] = None
    degradation_score: float = 0.0  # 0 = no degradation, 1 = complete failure

    # Details
    metrics: Dict[str, float] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    notes: str = ""


class ExplicitModel(ABC):
    """
    Base class for explicit, falsifiable models in Phase 2.3.

    Every model must:
    1. Define its rules explicitly
    2. Make testable predictions
    3. Specify its failure conditions
    4. Be able to be falsified
    """

    def __init__(self, store):
        self.store = store
        self.status = ModelStatus.UNTESTED
        self.disconfirmation_log: List[DisconfirmationResult] = []

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Unique identifier for this model."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable name."""
        pass

    @property
    @abstractmethod
    def explanation_class(self) -> str:
        """Which explanation class this model belongs to."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Full description of the model."""
        pass

    @property
    @abstractmethod
    def rules(self) -> List[str]:
        """Explicit rules that define this model."""
        pass

    @property
    @abstractmethod
    def failure_conditions(self) -> List[str]:
        """Conditions under which this model is falsified."""
        pass

    @abstractmethod
    def get_predictions(self) -> List[ModelPrediction]:
        """Return testable predictions this model makes."""
        pass

    @abstractmethod
    def test_prediction(self, prediction: ModelPrediction,
                        dataset_id: str) -> ModelPrediction:
        """Test a specific prediction against data."""
        pass

    @abstractmethod
    def apply_perturbation(self, perturbation_type: str,
                           dataset_id: str, strength: float) -> DisconfirmationResult:
        """Apply a perturbation and evaluate model survival."""
        pass

    def record_disconfirmation(self, result: DisconfirmationResult):
        """Record a disconfirmation test result."""
        self.disconfirmation_log.append(result)

        # Update status based on result
        if not result.survived:
            self.status = ModelStatus.FALSIFIED
        elif result.degradation_score > 0.5:
            if self.status != ModelStatus.FALSIFIED:
                self.status = ModelStatus.FRAGILE

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the model and its test results."""
        predictions = self.get_predictions()
        tested_predictions = [p for p in predictions if p.tested]
        passed_predictions = [p for p in tested_predictions if p.passed]

        failed_disconfirmations = [d for d in self.disconfirmation_log if not d.survived]

        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "explanation_class": self.explanation_class,
            "status": self.status.value,
            "total_predictions": len(predictions),
            "tested_predictions": len(tested_predictions),
            "passed_predictions": len(passed_predictions),
            "disconfirmation_tests": len(self.disconfirmation_log),
            "failures": len(failed_disconfirmations),
            "rules": self.rules,
            "failure_conditions": self.failure_conditions,
        }
