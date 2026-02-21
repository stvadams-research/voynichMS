"""
Phase 2.4: Anomaly Characterization and Constraint Closure

This module characterizes the unresolved anomaly revealed by Phase 2.3:
high information density combined with universal model failure.

The anomaly is treated as data, not as a hint.
No semantics are introduced. No interpretations are proposed.
"""

from phase2_analysis.anomaly.capacity_bounding import CapacityBoundingAnalyzer
from phase2_analysis.anomaly.constraint_analysis import ConstraintIntersectionAnalyzer
from phase2_analysis.anomaly.interface import (
    AnomalyDefinition,
    CapacityBound,
    ConstraintIntersection,
    ConstraintRecord,
    Phase24Findings,
    SemanticNecessity,
    SemanticNecessityResult,
    StabilityEnvelope,
    StructuralFeasibilityRegion,
)
from phase2_analysis.anomaly.semantic_necessity import SemanticNecessityAnalyzer
from phase2_analysis.anomaly.stability_analysis import AnomalyStabilityAnalyzer

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
