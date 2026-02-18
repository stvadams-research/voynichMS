"""
Line-reset Markov control generator.

Learns:
- empirical line-length distribution
- line-initial token distribution
- within-line bigram transitions

Generation resets state at each line boundary.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass
class LineResetMarkovConfig:
    random_state: int = 42
    fallback_min_line_length: int = 4
    fallback_max_line_length: int = 10


class LineResetMarkovGenerator:
    """Generates non-semantic text with line-reset local transition rules."""

    def __init__(self, config: LineResetMarkovConfig | None = None):
        self.config = config or LineResetMarkovConfig()
        self._rng = np.random.default_rng(self.config.random_state)
        self._is_fit = False

    def fit(self, lines: Sequence[Sequence[str]]) -> None:
        cleaned = [list(line) for line in lines if line]
        if not cleaned:
            raise ValueError("Cannot fit LineResetMarkovGenerator on empty lines")

        line_lengths = [len(line) for line in cleaned if len(line) > 0]
        if not line_lengths:
            line_lengths = list(
                range(
                    self.config.fallback_min_line_length,
                    self.config.fallback_max_line_length + 1,
                )
            )

        start_counts = Counter(line[0] for line in cleaned if line)
        unigram_counts = Counter(token for line in cleaned for token in line)
        transition_counts: dict[str, Counter[str]] = defaultdict(Counter)
        for line in cleaned:
            for prev, nxt in zip(line[:-1], line[1:], strict=True):
                transition_counts[prev][nxt] += 1

        self._line_lengths = np.array(line_lengths, dtype=np.int32)
        self._start_tokens, self._start_probs = self._counter_to_sampling_arrays(start_counts)
        self._unigram_tokens, self._unigram_probs = self._counter_to_sampling_arrays(unigram_counts)

        self._transition_sampling: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        for prev_token, cnt in transition_counts.items():
            self._transition_sampling[prev_token] = self._counter_to_sampling_arrays(cnt)

        self._fit_stats = {
            "num_lines": len(cleaned),
            "vocab_size": len(unigram_counts),
            "start_vocab_size": len(start_counts),
            "transition_states": len(self._transition_sampling),
            "avg_line_length": float(np.mean(self._line_lengths)),
        }
        self._is_fit = True

    def generate(self, target_tokens: int) -> dict[str, object]:
        if not self._is_fit:
            raise RuntimeError("Call fit() before generate()")
        if target_tokens <= 0:
            return {"lines": [], "tokens": []}

        lines: list[list[str]] = []
        tokens_out: list[str] = []

        while len(tokens_out) < target_tokens:
            line_len = int(self._rng.choice(self._line_lengths))
            line_len = max(1, line_len)

            line = [self._sample_start()]
            while len(line) < line_len:
                line.append(self._sample_next(line[-1]))

            remaining = target_tokens - len(tokens_out)
            if len(line) > remaining:
                line = line[:remaining]

            lines.append(line)
            tokens_out.extend(line)

        return {"lines": lines, "tokens": tokens_out}

    def fit_stats(self) -> dict[str, object]:
        if not self._is_fit:
            return {}
        return dict(self._fit_stats)

    def _sample_start(self) -> str:
        return str(self._rng.choice(self._start_tokens, p=self._start_probs))

    def _sample_next(self, prev_token: str) -> str:
        choices = self._transition_sampling.get(prev_token)
        if choices is None:
            return str(self._rng.choice(self._unigram_tokens, p=self._unigram_probs))
        tokens, probs = choices
        return str(self._rng.choice(tokens, p=probs))

    def _counter_to_sampling_arrays(self, counts: Counter[str]) -> tuple[np.ndarray, np.ndarray]:
        items = list(counts.items())
        tokens = np.array([token for token, _ in items], dtype=object)
        weights = np.array([count for _, count in items], dtype=np.float64)
        probs = weights / weights.sum()
        return tokens, probs

