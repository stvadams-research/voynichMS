"""
Music-like symbolic stream controls.

Generates non-linguistic structured token streams with motif repetition,
transposition-like variation, and phrase boundaries.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class MusicStreamConfig:
    target_tokens: int = 230000
    alphabet_size: int = 64
    pitch_classes: int = 12
    duration_classes: int = 4
    motif_count: int = 48
    motif_min_len: int = 4
    motif_max_len: int = 10
    repeat_probability: float = 0.45
    ornament_probability: float = 0.08
    random_state: int = 42


class MusicStreamControlBuilder:
    """
    Build music-like controls from a corpus-derived token alphabet.

    The model is intentionally non-semantic: it expresses periodicity and motif
    reuse while avoiding language-specific assumptions.
    """

    def __init__(self, config: MusicStreamConfig | None = None):
        self.config = config or MusicStreamConfig()
        self._rng = np.random.default_rng(self.config.random_state)

    def build_control(self, reference_tokens: list[str]) -> dict[str, Any]:
        if not reference_tokens:
            return {"status": "insufficient_data", "reason": "empty_reference_tokens"}

        alphabet = self._derive_alphabet(reference_tokens)
        motif_bank = self._build_motif_bank()
        tokens = self._generate_tokens(alphabet, motif_bank)

        return {
            "status": "ok",
            "config": self._config_dict(),
            "alphabet_size": len(alphabet),
            "motif_count": len(motif_bank),
            "generated_tokens": len(tokens),
            "tokens": tokens,
        }

    def _derive_alphabet(self, reference_tokens: list[str]) -> list[str]:
        top = Counter(reference_tokens).most_common(max(4, self.config.alphabet_size))
        alphabet = [token for token, _ in top]
        if len(alphabet) < self.config.alphabet_size:
            pad = [f"m_pad_{i}" for i in range(self.config.alphabet_size - len(alphabet))]
            alphabet.extend(pad)
        return alphabet[: self.config.alphabet_size]

    def _build_motif_bank(self) -> list[list[tuple[int, int]]]:
        bank: list[list[tuple[int, int]]] = []
        for _ in range(self.config.motif_count):
            length = int(
                self._rng.integers(self.config.motif_min_len, self.config.motif_max_len + 1)
            )
            pitch = int(self._rng.integers(0, self.config.pitch_classes))
            motif: list[tuple[int, int]] = []
            for _ in range(length):
                step = int(self._rng.choice(np.array([-3, -2, -1, 0, 1, 2, 3])))
                pitch = (pitch + step) % self.config.pitch_classes
                dur = int(self._rng.choice(np.array([0, 0, 1, 1, 2, 3])))
                motif.append((pitch, dur))
            bank.append(motif)
        return bank

    def _generate_tokens(
        self, alphabet: list[str], motif_bank: list[list[tuple[int, int]]]
    ) -> list[str]:
        out: list[str] = []
        last_motif_idx: int | None = None
        last_shift = 0

        while len(out) < self.config.target_tokens:
            if last_motif_idx is not None and self._rng.random() < self.config.repeat_probability:
                motif_idx = last_motif_idx
            else:
                motif_idx = int(self._rng.integers(0, len(motif_bank)))
            motif = motif_bank[motif_idx]

            shift = (
                last_shift
                if self._rng.random() < 0.6
                else int(self._rng.integers(-5, 6))
            )
            last_shift = shift

            phrase_repeats = int(self._rng.integers(1, 4))
            for _ in range(phrase_repeats):
                for pitch, dur in motif:
                    p = (pitch + shift) % self.config.pitch_classes
                    d = dur
                    if self._rng.random() < self.config.ornament_probability:
                        d = int(self._rng.choice(np.array([0, 1, 2, 3])))
                    idx = (p * self.config.duration_classes + d) % len(alphabet)
                    out.append(alphabet[idx])
                    if len(out) >= self.config.target_tokens:
                        break
                if len(out) >= self.config.target_tokens:
                    break

            last_motif_idx = motif_idx

        return out[: self.config.target_tokens]

    def _config_dict(self) -> dict[str, Any]:
        return {
            "target_tokens": self.config.target_tokens,
            "alphabet_size": self.config.alphabet_size,
            "pitch_classes": self.config.pitch_classes,
            "duration_classes": self.config.duration_classes,
            "motif_count": self.config.motif_count,
            "motif_min_len": self.config.motif_min_len,
            "motif_max_len": self.config.motif_max_len,
            "repeat_probability": self.config.repeat_probability,
            "ornament_probability": self.config.ornament_probability,
            "random_state": self.config.random_state,
        }
