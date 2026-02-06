from abc import ABC, abstractmethod
from typing import List, Dict, Any
from foundation.storage.metadata import MetadataStore

class MetricResult:
    def __init__(self, metric_name: str, dataset_id: str, scope: str, value: float, details: Dict[str, Any] = None):
        self.metric_name = metric_name
        self.dataset_id = dataset_id
        self.scope = scope
        self.value = value
        self.details = details

class Metric(ABC):
    def __init__(self, store: MetadataStore):
        self.store = store

    @abstractmethod
    def calculate(self, dataset_id: str) -> List[MetricResult]:
        """
        Calculate the metric for a given dataset.
        """
        pass
