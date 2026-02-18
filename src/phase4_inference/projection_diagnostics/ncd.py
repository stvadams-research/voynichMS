"""
Normalized Compression Distance (NCD) diagnostics.

NCD is a practical proxy for algorithmic similarity using a real compressor:
NCD(x, y) = (C(xy) - min(C(x), C(y))) / max(C(x), C(y))

This module provides:
- point-estimate NCD matrix across datasets
- bootstrap confidence summaries for rank stability relative to a focus dataset
"""

from __future__ import annotations

import zlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class NCDConfig:
    token_limit: int = 80000
    bootstraps: int = 60
    block_size: int = 512
    random_state: int = 42
    focus_dataset_id: str = "voynich_real"


class NCDAnalyzer:
    """NCD matrix and bootstrap rank stability diagnostics."""

    def __init__(self, config: NCDConfig | None = None):
        self.config = config or NCDConfig()
        self._rng = np.random.default_rng(self.config.random_state)

    def analyze(self, dataset_tokens: dict[str, Sequence[str]]) -> dict[str, Any]:
        dataset_ids = list(dataset_tokens.keys())
        if len(dataset_ids) < 2:
            return {
                "status": "insufficient_data",
                "reason": "requires_at_least_two_datasets",
                "config": self._config_dict(),
            }

        prepared = {dataset_id: list(tokens) for dataset_id, tokens in dataset_tokens.items()}
        point_payloads = {
            dataset_id: self._tokens_to_bytes(tokens[: self.config.token_limit])
            for dataset_id, tokens in prepared.items()
        }
        point_matrix, point_sizes = self._compute_ncd_matrix(point_payloads)

        focus = self.config.focus_dataset_id
        if focus not in dataset_ids:
            return {
                "status": "insufficient_data",
                "reason": f"focus_dataset_not_found:{focus}",
                "config": self._config_dict(),
                "dataset_ids": dataset_ids,
                "point_estimate_ncd": point_matrix,
            }

        bootstrap_rows = []
        others = [d for d in dataset_ids if d != focus]
        closest_counts = {d: 0 for d in others}
        rank_samples: dict[str, list[int]] = {d: [] for d in others}
        distance_samples: dict[str, list[float]] = {d: [] for d in others}

        for _ in range(self.config.bootstraps):
            sampled_payloads = {
                dataset_id: self._tokens_to_bytes(
                    self._sample_block_bootstrap(prepared[dataset_id], self.config.token_limit)
                )
                for dataset_id in dataset_ids
            }
            sampled_sizes = {k: self._compressed_size(v) for k, v in sampled_payloads.items()}
            focus_distances: dict[str, float] = {}
            for other in others:
                concat = sampled_payloads[focus] + b"\n--SEP--\n" + sampled_payloads[other]
                focus_distances[other] = self._ncd_from_sizes(
                    sampled_sizes[focus],
                    sampled_sizes[other],
                    self._compressed_size(concat),
                )
                distance_samples[other].append(float(focus_distances[other]))

            sorted_items = sorted(focus_distances.items(), key=lambda x: x[1])
            for rank, (dataset_id, _) in enumerate(sorted_items, start=1):
                rank_samples[dataset_id].append(rank)
            closest_counts[sorted_items[0][0]] += 1
            bootstrap_rows.append(focus_distances)

        bootstrap_summary = {}
        for other in others:
            vals = np.array(distance_samples[other], dtype=np.float64)
            ranks = np.array(rank_samples[other], dtype=np.float64)
            bootstrap_summary[other] = {
                "point_ncd": float(point_matrix[focus][other]),
                "bootstrap_mean_ncd": float(np.mean(vals)),
                "bootstrap_ci95_low_ncd": float(np.quantile(vals, 0.025)),
                "bootstrap_ci95_high_ncd": float(np.quantile(vals, 0.975)),
                "closest_probability": float(closest_counts[other] / self.config.bootstraps),
                "rank_mean": float(np.mean(ranks)),
                "rank_ci95_low": float(np.quantile(ranks, 0.025)),
                "rank_ci95_high": float(np.quantile(ranks, 0.975)),
            }

        return {
            "status": "ok",
            "config": self._config_dict(),
            "dataset_ids": dataset_ids,
            "point_estimate_ncd": point_matrix,
            "point_compressed_sizes": point_sizes,
            "focus_dataset_id": focus,
            "focus_bootstrap_summary": bootstrap_summary,
        }

    def _compute_ncd_matrix(
        self, payloads: dict[str, bytes]
    ) -> tuple[dict[str, dict[str, float]], dict[str, int]]:
        dataset_ids = list(payloads.keys())
        compressed = {k: self._compressed_size(v) for k, v in payloads.items()}
        matrix: dict[str, dict[str, float]] = {d: {} for d in dataset_ids}

        for i, di in enumerate(dataset_ids):
            matrix[di][di] = 0.0
            for dj in dataset_ids[i + 1 :]:
                cij = self._compressed_size(payloads[di] + b"\n--SEP--\n" + payloads[dj])
                ncd = self._ncd_from_sizes(compressed[di], compressed[dj], cij)
                matrix[di][dj] = ncd
                matrix[dj][di] = ncd
        return matrix, compressed

    def _sample_block_bootstrap(self, tokens: list[str], target_len: int) -> list[str]:
        if not tokens:
            return []
        if len(tokens) == 1:
            return [tokens[0]] * target_len

        out: list[str] = []
        block = max(2, self.config.block_size)
        while len(out) < target_len:
            block_len = min(block, target_len - len(out))
            if len(tokens) <= block_len:
                start = 0
            else:
                start = int(self._rng.integers(0, len(tokens) - block_len + 1))
            out.extend(tokens[start : start + block_len])
        return out[:target_len]

    def _tokens_to_bytes(self, tokens: list[str]) -> bytes:
        return " ".join(tokens).encode("utf-8", errors="ignore")

    def _compressed_size(self, payload: bytes) -> int:
        return len(zlib.compress(payload, level=9))

    def _ncd_from_sizes(self, cx: int, cy: int, cxy: int) -> float:
        denom = max(cx, cy)
        if denom == 0:
            return 0.0
        return float((cxy - min(cx, cy)) / denom)

    def _config_dict(self) -> dict[str, Any]:
        return {
            "token_limit": self.config.token_limit,
            "bootstraps": self.config.bootstraps,
            "block_size": self.config.block_size,
            "random_state": self.config.random_state,
            "focus_dataset_id": self.config.focus_dataset_id,
        }
