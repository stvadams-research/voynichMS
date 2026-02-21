#!/usr/bin/env python3
"""Phase 14Z4: Failure Taxonomy Deep-Dive.

Decomposes the 42.45% "wrong window" residual (14,690 tokens) into
actionable sub-categories.  The existing failure_diagnosis.json has only
per-section aggregates; noise_register.json caps at 1,000 entries and
lacks distance measurements.

This script produces a per-token record for ALL 34,605 tokens with:
  1. Full position metadata (folio, line, token position, section, hand)
  2. Distance to nearest window containing the word
  3. Mask-recoverability cross-reference (oracle offset from mask_inference)
  4. Distance distribution analysis (bimodality test)
  5. Bigram-predictable drift (information gain of prev_word on distance)
  6. Consistent offset families (dominant signed distances)
  7. Cross-transcription noise check (ZL-only vs structural failures)
  8. Section-correlated failure patterns
"""

import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import (  # noqa: E402
    load_canonical_lines,
    sanitize_token,
)
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import (  # noqa: E402
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = (
    project_root / "results/data/phase14_machine/full_palette_grid.json"
)
MASK_PATH = (
    project_root / "results/data/phase14_machine/mask_inference.json"
)
OUTPUT_PATH = (
    project_root / "results/data/phase14_machine/failure_taxonomy.json"
)
console = Console()

SECTIONS = {
    "Herbal A": (1, 57),
    "Herbal B": (58, 66),
    "Astro": (67, 74),
    "Biological": (75, 84),
    "Cosmo": (85, 86),
    "Pharma": (87, 102),
    "Stars": (103, 116),
}

# Cross-transcription sources to check
CROSS_SOURCES = ["voynich_transcription", "interim", "rene_friedman"]


def get_folio_num(folio_id):
    """Extract numeric folio index from page id."""
    match = re.search(r"f(\d+)", folio_id)
    return int(match.group(1)) if match else 0


def get_section(folio_num):
    """Map folio number into the canonical section bins."""
    for name, (lo, hi) in SECTIONS.items():
        if lo <= folio_num <= hi:
            return name
    return "Other"


def get_hand(folio_num):
    """Approximate Currier hand assignment."""
    if folio_num <= 66:
        return "Hand1"
    if 75 <= folio_num <= 84 or 103 <= folio_num <= 116:
        return "Hand2"
    return "Unknown"


def load_lines_with_metadata(store):
    """Load canonical ZL lines with folio and local line metadata.

    Returns list of dicts with tokens, folio_id, folio_num, line_index,
    section, hand.
    """
    session = store.Session()
    try:
        rows = (
            session.query(
                TranscriptionTokenRecord.content,
                PageRecord.id,
                TranscriptionLineRecord.id,
                TranscriptionLineRecord.line_index,
            )
            .join(
                TranscriptionLineRecord,
                TranscriptionTokenRecord.line_id
                == TranscriptionLineRecord.id,
            )
            .join(
                PageRecord,
                TranscriptionLineRecord.page_id == PageRecord.id,
            )
            .filter(PageRecord.dataset_id == "voynich_real")
            .filter(
                TranscriptionLineRecord.source_id == "zandbergen_landini"
            )
            .order_by(
                PageRecord.id,
                TranscriptionLineRecord.line_index,
                TranscriptionTokenRecord.token_index,
            )
            .all()
        )

        lines = []
        current_tokens = []
        current_folio = None
        current_line_id = None
        folio_local_line_idx = {}

        for content, folio_id, line_id, _line_index in rows:
            clean = sanitize_token(content)
            if not clean:
                continue

            if current_line_id is not None and line_id != current_line_id:
                if current_tokens:
                    local_idx = folio_local_line_idx.get(current_folio, 0)
                    f_num = get_folio_num(current_folio)
                    lines.append(
                        {
                            "tokens": current_tokens,
                            "folio_id": current_folio,
                            "folio_num": f_num,
                            "line_index": local_idx,
                            "section": get_section(f_num),
                            "hand": get_hand(f_num),
                        }
                    )
                    folio_local_line_idx[current_folio] = local_idx + 1
                current_tokens = []

            current_tokens.append(clean)
            current_folio = folio_id
            current_line_id = line_id

        if current_tokens:
            local_idx = folio_local_line_idx.get(current_folio, 0)
            f_num = get_folio_num(current_folio)
            lines.append(
                {
                    "tokens": current_tokens,
                    "folio_id": current_folio,
                    "folio_num": f_num,
                    "line_index": local_idx,
                    "section": get_section(f_num),
                    "hand": get_hand(f_num),
                }
            )

        return lines
    finally:
        session.close()


def load_palette(path):
    """Load lattice_map and window_contents from palette JSON."""
    with open(path) as f:
        data = json.load(f)["results"]
    lattice_map = data["lattice_map"]
    window_contents = {int(k): v for k, v in data["window_contents"].items()}
    return lattice_map, window_contents


def load_mask_schedule(path):
    """Load per-line oracle offsets from mask_inference.json.

    Returns dict: (folio_id, line_index) -> best_offset
    """
    if not path.exists():
        return {}
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    # Use "Original" palette schedule
    orig = results.get("Original", {})
    schedule = orig.get("line_schedule", [])
    lookup = {}
    for entry in schedule:
        key = (entry["folio_id"], entry["line_index"])
        lookup[key] = entry["best_offset"]
    return lookup


def score_line_with_offset(line, offset, lattice_map, window_contents, num_wins):
    """Score a single line's admissibility under a given mask offset.

    Returns (admissible_count, total_clamped).
    """
    admissible = 0
    total = 0
    current_window = 0

    for word in line:
        if word not in lattice_map:
            continue
        total += 1

        shifted_win = (current_window + offset) % num_wins

        found = False
        for d in [-1, 0, 1]:
            check_win = (shifted_win + d) % num_wins
            if word in window_contents.get(check_win, []):
                found = True
                assigned = lattice_map.get(word)
                if assigned is not None:
                    current_window = (assigned - offset) % num_wins
                break

        if found:
            admissible += 1
        else:
            assigned = lattice_map.get(word)
            if assigned is not None:
                current_window = (assigned - offset) % num_wins

    return admissible, total


def entropy(counts):
    """Shannon entropy of a count distribution in bits."""
    total = sum(counts)
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            h -= p * math.log2(p)
    return h


def hartigan_dip_proxy(distances):
    """Simple bimodality coefficient as a proxy for Hartigan's dip test.

    BC = (skewness^2 + 1) / kurtosis
    BC > 0.555 suggests bimodality.
    """
    if len(distances) < 4:
        return {"bc": 0.0, "is_bimodal": False, "n": len(distances)}
    arr = np.array(distances, dtype=float)
    mean = np.mean(arr)
    std = np.std(arr, ddof=1)
    if std == 0:
        return {"bc": 0.0, "is_bimodal": False, "n": len(distances)}
    skew = np.mean(((arr - mean) / std) ** 3)
    kurt = np.mean(((arr - mean) / std) ** 4)
    # Bimodality coefficient
    n = len(arr)
    bc = (skew ** 2 + 1) / (kurt + 3 * (n - 1) ** 2 / ((n - 2) * (n - 3)))
    return {
        "bc": float(bc),
        "skewness": float(skew),
        "kurtosis": float(kurt),
        "is_bimodal": bool(bc > 0.555),
        "n": len(distances),
    }


def main():
    console.print(
        "[bold yellow]Phase 14Z4: Failure Taxonomy Deep-Dive[/bold yellow]"
    )

    if not PALETTE_PATH.exists():
        console.print(f"[red]Error: {PALETTE_PATH} not found.[/red]")
        return

    # ── 1. Load lattice ──
    lattice_map, window_contents = load_palette(PALETTE_PATH)
    num_wins = len(window_contents)
    # Build reverse lookup: word -> set of windows containing it
    word_windows = defaultdict(set)
    for win_id, words in window_contents.items():
        for w in words:
            word_windows[w].add(win_id)

    console.print(
        f"Lattice: {len(lattice_map)} words, {num_wins} windows"
    )

    # ── 2. Load lines with metadata ──
    store = MetadataStore(DB_PATH)
    line_entries = load_lines_with_metadata(store)
    console.print(f"Loaded {len(line_entries)} lines with metadata.")

    # ── 3. Load mask schedule ──
    mask_schedule = load_mask_schedule(MASK_PATH)
    console.print(
        f"Loaded mask schedule for {len(mask_schedule)} lines."
    )

    # ── 4. Generate per-token records ──
    console.print("Generating per-token failure records...")
    token_records = []
    current_window = 0

    for line_entry in line_entries:
        tokens = line_entry["tokens"]
        folio_id = line_entry["folio_id"]
        line_index = line_entry["line_index"]
        section = line_entry["section"]
        hand = line_entry["hand"]

        # Get oracle offset for this line
        oracle_key = (folio_id, line_index)
        oracle_offset = mask_schedule.get(oracle_key, 0)

        prev_word = None
        for token_pos, word in enumerate(tokens):
            record = {
                "word": word,
                "folio_id": folio_id,
                "line_index": line_index,
                "token_position": token_pos,
                "section": section,
                "hand": hand,
                "prev_word": prev_word,
                "next_word": tokens[token_pos + 1] if token_pos + 1 < len(tokens) else None,
            }

            if word not in lattice_map:
                record["category"] = "not_in_palette"
                record["actual_distance"] = None
                record["signed_distance"] = None
                record["admissible_under_oracle"] = False
                record["oracle_offset"] = oracle_offset
                token_records.append(record)
                prev_word = word
                continue

            assigned_window = lattice_map[word]

            # Find distance to nearest window containing this word
            found_dist = None
            found_signed = None
            for dist in range(0, num_wins // 2 + 1):
                for direction in [1, -1]:
                    check_win = (current_window + (dist * direction)) % num_wins
                    if word in window_contents.get(check_win, []):
                        found_dist = dist
                        found_signed = dist * direction
                        break
                if found_dist is not None:
                    break

            # Categorize
            if found_dist is not None and found_dist <= 1:
                category = "admissible"
            elif found_dist is not None and found_dist <= 3:
                category = "extended_drift"
            elif found_dist is not None and found_dist <= 10:
                category = "wrong_window"
            elif found_dist is not None:
                category = "extreme_jump"
            else:
                # Word in lattice_map but not found in any window_contents
                # (shouldn't happen but handle gracefully)
                category = "extreme_jump"
                found_dist = num_wins // 2

            record["actual_distance"] = found_dist
            record["signed_distance"] = found_signed
            record["category"] = category

            # ── Mask-recoverability check ──
            # Under oracle offset, is this token admissible?
            shifted_win = (current_window + oracle_offset) % num_wins
            oracle_admissible = False
            for d in [-1, 0, 1]:
                check_win = (shifted_win + d) % num_wins
                if word in window_contents.get(check_win, []):
                    oracle_admissible = True
                    break
            record["admissible_under_oracle"] = oracle_admissible
            record["oracle_offset"] = oracle_offset

            # Advance window state
            current_window = assigned_window

            token_records.append(record)
            prev_word = word

    total_tokens = len(token_records)
    console.print(f"Generated {total_tokens:,} per-token records.")

    # ── 5. Category breakdown ──
    category_counts = Counter(r["category"] for r in token_records)
    console.print("\n[bold]Category Breakdown:[/bold]")
    table = Table(title="Per-Token Failure Categories")
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Rate", justify="right", style="bold green")
    for cat in ["admissible", "extended_drift", "wrong_window",
                "extreme_jump", "not_in_palette"]:
        count = category_counts.get(cat, 0)
        rate = count / total_tokens if total_tokens > 0 else 0
        table.add_row(cat, f"{count:,}", f"{rate * 100:.2f}%")
    console.print(table)

    # ── 6. Mask-recoverability analysis ──
    wrong_window_records = [
        r for r in token_records if r["category"] == "wrong_window"
    ]
    extended_drift_records = [
        r for r in token_records if r["category"] == "extended_drift"
    ]
    extreme_jump_records = [
        r for r in token_records if r["category"] == "extreme_jump"
    ]

    # Among wrong-window tokens, how many are admissible under oracle?
    ww_oracle_ok = sum(
        1 for r in wrong_window_records if r["admissible_under_oracle"]
    )
    ww_total = len(wrong_window_records)
    ww_recovery = ww_oracle_ok / ww_total if ww_total > 0 else 0

    # Same for extended drift
    ed_oracle_ok = sum(
        1 for r in extended_drift_records if r["admissible_under_oracle"]
    )
    ed_total = len(extended_drift_records)

    # Same for extreme jumps
    ej_oracle_ok = sum(
        1 for r in extreme_jump_records if r["admissible_under_oracle"]
    )
    ej_total = len(extreme_jump_records)

    console.print(
        "\n[bold]Mask Recoverability:[/bold]"
    )
    console.print(
        f"  Wrong-window tokens recoverable under oracle: "
        f"{ww_oracle_ok:,}/{ww_total:,} ({ww_recovery * 100:.1f}%)"
    )
    if ed_total > 0:
        console.print(
            f"  Extended-drift recoverable: "
            f"{ed_oracle_ok:,}/{ed_total:,} ({ed_oracle_ok / ed_total * 100:.1f}%)"
        )
    if ej_total > 0:
        console.print(
            f"  Extreme-jump recoverable: "
            f"{ej_oracle_ok:,}/{ej_total:,} ({ej_oracle_ok / ej_total * 100:.1f}%)"
        )

    # ── 7. Distance distribution analysis ──
    # Focus on wrong_window range (dist 2-10)
    ww_distances = [
        r["actual_distance"] for r in wrong_window_records
        if r["actual_distance"] is not None
    ]

    dist_histogram = Counter(ww_distances)
    bimodality = hartigan_dip_proxy(ww_distances)

    console.print("\n[bold]Distance Distribution (wrong_window, dist 2-10):[/bold]")
    console.print(f"  Bimodality coefficient: {bimodality['bc']:.3f}")
    console.print(
        f"  {'BIMODAL' if bimodality['is_bimodal'] else 'UNIMODAL'} "
        f"(threshold: 0.555)"
    )
    for dist in sorted(dist_histogram.keys()):
        count = dist_histogram[dist]
        bar = "#" * min(60, int(count / max(dist_histogram.values()) * 60))
        console.print(f"    dist={dist:2d}: {count:5,} {bar}")

    # Also look at full non-admissible distance distribution
    all_distances = [
        r["actual_distance"] for r in token_records
        if r["actual_distance"] is not None and r["category"] != "admissible"
    ]
    full_dist_histogram = Counter(all_distances)

    # ── 8. Bigram-predictable drift ──
    # H(actual_distance | prev_word) vs H(actual_distance) for wrong-window
    console.print("\n[bold]Bigram-Predictable Drift:[/bold]")

    # Filter to tokens with prev_word and actual_distance
    bigram_records = [
        r for r in token_records
        if r["prev_word"] is not None
        and r["actual_distance"] is not None
        and r["category"] in ("wrong_window", "extended_drift", "extreme_jump")
    ]

    # H(distance) unconditional
    uncond_dist_counts = Counter(r["actual_distance"] for r in bigram_records)
    h_uncond = entropy(list(uncond_dist_counts.values()))

    # H(distance | prev_word) — filter to prev_words with ≥5 observations
    prev_word_groups = defaultdict(list)
    for r in bigram_records:
        prev_word_groups[r["prev_word"]].append(r["actual_distance"])

    h_cond = 0.0
    eligible_total = 0
    eligible_words = 0
    for pw, dists in prev_word_groups.items():
        if len(dists) >= 5:
            eligible_total += len(dists)
            eligible_words += 1

    if eligible_total > 0:
        for pw, dists in prev_word_groups.items():
            if len(dists) >= 5:
                p_pw = len(dists) / eligible_total
                dist_counts = list(Counter(dists).values())
                h_cond += p_pw * entropy(dist_counts)

    info_gain = h_uncond - h_cond if eligible_total > 0 else 0

    console.print(f"  H(distance) = {h_uncond:.3f} bits")
    console.print(
        f"  H(distance | prev_word) = {h_cond:.3f} bits "
        f"({eligible_words} eligible prev_words, "
        f"{eligible_total} observations)"
    )
    console.print(f"  Information gain: {info_gain:.3f} bits")

    # ── 9. Consistent offset families ──
    console.print("\n[bold]Consistent Offset Families:[/bold]")
    signed_dists = [
        r["signed_distance"] for r in token_records
        if r["signed_distance"] is not None
        and r["category"] in ("wrong_window", "extended_drift", "extreme_jump")
    ]
    signed_counts = Counter(signed_dists)
    top_signed = signed_counts.most_common(15)

    table2 = Table(title="Top 15 Signed Distances (non-admissible tokens)")
    table2.add_column("Signed Distance", justify="right", style="cyan")
    table2.add_column("Count", justify="right")
    table2.add_column("% of failures", justify="right")
    total_failures = len(signed_dists)
    for sd, count in top_signed:
        rate = count / total_failures * 100 if total_failures > 0 else 0
        table2.add_row(f"{sd:+d}", f"{count:,}", f"{rate:.1f}%")
    console.print(table2)

    # ── 10. Cross-transcription noise check ──
    console.print("\n[bold]Cross-Transcription Noise Check:[/bold]")
    # For wrong-window tokens, check if same position fails in other sources
    # Load other transcriptions
    cross_results = {}
    for source_id in CROSS_SOURCES:
        try:
            src_lines = load_canonical_lines(store, source_id=source_id)
            if src_lines:
                cross_results[source_id] = src_lines
                console.print(
                    f"  Loaded {source_id}: {len(src_lines)} lines"
                )
        except Exception as e:
            console.print(f"  [yellow]Could not load {source_id}: {e}[/yellow]")

    # Build position lookup for cross-sources: (folio_line_idx) -> tokens
    # We'll use a simpler approach: for wrong-window tokens, check if the
    # same word at the same approximate corpus position fails in other sources
    zl_only_failures = 0
    structural_failures = 0
    cross_check_total = 0

    if cross_results:
        # Build per-source vocab sets for quick lookup
        source_vocabs = {}
        for sid, lines in cross_results.items():
            source_vocabs[sid] = set(t for line in lines for t in line)

        for r in wrong_window_records:
            word = r["word"]
            # Check if word exists in other sources at all
            in_other = sum(
                1 for sid, vocab in source_vocabs.items()
                if word in vocab
            )
            if in_other == 0:
                # Word only in ZL — likely transcription artifact
                zl_only_failures += 1
            else:
                structural_failures += 1
            cross_check_total += 1

        console.print(
            f"  Wrong-window tokens in ZL only: "
            f"{zl_only_failures:,}/{cross_check_total:,} "
            f"({zl_only_failures / cross_check_total * 100:.1f}%)"
        )
        console.print(
            f"  Structural (in ≥1 other source): "
            f"{structural_failures:,}/{cross_check_total:,} "
            f"({structural_failures / cross_check_total * 100:.1f}%)"
        )

    # ── 11. Section-correlated failure patterns ──
    console.print("\n[bold]Section-Correlated Failure Patterns:[/bold]")
    section_records = defaultdict(list)
    for r in token_records:
        section_records[r["section"]].append(r)

    table3 = Table(title="Per-Section Failure Profile")
    table3.add_column("Section", style="cyan")
    table3.add_column("Tokens", justify="right")
    table3.add_column("Admissible", justify="right", style="green")
    table3.add_column("Ext. Drift", justify="right")
    table3.add_column("Wrong Win", justify="right", style="yellow")
    table3.add_column("Extreme", justify="right", style="red")
    table3.add_column("Not Palette", justify="right")
    table3.add_column("Oracle Recov.", justify="right", style="bold")

    section_profiles = {}
    for section in sorted(
        section_records.keys(),
        key=lambda s: len(section_records[s]),
        reverse=True,
    ):
        records = section_records[section]
        n = len(records)
        if n == 0:
            continue

        cats = Counter(r["category"] for r in records)
        # Oracle recovery rate for non-admissible tokens
        non_adm = [r for r in records if r["category"] != "not_in_palette"
                    and r["category"] != "admissible"]
        oracle_ok = sum(1 for r in non_adm if r["admissible_under_oracle"])
        oracle_rate = oracle_ok / len(non_adm) if non_adm else 0

        # Section distance profile
        sec_distances = [
            r["actual_distance"] for r in records
            if r["actual_distance"] is not None
            and r["category"] in ("wrong_window", "extended_drift", "extreme_jump")
        ]
        sec_dist_hist = dict(Counter(sec_distances))

        section_profiles[section] = {
            "total_tokens": n,
            "admissible": cats.get("admissible", 0),
            "extended_drift": cats.get("extended_drift", 0),
            "wrong_window": cats.get("wrong_window", 0),
            "extreme_jump": cats.get("extreme_jump", 0),
            "not_in_palette": cats.get("not_in_palette", 0),
            "oracle_recovery_rate": oracle_rate,
            "distance_histogram": {str(k): v for k, v in sec_dist_hist.items()},
        }

        table3.add_row(
            section,
            f"{n:,}",
            f"{cats.get('admissible', 0) / n * 100:.1f}%",
            f"{cats.get('extended_drift', 0) / n * 100:.1f}%",
            f"{cats.get('wrong_window', 0) / n * 100:.1f}%",
            f"{cats.get('extreme_jump', 0) / n * 100:.1f}%",
            f"{cats.get('not_in_palette', 0) / n * 100:.1f}%",
            f"{oracle_rate * 100:.1f}%",
        )
    console.print(table3)

    # ── 12. Save results ──
    results = {
        "total_tokens": total_tokens,
        "category_counts": dict(category_counts),
        "category_rates": {
            k: v / total_tokens for k, v in category_counts.items()
        },
        "mask_recoverability": {
            "wrong_window": {
                "total": ww_total,
                "oracle_recoverable": ww_oracle_ok,
                "recovery_rate": ww_recovery,
            },
            "extended_drift": {
                "total": ed_total,
                "oracle_recoverable": ed_oracle_ok,
                "recovery_rate": ed_oracle_ok / ed_total if ed_total > 0 else 0,
            },
            "extreme_jump": {
                "total": ej_total,
                "oracle_recoverable": ej_oracle_ok,
                "recovery_rate": ej_oracle_ok / ej_total if ej_total > 0 else 0,
            },
        },
        "distance_distribution": {
            "wrong_window_histogram": {
                str(k): v for k, v in sorted(dist_histogram.items())
            },
            "full_failure_histogram": {
                str(k): v for k, v in sorted(full_dist_histogram.items())
            },
            "bimodality_test": bimodality,
        },
        "bigram_predictability": {
            "h_distance_unconditional": h_uncond,
            "h_distance_given_prev_word": h_cond,
            "information_gain_bits": info_gain,
            "eligible_prev_words": eligible_words,
            "eligible_observations": eligible_total,
        },
        "consistent_offset_families": {
            "top_15_signed_distances": [
                {"signed_distance": sd, "count": c}
                for sd, c in top_signed
            ],
            "total_non_admissible": total_failures,
        },
        "cross_transcription_noise": {
            "sources_checked": list(cross_results.keys()),
            "zl_only_failures": zl_only_failures,
            "structural_failures": structural_failures,
            "total_checked": cross_check_total,
            "zl_only_rate": (
                zl_only_failures / cross_check_total
                if cross_check_total > 0 else 0
            ),
        },
        "section_profiles": section_profiles,
        # Per-token records (compact: omit for JSON size, keep summary)
        "per_token_sample": [
            {k: v for k, v in r.items()}
            for r in token_records[:100]
        ],
        "per_token_count": total_tokens,
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved {OUTPUT_PATH}[/green]")

    # ── Overall verdict ──
    console.print("\n" + "=" * 60)
    console.print("[bold]Verdict:[/bold]")

    # Key findings
    if ww_recovery > 0.3:
        console.print(
            f"  [green]SIGNIFICANT:[/green] {ww_recovery * 100:.0f}% of "
            f"wrong-window tokens are recoverable under oracle mask. "
            f"Mask model is a promising avenue."
        )
    else:
        console.print(
            f"  [yellow]LIMITED:[/yellow] Only {ww_recovery * 100:.0f}% of "
            f"wrong-window tokens are recoverable under oracle mask."
        )

    if bimodality.get("is_bimodal"):
        console.print(
            "  [yellow]BIMODAL distance distribution[/yellow] suggests "
            "two distinct failure mechanisms."
        )
    else:
        console.print(
            "  Unimodal distance distribution suggests a single "
            "smooth drift mechanism."
        )

    if info_gain > 0.3:
        console.print(
            f"  [green]SIGNIFICANT bigram context:[/green] {info_gain:.2f} "
            f"bits of information gain from prev_word."
        )
    else:
        console.print(
            f"  Weak bigram context: {info_gain:.2f} bits of information gain."
        )

    if cross_check_total > 0 and zl_only_failures / cross_check_total > 0.2:
        console.print(
            f"  [yellow]WARNING:[/yellow] {zl_only_failures / cross_check_total * 100:.0f}% "
            f"of wrong-window tokens exist only in ZL — "
            f"possible transcription artifacts."
        )
    elif cross_check_total > 0:
        console.print(
            f"  [green]STRUCTURAL:[/green] {structural_failures / cross_check_total * 100:.0f}% "
            f"of wrong-window failures confirmed in other transcriptions."
        )


if __name__ == "__main__":
    with active_run(
        config={"seed": 42, "command": "run_14z4_failure_taxonomy"}
    ):
        main()
