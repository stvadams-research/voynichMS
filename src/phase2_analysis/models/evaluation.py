"""
Cross-Model Evaluation for Phase 2.3

Compares models across tracks and produces phase8_comparative evaluation matrices.
"""

import logging
from dataclasses import dataclass
from typing import Any

from phase1_foundation.config import get_model_params
from phase2_analysis.models.interface import ExplicitModel, ModelStatus

logger = logging.getLogger(__name__)


@dataclass
class ModelComparison:
    """Result of comparing two models."""
    model_a_id: str
    model_b_id: str
    dimension: str
    model_a_score: float
    model_b_score: float
    winner: str  # model_a_id, model_b_id, or "tie"
    notes: str = ""


@dataclass
class EvaluationMatrix:
    """Comparative evaluation matrix for all models."""
    dimensions: list[str]
    models: list[str]
    scores: dict[str, dict[str, float]]  # model_id -> dimension -> score
    rankings: dict[str, list[str]]  # dimension -> ranked model IDs
    overall_ranking: list[tuple[str, float]]  # (model_id, overall_score)


class CrossModelEvaluator:
    """
    Evaluates and compares models across multiple dimensions.

    Evaluation dimensions:
    - Prediction accuracy: How many predictions passed
    - Robustness: How well it survives perturbations
    - Explanatory scope: How much it explains
    - Parsimony: Simplicity of rules
    - Falsifiability: How testable it is
    """

    DIMENSIONS = [
        "prediction_accuracy",
        "robustness",
        "explanatory_scope",
        "parsimony",
        "falsifiability",
    ]

    def __init__(self, models: list[ExplicitModel]):
        self.models = {m.model_id: m for m in models}

    def evaluate_model(self, model: ExplicitModel) -> dict[str, float]:
        """
        Evaluate a model across all dimensions.

        Returns:
            Dict mapping dimension to score (0-1)
        """
        scores = {}

        # Prediction accuracy
        predictions = model.get_predictions()
        tested = [p for p in predictions if p.tested]
        passed = [p for p in tested if p.passed]
        scores["prediction_accuracy"] = (
            len(passed) / len(tested) if tested else 0.0
        )

        # Robustness (inverse of average degradation)
        if model.disconfirmation_log:
            avg_degradation = sum(
                r.degradation_score for r in model.disconfirmation_log
            ) / len(model.disconfirmation_log)
            scores["robustness"] = 1.0 - avg_degradation
        else:
            scores["robustness"] = 0.5  # Untested

        # Explanatory scope (based on rule count and prediction count)
        rule_count = len(model.rules)
        pred_count = len(predictions)
        # More predictions = more explanatory scope
        scores["explanatory_scope"] = min(1.0, pred_count / 5.0)

        # Parsimony (fewer rules = better)
        scores["parsimony"] = max(0.0, 1.0 - (rule_count - 3) / 7.0)

        # Falsifiability (more failure conditions = more falsifiable)
        failure_count = len(model.failure_conditions)
        scores["falsifiability"] = min(1.0, failure_count / 4.0)

        return scores

    def generate_matrix(self) -> EvaluationMatrix:
        """Generate the full phase8_comparative evaluation matrix."""
        scores = {}

        for model_id, model in self.models.items():
            scores[model_id] = self.evaluate_model(model)

        # Generate rankings per dimension
        rankings = {}
        for dim in self.DIMENSIONS:
            dim_scores = [(mid, scores[mid][dim]) for mid in self.models]
            dim_scores.sort(key=lambda x: x[1], reverse=True)
            rankings[dim] = [mid for mid, _ in dim_scores]

        # Overall ranking (weighted average)
        params = get_model_params()
        weights = params.get("evaluation", {}).get("dimension_weights", {
            "prediction_accuracy": 0.30,
            "robustness": 0.25,
            "explanatory_scope": 0.20,
            "parsimony": 0.10,
            "falsifiability": 0.15,
        })

        overall = []
        for model_id in self.models:
            model_scores = scores[model_id]
            weighted_sum = sum(
                model_scores[dim] * weights[dim] for dim in self.DIMENSIONS
            )
            overall.append((model_id, weighted_sum))

        overall.sort(key=lambda x: x[1], reverse=True)

        return EvaluationMatrix(
            dimensions=self.DIMENSIONS,
            models=list(self.models.keys()),
            scores=scores,
            rankings=rankings,
            overall_ranking=overall,
        )

    def compare_models(self, model_a_id: str, model_b_id: str) -> list[ModelComparison]:
        """Compare two specific models across all dimensions."""
        model_a = self.models[model_a_id]
        model_b = self.models[model_b_id]

        scores_a = self.evaluate_model(model_a)
        scores_b = self.evaluate_model(model_b)

        comparisons = []
        for dim in self.DIMENSIONS:
            score_a = scores_a[dim]
            score_b = scores_b[dim]

            if score_a > score_b + 0.05:
                winner = model_a_id
            elif score_b > score_a + 0.05:
                winner = model_b_id
            else:
                winner = "tie"

            comparisons.append(ModelComparison(
                model_a_id=model_a_id,
                model_b_id=model_b_id,
                dimension=dim,
                model_a_score=score_a,
                model_b_score=score_b,
                winner=winner,
            ))

        return comparisons

    def get_surviving_models(self) -> list[ExplicitModel]:
        """Get models that have not been falsified."""
        return [
            m for m in self.models.values()
            if m.status not in [ModelStatus.FALSIFIED, ModelStatus.DISCONTINUED]
        ]

    def generate_report(self) -> dict[str, Any]:
        """Generate a comprehensive evaluation report."""
        matrix = self.generate_matrix()

        # Summary by explanation class
        by_class = {}
        for model_id, model in self.models.items():
            exp_class = model.explanation_class
            if exp_class not in by_class:
                by_class[exp_class] = {
                    "models": [],
                    "surviving": 0,
                    "falsified": 0,
                    "best_model": None,
                    "best_score": 0.0,
                }
            by_class[exp_class]["models"].append(model_id)

            if model.status in [ModelStatus.FALSIFIED, ModelStatus.DISCONTINUED]:
                by_class[exp_class]["falsified"] += 1
            else:
                by_class[exp_class]["surviving"] += 1

            # Track best model
            overall_score = dict(matrix.overall_ranking).get(model_id, 0)
            if overall_score > by_class[exp_class]["best_score"]:
                by_class[exp_class]["best_score"] = overall_score
                by_class[exp_class]["best_model"] = model_id

        return {
            "total_models": len(self.models),
            "surviving_models": len(self.get_surviving_models()),
            "falsified_models": len(self.models) - len(self.get_surviving_models()),
            "by_class": by_class,
            "overall_ranking": matrix.overall_ranking,
            "dimension_rankings": matrix.rankings,
            "all_scores": matrix.scores,
        }
