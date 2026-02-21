"""Corpus-wide stroke feature extraction for Phase 11."""

from __future__ import annotations

import time
from collections import Counter, defaultdict
from collections.abc import Iterable
from typing import Any

import numpy as np
from rich.console import Console

from phase1_foundation.transcription.parsers import ParsedLine
from phase11_stroke.schema import FEATURE_NAMES, StrokeSchema


class StrokeExtractor:
    """Extracts stroke-based token, line, and page summaries from parsed EVA lines."""

    def __init__(self, schema: StrokeSchema):
        self.schema = schema
        self._inventory = set(schema.char_inventory())

    def extract_corpus(
        self, parsed_lines: Iterable[ParsedLine], console: Console | None = None
    ) -> dict[str, Any]:
        t_start = time.time()
        line_features: list[dict[str, Any]] = []
        token_occurrences: list[dict[str, Any]] = []
        skipped_chars_by_symbol: Counter[str] = Counter()

        page_running_aggregate: dict[str, np.ndarray] = defaultdict(
            lambda: np.zeros(len(FEATURE_NAMES), dtype=np.float64)
        )
        page_running_mean_sum: dict[str, np.ndarray] = defaultdict(
            lambda: np.zeros(len(FEATURE_NAMES), dtype=np.float64)
        )
        page_line_counts: Counter[str] = Counter()
        page_token_counts: Counter[str] = Counter()

        token_type_count: Counter[str] = Counter()
        token_type_mean_sum: dict[str, np.ndarray] = defaultdict(
            lambda: np.zeros(len(FEATURE_NAMES), dtype=np.float64)
        )
        token_type_boundary_sum: dict[str, np.ndarray] = defaultdict(
            lambda: np.zeros(len(FEATURE_NAMES) * 2, dtype=np.float64)
        )
        token_type_aggregate_sum: dict[str, np.ndarray] = defaultdict(
            lambda: np.zeros(len(FEATURE_NAMES), dtype=np.float64)
        )
        token_type_recognized_sum: Counter[str] = Counter()
        token_type_skipped_sum: Counter[str] = Counter()

        total_lines = 0
        total_tokens = 0
        total_chars = 0
        recognized_chars = 0

        current_page = None
        for parsed_line in parsed_lines:
            total_lines += 1
            page_id = parsed_line.folio
            line_id = f"{parsed_line.folio}:{parsed_line.line_index}"
            if console and current_page != page_id:
                console.print(f"[cyan]Processing page[/cyan] {page_id}")
                current_page = page_id

            tokens = [token.content for token in parsed_line.tokens]
            line_profiles_mean: list[np.ndarray] = []
            line_profiles_aggregate: list[np.ndarray] = []

            for token_idx, token in enumerate(tokens):
                total_tokens += 1
                total_chars += len(token)

                known_chars = [char for char in token if char in self._inventory]
                unknown_chars = [char for char in token if char not in self._inventory]
                recognized_count = len(known_chars)
                skipped_count = len(unknown_chars)
                recognized_chars += recognized_count
                if skipped_count:
                    skipped_chars_by_symbol.update(unknown_chars)

                mean_profile = self.schema.get_token_profile(token, mode="mean")
                boundary_profile = self.schema.get_token_profile(token, mode="boundary")
                aggregate_profile = self.schema.get_token_profile(token, mode="aggregate")
                line_profiles_mean.append(mean_profile)
                line_profiles_aggregate.append(aggregate_profile)

                token_occurrences.append(
                    {
                        "page_id": page_id,
                        "line_id": line_id,
                        "line_index": int(parsed_line.line_index),
                        "token_index": int(token_idx),
                        "token": token,
                        "mean_profile": mean_profile.tolist(),
                        "boundary_profile": boundary_profile.tolist(),
                        "aggregate_profile": aggregate_profile.tolist(),
                        "recognized_char_count": int(recognized_count),
                        "skipped_char_count": int(skipped_count),
                        "first_char": known_chars[0] if known_chars else "",
                        "last_char": known_chars[-1] if known_chars else "",
                    }
                )

                token_type_count[token] += 1
                token_type_mean_sum[token] += mean_profile
                token_type_boundary_sum[token] += boundary_profile
                token_type_aggregate_sum[token] += aggregate_profile
                token_type_recognized_sum[token] += recognized_count
                token_type_skipped_sum[token] += skipped_count

            if line_profiles_mean:
                line_mean_profile = np.mean(np.vstack(line_profiles_mean), axis=0, dtype=np.float64)
                line_aggregate_profile = np.sum(
                    np.vstack(line_profiles_aggregate), axis=0, dtype=np.float64
                )
            else:
                line_mean_profile = np.zeros(len(FEATURE_NAMES), dtype=np.float64)
                line_aggregate_profile = np.zeros(len(FEATURE_NAMES), dtype=np.float64)

            line_features.append(
                {
                    "page_id": page_id,
                    "line_id": line_id,
                    "line_index": int(parsed_line.line_index),
                    "tokens": tokens,
                    "token_count": int(len(tokens)),
                    "unique_token_count": int(len(set(tokens))),
                    "mean_profile": line_mean_profile.tolist(),
                    "aggregate_profile": line_aggregate_profile.tolist(),
                }
            )

            page_running_aggregate[page_id] += line_aggregate_profile
            page_running_mean_sum[page_id] += line_mean_profile
            page_line_counts[page_id] += 1
            page_token_counts[page_id] += len(tokens)

            if console and total_lines % 100 == 0:
                elapsed = time.time() - t_start
                console.print(
                    "[cyan]Extraction progress[/cyan] "
                    f"lines={total_lines} tokens={total_tokens} elapsed={elapsed:.1f}s"
                )

        token_type_features: dict[str, Any] = {}
        for token in sorted(token_type_count):
            count = token_type_count[token]
            token_type_features[token] = {
                "count": int(count),
                "mean_profile": (token_type_mean_sum[token] / count).tolist(),
                "boundary_profile": (token_type_boundary_sum[token] / count).tolist(),
                "aggregate_profile": (token_type_aggregate_sum[token] / count).tolist(),
                "recognized_char_count_mean": float(token_type_recognized_sum[token] / count),
                "skipped_char_count_mean": float(token_type_skipped_sum[token] / count),
            }

        page_features: dict[str, Any] = {}
        for page_id in sorted(page_line_counts):
            line_count = page_line_counts[page_id]
            page_features[page_id] = {
                "line_count": int(line_count),
                "token_count": int(page_token_counts[page_id]),
                "mean_profile": (page_running_mean_sum[page_id] / line_count).tolist(),
                "aggregate_profile": page_running_aggregate[page_id].tolist(),
            }

        result: dict[str, Any] = {
            "feature_names": self.schema.feature_names(),
            "char_inventory": self.schema.char_inventory(),
            "schema_version": self.schema.schema_version(),
            "corpus_stats": {
                "line_count": int(total_lines),
                "token_count": int(total_tokens),
                "character_count": int(total_chars),
                "recognized_character_count": int(recognized_chars),
                "skipped_character_count": int(total_chars - recognized_chars),
                "token_type_count": int(len(token_type_features)),
            },
            "skipped_characters": {
                "total": int(total_chars - recognized_chars),
                "by_symbol": dict(sorted(skipped_chars_by_symbol.items())),
            },
            "token_type_features": token_type_features,
            "line_features": line_features,
            "page_features": page_features,
            "token_occurrences": token_occurrences,
        }

        if console:
            elapsed = time.time() - t_start
            console.print(
                "[green]Extraction complete[/green] "
                f"lines={total_lines} tokens={total_tokens} "
                f"skipped_chars={total_chars - recognized_chars} elapsed={elapsed:.1f}s"
            )
        return result

