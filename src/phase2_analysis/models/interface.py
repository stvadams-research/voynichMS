"""
Model Interface for Phase 2.3

Defines the base class and structures for explicit, falsifiable models.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import logging
logger = logging.getLogger(__name__)


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

    def test_and_update(self, prediction: ModelPrediction,
                        dataset_id: str) -> ModelPrediction:
        """
        Test a prediction and update model status accordingly.

        This is the recommended way to test predictions as it ensures
        status is properly updated after each test.

        Args:
            prediction: The prediction to test.
            dataset_id: Dataset to test against.

        Returns:
            The tested ModelPrediction with results filled in.
        """
        result = self.test_prediction(prediction, dataset_id)
        self.update_status_from_predictions()
        return result

    def test_all_predictions(self, dataset_id: str) -> List[ModelPrediction]:
        """
        Test all predictions and update model status.

        Args:
            dataset_id: Dataset to test against.

        Returns:
            List of tested ModelPredictions.
        """
        predictions = self.get_predictions()
        results = []
        for prediction in predictions:
            result = self.test_prediction(prediction, dataset_id)
            results.append(result)

        # Update status after all predictions are tested
        self.update_status_from_predictions()
        return results

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

    def update_status_from_predictions(self):
        """
        Update model status based on prediction test results.

        This ensures that failed predictions properly propagate to model status,
        providing symmetry between disconfirmation and prediction-based testing.
        """
        predictions = self.get_predictions()
        tested = [p for p in predictions if p.tested]
        failed = [p for p in tested if not p.passed]

        if not tested:
            return  # No predictions tested yet

        failure_rate = len(failed) / len(tested)

        # Update status based on failure rate
        if failure_rate > 0.5 and self.status != ModelStatus.FALSIFIED:
            # Majority of predictions failed - falsify the model
            self.status = ModelStatus.FALSIFIED
        elif failure_rate > 0 and self.status == ModelStatus.UNTESTED:
            # Some predictions failed - mark as fragile
            self.status = ModelStatus.FRAGILE
        elif failure_rate == 0 and self.status == ModelStatus.UNTESTED:
            # All predictions passed - mark as surviving
            self.status = ModelStatus.SURVIVING

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
