"""
Line-reset backoff generator with tunable boundary persistence.

Adds partial cross-line memory: the first token of a new line can be sampled
from learned boundary transition tables with probability rho.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class LineResetPersistenceConfig:
    random_state: int = 42
    trigram_use_prob: float = 0.55
    unigram_noise_prob: float = 0.03
    min_trigram_context_count: int = 2
    boundary_persistence_rho: float = 0.25
    boundary_trigram_use_prob: float = 0.7


class LineResetPersistenceGenerator:
    """Hybrid backoff generator with tunable boundary persistence."""

    def __init__(self, config: LineResetPersistenceConfig | None = None):
        self.config = config or LineResetPersistenceConfig()
        self._rng = np.random.default_rng(self.config.random_state)
        self._is_fit = False

    def fit(self, lines: Sequence[Sequence[str]]) -> None:
        cleaned = [list(line) for line in lines if line]
        if not cleaned:
            raise ValueError("Cannot fit LineResetPersistenceGenerator on empty lines")

        line_lengths = [len(line) for line in cleaned]
        start_counts = Counter(line[0] for line in cleaned)
        unigram_counts = Counter(token for line in cleaned for token in line)

        bigram_counts: dict[str, Counter[str]] = defaultdict(Counter)
        trigram_counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
        trigram_context_totals: Counter[tuple[str, str]] = Counter()

        boundary_bigram: dict[str, Counter[str]] = defaultdict(Counter)
        boundary_trigram: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
        boundary_trigram_totals: Counter[tuple[str, str]] = Counter()

        for line in cleaned:
            for a, b in zip(line[:-1], line[1:], strict=True):
                bigram_counts[a][b] += 1
            for a, b, c in zip(line[:-2], line[1:-1], line[2:], strict=True):
                ctx = (a, b)
                trigram_counts[ctx][c] += 1
                trigram_context_totals[ctx] += 1

        for prev_line, next_line in zip(cleaned[:-1], cleaned[1:], strict=True):
            prev_last = prev_line[-1]
            next_first = next_line[0]
            boundary_bigram[prev_last][next_first] += 1
            if len(prev_line) >= 2:
                ctx2 = (prev_line[-2], prev_line[-1])
                boundary_trigram[ctx2][next_first] += 1
                boundary_trigram_totals[ctx2] += 1

        self._line_lengths = np.array(line_lengths, dtype=np.int32)
        self._starts, self._start_probs = self._counter_to_arrays(start_counts)
        self._unigrams, self._unigram_probs = self._counter_to_arrays(unigram_counts)

        self._bigram: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        for prev, cnt in bigram_counts.items():
            self._bigram[prev] = self._counter_to_arrays(cnt)

        self._trigram: dict[tuple[str, str], tuple[np.ndarray, np.ndarray]] = {}
        for ctx, cnt in trigram_counts.items():
            if trigram_context_totals[ctx] >= self.config.min_trigram_context_count:
                self._trigram[ctx] = self._counter_to_arrays(cnt)

        self._boundary_bigram: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        for prev, cnt in boundary_bigram.items():
            self._boundary_bigram[prev] = self._counter_to_arrays(cnt)

        self._boundary_trigram: dict[tuple[str, str], tuple[np.ndarray, np.ndarray]] = {}
        for ctx, cnt in boundary_trigram.items():
            if boundary_trigram_totals[ctx] >= self.config.min_trigram_context_count:
                self._boundary_trigram[ctx] = self._counter_to_arrays(cnt)

        self._fit_stats = {
            "num_lines": len(cleaned),
            "vocab_size": len(unigram_counts),
            "start_vocab_size": len(start_counts),
            "bigram_states": len(self._bigram),
            "trigram_states": len(self._trigram),
            "boundary_bigram_states": len(self._boundary_bigram),
            "boundary_trigram_states": len(self._boundary_trigram),
            "avg_line_length": float(np.mean(self._line_lengths)),
        }
        self._is_fit = True

    def generate(self, target_tokens: int) -> dict[str, object]:
        if not self._is_fit:
            raise RuntimeError("Call fit() before generate()")
        if target_tokens <= 0:
            return {"lines": [], "tokens": []}

        lines: list[list[str]] = []
        out: list[str] = []
        prev_line_tail: list[str] | None = None

        while len(out) < target_tokens:
            line_len = max(1, int(self._rng.choice(self._line_lengths)))
            start = self._sample_line_start(prev_line_tail)
            line = [start]

            while len(line) < line_len:
                line.append(self._sample_next_within_line(line))

            remaining = target_tokens - len(out)
            if len(line) > remaining:
                line = line[:remaining]
            lines.append(line)
            out.extend(line)
            prev_line_tail = line[-2:] if len(line) >= 2 else line[-1:]

        return {"lines": lines, "tokens": out}

    def fit_stats(self) -> dict[str, Any]:
        if not self._is_fit:
            return {}
        return dict(self._fit_stats)

    def _sample_line_start(self, prev_tail: list[str] | None) -> str:
        rho = float(np.clip(self.config.boundary_persistence_rho, 0.0, 1.0))
        use_boundary = prev_tail and (self._rng.random() < rho)
        if use_boundary:
            if (
                len(prev_tail) >= 2
                and tuple(prev_tail[-2:]) in self._boundary_trigram
                and self._rng.random() < self.config.boundary_trigram_use_prob
            ):
                return self._sample_from_tuple(self._boundary_trigram[tuple(prev_tail[-2:])])
            prev_last = prev_tail[-1]
            if prev_last in self._boundary_bigram:
                return self._sample_from_tuple(self._boundary_bigram[prev_last])

        return str(self._rng.choice(self._starts, p=self._start_probs))

    def _sample_next_within_line(self, line: list[str]) -> str:
        if self._rng.random() < self.config.unigram_noise_prob:
            return self._sample_unigram()

        if len(line) >= 2:
            ctx = (line[-2], line[-1])
            if ctx in self._trigram and self._rng.random() < self.config.trigram_use_prob:
                return self._sample_from_tuple(self._trigram[ctx])

        prev = line[-1]
        if prev in self._bigram:
            return self._sample_from_tuple(self._bigram[prev])
        return self._sample_unigram()

    def _sample_unigram(self) -> str:
        return str(self._rng.choice(self._unigrams, p=self._unigram_probs))

    def _sample_from_tuple(self, table: tuple[np.ndarray, np.ndarray]) -> str:
        tokens, probs = table
        return str(self._rng.choice(tokens, p=probs))

    def _counter_to_arrays(self, counts: Counter[str]) -> tuple[np.ndarray, np.ndarray]:
        items = list(counts.items())
        tokens = np.array([token for token, _ in items], dtype=object)
        weights = np.array([count for _, count in items], dtype=np.float64)
        probs = weights / weights.sum()
        return tokens, probs

