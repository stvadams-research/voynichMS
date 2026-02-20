"""Test A: non-random stroke-feature clustering analysis."""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from rich.console import Console
from rich.progress import Progress

from phase11_stroke.schema import CHAR_INVENTORY, StrokeSchema


def _rankdata(values: np.ndarray) -> np.ndarray:
    """Return average ranks (1-indexed) with stable tie handling."""
    if values.size == 0:
        return np.array([], dtype=np.float64)

    n = values.size
    order = np.argsort(values, kind="mergesort")
    sorted_values = values[order]
    group_starts = np.empty(n, dtype=bool)
    group_starts[0] = True
    group_starts[1:] = sorted_values[1:] != sorted_values[:-1]
    start_idx = np.flatnonzero(group_starts)
    end_idx = np.append(start_idx[1:], n)
    rank_values = 0.5 * (start_idx + end_idx - 1) + 1.0
    group_sizes = end_idx - start_idx
    ranks_sorted = np.repeat(rank_values, group_sizes)

    ranks = np.empty(n, dtype=np.float64)
    ranks[order] = ranks_sorted
    return ranks


def _pearson_corr(x: np.ndarray, y: np.ndarray) -> float:
    if x.size < 2 or y.size < 2:
        return 0.0
    x_centered = x - np.mean(x)
    y_centered = y - np.mean(y)
    denom = np.linalg.norm(x_centered) * np.linalg.norm(y_centered)
    if denom <= 1e-12:
        return 0.0
    return float(np.dot(x_centered, y_centered) / denom)


def _spearman_corr(x: np.ndarray, y: np.ndarray) -> float:
    return _pearson_corr(_rankdata(x), _rankdata(y))


def _residualize(target: np.ndarray, control_centered: np.ndarray, control_var: float) -> np.ndarray:
    centered = target - np.mean(target)
    if control_var <= 1e-12:
        return centered
    beta = float(np.dot(control_centered, centered) / control_var)
    return centered - beta * control_centered


class ClusteringAnalyzer:
    """Runs Test A from the Phase 11 plan."""

    def __init__(self, schema: StrokeSchema | None = None, min_occurrence: int = 5):
        self.schema = schema or StrokeSchema()
        self.min_occurrence = min_occurrence
        self._char_to_index = {char: idx for idx, char in enumerate(CHAR_INVENTORY)}
        base_table = self.schema.feature_table()
        feature_matrix = np.array([base_table[char] for char in CHAR_INVENTORY], dtype=np.float64)
        self._normalized_feature_matrix = self.schema.normalize(feature_matrix)

    def run(
        self,
        extracted_data: dict[str, Any],
        n_permutations: int,
        rng: np.random.Generator,
        console: Console | None = None,
        progress: Progress | None = None,
        task_id: int | None = None,
    ) -> dict[str, Any]:
        t_start = time.time()
        token_features = extracted_data.get("token_type_features", {})
        line_features = extracted_data.get("line_features", [])

        eligible_tokens = sorted(
            token
            for token, values in token_features.items()
            if int(values.get("count", 0)) >= self.min_occurrence
        )
        n_tokens = len(eligible_tokens)
        n_lines = len(line_features)

        if n_tokens < 2 or n_lines == 0:
            return {
                "test_id": "A",
                "observed_raw_rho": 0.0,
                "observed_partial_rho": 0.0,
                "p_value": 1.0,
                "n_permutations": int(n_permutations),
                "determination": "indeterminate",
                "details": {
                    "reason": "insufficient_data",
                    "eligible_token_count": int(n_tokens),
                    "line_count": int(n_lines),
                },
                "duration_seconds": float(time.time() - t_start),
            }

        token_to_idx = {token: idx for idx, token in enumerate(eligible_tokens)}
        frequencies = np.array(
            [float(token_features[token]["count"]) for token in eligible_tokens], dtype=np.float64
        )

        if console:
            console.print(
                "[cyan]Test A[/cyan] "
                f"eligible_tokens={n_tokens} lines={n_lines} permutations={n_permutations}"
            )

        # Binary token-line incidence matrix for co-occurrence rates.
        incidence = np.zeros((n_tokens, n_lines), dtype=np.uint8)
        for line_idx, line in enumerate(line_features):
            present = {token for token in line.get("tokens", []) if token in token_to_idx}
            for token in present:
                incidence[token_to_idx[token], line_idx] = 1

        co_counts = incidence.astype(np.int16) @ incidence.astype(np.int16).T
        co_rates = co_counts.astype(np.float64) / float(max(n_lines, 1))

        upper_i, upper_j = np.triu_indices(n_tokens, k=1)
        pair_count = int(upper_i.size)

        control = np.log(frequencies[upper_i]) + np.log(frequencies[upper_j])
        control_centered = control - np.mean(control)
        control_var = float(np.dot(control_centered, control_centered))
        y = co_rates[upper_i, upper_j]
        y_resid = _residualize(y, control_centered, control_var)
        y_resid_rank = _rankdata(y_resid)
        y_resid_rank_centered = y_resid_rank - np.mean(y_resid_rank)
        y_resid_rank_norm = float(np.linalg.norm(y_resid_rank_centered))

        char_composition = self._token_char_composition(eligible_tokens)
        observed_profiles = char_composition @ self._normalized_feature_matrix
        observed_similarity = self._pairwise_cosine_upper(observed_profiles, upper_i, upper_j)

        observed_raw_rho = _spearman_corr(observed_similarity, y)
        observed_partial_rho = _spearman_corr(_residualize(observed_similarity, control_centered, control_var), y_resid)

        if console:
            console.print("[cyan]Test A[/cyan] observed statistics computed")

        null_partial = np.zeros(n_permutations, dtype=np.float64)
        heartbeat_every = min(500, max(1, n_permutations // 20))
        loop_start = time.time()
        last_heartbeat = loop_start

        for idx in range(n_permutations):
            perm = rng.permutation(len(CHAR_INVENTORY))
            perm_feature_matrix = self._normalized_feature_matrix[perm]
            perm_profiles = char_composition @ perm_feature_matrix
            perm_similarity = self._pairwise_cosine_upper(perm_profiles, upper_i, upper_j)
            perm_resid = _residualize(perm_similarity, control_centered, control_var)
            perm_rank = _rankdata(perm_resid)
            perm_rank_centered = perm_rank - np.mean(perm_rank)
            denom = np.linalg.norm(perm_rank_centered) * y_resid_rank_norm
            if denom <= 1e-12:
                null_partial[idx] = 0.0
            else:
                null_partial[idx] = float(np.dot(perm_rank_centered, y_resid_rank_centered) / denom)

            if progress is not None and task_id is not None:
                progress.update(task_id, completed=idx + 1)
            now = time.time()
            if console and (
                (idx + 1) % heartbeat_every == 0
                or idx + 1 == n_permutations
                or (now - last_heartbeat) >= 30.0
            ):
                elapsed = time.time() - loop_start
                completed = idx + 1
                rate = elapsed / completed if completed else 0.0
                eta = rate * (n_permutations - completed)
                running_stat = float(np.mean(null_partial[:completed]))
                console.print(
                    "[cyan]Test A heartbeat[/cyan] "
                    f"{completed}/{n_permutations} elapsed={elapsed:.1f}s eta={eta:.1f}s "
                    f"running_partial_rho={running_stat:.4f}"
                )
                last_heartbeat = now

        p_value = float(np.mean(null_partial >= observed_partial_rho)) if n_permutations else 1.0
        if p_value < 0.01 and observed_partial_rho > 0.05:
            determination = "significant"
        elif p_value < 0.01 and observed_partial_rho <= 0.05:
            determination = "indeterminate"
        else:
            determination = "null"

        duration = time.time() - t_start
        return {
            "test_id": "A",
            "observed_raw_rho": float(observed_raw_rho),
            "observed_partial_rho": float(observed_partial_rho),
            "p_value": p_value,
            "n_permutations": int(n_permutations),
            "determination": determination,
            "details": {
                "min_occurrence": int(self.min_occurrence),
                "eligible_token_count": int(n_tokens),
                "pair_count": pair_count,
                "line_count": int(n_lines),
                "null_distribution_summary": {
                    "mean": float(np.mean(null_partial)),
                    "std": float(np.std(null_partial)),
                    "percentile_95": float(np.quantile(null_partial, 0.95)),
                    "percentile_99": float(np.quantile(null_partial, 0.99)),
                },
            },
            "duration_seconds": float(duration),
        }

    def _token_char_composition(self, tokens: list[str]) -> np.ndarray:
        matrix = np.zeros((len(tokens), len(CHAR_INVENTORY)), dtype=np.float64)
        for token_idx, token in enumerate(tokens):
            recognized = [char for char in token if char in self._char_to_index]
            if not recognized:
                continue
            for char in recognized:
                matrix[token_idx, self._char_to_index[char]] += 1.0
            matrix[token_idx, :] /= float(len(recognized))
        return matrix

    @staticmethod
    def _pairwise_cosine_upper(
        profile_matrix: np.ndarray, upper_i: np.ndarray, upper_j: np.ndarray
    ) -> np.ndarray:
        norms = np.linalg.norm(profile_matrix, axis=1, keepdims=True)
        safe_norms = np.where(norms <= 1e-12, 1.0, norms)
        normalized_profiles = profile_matrix / safe_norms
        similarity_matrix = normalized_profiles @ normalized_profiles.T
        return similarity_matrix[upper_i, upper_j]
