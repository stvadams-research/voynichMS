import pytest

from phase1_foundation.core.models import Scale

pytestmark = pytest.mark.unit


def test_scale_values_are_stable():
    assert Scale.PAGE.value == "page"
    assert Scale.REGION.value == "region"
    assert Scale.LINE.value == "line"
    assert Scale.WORD.value == "word"
    assert Scale.GLYPH.value == "glyph"
    assert Scale.STROKE.value == "stroke"


def test_scale_string_representation_matches_value():
    assert str(Scale.PAGE) == "page"
    assert str(Scale.GLYPH) == "glyph"
