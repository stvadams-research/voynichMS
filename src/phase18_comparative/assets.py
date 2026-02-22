import re
import statistics
from collections import Counter, defaultdict
from datetime import UTC, datetime

class FolioAssetBuilder:
    """Builds folio schedule and page priors for the Voynich analysis."""

    LINE_PATTERN = re.compile(r"^<([^>]+)>\s*(.*)$")
    FOLIO_META_PATTERN = re.compile(r"^f\d+[rv]\d*$")

    SECTIONS = {
        "Herbal A": (1, 57),
        "Herbal B": (58, 66),
        "Astro": (67, 74),
        "Biological": (75, 84),
        "Cosmo": (85, 86),
        "Pharma": (87, 102),
        "Stars": (103, 116),
    }

    @staticmethod
    def folio_sort_key(folio_id: str) -> tuple[int, int, int, str]:
        match = re.match(r"^f(\d+)([rv])(\d*)$", folio_id)
        if not match:
            return (10**9, 1, 10**9, folio_id)
        number = int(match.group(1))
        side = 0 if match.group(2) == "r" else 1
        suffix = int(match.group(3) or "0")
        return (number, side, suffix, folio_id)

    @staticmethod
    def get_folio_num(folio_id: str) -> int:
        match = re.search(r"f(\d+)", folio_id)
        return int(match.group(1)) if match else 0

    @classmethod
    def get_section(cls, folio_id: str) -> str:
        folio_num = cls.get_folio_num(folio_id)
        for section_name, (low, high) in cls.SECTIONS.items():
            if low <= folio_num <= high:
                return section_name
        return "Other"

    @classmethod
    def get_hand(cls, folio_id: str) -> str:
        folio_num = cls.get_folio_num(folio_id)
        if folio_num <= 66:
            return "Hand1"
        if 75 <= folio_num <= 84 or 103 <= folio_num <= 116:
            return "Hand2"
        return "Unknown"

    @staticmethod
    def get_side(folio_id: str) -> str:
        if folio_id.endswith("r"):
            return "r"
        if folio_id.endswith("v"):
            return "v"
        return "unknown"

    @classmethod
    def parse_folio_lines(cls, path) -> dict[str, list[dict]]:
        by_folio: dict[str, list[dict]] = defaultdict(list)
        serial = 0
        
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            match = cls.LINE_PATTERN.match(line)
            if not match:
                continue

            location = match.group(1).strip()
            content = match.group(2).strip()
            if cls.FOLIO_META_PATTERN.match(location):
                continue
            if not content:
                continue

            serial += 1
            folio_id = location.split(".", 1)[0].strip()
            marker = ""
            line_no = None
            if "," in location:
                marker = location.split(",", 1)[1].strip()
            if "." in location:
                tail = location.split(".", 1)[1]
                line_head = tail.split(",", 1)[0]
                if line_head.isdigit():
                    line_no = int(line_head)

            by_folio[folio_id].append(
                {
                    "location": location,
                    "line_no": line_no,
                    "marker": marker,
                    "_serial": serial,
                }
            )

        for folio_id in list(by_folio.keys()):
            rows = sorted(
                by_folio[folio_id],
                key=lambda row: (
                    1 if row["line_no"] is None else 0,
                    row["line_no"] if row["line_no"] is not None else row["_serial"],
                    row["_serial"],
                ),
            )
            normalized = []
            for idx, row in enumerate(rows):
                normalized.append(
                    {
                        "location": row["location"],
                        "line_no": int(row["line_no"]) if row["line_no"] is not None else idx + 1,
                        "line_index": idx,
                        "marker": row["marker"],
                    }
                )
            by_folio[folio_id] = normalized

        return by_folio

    @staticmethod
    def _mode(values: list[int], fallback: int) -> int:
        if not values:
            return fallback
        return Counter(values).most_common(1)[0][0]

    @staticmethod
    def _normalize_counts(counter: Counter) -> dict[str, float]:
        total = sum(counter.values())
        if total <= 0:
            return {}
        return {
            key: (count / total)
            for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
        }

    @staticmethod
    def _distribution(values: list[int]) -> dict:
        counter = Counter(values)
        return {
            "count": len(values),
            "min": min(values) if values else 0,
            "max": max(values) if values else 0,
            "mean": statistics.mean(values) if values else 0.0,
            "median": statistics.median(values) if values else 0.0,
            "histogram": {str(k): int(v) for k, v in sorted(counter.items())},
        }

    @classmethod
    def build_folio_schedule(
        cls,
        folio_lines: dict[str, list[dict]],
        mask_inference: dict,
        mask_prediction: dict,
        folio_source_path: str,
    ) -> dict:
        reordered = mask_inference.get("Reordered", {})
        line_schedule = reordered.get("line_schedule", [])
        line_map: dict[tuple[str, int], dict] = {}
        folio_inferred_offsets: dict[str, list[int]] = defaultdict(list)

        for row in line_schedule:
            folio_id = str(row.get("folio_id", "")).strip()
            line_idx = int(row.get("line_index", 0))
            if not folio_id:
                continue
            key = (folio_id, line_idx)
            line_map[key] = row
            folio_inferred_offsets[folio_id].append(int(row.get("best_offset", 0)))

        global_mode = int(mask_prediction.get("global_mode_offset", 17))
        section_modes_raw = mask_prediction.get("section_mode_offsets", {})
        section_modes = {str(k): int(v) for k, v in section_modes_raw.items()}

        baselines = {
            "baseline_no_mask_admissibility": float(mask_prediction.get("baseline_admissibility", 0.0)),
            "global_mode_admissibility": float(
                (mask_prediction.get("rules", {}).get("global_mode") or {}).get(
                    "admissibility", 0.0
                )
            ),
            "oracle_admissibility": float(mask_prediction.get("oracle_admissibility", 0.0)),
            "global_mode_capture_pct": float(
                (mask_prediction.get("rules", {}).get("global_mode") or {}).get(
                    "capture_pct", 0.0
                )
            ),
        }

        folios = []
        source_counts = Counter()
        for folio_id in sorted(folio_lines.keys(), key=cls.folio_sort_key):
            lines = folio_lines[folio_id]
            section = cls.get_section(folio_id)
            hand = cls.get_hand(folio_id)
            side = cls.get_side(folio_id)

            folio_mode = cls._mode(folio_inferred_offsets.get(folio_id, []), global_mode)
            section_mode = section_modes.get(section, global_mode)

            resolved_lines = []
            folio_source_counts = Counter()
            for line in lines:
                idx = int(line["line_index"])
                marker = str(line["marker"])
                inferred = line_map.get((folio_id, idx))
                source = "global_mode"
                score = None
                if inferred is not None:
                    offset = int(inferred.get("best_offset", global_mode))
                    score = float(inferred.get("line_score", 0.0))
                    source = "line_inferred"
                elif folio_inferred_offsets.get(folio_id):
                    offset = int(folio_mode)
                    source = "folio_mode"
                elif section in section_modes:
                    offset = int(section_mode)
                    source = "section_mode"
                else:
                    offset = int(global_mode)

                source_counts[source] += 1
                folio_source_counts[source] += 1
                resolved_lines.append(
                    {
                        "line_index": idx,
                        "line_no": int(line["line_no"]),
                        "marker": marker,
                        "offset": offset,
                        "source": source,
                        "line_score": score,
                    }
                )

            folios.append(
                {
                    "folio": folio_id,
                    "folio_num": cls.get_folio_num(folio_id),
                    "section": section,
                    "hand": hand,
                    "side": side,
                    "line_count": len(lines),
                    "folio_mode_offset": int(folio_mode),
                    "section_mode_offset": int(section_mode),
                    "global_mode_offset": int(global_mode),
                    "line_source_counts": {
                        key: int(value)
                        for key, value in sorted(folio_source_counts.items())
                    },
                    "lines": resolved_lines,
                }
            )

        return {
            "schema_version": "phase18_folio_schedule_v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "sources": {
                "folio_transliteration": str(folio_source_path),
            },
            "global_mode_offset": int(global_mode),
            "section_mode_offsets": section_modes,
            "baselines": baselines,
            "summary": {
                "folio_count": len(folios),
                "line_count": sum(folio["line_count"] for folio in folios),
                "source_counts": {
                    key: int(value)
                    for key, value in sorted(source_counts.items())
                },
                "section_mapped_folios": sum(
                    1 for folio in folios if folio["section"] != "Other"
                ),
                "global_fallback_folios": sum(
                    1
                    for folio in folios
                    if folio["section"] == "Other" or folio["line_source_counts"].get("global_mode", 0) > 0
                ),
            },
            "folios": folios,
        }

    @classmethod
    def build_page_priors(cls, folio_lines: dict[str, list[dict]], folio_source_path: str) -> dict:
        line_counts_global = []
        line_counts_by_section: dict[str, list[int]] = defaultdict(list)
        line_counts_by_side: dict[str, list[int]] = defaultdict(list)

        first_marker_global = Counter()
        cont_marker_global = Counter()
        first_marker_by_section: dict[str, Counter] = defaultdict(Counter)
        cont_marker_by_section: dict[str, Counter] = defaultdict(Counter)
        first_marker_by_side: dict[str, Counter] = defaultdict(Counter)
        cont_marker_by_side: dict[str, Counter] = defaultdict(Counter)

        observed_profiles = {}

        for folio_id in sorted(folio_lines.keys(), key=cls.folio_sort_key):
            lines = folio_lines[folio_id]
            if not lines:
                continue

            section = cls.get_section(folio_id)
            side = cls.get_side(folio_id)
            line_count = len(lines)
            line_counts_global.append(line_count)
            line_counts_by_section[section].append(line_count)
            line_counts_by_side[side].append(line_count)

            marker_sequence = []
            for idx, line in enumerate(lines):
                marker = str(line["marker"])
                marker_sequence.append(marker)
                if idx == 0:
                    first_marker_global[marker] += 1
                    first_marker_by_section[section][marker] += 1
                    first_marker_by_side[side][marker] += 1
                else:
                    cont_marker_global[marker] += 1
                    cont_marker_by_section[section][marker] += 1
                    cont_marker_by_side[side][marker] += 1

            observed_profiles[folio_id] = {
                "section": section,
                "side": side,
                "line_count": line_count,
                "marker_sequence": marker_sequence,
            }

        return {
            "schema_version": "phase18_page_priors_v1",
            "generated_at": datetime.now(UTC).isoformat(),
            "sources": {
                "folio_transliteration": str(folio_source_path),
            },
            "section_definitions": cls.SECTIONS,
            "line_count_priors": {
                "global": cls._distribution(line_counts_global),
                "by_section": {
                    section: cls._distribution(values)
                    for section, values in sorted(line_counts_by_section.items())
                },
                "by_side": {
                    side: cls._distribution(values)
                    for side, values in sorted(line_counts_by_side.items())
                },
            },
            "marker_priors": {
                "global": {
                    "first_line": cls._normalize_counts(first_marker_global),
                    "continuation": cls._normalize_counts(cont_marker_global),
                },
                "by_section": {
                    section: {
                        "first_line": cls._normalize_counts(first_marker_by_section[section]),
                        "continuation": cls._normalize_counts(cont_marker_by_section[section]),
                    }
                    for section in sorted(line_counts_by_section.keys())
                },
                "by_side": {
                    side: {
                        "first_line": cls._normalize_counts(first_marker_by_side[side]),
                        "continuation": cls._normalize_counts(cont_marker_by_side[side]),
                    }
                    for side in sorted(line_counts_by_side.keys())
                },
            },
            "observed_folios": observed_profiles,
            "summary": {
                "folio_count": len(observed_profiles),
                "line_count_total": sum(line_counts_global),
                "sections": sorted(line_counts_by_section.keys()),
                "sides": sorted(line_counts_by_side.keys()),
            },
        }
