"""
Disconfirmation Engine for Phase 2.3

Actively attempts to break models through systematic perturbation testing.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import logging
from phase2_analysis.models.interface import (
    ExplicitModel,
    DisconfirmationResult,
    ModelStatus,
)
from phase1_foundation.config import get_model_params

logger = logging.getLogger(__name__)


@dataclass
class PerturbationConfig:
    """Configuration for a perturbation test."""
    perturbation_type: str
    description: str
    strength_levels: List[float]
    failure_threshold: float  # Degradation above this = failure


class DisconfirmationEngine:
    """
    Engine for systematically attempting to falsify models.

    Per Phase 2.3 principles:
    - Models that require parameter tuning to survive are considered failed
    - Failures must be catastrophic or graceful
    - All failures are logged with evidence
    """

    # Standard perturbation battery
    PERTURBATION_BATTERY = [
        PerturbationConfig(
            perturbation_type="segmentation",
            description="Shift word/glyph boundaries",
            strength_levels=[0.05, 0.10, 0.15],
            failure_threshold=0.6
        ),
        PerturbationConfig(
            perturbation_type="ordering",
            description="Reorder elements within context",
            strength_levels=[0.10, 0.20, 0.30],
            failure_threshold=0.6
        ),
        PerturbationConfig(
            perturbation_type="omission",
            description="Remove elements",
            strength_levels=[0.05, 0.10, 0.20],
            failure_threshold=0.7
        ),
        PerturbationConfig(
            perturbation_type="anchor_disruption",
            description="Disrupt text-region anchors",
            strength_levels=[0.10, 0.25, 0.50],
            failure_threshold=0.5
        ),
    ]

    def __init__(self, store, perturbation_battery: List[PerturbationConfig] | None = None):
        self.store = store
        self.perturbation_battery = perturbation_battery or self._load_perturbation_battery()

    def _load_perturbation_battery(self) -> List[PerturbationConfig]:
        """Load perturbation battery from config when available."""
        params = get_model_params()
        configured = params.get("disconfirmation", {}).get("perturbation_battery", [])
        if not configured:
            return list(self.PERTURBATION_BATTERY)

        battery: List[PerturbationConfig] = []
        for item in configured:
            try:
                battery.append(
                    PerturbationConfig(
                        perturbation_type=str(item["perturbation_type"]),
                        description=str(item.get("description", item["perturbation_type"])),
                        strength_levels=[float(v) for v in item.get("strength_levels", [])],
                        failure_threshold=float(item.get("failure_threshold", 0.6)),
                    )
                )
            except (KeyError, TypeError, ValueError):
                logger.warning("Invalid perturbation config entry; skipping: %s", item)
        return battery or list(self.PERTURBATION_BATTERY)

    def run_full_battery(self, model: ExplicitModel,
                         dataset_id: str) -> List[DisconfirmationResult]:
        """
        Run the full perturbation battery against a model.

        Args:
            model: The model to test
            dataset_id: Dataset to use for testing

        Returns:
            List of disconfirmation results
        """
        results = []

        for config in self.perturbation_battery:
            for strength in config.strength_levels:
                result = self._run_perturbation(
                    model, dataset_id, config, strength
                )
                results.append(result)
                model.record_disconfirmation(result)

                # Stop testing this perturbation type if model failed
                if not result.survived:
                    break

        return results

    def _run_perturbation(self, model: ExplicitModel, dataset_id: str,
                          config: PerturbationConfig, strength: float) -> DisconfirmationResult:
        """Run a single perturbation test."""
        test_id = f"{config.perturbation_type}_{strength:.2f}"

        # Apply perturbation through model's interface
        result = model.apply_perturbation(
            config.perturbation_type, dataset_id, strength
        )

        # Check against failure threshold
        if result.degradation_score > config.failure_threshold:
            result.survived = False
            result.failure_mode = (
                f"Degradation {result.degradation_score:.2f} exceeds "
                f"threshold {config.failure_threshold:.2f}"
            )

        return result

    def run_prediction_tests(self, model: ExplicitModel,
                             dataset_id: str) -> Dict[str, Any]:
        """
        Test all predictions a model makes.

        Returns:
            Summary of prediction test results
        """
        predictions = model.get_predictions()
        results = []

        for pred in predictions:
            tested_pred = model.test_prediction(pred, dataset_id)
            results.append({
                "prediction_id": tested_pred.prediction_id,
                "description": tested_pred.description,
                "passed": tested_pred.passed,
                "actual_result": tested_pred.actual_result,
                "confidence": tested_pred.confidence,
            })

        passed = sum(1 for r in results if r["passed"])
        failed = len(results) - passed

        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(results) if results else 0,
            "predictions": results,
        }

    def generate_disconfirmation_log(self, model: ExplicitModel) -> Dict[str, Any]:
        """Generate a disconfirmation log for a model."""
        log = model.disconfirmation_log

        by_type = {}
        for result in log:
            ptype = result.perturbation_type
            if ptype not in by_type:
                by_type[ptype] = {"tests": 0, "survived": 0, "failed": 0}
            by_type[ptype]["tests"] += 1
            if result.survived:
                by_type[ptype]["survived"] += 1
            else:
                by_type[ptype]["failed"] += 1

        failures = [r for r in log if not r.survived]

        return {
            "model_id": model.model_id,
            "total_tests": len(log),
            "total_survived": sum(1 for r in log if r.survived),
            "total_failed": len(failures),
            "by_perturbation_type": by_type,
            "failures": [
                {
                    "test_id": f.test_id,
                    "perturbation_type": f.perturbation_type,
                    "failure_mode": f.failure_mode,
                    "degradation": f.degradation_score,
                }
                for f in failures
            ],
            "final_status": model.status.value,
        }
