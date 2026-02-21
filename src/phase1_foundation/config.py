"""
Configuration for Foundation Layer

Feature flags to enable incremental rollout of real computations
replacing simulated implementations.

CRITICAL: REQUIRE_COMPUTED mode enforces that no simulated fallbacks are allowed.
When enabled, any simulation causes immediate pipeline failure.
"""

import json
import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ComputationMethod(Enum):
    """How a value was obtained."""
    COMPUTED = "computed"
    SIMULATED = "simulated"
    CACHED = "cached"


class SimulationViolationError(Exception):
    """
    Raised when simulation fallback occurs while REQUIRE_COMPUTED is enabled.

    This is a hard failure that prevents the pipeline from continuing.
    """
    def __init__(self, component: str, category: str, reason: str = ""):
        self.component = component
        self.category = category
        self.reason = reason
        super().__init__(
            f"SIMULATION VIOLATION: {component} (category: {category}) "
            f"attempted simulation fallback while REQUIRE_COMPUTED=1. {reason}"
        )


@dataclass
class ComputationRecord:
    """Record of a single computation."""
    component: str
    category: str
    method: ComputationMethod
    timestamp: datetime
    row_count: int = 0
    parameters: dict[str, Any] = field(default_factory=dict)
    details: str = ""


@dataclass
class CoverageReport:
    """
    Machine-readable report of computation coverage for a run.

    This proves what was actually computed vs simulated.
    """
    run_id: str
    timestamp: datetime
    require_computed: bool

    # Counts
    total_computed: int = 0
    total_simulated: int = 0
    total_cached: int = 0

    # Detailed records
    records: list[ComputationRecord] = field(default_factory=list)

    # Fallback components (should be empty if REQUIRE_COMPUTED)
    fallback_components: list[str] = field(default_factory=list)

    def add_record(self, record: ComputationRecord):
        """Add a computation record."""
        self.records.append(record)

        if record.method == ComputationMethod.COMPUTED:
            self.total_computed += 1
        elif record.method == ComputationMethod.SIMULATED:
            self.total_simulated += 1
            self.fallback_components.append(
                f"{record.component}:{record.category}"
            )
        elif record.method == ComputationMethod.CACHED:
            self.total_cached += 1

    def is_clean(self) -> bool:
        """Check if no simulations occurred."""
        return self.total_simulated == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "require_computed": self.require_computed,
            "summary": {
                "total_computed": self.total_computed,
                "total_simulated": self.total_simulated,
                "total_cached": self.total_cached,
                "is_clean": self.is_clean(),
            },
            "fallback_components": self.fallback_components,
            "records": [
                {
                    "component": r.component,
                    "category": r.category,
                    "method": r.method.value,
                    "timestamp": r.timestamp.isoformat(),
                    "row_count": r.row_count,
                    "parameters": r.parameters,
                    "details": r.details,
                }
                for r in self.records
            ],
        }


class ComputationTracker:
    """
    Thread-safe tracker for computation coverage.

    Enforces REQUIRE_COMPUTED mode and generates coverage reports.
    """
    _instance: Optional["ComputationTracker"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._thread_local = threading.local()
        self._require_computed = os.environ.get("REQUIRE_COMPUTED", "0") == "1"

    def _get_report(self) -> CoverageReport | None:
        """Get current thread's coverage report."""
        return getattr(self._thread_local, "report", None)

    def _set_report(self, report: CoverageReport | None):
        """Set current thread's coverage report."""
        self._thread_local.report = report

    @property
    def require_computed(self) -> bool:
        """Check if REQUIRE_COMPUTED mode is enabled."""
        return self._require_computed

    def set_require_computed(self, value: bool):
        """Set REQUIRE_COMPUTED mode (for testing)."""
        self._require_computed = value

    def start_run(self, run_id: str):
        """Start tracking a new run."""
        report = CoverageReport(
            run_id=run_id,
            timestamp=datetime.utcnow(),
            require_computed=self._require_computed,
        )
        self._set_report(report)

    def end_run(self) -> CoverageReport | None:
        """End the current run and return the coverage report."""
        report = self._get_report()
        self._set_report(None)
        return report

    def record_computation(
        self,
        component: str,
        category: str,
        method: ComputationMethod,
        row_count: int = 0,
        parameters: dict[str, Any] | None = None,
        details: str = "",
    ):
        """
        Record a computation.

        Raises SimulationViolationError if method is SIMULATED and
        REQUIRE_COMPUTED is enabled.
        """
        # Enforce REQUIRE_COMPUTED
        if method == ComputationMethod.SIMULATED and self._require_computed:
            raise SimulationViolationError(
                component=component,
                category=category,
                reason=details,
            )

        # Record if we have an active report
        report = self._get_report()
        if report:
            record = ComputationRecord(
                component=component,
                category=category,
                method=method,
                timestamp=datetime.utcnow(),
                row_count=row_count,
                parameters=parameters or {},
                details=details,
            )
            report.add_record(record)

    def record_computed(
        self,
        component: str,
        category: str,
        row_count: int = 0,
        parameters: dict[str, Any] | None = None,
    ):
        """Shorthand for recording a computed value."""
        self.record_computation(
            component=component,
            category=category,
            method=ComputationMethod.COMPUTED,
            row_count=row_count,
            parameters=parameters,
        )

    def record_simulated(
        self,
        component: str,
        category: str,
        reason: str = "",
    ):
        """
        Shorthand for recording a simulated value.

        WILL RAISE if REQUIRE_COMPUTED is enabled.
        """
        self.record_computation(
            component=component,
            category=category,
            method=ComputationMethod.SIMULATED,
            details=reason,
        )

    def get_current_report(self) -> CoverageReport | None:
        """Get the current run's coverage report (for inspection)."""
        return self._get_report()


# Global tracker instance
_tracker = ComputationTracker()


def get_tracker() -> ComputationTracker:
    """Get the global computation tracker."""
    return _tracker


def require_seed_if_strict(seed, component: str) -> None:
    """
    Raise if seed is None and REQUIRE_COMPUTED=1 is set.

    Call this at the top of any constructor or function that creates a
    ``random.Random(seed)`` instance from an Optional[int] seed parameter.
    In strict replication mode, every source of randomness must be
    explicitly seeded.
    """
    if seed is None and os.environ.get("REQUIRE_COMPUTED", "0") == "1":
        raise RuntimeError(
            f"No seed provided to {component} while REQUIRE_COMPUTED=1 is set. "
            "All randomness must be explicitly seeded for reproducibility."
        )


# Generation Constants
POSITIONAL_BIAS_PROBABILITY = 0.4
DEFAULT_SEED = 42

# Analysis Limits
MAX_PAGES_PER_TEST = 50
MAX_TOKENS_ANALYZED = 10000

SCRAMBLED_CONTROL_PARAMS = {
    "jar_count_range": (2, 6),
    "word_count_range": (40, 120),
    "mean_word_length": {"baseline": 5.0, "spread": 1.5},
    "repetition_rate": {"baseline": 0.10, "offset_min": -0.05, "offset_max": 0.15},
    "positional_entropy": {"baseline": 0.80, "offset_min": -0.10, "offset_max": 0.15},
    "locality_radius": {"baseline": 6.0, "offset_min": -1.0, "offset_max": 3.0},
    "information_density": {"baseline": 2.0, "offset_min": -0.5, "offset_max": 1.0},
    "layout_density_range": (5, 25)
}


# Feature flags for real vs simulated computations
# Set to True to enable real database-driven computations
# Set to False to use legacy simulated values
USE_REAL_COMPUTATIONS = {
    # Phase 1: Foundation Metrics
    "metrics": True,

    # Phase 2: Foundation Hypotheses
    "hypotheses": True,

    # Phase 3: Analysis Stress Tests
    "stress_tests": True,

    # Phase 4: Analysis Models
    "models": True,

    # Phase 5: Synthesis
    "phase3_synthesis": True,
}


def use_real_computation(category: str) -> bool:
    """
    Check if real computation should be used for a given category.

    Args:
        category: One of 'metrics', 'hypotheses', 'stress_tests', 'models', 'phase3_synthesis'

    Returns:
        True if real computation should be used, False for simulated

    Note: Even if this returns True, the actual computation might still
    fall back to simulation if data is missing. Use the ComputationTracker
    to record and enforce what actually happened.
    """
    return USE_REAL_COMPUTATIONS.get(category, False)


def _load_json_config(config_path: Path, config_label: str) -> dict[str, Any]:
    """
    Load JSON config with explicit missing-file policy.

    Policy is controlled by ``MISSING_CONFIG_POLICY``:
    - ``error`` (default): raise FileNotFoundError / ValueError.
    - ``warn``: log and return empty dict for backward compatibility.
    """
    policy = os.getenv("MISSING_CONFIG_POLICY", "error").strip().lower()

    if not config_path.exists():
        message = f"{config_label} config not found at {config_path}"
        if policy == "warn":
            logger.warning("%s; returning empty configuration due to warn policy.", message)
            return {}
        raise FileNotFoundError(
            f"{message}. Set MISSING_CONFIG_POLICY=warn to continue with empty defaults."
        )

    try:
        with open(config_path) as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        message = f"{config_label} config at {config_path} is invalid JSON"
        if policy == "warn":
            logger.warning("%s; returning empty configuration due to warn policy.", message)
            return {}
        raise ValueError(message) from exc


def get_model_params() -> dict[str, Any]:
    """
    Load externalized model parameters from JSON config.
    """
    config_path = Path("configs/phase6_functional/model_params.json")
    return _load_json_config(config_path, "Model params")


def get_analysis_thresholds() -> dict[str, Any]:
    """
    Load centralized phase2_analysis thresholds from JSON config.
    """
    config_path = Path("configs/phase2_analysis/thresholds.json")
    return _load_json_config(config_path, "Analysis thresholds")


def get_anomaly_observed_values() -> dict[str, Any]:
    """
    Load observed anomaly/reference values used as phase-input constants.
    """
    config_path = Path("configs/phase2_analysis/anomaly_observed.json")
    return _load_json_config(config_path, "Anomaly observed values")
