"""
Phase 2.4: Anomaly Characterization and Constraint Closure

This module characterizes the unresolved anomaly revealed by Phase 2.3:
high information density combined with universal model failure.

The anomaly is treated as data, not as a hint.
No semantics are introduced. No interpretations are proposed.
"""

from analysis.anomaly.interface import (
    AnomalyDefinition,
    ConstraintRecord,
    ConstraintIntersection,
    StabilityEnvelope,
    CapacityBound,
    SemanticNecessityResult,
    SemanticNecessity,
    Phase24Findings,
    StructuralFeasibilityRegion,
)
from analysis.anomaly.constraint_analysis import ConstraintIntersectionAnalyzer
from analysis.anomaly.stability_analysis import AnomalyStabilityAnalyzer
from analysis.anomaly.capacity_bounding import CapacityBoundingAnalyzer
from analysis.anomaly.semantic_necessity import SemanticNecessityAnalyzer

__all__ = [
    # Data structures
    "AnomalyDefinition",
    "ConstraintRecord",
    "ConstraintIntersection",
    "StabilityEnvelope",
    "CapacityBound",
    "SemanticNecessityResult",
    "SemanticNecessity",
    "Phase24Findings",
    "StructuralFeasibilityRegion",
    # Analyzers
    "ConstraintIntersectionAnalyzer",
    "AnomalyStabilityAnalyzer",
    "CapacityBoundingAnalyzer",
    "SemanticNecessityAnalyzer",
]
