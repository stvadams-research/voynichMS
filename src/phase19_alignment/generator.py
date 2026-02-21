from __future__ import annotations

import re
from dataclasses import dataclass

from .data import (
    build_folio_map,
    build_schedule_map,
    load_folio_data,
    load_lattice_data,
    load_page_priors,
    load_page_schedule,
    normalized_window_contents,
    project_root,
)

_PROFILES = {
    "hand1": {
        "suffixWeights": {"dy": 12, "in": 4, "y": 8, "m": 3},
        "overlapWeight": 2,
    },
    "hand2": {
        "suffixWeights": {"in": 20, "dy": 2, "m": 10, "y": 5},
        "overlapWeight": 2,
    },
}

_PREFIX_AFFIX_RE = re.compile(r"^((?:<[^>]+>)+)")
_SUFFIX_AFFIX_RE = re.compile(r"((?:<[^>]+>)+)$")


@dataclass
class PageGenerationOptions:
    folio_id: str
    seed: int = 42
    schedule_mode: str = "auto"
    line_count_mode: str = "observed"
    min_words: int = 6
    max_words: int = 12
    profile: str = "hand1"
    canonical_filter: bool = True
    format: str = "content"
    target_words_by_line: list[int] | None = None


class Mulberry32:
    def __init__(self, seed: int) -> None:
        self.t = (int(seed) & 0xFFFFFFFF) or 1

    @staticmethod
    def _u32(value: int) -> int:
        return value & 0xFFFFFFFF

    @staticmethod
    def _imul(a: int, b: int) -> int:
        return ((a & 0xFFFFFFFF) * (b & 0xFFFFFFFF)) & 0xFFFFFFFF

    def random(self) -> float:
        self.t = self._u32(self.t + 0x6D2B79F5)
        x = self.t
        x = self._imul(self._u32(x ^ (x >> 15)), self._u32(x | 1))
        x = self._u32(x ^ self._u32(x + self._imul(self._u32(x ^ (x >> 7)), self._u32(x | 61))))
        return self._u32(x ^ (x >> 14)) / 4294967296.0


class PageGeneratorModel:
    def __init__(
        self,
        folio_map: dict[str, dict],
        lattice_map: dict[str, int],
        window_contents: dict[int, list[str]],
        schedule_map: dict[str, dict],
        priors: dict,
        global_mode_offset: int,
    ) -> None:
        self.folio_map = folio_map
        self.lattice_map = {str(k): int(v) for k, v in lattice_map.items()}
        self.window_contents = {int(k): list(v) for k, v in window_contents.items()}
        self.schedule_map = schedule_map
        self.priors = priors
        self.global_mode_offset = int(global_mode_offset)
        self.window_ids = sorted(self.window_contents.keys())
        self.num_windows = len(self.window_ids)

    @classmethod
    def from_project_root(cls, root: str | None = None) -> "PageGeneratorModel":
        base = project_root() if root is None else project_root() if root == "" else None
        if base is None:
            from pathlib import Path

            base = Path(root)
        folio_payload = load_folio_data(base)
        lattice_payload = load_lattice_data(base)
        schedule_payload = load_page_schedule(base)
        priors_payload = load_page_priors(base)
        return cls(
            folio_map=build_folio_map(folio_payload),
            lattice_map=lattice_payload["lattice_map"],
            window_contents=normalized_window_contents(lattice_payload["window_contents"]),
            schedule_map=build_schedule_map(schedule_payload),
            priors=priors_payload,
            global_mode_offset=int(schedule_payload.get("global_mode_offset", 17)),
        )

    @staticmethod
    def _modulo(value: int, size: int) -> int:
        return ((int(value) % size) + size) % size

    @staticmethod
    def _rand_int(rng: Mulberry32, min_value: int, max_value: int) -> int:
        low = min(min_value, max_value)
        high = max(min_value, max_value)
        return low + int(rng.random() * (high - low + 1))

    @staticmethod
    def _parse_marker(location: str) -> str:
        if "," not in location:
            return ""
        return location.split(",", 1)[1].strip()

    @staticmethod
    def _extract_affix(content: str) -> dict[str, str]:
        raw = str(content or "").strip()
        if not raw:
            return {"prefix": "", "suffix": ""}
        prefix_match = _PREFIX_AFFIX_RE.match(raw)
        suffix_match = _SUFFIX_AFFIX_RE.search(raw)
        return {
            "prefix": prefix_match.group(1) if prefix_match else "",
            "suffix": suffix_match.group(1) if suffix_match else "",
        }

    def get_window_words(self, window_id: int) -> list[str]:
        return self.window_contents.get(int(window_id), [])

    def _score_word(self, word: str, prev_word: str | None, profile: dict) -> float:
        score = 1.0
        for suffix, value in profile["suffixWeights"].items():
            if word.endswith(suffix):
                score += float(value)

        if prev_word:
            seen = set(prev_word)
            overlap = sum(1 for ch in word if ch in seen)
            score += overlap * float(profile["overlapWeight"])
        return score

    def _choose_weighted(
        self,
        words: list[str],
        prev_word: str | None,
        profile: dict,
        rng: Mulberry32,
    ) -> str:
        if not words:
            return ""
        weights = [self._score_word(word, prev_word, profile) for word in words]
        total = sum(weights)
        if total <= 0:
            return words[self._rand_int(rng, 0, len(words) - 1)]
        pivot = rng.random() * total
        for word, weight in zip(words, weights):
            pivot -= weight
            if pivot <= 0:
                return word
        return words[-1]

    def _get_observed_markers(self, folio: dict) -> list[str]:
        markers: list[str] = []
        for idx, line in enumerate(folio.get("lines", [])):
            marker = self._parse_marker(str(line.get("location", "")))
            markers.append(marker if marker else ("@P0" if idx == 0 else "+P0"))
        return markers

    def _get_observed_affixes(self, folio: dict) -> list[dict[str, str]]:
        return [self._extract_affix(str(line.get("content", ""))) for line in folio.get("lines", [])]

    def _pick_from_prob_map(self, prob_map: dict[str, float], rng: Mulberry32, fallback: str) -> str:
        entries = list(prob_map.items())
        if not entries:
            return fallback
        pivot = rng.random()
        for key, probability in entries:
            pivot -= float(probability)
            if pivot <= 0:
                return key
        return entries[-1][0] if entries else fallback

    def _get_section_marker_prior(self, section: str, side: str, first_line: bool) -> dict[str, float]:
        marker_priors = self.priors.get("marker_priors", {})
        field = "first_line" if first_line else "continuation"
        by_section = marker_priors.get("by_section", {}).get(section, {})
        by_side = marker_priors.get("by_side", {}).get(side, {})
        global_entry = marker_priors.get("global", {})
        return by_section.get(field) or by_side.get(field) or global_entry.get(field) or {}

    def _sample_line_count(
        self,
        section: str,
        side: str,
        rng: Mulberry32,
        fallback: int,
    ) -> tuple[int, str]:
        priors = self.priors.get("line_count_priors", {})
        by_section = priors.get("by_section", {}).get(section)
        by_side = priors.get("by_side", {}).get(side)
        global_entry = priors.get("global", {})
        histogram = (
            (by_section or {}).get("histogram")
            or (by_side or {}).get("histogram")
            or global_entry.get("histogram")
            or {}
        )
        if not histogram:
            return fallback, "fallback_observed"

        entries = [(int(k), float(v)) for k, v in histogram.items()]
        total = sum(value for _, value in entries)
        if total <= 0:
            return fallback, "fallback_observed"

        pivot = rng.random() * total
        for line_count, count in entries:
            pivot -= count
            if pivot <= 0 and line_count > 0:
                if by_section and by_section.get("histogram"):
                    return line_count, "section_prior"
                if by_side and by_side.get("histogram"):
                    return line_count, "side_prior"
                return line_count, "global_prior"
        line_count = entries[-1][0]
        return (line_count if line_count > 0 else fallback), "global_prior"

    def resolve_line_offset(
        self,
        schedule_entry: dict | None,
        line_index: int,
        schedule_mode: str,
    ) -> tuple[int, str]:
        if schedule_mode == "global_only":
            return self.global_mode_offset, "global_mode"
        if not schedule_entry:
            return self.global_mode_offset, "global_mode"

        lines = schedule_entry.get("lines", [])
        if line_index < len(lines):
            line = lines[line_index]
            if line is not None and line.get("offset") is not None:
                return int(line.get("offset", self.global_mode_offset)), str(
                    line.get("source", "line_inferred")
                )

        if schedule_entry.get("folio_mode_offset") is not None:
            return int(schedule_entry["folio_mode_offset"]), "folio_mode"
        if schedule_entry.get("section_mode_offset") is not None:
            return int(schedule_entry["section_mode_offset"]), "section_mode"
        return self.global_mode_offset, "global_mode"

    def generate_page(self, options: PageGenerationOptions) -> dict:
        folio_id = str(options.folio_id).strip()
        folio = self.folio_map.get(folio_id)
        if not folio:
            return {"ok": False, "message": f"Unknown folio \"{folio_id}\"."}
        if not self.window_ids:
            return {"ok": False, "message": "Lattice windows unavailable."}

        rng = Mulberry32(int(options.seed))
        profile = _PROFILES.get(options.profile, _PROFILES["hand1"])
        canonical_filter = bool(options.canonical_filter)
        schedule_entry = self.schedule_map.get(folio_id)
        section = str((schedule_entry or {}).get("section") or "Other")
        hand = str((schedule_entry or {}).get("hand") or "Unknown")
        side = "r" if folio_id.endswith("r") else ("v" if folio_id.endswith("v") else "unknown")

        observed_line_count = max(1, int(folio.get("line_count", 1)))
        line_count = observed_line_count
        line_count_source = "observed"
        warnings: list[str] = []

        if options.line_count_mode == "sampled":
            line_count, line_count_source = self._sample_line_count(section, side, rng, observed_line_count)
            if line_count_source == "fallback_observed":
                warnings.append(
                    "Sampled line count unavailable for this context; using observed line count."
                )

        if schedule_entry is None:
            warnings.append("No folio schedule entry found; using global mode offset fallback.")

        min_words = max(1, int(options.min_words))
        max_words = max(min_words, int(options.max_words))

        observed_markers = self._get_observed_markers(folio)
        observed_affixes = self._get_observed_affixes(folio)

        source_counts: dict[str, int] = {}
        line_diagnostics: list[dict] = []
        content_lines: list[str] = []
        ivtff_lines: list[str] = []

        for line_idx in range(line_count):
            offset, source = self.resolve_line_offset(schedule_entry, line_idx, options.schedule_mode)
            source_counts[source] = source_counts.get(source, 0) + 1

            if options.target_words_by_line and line_idx < len(options.target_words_by_line):
                target_words = max(1, int(options.target_words_by_line[line_idx]))
            else:
                target_words = self._rand_int(rng, min_words, max_words)

            marker = observed_markers[line_idx] if line_idx < len(observed_markers) else ""
            if not marker:
                if options.line_count_mode == "sampled":
                    prior = self._get_section_marker_prior(section, side, line_idx == 0)
                    marker = self._pick_from_prob_map(prior, rng, "@P0" if line_idx == 0 else "+P0")
                else:
                    marker = "@P0" if line_idx == 0 else "+P0"

            current_window = self._rand_int(rng, 0, self.num_windows - 1)
            prev_word: str | None = None
            tokens: list[str] = []

            for _ in range(target_words):
                shifted_window = self._modulo(current_window + offset, self.num_windows)
                shifted_words = self.get_window_words(shifted_window)
                if canonical_filter:
                    candidates = [word for word in shifted_words if not re.search(r"[A-Z]", word)]
                else:
                    candidates = list(shifted_words)

                if not candidates:
                    tokens.append("???")
                    current_window = self._modulo(current_window + 1, self.num_windows)
                    prev_word = "???"
                    continue

                word = self._choose_weighted(candidates, prev_word, profile, rng)
                tokens.append(word)

                assigned_raw = self.lattice_map.get(word)
                assigned_window = (
                    self._modulo(current_window + 1, self.num_windows)
                    if assigned_raw is None
                    else int(assigned_raw)
                )
                current_window = self._modulo(assigned_window - offset, self.num_windows)
                prev_word = word

            affix = observed_affixes[line_idx] if line_idx < len(observed_affixes) else {"prefix": "", "suffix": ""}
            content = ".".join(tokens)
            if affix.get("prefix"):
                content = f"{affix['prefix']}{content}"
            if affix.get("suffix"):
                content = f"{content}{affix['suffix']}"

            content_lines.append(content)
            if options.format == "ivtff":
                ivtff_lines.append(f"<{folio_id}.{line_idx + 1},{marker}>      {content}")

            line_diagnostics.append(
                {
                    "lineIndex": line_idx,
                    "marker": marker,
                    "offset": offset,
                    "offsetSource": source,
                    "words": len(tokens),
                }
            )

        text = "\n".join(ivtff_lines if options.format == "ivtff" else content_lines)
        avg_words = (
            sum(diag["words"] for diag in line_diagnostics) / len(line_diagnostics)
            if line_diagnostics
            else 0.0
        )

        return {
            "ok": True,
            "seed": int(options.seed),
            "folioId": folio_id,
            "section": section,
            "hand": hand,
            "lineCount": line_count,
            "lineCountSource": line_count_source,
            "scheduleMode": options.schedule_mode,
            "format": options.format,
            "avgWordsPerLine": avg_words,
            "warnings": warnings,
            "sourceCounts": source_counts,
            "lineDiagnostics": line_diagnostics,
            "globalOffset": self.global_mode_offset,
            "text": text,
            "contentLines": content_lines,
            "ivtffLines": ivtff_lines,
        }
