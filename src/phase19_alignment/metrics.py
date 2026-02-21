from __future__ import annotations

import math
import re
from collections import Counter

_FULL_LINE_PATTERN = re.compile(r"^<([^>]+)>\s*(.*)$")
_FOLIO_ONLY_PATTERN = re.compile(r"^f\d+[rv]\d*$")
_PREFIX_AFFIX_RE = re.compile(r"^((?:<[^>]+>)+)")
_SUFFIX_AFFIX_RE = re.compile(r"((?:<[^>]+>)+)$")

_RE_INLINE_META = re.compile(r"<!.*?>")
_RE_ANGLE_TAGS = re.compile(r"<.*?>")
_RE_ANGLE_UNCLOSED = re.compile(r"<[!%$].*")
_RE_BRACKET_CONTENT = re.compile(r"\[.*?\]")
_RE_SYMBOLS = re.compile(r"[{}*$<>]")
_RE_PUNCT = re.compile(r"[,\.;]")


def split_tokens(content: str) -> list[str]:
    return [token.strip() for token in re.split(r"[.\s]+", content) if token.strip()]


def sanitize_token(token: str) -> str:
    text = str(token)
    text = _RE_INLINE_META.sub("", text)
    text = _RE_ANGLE_TAGS.sub("", text)
    text = _RE_ANGLE_UNCLOSED.sub("", text)
    text = _RE_BRACKET_CONTENT.sub("", text)
    text = _RE_SYMBOLS.sub("", text)
    text = _RE_PUNCT.sub("", text)
    return text.strip().lower()


def extract_affix(content: str) -> dict[str, str]:
    raw = str(content or "").strip()
    if not raw:
        return {"prefix": "", "suffix": ""}
    prefix_match = _PREFIX_AFFIX_RE.match(raw)
    suffix_match = _SUFFIX_AFFIX_RE.search(raw)
    return {
        "prefix": prefix_match.group(1) if prefix_match else "",
        "suffix": suffix_match.group(1) if suffix_match else "",
    }


def parse_marker(location: str | None) -> str:
    raw = str(location or "")
    if "," not in raw:
        return ""
    return raw.split(",", 1)[1].strip()


def parse_text_lines(text: str) -> list[dict]:
    parsed: list[dict] = []
    rows = str(text or "").splitlines()
    for index, raw in enumerate(rows, start=1):
        line = str(raw).strip()
        if not line or line.startswith("#"):
            continue

        location = None
        content = line
        line_type = "content_only"

        if line.startswith("<%>") or line.startswith("<$>") or line.startswith("<!"):
            content = line
        elif line.startswith("<"):
            match = _FULL_LINE_PATTERN.match(line)
            if match:
                location = match.group(1)
                content = match.group(2).strip()
                line_type = "full_line"
                if _FOLIO_ONLY_PATTERN.match(location) and content.startswith("<!"):
                    continue

        if not content:
            continue

        tokens_raw = split_tokens(content)
        tokens = [sanitize_token(token) for token in tokens_raw]
        tokens = [token for token in tokens if token]
        affix = extract_affix(content)
        parsed.append(
            {
                "row_index": index,
                "line_type": line_type,
                "location": location,
                "marker": parse_marker(location),
                "content": content,
                "tokens_raw": tokens_raw,
                "tokens": tokens,
                "affix_prefix": affix["prefix"],
                "affix_suffix": affix["suffix"],
            }
        )
    return parsed


def levenshtein_distance(left: list[str], right: list[str]) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    for i, left_token in enumerate(left, start=1):
        current = [i]
        for j, right_token in enumerate(right, start=1):
            substitution = previous[j - 1] + (0 if left_token == right_token else 1)
            insertion = current[j - 1] + 1
            deletion = previous[j] + 1
            current.append(min(substitution, insertion, deletion))
        previous = current
    return previous[-1]


def ngram_counter(tokens: list[str], n: int) -> Counter:
    if n <= 0 or len(tokens) < n:
        return Counter()
    return Counter(tuple(tokens[idx : idx + n]) for idx in range(len(tokens) - n + 1))


def _counter_to_probs(counter: Counter) -> dict:
    total = sum(counter.values())
    if total <= 0:
        return {}
    return {key: value / total for key, value in counter.items()}


def jensen_shannon_divergence(counter_a: Counter, counter_b: Counter) -> float:
    probs_a = _counter_to_probs(counter_a)
    probs_b = _counter_to_probs(counter_b)
    if not probs_a and not probs_b:
        return 0.0

    keys = set(probs_a.keys()) | set(probs_b.keys())
    m = {key: 0.5 * (probs_a.get(key, 0.0) + probs_b.get(key, 0.0)) for key in keys}

    def kl_div(p: dict, q: dict) -> float:
        total = 0.0
        for key, value in p.items():
            if value <= 0.0:
                continue
            qv = max(q.get(key, 0.0), 1e-12)
            total += value * math.log2(value / qv)
        return total

    return 0.5 * kl_div(probs_a, m) + 0.5 * kl_div(probs_b, m)


def score_alignment(generated_text: str, actual_text: str) -> dict:
    generated_lines = parse_text_lines(generated_text)
    actual_lines = parse_text_lines(actual_text)

    max_lines = max(len(generated_lines), len(actual_lines))
    line_errors: list[float] = []
    exact_matches = 0
    exact_total = 0
    affix_matches = 0
    affix_total = 0
    marker_matches = 0
    marker_total = 0
    per_line = []

    for idx in range(max_lines):
        generated = generated_lines[idx] if idx < len(generated_lines) else None
        actual = actual_lines[idx] if idx < len(actual_lines) else None

        generated_tokens = generated["tokens"] if generated else []
        actual_tokens = actual["tokens"] if actual else []

        denom = max(len(generated_tokens), len(actual_tokens), 1)
        edit = levenshtein_distance(generated_tokens, actual_tokens)
        line_errors.append(edit / denom)

        pos_limit = min(len(generated_tokens), len(actual_tokens))
        exact_matches += sum(
            1
            for pos in range(pos_limit)
            if generated_tokens[pos] == actual_tokens[pos]
        )
        exact_total += denom

        if actual is not None:
            affix_total += 1
            if generated is not None and (
                generated["affix_prefix"] == actual["affix_prefix"]
                and generated["affix_suffix"] == actual["affix_suffix"]
            ):
                affix_matches += 1

            if actual.get("marker"):
                marker_total += 1
                if generated is not None and generated.get("marker") == actual.get("marker"):
                    marker_matches += 1

        if idx < 20:
            per_line.append(
                {
                    "line_index": idx,
                    "generated_tokens": len(generated_tokens),
                    "actual_tokens": len(actual_tokens),
                    "normalized_edit_distance": round(edit / denom, 6),
                    "marker_match": (
                        bool(generated and actual and generated.get("marker") == actual.get("marker"))
                        if actual and actual.get("marker")
                        else None
                    ),
                }
            )

    generated_tokens_flat = [token for line in generated_lines for token in line["tokens"]]
    actual_tokens_flat = [token for line in actual_lines for token in line["tokens"]]

    js_1 = jensen_shannon_divergence(ngram_counter(generated_tokens_flat, 1), ngram_counter(actual_tokens_flat, 1))
    js_2 = jensen_shannon_divergence(ngram_counter(generated_tokens_flat, 2), ngram_counter(actual_tokens_flat, 2))
    js_3 = jensen_shannon_divergence(ngram_counter(generated_tokens_flat, 3), ngram_counter(actual_tokens_flat, 3))

    exact_token_rate = exact_matches / exact_total if exact_total else 0.0
    normalized_edit_distance = sum(line_errors) / len(line_errors) if line_errors else 1.0
    affix_fidelity = affix_matches / affix_total if affix_total else 0.0
    marker_fidelity = marker_matches / marker_total if marker_total else 0.0
    ngram_divergence_avg = (js_1 + js_2 + js_3) / 3.0

    line_count_error = abs(len(generated_lines) - len(actual_lines))
    line_count_error_rel = line_count_error / max(len(actual_lines), 1)

    lexical_component = (0.55 * exact_token_rate) + (0.45 * (1.0 - normalized_edit_distance))
    structure_component = (0.5 * affix_fidelity) + (0.5 * marker_fidelity)
    divergence_component = 1.0 - min(1.0, ngram_divergence_avg)
    line_component = 1.0 - min(1.0, line_count_error_rel)
    composite = (
        0.45 * lexical_component
        + 0.2 * structure_component
        + 0.2 * divergence_component
        + 0.15 * line_component
    )

    return {
        "line_count_generated": len(generated_lines),
        "line_count_actual": len(actual_lines),
        "line_count_error": line_count_error,
        "line_count_error_rel": line_count_error_rel,
        "exact_token_rate": exact_token_rate,
        "normalized_edit_distance": normalized_edit_distance,
        "affix_fidelity": affix_fidelity,
        "marker_fidelity": marker_fidelity,
        "ngram_divergence": {
            "n1_jsd": js_1,
            "n2_jsd": js_2,
            "n3_jsd": js_3,
            "avg_jsd": ngram_divergence_avg,
        },
        "composite_score": max(0.0, min(1.0, composite)),
        "token_totals": {
            "generated": len(generated_tokens_flat),
            "actual": len(actual_tokens_flat),
        },
        "sample_line_diagnostics": per_line,
    }
