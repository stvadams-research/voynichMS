import os
from pathlib import Path
from typing import Union
from foundation.storage.interface import StorageInterface

class FileSystemStorage(StorageInterface):
    """
    Local file system storage implementation.
    """
    def __init__(self, base_path: Union[str, Path]):
        self.base_path = Path(base_path).resolve()
        if not self.base_path.exists():
            self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        full_path = (self.base_path / path).resolve()
        if not str(full_path).startswith(str(self.base_path)):
            raise ValueError(f"Path traversal attempt: {path}")
        return full_path

    def save(self, path: str, data: Union[bytes, str], overwrite: bool = False) -> Path:
        target = self._resolve(path)
        if target.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {path}")
        
        target.parent.mkdir(parents=True, exist_ok=True)
        
        mode = "wb" if isinstance(data, bytes) else "w"
        with open(target, mode) as f:
            f.write(data)
            
        return target

    def load(self, path: str, binary: bool = False) -> Union[bytes, str]:
        target = self._resolve(path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {path}")
            
        mode = "rb" if binary else "r"
        with open(target, mode) as f:
            return f.read()

    def exists(self, path: str) -> bool:
        return self._resolve(path).exists()
