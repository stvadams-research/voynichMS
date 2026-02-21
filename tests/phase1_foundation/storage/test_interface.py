from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

from phase1_foundation.storage.interface import StorageInterface


def test_storage_interface_cannot_be_instantiated_without_implementation():
    class IncompleteStorage(StorageInterface):
        pass

    with pytest.raises(TypeError):
        IncompleteStorage()


def test_storage_interface_concrete_subclass_contract():
    class InMemoryStorage(StorageInterface):
        def __init__(self):
            self._store = {}

        def save(self, path: str, data: bytes | str, overwrite: bool = False) -> Path:
            if not overwrite and path in self._store:
                raise FileExistsError(path)
            self._store[path] = data
            return Path(path)

        def load(self, path: str, binary: bool = False) -> bytes | str:
            return self._store[path]

        def exists(self, path: str) -> bool:
            return path in self._store

    storage = InMemoryStorage()
    saved = storage.save("artifact.txt", "payload")
    assert saved == Path("artifact.txt")
    assert storage.exists("artifact.txt")
    assert storage.load("artifact.txt") == "payload"
