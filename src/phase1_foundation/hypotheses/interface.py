import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from phase1_foundation.storage.metadata import MetadataStore

logger = logging.getLogger(__name__)

class HypothesisOutcome(Enum):
    SUPPORTED = "SUPPORTED"
    WEAKLY_SUPPORTED = "WEAKLY_SUPPORTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    FALSIFIED = "FALSIFIED"
    INCONCLUSIVE = "INCONCLUSIVE"

@dataclass
class HypothesisResult:
    outcome: HypothesisOutcome
    metrics: dict[str, float]
    summary: dict[str, Any]

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
    def run(self, real_dataset_id: str, control_dataset_ids: list[str]) -> HypothesisResult:
        """
        Run the hypothesis against real and control datasets.
        """
        pass
