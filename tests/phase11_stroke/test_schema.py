import numpy as np
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

pytestmark = pytest.mark.unit

from phase11_stroke.schema import CHAR_INVENTORY, FEATURE_NAMES, STROKE_FEATURES, StrokeSchema


def test_schema_has_complete_character_inventory() -> None:
    schema = StrokeSchema()
    inventory = schema.char_inventory()
    assert len(inventory) == 21
    assert set(inventory) == set(CHAR_INVENTORY)


def test_feature_vectors_have_valid_values() -> None:
    schema = StrokeSchema()
    for char in schema.char_inventory():
        vector = schema.get_char_features(char)
        assert vector is not None
        assert vector.shape == (6,)
        assert set(vector[:5]).issubset({0.0, 1.0})
        assert 1.0 <= float(vector[5]) <= 4.0


def test_normalization_maps_stroke_count_to_unit_interval() -> None:
    schema = StrokeSchema()
    base = np.array([1.0, 0.0, 1.0, 0.0, 1.0, 4.0], dtype=np.float64)
    normalized = schema.normalize(base)
    assert float(normalized[5]) == 1.0

    matrix = np.array([base, np.array([0.0, 1.0, 0.0, 1.0, 0.0, 2.0])], dtype=np.float64)
    normalized_matrix = schema.normalize(matrix)
    assert np.all(normalized_matrix[:, 5] >= 0.0)
    assert np.all(normalized_matrix[:, 5] <= 1.0)


def test_permuted_table_preserves_feature_vector_multiset() -> None:
    schema = StrokeSchema()
    rng = np.random.default_rng(42)
    permuted = schema.permuted_table(rng)

    original_vectors = sorted(tuple(STROKE_FEATURES[char]) for char in sorted(STROKE_FEATURES))
    permuted_vectors = sorted(tuple(int(v) for v in permuted[char]) for char in sorted(permuted))
    assert permuted_vectors == original_vectors


def test_token_profile_edge_cases_are_supported() -> None:
    schema = StrokeSchema()

    empty_mean = schema.get_token_profile("", mode="mean")
    assert np.allclose(empty_mean, np.zeros(len(FEATURE_NAMES)))

    unknown_mean = schema.get_token_profile("123", mode="mean")
    assert np.allclose(unknown_mean, np.zeros(len(FEATURE_NAMES)))

    single = schema.get_token_profile("i", mode="mean")
    assert np.allclose(single, np.array([0.0, 0.0, 0.0, 0.0, 1.0, 1.0]))

    boundary_unknown = schema.get_token_profile("??", mode="boundary")
    assert np.allclose(boundary_unknown, np.zeros(12))
