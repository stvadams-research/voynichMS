import os
import tempfile
from pathlib import Path
from typing import Union
from foundation.storage.interface import StorageInterface


class FileSystemStorage(StorageInterface):
    """
    Local file system storage implementation.

    Uses atomic writes (temp file + rename) to prevent partial/corrupted files
    on crash or interruption.
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
        """
        Save data to a file atomically.

        Uses a temporary file and atomic rename to ensure the file is never
        left in a partial/corrupted state, even on crash.

        Args:
            path: Relative path within the storage directory.
            data: Content to write (bytes or str).
            overwrite: If True, overwrite existing files. If False, raise FileExistsError.

        Returns:
            The absolute Path of the saved file.

        Raises:
            FileExistsError: If file exists and overwrite is False.
        """
        target = self._resolve(path)
        if target.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {path}")

        target.parent.mkdir(parents=True, exist_ok=True)

        mode = "wb" if isinstance(data, bytes) else "w"

        # Write to temporary file in the same directory (same filesystem for atomic rename)
        try:
            with tempfile.NamedTemporaryFile(
                mode=mode,
                dir=target.parent,
                delete=False,
                prefix=".tmp_",
                suffix="_" + target.name
            ) as tmp:
                tmp.write(data)
                tmp_path = tmp.name

            # Atomic rename (on POSIX systems; on Windows, replaces if exists)
            os.replace(tmp_path, target)
        except Exception:
            # Clean up temp file on failure
            try:
                if 'tmp_path' in locals():
                    os.unlink(tmp_path)
            except OSError:
                pass
            raise

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
