"""
Order-constraint diagnostics with permutation baselines.

Metrics:
- Bigram conditional entropy H(w_t | w_{t-1})
- Trigram conditional entropy H(w_t | w_{t-2}, w_{t-1})
- Bigram mutual information I(w_{t-1}; w_t)

Each metric is compared against shuffled-token null distributions.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class OrderConstraintConfig:
    token_limit: int = 120000
    vocab_limit: int = 500
    permutations: int = 50
    random_state: int = 42


class OrderConstraintAnalyzer:
    """Computes order-constraint metrics and permutation baselines per dataset."""

    def __init__(self, config: OrderConstraintConfig | None = None):
        self.config = config or OrderConstraintConfig()
        self._rng = np.random.default_rng(self.config.random_state)

    def analyze(self, dataset_tokens: dict[str, Sequence[str]]) -> dict[str, Any]:
        results: dict[str, Any] = {
            "status": "ok",
            "config": self._config_dict(),
            "datasets": {},
        }

        for dataset_id, tokens in dataset_tokens.items():
            token_list = list(tokens)[: self.config.token_limit]
            if len(token_list) < 4:
                results["datasets"][dataset_id] = {
                    "status": "insufficient_data",
                    "token_count": len(token_list),
                }
                continue

            ids = self._encode_tokens(token_list)
            observed = self._compute_metrics_from_ids(ids)

            perm_samples = {
                "bigram_cond_entropy": [],
                "trigram_cond_entropy": [],
                "bigram_mutual_information": [],
            }
            for _ in range(self.config.permutations):
                perm_ids = self._rng.permutation(ids)
                m = self._compute_metrics_from_ids(perm_ids)
                perm_samples["bigram_cond_entropy"].append(m["bigram_cond_entropy"])
                perm_samples["trigram_cond_entropy"].append(m["trigram_cond_entropy"])
                perm_samples["bigram_mutual_information"].append(m["bigram_mutual_information"])

            metrics = {
                "bigram_cond_entropy": self._summarize_metric(
                    observed=observed["bigram_cond_entropy"],
                    samples=np.array(perm_samples["bigram_cond_entropy"]),
                    direction="lower",
                ),
                "trigram_cond_entropy": self._summarize_metric(
                    observed=observed["trigram_cond_entropy"],
                    samples=np.array(perm_samples["trigram_cond_entropy"]),
                    direction="lower",
                ),
                "bigram_mutual_information": self._summarize_metric(
                    observed=observed["bigram_mutual_information"],
                    samples=np.array(perm_samples["bigram_mutual_information"]),
                    direction="higher",
                ),
            }

            results["datasets"][dataset_id] = {
                "status": "ok",
                "token_count": len(token_list),
                "vocab_size": int(observed["vocab_size"]),
                "metrics": metrics,
            }

        return results

    def _encode_tokens(self, tokens: list[str]) -> np.ndarray:
        if self.config.vocab_limit and self.config.vocab_limit > 1:
            top_n = self.config.vocab_limit - 1
            common = Counter(tokens).most_common(top_n)
            vocab = {token: i for i, (token, _) in enumerate(common)}
            unk_id = len(vocab)
            ids = np.empty(len(tokens), dtype=np.int64)
            for i, token in enumerate(tokens):
                ids[i] = vocab.get(token, unk_id)
            return ids

        vocab: dict[str, int] = {}
        ids = np.empty(len(tokens), dtype=np.int64)
        next_id = 0
        for i, token in enumerate(tokens):
            idx = vocab.get(token)
            if idx is None:
                idx = next_id
                vocab[token] = idx
                next_id += 1
            ids[i] = idx
        return ids

    def _compute_metrics_from_ids(self, ids: np.ndarray) -> dict[str, float]:
        vocab_size = int(ids.max()) + 1

        prev = ids[:-1]
        nxt = ids[1:]
        bigram_codes = prev * vocab_size + nxt
        h_nxt = self._entropy_from_counts(np.unique(nxt, return_counts=True)[1])
        h_bigram_joint = self._entropy_from_counts(np.unique(bigram_codes, return_counts=True)[1])
        h_prev = self._entropy_from_counts(np.unique(prev, return_counts=True)[1])
        bigram_cond_entropy = h_bigram_joint - h_prev
        bigram_mi = h_nxt - bigram_cond_entropy

        prev2 = ids[:-2]
        prev1 = ids[1:-1]
        nxt2 = ids[2:]
        context2_codes = prev2 * vocab_size + prev1
        trigram_codes = context2_codes * vocab_size + nxt2
        h_trigram_joint = self._entropy_from_counts(np.unique(trigram_codes, return_counts=True)[1])
        h_context2 = self._entropy_from_counts(np.unique(context2_codes, return_counts=True)[1])
        trigram_cond_entropy = h_trigram_joint - h_context2

        return {
            "vocab_size": float(vocab_size),
            "bigram_cond_entropy": float(bigram_cond_entropy),
            "trigram_cond_entropy": float(trigram_cond_entropy),
            "bigram_mutual_information": float(bigram_mi),
        }

    def _entropy_from_counts(self, counts: np.ndarray) -> float:
        counts_f = counts.astype(np.float64)
        probs = counts_f / np.sum(counts_f)
        return float(-np.sum(probs * np.log2(probs)))

    def _summarize_metric(
        self, observed: float, samples: np.ndarray, direction: str
    ) -> dict[str, float | int]:
        mean = float(np.mean(samples))
        std = float(np.std(samples))
        z_score = float((observed - mean) / std) if std > 0 else 0.0

        if direction == "lower":
            p_directional = float((np.sum(samples <= observed) + 1) / (len(samples) + 1))
        else:
            p_directional = float((np.sum(samples >= observed) + 1) / (len(samples) + 1))

        return {
            "observed": float(observed),
            "perm_mean": mean,
            "perm_std": std,
            "delta": float(observed - mean),
            "z_score": z_score,
            "p_directional": p_directional,
            "num_permutations": int(len(samples)),
        }

    def _config_dict(self) -> dict[str, Any]:
        return {
            "token_limit": self.config.token_limit,
            "vocab_limit": self.config.vocab_limit,
            "permutations": self.config.permutations,
            "random_state": self.config.random_state,
        }
