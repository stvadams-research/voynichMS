"""Test B: stroke-feature transition constraints at token boundaries."""

from __future__ import annotations

import time
from typing import Any, Iterable

import numpy as np
from rich.console import Console
from rich.progress import Progress

from phase1_foundation.transcription.parsers import ParsedLine
from phase11_stroke.schema import CHAR_INVENTORY, StrokeSchema


def _mutual_information(
    a: np.ndarray, b: np.ndarray, a_cardinality: int, b_cardinality: int
) -> float:
    if a.size == 0 or b.size == 0 or a.size != b.size:
        return 0.0

    joint_codes = a * b_cardinality + b
    joint = np.bincount(joint_codes, minlength=a_cardinality * b_cardinality).astype(np.float64)
    joint = joint.reshape((a_cardinality, b_cardinality))
    n = float(a.size)
    if n <= 0:
        return 0.0

    joint_prob = joint / n
    row_prob = np.sum(joint_prob, axis=1, keepdims=True)
    col_prob = np.sum(joint_prob, axis=0, keepdims=True)
    expected = row_prob @ col_prob

    mask = joint_prob > 0
    ratio = np.zeros_like(joint_prob)
    ratio[mask] = joint_prob[mask] / expected[mask]
    return float(np.sum(joint_prob[mask] * np.log2(ratio[mask])))


class TransitionAnalyzer:
    """Runs Test B (boundary MI, intra-token MI, and abstraction ratio)."""

    def __init__(self, schema: StrokeSchema | None = None):
        self.schema = schema or StrokeSchema()
        self._char_to_idx = {char: idx for idx, char in enumerate(CHAR_INVENTORY)}
        table = self.schema.feature_table()
        feature_matrix = np.array([table[char] for char in CHAR_INVENTORY], dtype=np.float64)
        _, inverse = np.unique(feature_matrix, axis=0, return_inverse=True)
        self._char_to_feature_class = inverse.astype(np.int64)
        self._feature_class_count = int(np.max(self._char_to_feature_class)) + 1

    @staticmethod
    def information_ratio(stroke_mi: float, character_mi: float) -> float:
        if character_mi <= 1e-12:
            return 0.0
        return float(stroke_mi / character_mi)

    def run(
        self,
        parsed_lines: Iterable[ParsedLine],
        schema: StrokeSchema,
        n_permutations: int,
        rng: np.random.Generator,
        console: Console | None = None,
        progress: Progress | None = None,
        task_id: int | None = None,
    ) -> dict[str, Any]:
        t_start = time.time()
        boundary_out, boundary_in, intra_prev, intra_next = self._extract_pairs(parsed_lines)

        if console:
            console.print(
                "[cyan]Test B[/cyan] "
                f"boundary_pairs={boundary_out.size} intra_pairs={intra_prev.size} "
                f"permutations={n_permutations}"
            )

        observed_boundary_mi = _mutual_information(
            self._char_to_feature_class[boundary_out],
            self._char_to_feature_class[boundary_in],
            self._feature_class_count,
            self._feature_class_count,
        )
        observed_intra_mi = _mutual_information(
            self._char_to_feature_class[intra_prev],
            self._char_to_feature_class[intra_next],
            self._feature_class_count,
            self._feature_class_count,
        )
        observed_char_mi = _mutual_information(
            boundary_out,
            boundary_in,
            len(CHAR_INVENTORY),
            len(CHAR_INVENTORY),
        )
        observed_ratio = self.information_ratio(observed_boundary_mi, observed_char_mi)

        null_boundary = np.zeros(n_permutations, dtype=np.float64)
        null_intra = np.zeros(n_permutations, dtype=np.float64)
        loop_start = time.time()
        heartbeat_every = min(500, max(1, n_permutations // 20))
        last_heartbeat = loop_start

        for idx in range(n_permutations):
            perm = rng.permutation(len(CHAR_INVENTORY))
            perm_char_to_feature_class = self._char_to_feature_class[perm]
            null_boundary[idx] = _mutual_information(
                perm_char_to_feature_class[boundary_out],
                perm_char_to_feature_class[boundary_in],
                self._feature_class_count,
                self._feature_class_count,
            )
            null_intra[idx] = _mutual_information(
                perm_char_to_feature_class[intra_prev],
                perm_char_to_feature_class[intra_next],
                self._feature_class_count,
                self._feature_class_count,
            )

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
                console.print(
                    "[cyan]Test B heartbeat[/cyan] "
                    f"{completed}/{n_permutations} elapsed={elapsed:.1f}s eta={eta:.1f}s "
                    f"running_boundary_mean={float(np.mean(null_boundary[:completed])):.4f}"
                )
                last_heartbeat = now

        p_boundary = float(np.mean(null_boundary >= observed_boundary_mi)) if n_permutations else 1.0
        p_intra = float(np.mean(null_intra >= observed_intra_mi)) if n_permutations else 1.0

        b1_determination = "significant" if p_boundary < 0.01 else "null"
        b2_determination = "significant" if p_intra < 0.01 else "null"
        production_constraint = (
            b1_determination == "significant"
            and b2_determination == "significant"
            and observed_intra_mi > observed_boundary_mi
        )
        abstraction_quality = "non_trivial" if observed_ratio > 0.3 else "low"

        return {
            "test_id": "B",
            "B1_boundary_mi": float(observed_boundary_mi),
            "B1_p_value": p_boundary,
            "B1_determination": b1_determination,
            "B2_intra_mi": float(observed_intra_mi),
            "B2_p_value": p_intra,
            "B2_determination": b2_determination,
            "B3_character_mi": float(observed_char_mi),
            "B3_information_ratio": float(observed_ratio),
            "production_constraint_evidence": bool(production_constraint),
            "abstraction_quality": abstraction_quality,
            "n_permutations": int(n_permutations),
            "details": {
                "boundary_pair_count": int(boundary_out.size),
                "intra_pair_count": int(intra_prev.size),
                "null_distribution_summary_boundary": {
                    "mean": float(np.mean(null_boundary)),
                    "std": float(np.std(null_boundary)),
                    "percentile_95": float(np.quantile(null_boundary, 0.95)),
                    "percentile_99": float(np.quantile(null_boundary, 0.99)),
                },
                "null_distribution_summary_intra": {
                    "mean": float(np.mean(null_intra)),
                    "std": float(np.std(null_intra)),
                    "percentile_95": float(np.quantile(null_intra, 0.95)),
                    "percentile_99": float(np.quantile(null_intra, 0.99)),
                },
            },
            "duration_seconds": float(time.time() - t_start),
        }

    def _extract_pairs(
        self, parsed_lines: Iterable[ParsedLine]
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        boundary_out: list[int] = []
        boundary_in: list[int] = []
        intra_prev: list[int] = []
        intra_next: list[int] = []

        for line in parsed_lines:
            tokens = [token.content for token in line.tokens]
            line_first_last: list[tuple[int, int]] = []

            for token in tokens:
                valid_chars = [char for char in token if char in self._char_to_idx]
                if not valid_chars:
                    continue
                first_idx = self._char_to_idx[valid_chars[0]]
                last_idx = self._char_to_idx[valid_chars[-1]]
                line_first_last.append((first_idx, last_idx))

                for pos in range(len(token) - 1):
                    char_left = token[pos]
                    char_right = token[pos + 1]
                    if char_left in self._char_to_idx and char_right in self._char_to_idx:
                        intra_prev.append(self._char_to_idx[char_left])
                        intra_next.append(self._char_to_idx[char_right])

            for idx in range(len(line_first_last) - 1):
                boundary_out.append(line_first_last[idx][1])
                boundary_in.append(line_first_last[idx + 1][0])

        return (
            np.array(boundary_out, dtype=np.int64),
            np.array(boundary_in, dtype=np.int64),
            np.array(intra_prev, dtype=np.int64),
            np.array(intra_next, dtype=np.int64),
        )
