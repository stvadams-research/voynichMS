import logging
from abc import ABC, abstractmethod
from typing import Any, Literal

from phase1_foundation.core.profiling import timing_profile
from phase1_foundation.storage.metadata import MetadataStore

logger = logging.getLogger(__name__)


# Type for calculation method tracking
CalculationMethod = Literal["computed", "simulated", "cached"]


class MetricResult:
    """
    Result of a metric calculation.

    Attributes:
        metric_name: Name of the metric.
        dataset_id: Dataset this was calculated for.
        scope: Scope of the metric (e.g., "page", "region", "global").
        value: The computed metric value.
        details: Optional additional details as a dict.
        calculation_method: How the value was obtained:
            - "computed": Real computation from actual data
            - "simulated": Placeholder/fallback value (not real)
            - "cached": Loaded from a previous computation

    The calculation_method field enables auditing whether values are
    genuine computations or simulated placeholders.
    """
    def __init__(
        self,
        metric_name: str,
        dataset_id: str,
        scope: str,
        value: float,
        details: dict[str, Any] | None = None,
        calculation_method: CalculationMethod = "computed"
    ):
        self.metric_name = metric_name
        self.dataset_id = dataset_id
        self.scope = scope
        self.value = value
        self.details = details
        self.calculation_method = calculation_method

    def is_real(self) -> bool:
        """Check if this is a real computation (not simulated)."""
        return self.calculation_method == "computed"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "metric_name": self.metric_name,
            "dataset_id": self.dataset_id,
            "scope": self.scope,
            "value": self.value,
            "details": self.details,
            "calculation_method": self.calculation_method,
        }


class Metric(ABC):
    def __init__(self, store: MetadataStore):
        self.store = store

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if "calculate" in cls.__dict__:
            cls.calculate = timing_profile(cls.calculate)

    @abstractmethod
    def calculate(self, dataset_id: str) -> list[MetricResult]:
        """
        Calculate the metric for a given dataset.

        Implementations should set calculation_method appropriately:
        - "computed" for real calculations from data
        - "simulated" for placeholder values
        - "cached" for values loaded from storage
        """
        pass
