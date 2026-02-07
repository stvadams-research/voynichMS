"""
Model Registry for Phase 2.3

Maintains a registry of all explicit models being evaluated.
"""

from typing import Dict, List, Any, Type
from analysis.models.interface import ExplicitModel, ModelStatus


class ModelRegistry:
    """
    Registry for explicit models in Phase 2.3.

    Responsibilities:
    - Register and track models
    - Provide access to models by ID or class
    - Track model status changes
    - Generate registry reports
    """

    def __init__(self, store):
        self.store = store
        self._models: Dict[str, ExplicitModel] = {}
        self._by_class: Dict[str, List[str]] = {}

    def register(self, model_class: Type[ExplicitModel]) -> ExplicitModel:
        """
        Register a model class and return an instance.

        Args:
            model_class: The model class to register

        Returns:
            Instantiated model
        """
        model = model_class(self.store)
        model_id = model.model_id

        if model_id in self._models:
            raise ValueError(f"Model {model_id} already registered")

        self._models[model_id] = model

        # Track by explanation class
        exp_class = model.explanation_class
        if exp_class not in self._by_class:
            self._by_class[exp_class] = []
        self._by_class[exp_class].append(model_id)

        return model

    def get(self, model_id: str) -> ExplicitModel:
        """Get a model by ID."""
        if model_id not in self._models:
            raise KeyError(f"Model {model_id} not found")
        return self._models[model_id]

    def get_by_class(self, explanation_class: str) -> List[ExplicitModel]:
        """Get all models for an explanation class."""
        model_ids = self._by_class.get(explanation_class, [])
        return [self._models[mid] for mid in model_ids]

    def get_all(self) -> List[ExplicitModel]:
        """Get all registered models."""
        return list(self._models.values())

    def get_surviving(self) -> List[ExplicitModel]:
        """Get models that have not been falsified."""
        return [m for m in self._models.values()
                if m.status not in [ModelStatus.FALSIFIED, ModelStatus.DISCONTINUED]]

    def get_falsified(self) -> List[ExplicitModel]:
        """Get models that have been falsified."""
        return [m for m in self._models.values()
                if m.status == ModelStatus.FALSIFIED]

    def discontinue(self, model_id: str, reason: str):
        """Mark a model as discontinued."""
        model = self.get(model_id)
        model.status = ModelStatus.DISCONTINUED
        # Log reason (could be stored in model or separate log)

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive registry report."""
        all_models = self.get_all()

        by_status = {}
        for status in ModelStatus:
            by_status[status.value] = [
                m.model_id for m in all_models if m.status == status
            ]

        by_class = {}
        for exp_class, model_ids in self._by_class.items():
            by_class[exp_class] = {
                "total": len(model_ids),
                "surviving": len([mid for mid in model_ids
                                  if self._models[mid].status not in
                                  [ModelStatus.FALSIFIED, ModelStatus.DISCONTINUED]]),
                "falsified": len([mid for mid in model_ids
                                  if self._models[mid].status == ModelStatus.FALSIFIED]),
            }

        return {
            "total_models": len(all_models),
            "by_status": by_status,
            "by_class": by_class,
            "models": [m.get_summary() for m in all_models],
        }
