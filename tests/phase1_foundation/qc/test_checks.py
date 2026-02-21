import logging

import pytest

pytestmark = pytest.mark.unit

from phase1_foundation.qc.checks import check_folio_format, check_unique_ids


def test_check_unique_ids_detects_duplicates():
    assert check_unique_ids(["a", "b", "c"])
    assert not check_unique_ids(["a", "b", "a"])


def test_check_folio_format_returns_invalid_and_logs_warnings(caplog):
    caplog.set_level(logging.WARNING, logger="phase1_foundation.qc.checks")
    invalid = check_folio_format(["f1r", "f2v1", "bad", "f_3", "f10v"])

    assert invalid == ["bad", "f_3"]
    assert "Invalid folio ID detected during QC: bad" in caplog.text
    assert "Invalid folio ID detected during QC: f_3" in caplog.text
