from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

from phase1_foundation.storage.filesystem import FileSystemStorage


def test_filesystem_storage_save_load_and_exists_text(tmp_path):
    store = FileSystemStorage(tmp_path)

    saved = store.save("nested/file.txt", "hello world")
    assert saved == (tmp_path / "nested" / "file.txt").resolve()
    assert store.exists("nested/file.txt")
    assert store.load("nested/file.txt") == "hello world"


def test_filesystem_storage_save_and_load_binary(tmp_path):
    store = FileSystemStorage(tmp_path)
    payload = b"\x00\x01\x02"

    store.save("binary/data.bin", payload)
    assert store.load("binary/data.bin", binary=True) == payload


def test_filesystem_storage_rejects_overwrite_without_flag(tmp_path):
    store = FileSystemStorage(tmp_path)
    store.save("one.txt", "first")

    with pytest.raises(FileExistsError):
        store.save("one.txt", "second", overwrite=False)

    store.save("one.txt", "second", overwrite=True)
    assert store.load("one.txt") == "second"


def test_filesystem_storage_rejects_path_traversal(tmp_path):
    store = FileSystemStorage(tmp_path)

    with pytest.raises(ValueError, match="Path traversal attempt"):
        store.save("../escape.txt", "bad")


def test_filesystem_storage_cleans_up_temp_file_on_write_failure(tmp_path):
    store = FileSystemStorage(tmp_path)
    before = set(tmp_path.rglob("*"))

    with pytest.raises(TypeError):
        store.save("bad.txt", object(), overwrite=True)

    after = set(tmp_path.rglob("*"))
    assert before == after
