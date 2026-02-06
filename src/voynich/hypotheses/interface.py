from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List
from voynich.storage.metadata import MetadataStore

@dataclass
class HypothesisResult:
    outcome: str # SUPPORTED, WEAKLY_SUPPORTED, NOT_SUPPORTED, FALSIFIED
    metrics: Dict[str, float]
    summary: Dict[str, Any]

class Hypothesis(ABC):
    def __init__(self, store: MetadataStore):
        self.store = store

    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def assumptions(self) -> str:
        pass

    @property
    @abstractmethod
    def falsification_criteria(self) -> str:
        pass

    @abstractmethod
    def run(self, real_dataset_id: str, control_dataset_ids: List[str]) -> HypothesisResult:
        """
        Run the hypothesis against real and control datasets.
        """
        pass
