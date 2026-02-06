from abc import ABC, abstractmethod
from typing import Dict, Any
from voynich.storage.metadata import MetadataStore

class ControlGenerator(ABC):
    def __init__(self, store: MetadataStore):
        self.store = store

    @abstractmethod
    def generate(self, source_dataset_id: str, control_id: str, seed: int = 42, params: Dict[str, Any] = None) -> str:
        """
        Generate a control dataset.
        Returns the ID of the generated control dataset.
        """
        pass
