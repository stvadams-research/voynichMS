"""
Bounded latent-space projection diagnostics.

This module treats low-dimensional projections as descriptive aids and pairs them
with permutation-based silhouette baselines to reduce over-interpretation risk.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score

logger = logging.getLogger(__name__)


@dataclass
class ProjectionDiagnosticsConfig:
    window_size: int = 72
    windows_per_dataset: int = 160
    max_features: int = 2000
    tsne_perplexity: int = 30
    permutations: int = 100
    random_state: int = 42


class ProjectionDiagnosticsAnalyzer:
    """
    Runs bounded projection checks across matched corpora.

    Workflow:
    1) Build balanced document windows per dataset.
    2) Vectorize in TF-IDF space.
    3) Score separability in high-dimensional space.
    4) Project to 2D via PCA/t-SNE/(optional UMAP), and re-score.
    5) Compare each observed score to a label permutation baseline.
    """

    def __init__(self, config: ProjectionDiagnosticsConfig | None = None):
        self.config = config or ProjectionDiagnosticsConfig()
        self._rng = np.random.default_rng(self.config.random_state)

    def analyze(self, dataset_tokens: dict[str, Sequence[str]]) -> dict[str, Any]:
        docs, labels, doc_counts = self._build_balanced_docs(dataset_tokens)
        if len(docs) < 3 or len(set(labels)) < 2:
            logger.warning("ProjectionDiagnosticsAnalyzer: insufficient data")
            return {
                "status": "insufficient_data",
                "config": self._config_dict(),
                "doc_counts": doc_counts,
                "n_docs": len(docs),
                "n_labels": len(set(labels)),
                "methods": {},
                "projections": {},
            }

        vectorizer = TfidfVectorizer(
            max_features=self.config.max_features,
            token_pattern=r"(?u)\b\w+\b",
            lowercase=False,
        )
        X = vectorizer.fit_transform(docs)
        y = np.array(labels)
        dense = X.toarray()

        results: dict[str, Any] = {
            "status": "ok",
            "config": self._config_dict(),
            "doc_counts": doc_counts,
            "n_docs": int(X.shape[0]),
            "n_features": int(X.shape[1]),
            "methods": {},
            "projections": {},
        }

        # High-dimensional baseline
        results["methods"]["high_dim_tfidf"] = self._permutation_baseline(
            X,
            y,
            metric="cosine",
        )

        # PCA projection
        pca = PCA(n_components=2, random_state=self.config.random_state)
        pca_2d = pca.fit_transform(dense)
        pca_eval = self._permutation_baseline(pca_2d, y, metric="euclidean")
        pca_eval["explained_variance_ratio"] = [float(v) for v in pca.explained_variance_ratio_]
        results["methods"]["pca_2d"] = pca_eval
        results["projections"]["pca_2d"] = self._pack_projection(pca_2d, labels)

        # t-SNE projection
        tsne_perplexity = self._safe_tsne_perplexity(len(docs), self.config.tsne_perplexity)
        if tsne_perplexity is None:
            results["methods"]["tsne_2d"] = {
                "status": "unavailable",
                "reason": "insufficient_samples_for_tsne",
            }
        else:
            tsne = TSNE(
                n_components=2,
                perplexity=float(tsne_perplexity),
                init="pca",
                learning_rate="auto",
                random_state=self.config.random_state,
            )
            tsne_2d = tsne.fit_transform(dense)
            tsne_eval = self._permutation_baseline(tsne_2d, y, metric="euclidean")
            tsne_eval["perplexity"] = float(tsne_perplexity)
            results["methods"]["tsne_2d"] = tsne_eval
            results["projections"]["tsne_2d"] = self._pack_projection(tsne_2d, labels)

        # Optional UMAP projection
        try:
            import umap  # type: ignore

            umap_model = umap.UMAP(
                n_components=2,
                n_neighbors=15,
                min_dist=0.1,
                random_state=self.config.random_state,
            )
            umap_2d = umap_model.fit_transform(dense)
            results["methods"]["umap_2d"] = self._permutation_baseline(
                umap_2d,
                y,
                metric="euclidean",
            )
            results["projections"]["umap_2d"] = self._pack_projection(umap_2d, labels)
        except Exception as exc:
            results["methods"]["umap_2d"] = {
                "status": "unavailable",
                "reason": str(exc),
            }

        return results

    def _build_balanced_docs(
        self, dataset_tokens: dict[str, Sequence[str]]
    ) -> tuple[list[str], list[str], dict[str, int]]:
        docs: list[str] = []
        labels: list[str] = []
        counts: dict[str, int] = {}
        w = self.config.window_size

        for dataset_id, tokens in dataset_tokens.items():
            positions = list(range(0, max(len(tokens) - w + 1, 0), w))
            if not positions:
                counts[dataset_id] = 0
                continue

            if len(positions) <= self.config.windows_per_dataset:
                chosen = positions
            else:
                idxs = np.linspace(
                    0, len(positions) - 1, self.config.windows_per_dataset, dtype=int
                )
                chosen = [positions[i] for i in idxs]

            counts[dataset_id] = len(chosen)
            for start in chosen:
                docs.append(" ".join(tokens[start : start + w]))
                labels.append(dataset_id)

        return docs, labels, counts

    def _safe_silhouette(self, X: Any, y: np.ndarray, metric: str) -> float | None:
        unique_labels = np.unique(y)
        if len(unique_labels) < 2 or len(y) <= len(unique_labels):
            return None
        try:
            return float(silhouette_score(X, y, metric=metric))
        except Exception as exc:
            logger.warning("Silhouette failed for metric=%s: %s", metric, exc)
            return None

    def _permutation_baseline(self, X: Any, y: np.ndarray, metric: str) -> dict[str, Any]:
        observed = self._safe_silhouette(X, y, metric=metric)
        if observed is None:
            return {"status": "unavailable", "reason": "silhouette_failed"}

        perm_scores: list[float] = []
        for _ in range(self.config.permutations):
            shuffled = self._rng.permutation(y)
            score = self._safe_silhouette(X, shuffled, metric=metric)
            if score is not None:
                perm_scores.append(score)

        if not perm_scores:
            return {"status": "unavailable", "reason": "permutation_failed"}

        perm = np.array(perm_scores)
        mean = float(np.mean(perm))
        std = float(np.std(perm))
        z_score = float((observed - mean) / std) if std > 0 else None
        p_ge_obs = float((np.sum(perm >= observed) + 1) / (len(perm) + 1))

        return {
            "status": "ok",
            "metric": metric,
            "observed_silhouette": float(observed),
            "perm_mean": mean,
            "perm_std": std,
            "z_score": z_score,
            "p_ge_obs": p_ge_obs,
            "num_permutations": len(perm_scores),
        }

    def _pack_projection(
        self, points_2d: np.ndarray, labels: Sequence[str]
    ) -> list[dict[str, Any]]:
        packed: list[dict[str, Any]] = []
        for idx, (x, y) in enumerate(points_2d):
            packed.append(
                {
                    "index": idx,
                    "dataset_id": labels[idx],
                    "x": float(x),
                    "y": float(y),
                }
            )
        return packed

    def _safe_tsne_perplexity(self, n_samples: int, target: int) -> int | None:
        if n_samples < 4:
            return None
        max_allowed = n_samples - 1
        return max(2, min(target, max_allowed))

    def _config_dict(self) -> dict[str, Any]:
        return {
            "window_size": self.config.window_size,
            "windows_per_dataset": self.config.windows_per_dataset,
            "max_features": self.config.max_features,
            "tsne_perplexity": self.config.tsne_perplexity,
            "permutations": self.config.permutations,
            "random_state": self.config.random_state,
        }
