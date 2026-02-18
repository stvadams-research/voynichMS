"""
Discrimination-oriented bounded checks for matched corpora.

The goal is not semantic proof. We quantify which corpus family Voynich is
closest to under simple, reproducible TF-IDF similarity models.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier

logger = logging.getLogger(__name__)


@dataclass
class DiscriminationCheckConfig:
    window_size: int = 72
    windows_per_dataset: int = 160
    max_features: int = 2000
    ngram_min: int = 1
    ngram_max: int = 1
    train_fraction: float = 0.7
    random_state: int = 42
    voynich_dataset_id: str = "voynich_real"


class DiscriminationCheckAnalyzer:
    """Runs bounded train/test corpus discrimination diagnostics."""

    def __init__(self, config: DiscriminationCheckConfig | None = None):
        self.config = config or DiscriminationCheckConfig()
        self._rng = np.random.default_rng(self.config.random_state)

    def analyze(self, dataset_tokens: dict[str, Sequence[str]]) -> dict[str, Any]:
        docs, labels, doc_counts = self._build_balanced_docs(dataset_tokens)
        label_set = sorted(set(labels))
        if len(docs) < 3 or len(label_set) < 2:
            return {
                "status": "insufficient_data",
                "config": self._config_dict(),
                "doc_counts": doc_counts,
                "n_docs": len(docs),
                "n_labels": len(label_set),
            }

        split = self._stratified_split(labels)
        if split is None:
            return {
                "status": "insufficient_data",
                "reason": "not_enough_samples_per_label_for_train_test",
                "config": self._config_dict(),
                "doc_counts": doc_counts,
                "n_docs": len(docs),
                "n_labels": len(label_set),
            }

        train_idx, test_idx = split
        train_docs = [docs[i] for i in train_idx]
        test_docs = [docs[i] for i in test_idx]
        y_train = np.array([labels[i] for i in train_idx])
        y_test = np.array([labels[i] for i in test_idx])
        classes = sorted(set(y_train.tolist()))

        vectorizer = TfidfVectorizer(
            max_features=self.config.max_features,
            token_pattern=r"(?u)\b\w+\b",
            lowercase=False,
            ngram_range=(self.config.ngram_min, self.config.ngram_max),
        )
        X_train = vectorizer.fit_transform(train_docs)
        X_test = vectorizer.transform(test_docs)

        # Nearest-centroid in cosine space.
        centroid_data = self._compute_centroids(X_train, y_train, classes)
        y_pred_centroid = self._predict_nearest_centroid(X_test, centroid_data["matrix"], classes)
        centroid_conf = self._build_confusion(y_test.tolist(), y_pred_centroid, classes)
        centroid_acc = float(np.mean(y_test == np.array(y_pred_centroid)))

        # 1-NN in cosine space.
        X_train_dense = X_train.toarray()
        X_test_dense = X_test.toarray()
        knn = KNeighborsClassifier(n_neighbors=1, metric="cosine", algorithm="brute")
        knn.fit(X_train_dense, y_train)
        y_pred_knn = knn.predict(X_test_dense).tolist()
        knn_conf = self._build_confusion(y_test.tolist(), y_pred_knn, classes)
        knn_acc = float(np.mean(y_test == np.array(y_pred_knn)))

        centroid_distances = self._pairwise_centroid_distances(centroid_data["matrix"], classes)
        voynich_summary = self._voynich_summary(
            classes,
            centroid_distances,
            centroid_conf["row_normalized"],
            knn_conf["row_normalized"],
        )

        return {
            "status": "ok",
            "config": self._config_dict(),
            "doc_counts": doc_counts,
            "n_docs": len(docs),
            "n_features": int(X_train.shape[1]),
            "n_train": len(train_idx),
            "n_test": len(test_idx),
            "classes": classes,
            "models": {
                "nearest_centroid": {
                    "accuracy": centroid_acc,
                    "confusion_counts": centroid_conf["counts"],
                    "confusion_row_normalized": centroid_conf["row_normalized"],
                },
                "knn_1_cosine": {
                    "accuracy": knn_acc,
                    "confusion_counts": knn_conf["counts"],
                    "confusion_row_normalized": knn_conf["row_normalized"],
                },
            },
            "centroid_cosine_distance": centroid_distances,
            "voynich_summary": voynich_summary,
        }

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

    def _stratified_split(self, labels: list[str]) -> tuple[list[int], list[int]] | None:
        by_label: dict[str, list[int]] = defaultdict(list)
        for idx, label in enumerate(labels):
            by_label[label].append(idx)

        train_idx: list[int] = []
        test_idx: list[int] = []
        for label, idxs in by_label.items():
            if len(idxs) < 2:
                logger.warning("Label %s has <2 samples; cannot split", label)
                return None

            shuffled = np.array(idxs)
            self._rng.shuffle(shuffled)

            n_train = int(np.floor(len(shuffled) * self.config.train_fraction))
            n_train = max(1, min(len(shuffled) - 1, n_train))
            train_idx.extend(shuffled[:n_train].tolist())
            test_idx.extend(shuffled[n_train:].tolist())

        return train_idx, test_idx

    def _compute_centroids(
        self, X_train: Any, y_train: np.ndarray, classes: list[str]
    ) -> dict[str, np.ndarray]:
        centroids = []
        for label in classes:
            idx = np.where(y_train == label)[0]
            centroid = np.asarray(X_train[idx].mean(axis=0)).ravel()
            centroids.append(centroid)
        matrix = np.vstack(centroids)
        return {"matrix": self._l2_normalize_rows(matrix)}

    def _predict_nearest_centroid(
        self, X_test: Any, centroid_matrix: np.ndarray, classes: list[str]
    ) -> list[str]:
        X = self._l2_normalize_rows(X_test.toarray())
        sims = X @ centroid_matrix.T
        pred_idx = np.argmax(sims, axis=1)
        return [classes[i] for i in pred_idx]

    def _pairwise_centroid_distances(
        self, centroid_matrix: np.ndarray, classes: list[str]
    ) -> dict[str, dict[str, float]]:
        similarities = centroid_matrix @ centroid_matrix.T
        distances = 1.0 - similarities
        matrix: dict[str, dict[str, float]] = {}
        for i, row_label in enumerate(classes):
            matrix[row_label] = {}
            for j, col_label in enumerate(classes):
                matrix[row_label][col_label] = float(distances[i, j])
        return matrix

    def _build_confusion(
        self, y_true: list[str], y_pred: list[str], classes: list[str]
    ) -> dict[str, dict[str, dict[str, float] | dict[str, int]]]:
        counts: dict[str, dict[str, int]] = {
            true_label: {pred_label: 0 for pred_label in classes} for true_label in classes
        }
        for true_label, pred_label in zip(y_true, y_pred, strict=True):
            counts[true_label][pred_label] += 1

        row_norm: dict[str, dict[str, float]] = {}
        for true_label, row in counts.items():
            total = sum(row.values())
            if total == 0:
                row_norm[true_label] = {pred_label: 0.0 for pred_label in classes}
                continue
            row_norm[true_label] = {
                pred_label: float(row[pred_label] / total) for pred_label in classes
            }

        return {"counts": counts, "row_normalized": row_norm}

    def _voynich_summary(
        self,
        classes: list[str],
        centroid_distances: dict[str, dict[str, float]],
        centroid_confusion: dict[str, dict[str, float]],
        knn_confusion: dict[str, dict[str, float]],
    ) -> dict[str, Any]:
        v = self.config.voynich_dataset_id
        if v not in classes:
            return {"status": "voynich_label_not_found"}

        close = [
            {"dataset_id": label, "cosine_distance": centroid_distances[v][label]}
            for label in classes
            if label != v
        ]
        close.sort(key=lambda x: x["cosine_distance"])

        return {
            "status": "ok",
            "voynich_dataset_id": v,
            "closest_centroids": close,
            "voynich_test_assignment_nearest_centroid": centroid_confusion.get(v, {}),
            "voynich_test_assignment_knn_1": knn_confusion.get(v, {}),
        }

    def _l2_normalize_rows(self, X: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return X / norms

    def _config_dict(self) -> dict[str, Any]:
        return {
            "window_size": self.config.window_size,
            "windows_per_dataset": self.config.windows_per_dataset,
            "max_features": self.config.max_features,
            "ngram_min": self.config.ngram_min,
            "ngram_max": self.config.ngram_max,
            "train_fraction": self.config.train_fraction,
            "random_state": self.config.random_state,
            "voynich_dataset_id": self.config.voynich_dataset_id,
        }
