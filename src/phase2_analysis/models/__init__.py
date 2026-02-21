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

from phase2_analysis.models.constructed_system import (
    GlossalialSystemModel,
    MeaningfulConstructModel,
    ProceduralGenerationModel,
)
from phase2_analysis.models.disconfirmation import DisconfirmationEngine
from phase2_analysis.models.evaluation import CrossModelEvaluator, EvaluationMatrix
from phase2_analysis.models.interface import (
    DisconfirmationResult,
    ExplicitModel,
    ModelPrediction,
    ModelStatus,
    PredictionType,
)
from phase2_analysis.models.registry import ModelRegistry

# Model implementations
from phase2_analysis.models.visual_grammar import (
    AdjacencyGrammarModel,
    ContainmentGrammarModel,
    DiagramAnnotationModel,
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
