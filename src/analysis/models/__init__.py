"""
Phase 2.3: Explicit Model Instantiation and Disconfirmation

This module provides infrastructure for defining, testing, and comparing
explicit falsifiable models within admissible explanation classes.

Models must satisfy:
- Explicit generative or organizational rules
- Defined inputs and outputs
- Testable predictions under perturbation
- Clear failure conditions
"""

from analysis.models.interface import (
    ExplicitModel,
    ModelPrediction,
    DisconfirmationResult,
    ModelStatus,
    PredictionType,
)
from analysis.models.registry import ModelRegistry
from analysis.models.disconfirmation import DisconfirmationEngine
from analysis.models.evaluation import CrossModelEvaluator, EvaluationMatrix

# Model implementations
from analysis.models.visual_grammar import (
    AdjacencyGrammarModel,
    ContainmentGrammarModel,
    DiagramAnnotationModel,
)
from analysis.models.constructed_system import (
    ProceduralGenerationModel,
    GlossalialSystemModel,
    MeaningfulConstructModel,
)

__all__ = [
    # Core interfaces
    "ExplicitModel",
    "ModelPrediction",
    "DisconfirmationResult",
    "ModelStatus",
    "PredictionType",
    # Infrastructure
    "ModelRegistry",
    "DisconfirmationEngine",
    "CrossModelEvaluator",
    "EvaluationMatrix",
    # Visual Grammar models
    "AdjacencyGrammarModel",
    "ContainmentGrammarModel",
    "DiagramAnnotationModel",
    # Constructed System models
    "ProceduralGenerationModel",
    "GlossalialSystemModel",
    "MeaningfulConstructModel",
]
