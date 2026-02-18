"""
Kolmogorov complexity proxy via lossless compression.

True Kolmogorov complexity is uncomputable. We approximate it by measuring how
well generic compressors encode token streams, and compare against shuffled
null baselines with identical token marginals.
"""

from __future__ import annotations

import bz2
import lzma
import zlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class KolmogorovProxyConfig:
    token_limit: int = 120000
    permutations: int = 30
    random_state: int = 42
    codecs: tuple[str, ...] = ("zlib", "lzma")


class KolmogorovProxyAnalyzer:
    """Compression-based complexity proxy with shuffled-token baselines."""

    def __init__(self, config: KolmogorovProxyConfig | None = None):
        self.config = config or KolmogorovProxyConfig()
        self._rng = np.random.default_rng(self.config.random_state)

    def analyze(self, dataset_tokens: dict[str, Sequence[str]]) -> dict[str, Any]:
        results: dict[str, Any] = {
            "status": "ok",
            "config": self._config_dict(),
            "datasets": {},
        }

        for dataset_id, tokens in dataset_tokens.items():
            token_list = list(tokens)[: self.config.token_limit]
            if len(token_list) < 8:
                results["datasets"][dataset_id] = {
                    "status": "insufficient_data",
                    "token_count": len(token_list),
                }
                continue

            codec_results: dict[str, Any] = {}
            for codec in self.config.codecs:
                observed = self._compressed_bytes(token_list, codec)
                raw_bytes = len(self._to_bytes(token_list))

                perm_scores: list[int] = []
                for _ in range(self.config.permutations):
                    shuffled = self._rng.permutation(token_list).tolist()
                    perm_scores.append(self._compressed_bytes(shuffled, codec))

                perm = np.array(perm_scores, dtype=np.float64)
                mean = float(np.mean(perm))
                std = float(np.std(perm))
                z_score = float((observed - mean) / std) if std > 0 else 0.0
                p_low = float((np.sum(perm <= observed) + 1) / (len(perm) + 1))

                codec_results[codec] = {
                    "observed_compressed_bytes": int(observed),
                    "raw_bytes": int(raw_bytes),
                    "observed_compression_ratio": float(observed / raw_bytes),
                    "observed_bits_per_token": float((observed * 8.0) / len(token_list)),
                    "perm_mean_compressed_bytes": mean,
                    "perm_std_compressed_bytes": std,
                    "delta_bytes_vs_perm_mean": float(observed - mean),
                    "z_score": z_score,
                    "p_low_bytes": p_low,
                    "num_permutations": len(perm_scores),
                }

            results["datasets"][dataset_id] = {
                "status": "ok",
                "token_count": len(token_list),
                "codec_results": codec_results,
            }

        return results

    def _to_bytes(self, tokens: list[str]) -> bytes:
        return " ".join(tokens).encode("utf-8", errors="ignore")

    def _compressed_bytes(self, tokens: list[str], codec: str) -> int:
        payload = self._to_bytes(tokens)
        if codec == "zlib":
            return len(zlib.compress(payload, level=9))
        if codec == "lzma":
            return len(lzma.compress(payload, preset=9))
        if codec == "bz2":
            return len(bz2.compress(payload, compresslevel=9))
        raise ValueError(f"Unsupported codec: {codec}")

    def _config_dict(self) -> dict[str, Any]:
        return {
            "token_limit": self.config.token_limit,
            "permutations": self.config.permutations,
            "random_state": self.config.random_state,
            "codecs": list(self.config.codecs),
        }

