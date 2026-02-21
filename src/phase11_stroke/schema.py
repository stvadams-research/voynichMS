"""Stroke feature schema and token-level profile helpers for Phase 11."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence

import numpy as np

CHAR_INVENTORY: tuple[str, ...] = (
    "a",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "v",
    "x",
    "y",
)

FEATURE_NAMES: tuple[str, ...] = (
    "gallows",
    "loop",
    "bench",
    "descender",
    "minimal",
    "stroke_count",
)

BINARY_FEATURE_COUNT = 5
MAX_STROKE_COUNT = 4.0

STROKE_FEATURES: dict[str, tuple[int, int, int, int, int, int]] = {
    "a": (0, 1, 0, 0, 0, 2),
    "c": (0, 0, 1, 0, 0, 1),
    "d": (0, 1, 0, 0, 0, 2),
    "e": (0, 1, 0, 0, 0, 1),
    "f": (1, 1, 0, 0, 0, 4),
    "g": (0, 1, 0, 1, 0, 2),
    "h": (0, 0, 1, 0, 0, 2),
    "i": (0, 0, 0, 0, 1, 1),
    "k": (1, 0, 0, 0, 0, 3),
    "l": (0, 0, 0, 0, 1, 2),
    "m": (0, 0, 0, 1, 0, 3),
    "n": (0, 0, 0, 0, 0, 2),
    "o": (0, 1, 0, 0, 0, 1),
    "p": (1, 1, 0, 0, 0, 4),
    # EVA q is modeled as a looped glyph with a descending tail.
    "q": (0, 1, 0, 1, 0, 2),
    "r": (0, 0, 0, 0, 1, 1),
    "s": (0, 0, 0, 1, 0, 1),
    "t": (1, 1, 0, 0, 0, 3),
    "v": (0, 0, 0, 0, 0, 3),
    "x": (0, 0, 0, 0, 0, 2),
    "y": (0, 0, 0, 1, 0, 2),
}


def _validate_feature_table(feature_table: Mapping[str, Sequence[int | float]]) -> None:
    missing = [char for char in CHAR_INVENTORY if char not in feature_table]
    if missing:
        raise ValueError(f"Missing stroke feature assignments for characters: {missing}")

    for char in CHAR_INVENTORY:
        vector = feature_table[char]
        if len(vector) != len(FEATURE_NAMES):
            raise ValueError(
                f"Character '{char}' has vector length {len(vector)}; "
                f"expected {len(FEATURE_NAMES)}"
            )
        for idx in range(BINARY_FEATURE_COUNT):
            value = float(vector[idx])
            if value not in (0.0, 1.0):
                raise ValueError(
                    f"Character '{char}' has invalid binary feature value "
                    f"{value} at index {idx}"
                )
        stroke_count = int(vector[BINARY_FEATURE_COUNT])
        if stroke_count < 1 or stroke_count > int(MAX_STROKE_COUNT):
            raise ValueError(
                f"Character '{char}' has invalid stroke_count {stroke_count}; "
                f"expected integer in [1, {int(MAX_STROKE_COUNT)}]"
            )


def _canonical_feature_table(feature_table: Mapping[str, Sequence[int | float]]) -> dict[str, list[float]]:
    return {char: [float(v) for v in feature_table[char]] for char in sorted(feature_table)}


def feature_table_hash(feature_table: Mapping[str, Sequence[int | float]]) -> str:
    canonical = _canonical_feature_table(feature_table)
    payload = json.dumps(canonical, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class StrokeSchema:
    """Defines and applies the fixed EVA character stroke feature table."""

    def __init__(self, feature_table: Mapping[str, Sequence[int | float]] | None = None):
        source = feature_table or STROKE_FEATURES
        _validate_feature_table(source)
        self._feature_table: dict[str, np.ndarray] = {
            char: np.array(source[char], dtype=np.float64) for char in CHAR_INVENTORY
        }
        self._schema_version = feature_table_hash(source)

    def get_char_features(self, char: str) -> np.ndarray | None:
        """Return a copy of the 6-element feature vector for one character."""
        vector = self._feature_table.get(char)
        if vector is None:
            return None
        return np.array(vector, copy=True)

    def get_token_profile(self, token: str, mode: str) -> np.ndarray:
        """
        Compute a token-level profile.

        Modes:
        - mean: 6D mean profile over recognized characters
        - boundary: 12D first-char + last-char concatenation
        - aggregate: 6D sum profile over recognized characters
        """
        if mode not in {"mean", "boundary", "aggregate"}:
            raise ValueError(f"Unknown token profile mode '{mode}'")

        recognized = [self._feature_table[char] for char in token if char in self._feature_table]
        if not recognized:
            if mode == "boundary":
                return np.zeros(len(FEATURE_NAMES) * 2, dtype=np.float64)
            return np.zeros(len(FEATURE_NAMES), dtype=np.float64)

        matrix = np.vstack(recognized)
        if mode == "mean":
            return np.mean(matrix, axis=0, dtype=np.float64)
        if mode == "boundary":
            return np.concatenate((matrix[0], matrix[-1]))
        return np.sum(matrix, axis=0, dtype=np.float64)

    def normalize(self, features: np.ndarray) -> np.ndarray:
        """Normalize stroke_count dimensions to [0, 1] while preserving other values."""
        normalized = np.array(features, dtype=np.float64, copy=True)
        if normalized.ndim == 1:
            if normalized.shape[0] == len(FEATURE_NAMES):
                normalized[BINARY_FEATURE_COUNT] /= MAX_STROKE_COUNT
                return normalized
            if normalized.shape[0] == 2 * len(FEATURE_NAMES):
                normalized[BINARY_FEATURE_COUNT] /= MAX_STROKE_COUNT
                normalized[len(FEATURE_NAMES) + BINARY_FEATURE_COUNT] /= MAX_STROKE_COUNT
                return normalized
            raise ValueError(
                "normalize expects vectors of length 6 (single profile) or 12 (boundary profile)."
            )

        if normalized.shape[-1] == len(FEATURE_NAMES):
            normalized[..., BINARY_FEATURE_COUNT] /= MAX_STROKE_COUNT
            return normalized
        if normalized.shape[-1] == 2 * len(FEATURE_NAMES):
            normalized[..., BINARY_FEATURE_COUNT] /= MAX_STROKE_COUNT
            normalized[..., len(FEATURE_NAMES) + BINARY_FEATURE_COUNT] /= MAX_STROKE_COUNT
            return normalized
        raise ValueError("normalize expects arrays whose final dimension is 6 or 12.")

    def char_inventory(self) -> list[str]:
        return list(CHAR_INVENTORY)

    def feature_names(self) -> list[str]:
        return list(FEATURE_NAMES)

    def feature_table(self) -> dict[str, list[float]]:
        return {
            char: [float(value) for value in self._feature_table[char]]
            for char in CHAR_INVENTORY
        }

    def schema_version(self) -> str:
        return self._schema_version

    def permuted_table(self, rng: np.random.Generator) -> dict[str, list[float]]:
        """Return a lookup table with feature vectors reassigned across characters."""
        base_vectors = [self._feature_table[char] for char in CHAR_INVENTORY]
        permutation = rng.permutation(len(CHAR_INVENTORY))
        return {
            char: [float(value) for value in base_vectors[int(permutation[idx])]]
            for idx, char in enumerate(CHAR_INVENTORY)
        }
