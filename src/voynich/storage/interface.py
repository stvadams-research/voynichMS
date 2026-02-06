from abc import ABC, abstractmethod
from typing import Any, BinaryIO, Optional
from pathlib import Path

class StorageInterface(ABC):
    """
    Abstract base class for storage backends.
    """
    
    @abstractmethod
    def save(self, path: str, data: bytes | str, overwrite: bool = False) -> Path:
        """
        Save data to the specified path.
        """
        pass

    @abstractmethod
    def load(self, path: str, binary: bool = False) -> bytes | str:
        """
        Load data from the specified path.
        """
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """
        Check if a path exists.
        """
        pass
