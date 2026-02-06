import pytest
from foundation.core.ids import FolioID, PageID, RunID

def test_folio_id_valid():
    assert FolioID("f1r") == "f1r"
    assert FolioID("f102v") == "f102v"
    assert FolioID("f1v1") == "f1v1"

def test_folio_id_invalid():
    with pytest.raises(ValueError):
        FolioID("1r")
    with pytest.raises(ValueError):
        FolioID("fr")
    with pytest.raises(ValueError):
        FolioID("f1") # Missing side

def test_page_id():
    p1 = PageID(folio="f1r")
    p2 = PageID(folio="f1r")
    assert p1 == p2
    assert hash(p1) == hash(p2)
    assert str(p1) == "f1r"

def test_page_id_validation():
    with pytest.raises(ValueError):
        PageID(folio="invalid")

def test_run_id():
    r1 = RunID()
    assert len(r1) > 0
    r2 = RunID(str(r1))
    assert r1 == r2

def test_run_id_invalid():
    with pytest.raises(ValueError):
        RunID("not-a-uuid")
