from __future__ import annotations

import hashlib
import math
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass

from .generator import Mulberry32, PageGenerationOptions, PageGeneratorModel
from .metrics import sanitize_token, score_alignment, split_tokens


@dataclass
class TrainingStats:
    global_tokens: Counter
    section_tokens: dict[str, Counter]
    global_bigrams: Counter
    section_bigrams: dict[str, Counter]
    first_tokens_global: Counter
    first_tokens_section: dict[str, Counter]
    line_bank: list[dict]
    section_line_bank: dict[str, list[dict]]


def actual_folio_text(folio: dict, fmt: str = "content") -> str:
    rows: list[str] = []
    for line in folio.get("lines", []):
        location = str(line.get("location", "")).strip()
        content = str(line.get("content", "")).strip()
        if not content:
            continue
        if fmt == "ivtff" and location:
            rows.append(f"<{location}>      {content}")
        else:
            rows.append(content)
    return "\n".join(rows)


def content_lines(folio: dict) -> list[str]:
    return [str(line.get("content", "")).strip() for line in folio.get("lines", []) if str(line.get("content", "")).strip()]


def marker_from_location(location: str) -> str:
    if "," not in location:
        return ""
    return location.split(",", 1)[1].strip()


def sanitized_tokens_from_content(content: str) -> list[str]:
    return [token for token in (sanitize_token(token) for token in split_tokens(content)) if token]


def stable_seed(base_seed: int, folio_id: str, method_tag: str) -> int:
    digest = hashlib.sha256(f"{base_seed}:{method_tag}:{folio_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def build_training_stats(model: PageGeneratorModel, train_folios: list[str]) -> TrainingStats:
    global_tokens: Counter = Counter()
    section_tokens: dict[str, Counter] = defaultdict(Counter)
    global_bigrams: Counter = Counter()
    section_bigrams: dict[str, Counter] = defaultdict(Counter)
    first_tokens_global: Counter = Counter()
    first_tokens_section: dict[str, Counter] = defaultdict(Counter)
    line_bank: list[dict] = []
    section_line_bank: dict[str, list[dict]] = defaultdict(list)

    for folio_id in train_folios:
        folio = model.folio_map.get(folio_id)
        if not folio:
            continue
        section = str((model.schedule_map.get(folio_id) or {}).get("section") or "Other")
        lines = content_lines(folio)
        line_total = max(len(lines), 1)
        for line_idx, content in enumerate(lines):
            tokens = sanitized_tokens_from_content(content)
            if not tokens:
                continue

            global_tokens.update(tokens)
            section_tokens[section].update(tokens)
            first_tokens_global[tokens[0]] += 1
            first_tokens_section[section][tokens[0]] += 1

            for left, right in zip(tokens, tokens[1:]):
                global_bigrams[(left, right)] += 1
                section_bigrams[section][(left, right)] += 1

            marker = marker_from_location(str(folio.get("lines", [])[line_idx].get("location", "")))
            marker_bucket = "first" if line_idx == 0 else "cont"
            line_record = {
                "folio": folio_id,
                "section": section,
                "line_index": line_idx,
                "line_index_norm": line_idx / max(line_total - 1, 1),
                "marker": marker,
                "marker_bucket": marker_bucket,
                "token_count": len(tokens),
                "tokens": tokens,
                "content": content,
            }
            line_bank.append(line_record)
            section_line_bank[section].append(line_record)

    return TrainingStats(
        global_tokens=global_tokens,
        section_tokens=dict(section_tokens),
        global_bigrams=global_bigrams,
        section_bigrams=dict(section_bigrams),
        first_tokens_global=first_tokens_global,
        first_tokens_section=dict(first_tokens_section),
        line_bank=line_bank,
        section_line_bank=dict(section_line_bank),
    )


def _language_score(
    token: str,
    prev_token: str | None,
    section: str,
    token_pos: int,
    stats: TrainingStats,
) -> float:
    section_count = stats.section_tokens.get(section, Counter()).get(token, 0)
    global_count = stats.global_tokens.get(token, 0)
    score = math.log1p((2.0 * section_count) + global_count)

    if prev_token is not None:
        section_bigram = stats.section_bigrams.get(section, Counter()).get((prev_token, token), 0)
        global_bigram = stats.global_bigrams.get((prev_token, token), 0)
        score += math.log1p((3.0 * section_bigram) + global_bigram)
    elif token_pos == 0:
        section_first = stats.first_tokens_section.get(section, Counter()).get(token, 0)
        global_first = stats.first_tokens_global.get(token, 0)
        score += math.log1p((2.0 * section_first) + global_first)

    return score


def generate_phase18_baseline(
    model: PageGeneratorModel,
    folio_id: str,
    seed: int = 42,
) -> dict:
    schedule = model.schedule_map.get(folio_id, {})
    hand = str(schedule.get("hand") or "Unknown")
    profile = "hand2" if hand == "Hand2" else "hand1"
    options = PageGenerationOptions(
        folio_id=folio_id,
        seed=stable_seed(seed, folio_id, "baseline"),
        schedule_mode="auto",
        line_count_mode="observed",
        min_words=6,
        max_words=12,
        profile=profile,
        canonical_filter=True,
        format="content",
    )
    return model.generate_page(options)


def generate_unigram_window_control(
    model: PageGeneratorModel,
    folio_id: str,
    stats: TrainingStats,
    seed: int = 42,
) -> dict:
    folio = model.folio_map[folio_id]
    schedule = model.schedule_map.get(folio_id, {})
    section = str(schedule.get("section") or "Other")

    rng = Mulberry32(stable_seed(seed, folio_id, "unigram_control"))
    observed_affixes = model._get_observed_affixes(folio)  # noqa: SLF001
    raw_lines = content_lines(folio)
    target_words = [max(1, len(sanitized_tokens_from_content(line))) for line in raw_lines]

    generated_lines: list[str] = []
    diagnostics: list[dict] = []

    for line_idx in range(len(raw_lines)):
        offset, source = model.resolve_line_offset(schedule, line_idx, "auto")
        words_target = target_words[line_idx]
        current_window = model._rand_int(rng, 0, model.num_windows - 1)  # noqa: SLF001
        tokens: list[str] = []
        for _ in range(words_target):
            shifted_window = model._modulo(current_window + offset, model.num_windows)  # noqa: SLF001
            candidates = [
                word
                for word in model.get_window_words(shifted_window)
                if not any(ch.isupper() for ch in word)
            ]
            token = _pick_frequent_candidate(candidates, section, stats)
            assigned_raw = model.lattice_map.get(token)
            assigned_window = (
                model._modulo(current_window + 1, model.num_windows)  # noqa: SLF001
                if assigned_raw is None
                else int(assigned_raw)
            )
            current_window = model._modulo(assigned_window - offset, model.num_windows)  # noqa: SLF001
            tokens.append(token)

        affix = observed_affixes[line_idx] if line_idx < len(observed_affixes) else {"prefix": "", "suffix": ""}
        content = ".".join(tokens)
        if affix.get("prefix"):
            content = f"{affix['prefix']}{content}"
        if affix.get("suffix"):
            content = f"{content}{affix['suffix']}"
        generated_lines.append(content)
        diagnostics.append(
            {
                "line_index": line_idx,
                "offset": offset,
                "offset_source": source,
                "target_words": words_target,
            }
        )

    return {
        "ok": True,
        "folioId": folio_id,
        "method": "unigram_window_control",
        "text": "\n".join(generated_lines),
        "contentLines": generated_lines,
        "diagnostics": diagnostics,
    }


def generate_line_conditioned(
    model: PageGeneratorModel,
    folio_id: str,
    stats: TrainingStats,
    seed: int = 42,
    beam_width: int = 4,
    max_candidates: int = 20,
) -> dict:
    folio = model.folio_map[folio_id]
    schedule = model.schedule_map.get(folio_id, {})
    section = str(schedule.get("section") or "Other")
    hand = str(schedule.get("hand") or "Unknown")
    profile = "hand2" if hand == "Hand2" else "hand1"

    rng = Mulberry32(stable_seed(seed, folio_id, "line_conditioned"))

    observed_markers = model._get_observed_markers(folio)  # noqa: SLF001
    observed_affixes = model._get_observed_affixes(folio)  # noqa: SLF001
    raw_lines = content_lines(folio)
    target_words = [max(1, len(sanitized_tokens_from_content(line))) for line in raw_lines]

    generated_lines: list[str] = []
    diagnostics: list[dict] = []

    for line_idx in range(len(raw_lines)):
        offset, source = model.resolve_line_offset(schedule, line_idx, "auto")
        words_target = target_words[line_idx]
        current_window = model._rand_int(rng, 0, model.num_windows - 1)  # noqa: SLF001

        beam = [
            {
                "tokens": [],
                "current_window": current_window,
                "prev_token": None,
                "score": 0.0,
            }
        ]

        for token_pos in range(words_target):
            next_beam = []
            for state in beam:
                shifted_window = model._modulo(state["current_window"] + offset, model.num_windows)  # noqa: SLF001
                candidates = [
                    word
                    for word in model.get_window_words(shifted_window)
                    if not any(ch.isupper() for ch in word)
                ]
                if not candidates:
                    candidates = ["???"]

                scored_candidates = sorted(
                    candidates,
                    key=lambda token: _language_score(
                        token,
                        state["prev_token"],
                        section,
                        token_pos,
                        stats,
                    ),
                    reverse=True,
                )[:max_candidates]

                for token in scored_candidates:
                    token_score = _language_score(
                        token,
                        state["prev_token"],
                        section,
                        token_pos,
                        stats,
                    )
                    assigned_raw = model.lattice_map.get(token)
                    assigned_window = (
                        model._modulo(state["current_window"] + 1, model.num_windows)  # noqa: SLF001
                        if assigned_raw is None
                        else int(assigned_raw)
                    )
                    next_window = model._modulo(assigned_window - offset, model.num_windows)  # noqa: SLF001
                    next_beam.append(
                        {
                            "tokens": state["tokens"] + [token],
                            "current_window": next_window,
                            "prev_token": token,
                            "score": state["score"] + token_score,
                        }
                    )

            next_beam.sort(key=lambda state: state["score"], reverse=True)
            beam = next_beam[:beam_width] if next_beam else beam

        best = beam[0]
        affix = observed_affixes[line_idx] if line_idx < len(observed_affixes) else {"prefix": "", "suffix": ""}
        marker = observed_markers[line_idx] if line_idx < len(observed_markers) else ("@P0" if line_idx == 0 else "+P0")
        content = ".".join(best["tokens"])
        if affix.get("prefix"):
            content = f"{affix['prefix']}{content}"
        if affix.get("suffix"):
            content = f"{content}{affix['suffix']}"
        generated_lines.append(content)

        diagnostics.append(
            {
                "line_index": line_idx,
                "offset": offset,
                "offset_source": source,
                "marker": marker,
                "beam_score": best["score"],
                "target_words": words_target,
            }
        )

    return {
        "ok": True,
        "folioId": folio_id,
        "method": "line_conditioned_decoder",
        "text": "\n".join(generated_lines),
        "contentLines": generated_lines,
        "diagnostics": diagnostics,
        "profile": profile,
    }


def _best_retrieval_line(
    section: str,
    marker_bucket: str,
    line_index_norm: float,
    target_words: int,
    stats: TrainingStats,
) -> dict | None:
    pool = stats.section_line_bank.get(section) or stats.line_bank
    if not pool:
        return None

    def rank(item: dict) -> float:
        marker_match = 1.0 if item.get("marker_bucket") == marker_bucket else 0.0
        length_gap = abs(item.get("token_count", 0) - target_words)
        length_score = 1.0 / (1.0 + length_gap)
        index_gap = abs(item.get("line_index_norm", 0.0) - line_index_norm)
        index_score = 1.0 - min(1.0, index_gap)
        return (2.0 * marker_match) + (1.5 * length_score) + (1.0 * index_score)

    return max(pool, key=rank)


def _pick_frequent_candidate(candidates: list[str], section: str, stats: TrainingStats) -> str:
    if not candidates:
        return "???"
    section_counter = stats.section_tokens.get(section, Counter())

    def score(token: str) -> tuple[int, int, str]:
        return (
            section_counter.get(token, 0),
            stats.global_tokens.get(token, 0),
            token,
        )

    return max(candidates, key=score)


def generate_retrieval_edit(
    model: PageGeneratorModel,
    folio_id: str,
    stats: TrainingStats,
    seed: int = 42,
) -> dict:
    folio = model.folio_map[folio_id]
    schedule = model.schedule_map.get(folio_id, {})
    section = str(schedule.get("section") or "Other")

    rng = Mulberry32(stable_seed(seed, folio_id, "retrieval_edit"))

    observed_markers = model._get_observed_markers(folio)  # noqa: SLF001
    observed_affixes = model._get_observed_affixes(folio)  # noqa: SLF001
    raw_lines = content_lines(folio)
    target_words = [max(1, len(sanitized_tokens_from_content(line))) for line in raw_lines]

    generated_lines: list[str] = []
    diagnostics: list[dict] = []
    line_total = max(len(raw_lines), 1)

    for line_idx in range(len(raw_lines)):
        offset, source = model.resolve_line_offset(schedule, line_idx, "auto")
        marker_bucket = "first" if line_idx == 0 else "cont"
        line_index_norm = line_idx / max(line_total - 1, 1)
        target_word_count = target_words[line_idx]

        retrieved = _best_retrieval_line(
            section=section,
            marker_bucket=marker_bucket,
            line_index_norm=line_index_norm,
            target_words=target_word_count,
            stats=stats,
        )
        retrieved_tokens = list(retrieved.get("tokens", [])) if retrieved else []

        current_window = model._rand_int(rng, 0, model.num_windows - 1)  # noqa: SLF001
        tokens: list[str] = []
        for token_pos in range(target_word_count):
            shifted_window = model._modulo(current_window + offset, model.num_windows)  # noqa: SLF001
            candidates = [
                word
                for word in model.get_window_words(shifted_window)
                if not any(ch.isupper() for ch in word)
            ]
            if not candidates:
                token = "???"
                current_window = model._modulo(current_window + 1, model.num_windows)  # noqa: SLF001
                tokens.append(token)
                continue

            desired = retrieved_tokens[token_pos] if token_pos < len(retrieved_tokens) else None
            if desired in candidates:
                token = desired
            else:
                token = _pick_frequent_candidate(candidates, section, stats)

            assigned_raw = model.lattice_map.get(token)
            assigned_window = (
                model._modulo(current_window + 1, model.num_windows)  # noqa: SLF001
                if assigned_raw is None
                else int(assigned_raw)
            )
            current_window = model._modulo(assigned_window - offset, model.num_windows)  # noqa: SLF001
            tokens.append(token)

        affix = observed_affixes[line_idx] if line_idx < len(observed_affixes) else {"prefix": "", "suffix": ""}
        marker = observed_markers[line_idx] if line_idx < len(observed_markers) else ("@P0" if line_idx == 0 else "+P0")
        content = ".".join(tokens)
        if affix.get("prefix"):
            content = f"{affix['prefix']}{content}"
        if affix.get("suffix"):
            content = f"{content}{affix['suffix']}"
        generated_lines.append(content)

        diagnostics.append(
            {
                "line_index": line_idx,
                "offset": offset,
                "offset_source": source,
                "marker": marker,
                "retrieved_folio": (retrieved or {}).get("folio"),
                "retrieved_line_index": (retrieved or {}).get("line_index"),
                "target_words": target_word_count,
            }
        )

    return {
        "ok": True,
        "folioId": folio_id,
        "method": "retrieval_edit",
        "text": "\n".join(generated_lines),
        "contentLines": generated_lines,
        "diagnostics": diagnostics,
    }


def summarize_metric(values: list[float]) -> dict:
    if not values:
        return {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "stdev": 0.0}
    return {
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "stdev": statistics.pstdev(values),
    }


def bootstrap_ci(values: list[float], seed: int, rounds: int = 300) -> dict:
    if not values:
        return {"mean": 0.0, "ci95_low": 0.0, "ci95_high": 0.0, "rounds": 0}
    rng = Mulberry32(seed)
    means: list[float] = []
    n = len(values)
    for _ in range(rounds):
        sample = [values[int(rng.random() * n)] for _ in range(n)]
        means.append(statistics.mean(sample))
    means.sort()
    lo_idx = int(0.025 * (rounds - 1))
    hi_idx = int(0.975 * (rounds - 1))
    return {
        "mean": statistics.mean(values),
        "ci95_low": means[lo_idx],
        "ci95_high": means[hi_idx],
        "rounds": rounds,
    }


def evaluate_single_method(
    model: PageGeneratorModel,
    folio_ids: list[str],
    method_name: str,
    generator_fn,
) -> dict:
    rows = []
    metric_columns: dict[str, list[float]] = defaultdict(list)

    for folio_id in folio_ids:
        folio = model.folio_map[folio_id]
        actual_text = actual_folio_text(folio, fmt="content")
        generated = generator_fn(folio_id)
        generated_text = generated.get("text", "") if generated.get("ok") else ""
        scores = score_alignment(generated_text, actual_text)
        row = {
            "folio": folio_id,
            "section": str((model.schedule_map.get(folio_id) or {}).get("section") or "Other"),
            "scores": scores,
        }
        rows.append(row)
        metric_columns["composite_score"].append(scores["composite_score"])
        metric_columns["exact_token_rate"].append(scores["exact_token_rate"])
        metric_columns["normalized_edit_distance"].append(scores["normalized_edit_distance"])
        metric_columns["affix_fidelity"].append(scores["affix_fidelity"])
        metric_columns["marker_fidelity"].append(scores["marker_fidelity"])
        metric_columns["line_count_error_rel"].append(scores["line_count_error_rel"])
        metric_columns["ngram_jsd_avg"].append(scores["ngram_divergence"]["avg_jsd"])

    summary = {
        "method": method_name,
        "folio_count": len(rows),
        "metrics": {
            metric: {
                "summary": summarize_metric(values),
                "bootstrap": bootstrap_ci(values, seed=stable_seed(420, method_name, metric)),
            }
            for metric, values in sorted(metric_columns.items())
        },
    }
    return {
        "summary": summary,
        "rows": rows,
    }
