#!/usr/bin/env python3
"""Phase 14Z2: Mask Rotation Prediction.

Oracle mask inference (run_14x) raises admissibility from 39.57% to 53.91%
(+14.3pp) by trying all 50 offsets per line and picking the best. This script
tests whether simple metadata-based rules can predict mask offsets generatively.

Prediction rules tested:
1. global_mode: All lines use the single most common offset
2. per_section: Each of 7 sections uses its mode offset
3. per_quire: Each quire uses its mode offset
4. per_hand: Hand 1 vs Hand 2 each use their mode offset
5. per_page: All lines on a page share that page's mode offset
6. prev_line_carry: Each line uses the previous line's oracle offset
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import sanitize_token  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import (  # noqa: E402
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)

DB_PATH = "sqlite:///data/voynich.db"
REORDERED_PATH = (
    project_root / "results/data/phase14_machine/reordered_palette.json"
)
OUTPUT_PATH = (
    project_root / "results/data/phase14_machine/mask_prediction.json"
)
console = Console()

# Section definitions (folio ranges)
SECTIONS = {
    "Herbal A": (1, 57),
    "Herbal B": (58, 66),
    "Astro": (67, 74),
    "Biological": (75, 84),
    "Cosmo": (85, 86),
    "Pharma": (87, 102),
    "Stars": (103, 116),
}


def get_folio_num(folio_id):
    """Extract numeric folio number from page ID."""
    match = re.search(r"f(\d+)", folio_id)
    return int(match.group(1)) if match else 0


def get_section(folio_num):
    """Map folio number to manuscript section."""
    for name, (lo, hi) in SECTIONS.items():
        if lo <= folio_num <= hi:
            return name
    return "Other"


def get_hand(folio_num):
    """Derive Currier hand from folio number."""
    if folio_num <= 66:
        return "Hand1"
    elif 75 <= folio_num <= 84 or 103 <= folio_num <= 116:
        return "Hand2"
    return "Unknown"


def get_quire(folio_num):
    """Approximate quire number (8 folios per quire)."""
    return (folio_num - 1) // 8 + 1


def load_lines_with_metadata(store):
    """Load ZL lines with full metadata (folio, section, hand, quire)."""
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
        current_line = []
        current_folio = None
        current_line_idx = None
        last_line_id = None

        for content, folio_id, line_id, line_idx in rows:
            clean = sanitize_token(content)
            if not clean:
                continue
            if last_line_id is not None and line_id != last_line_id:
                if current_line:
                    f_num = get_folio_num(current_folio)
                    lines.append({
                        "tokens": current_line,
                        "folio_id": current_folio,
                        "folio_num": f_num,
                        "line_index": current_line_idx,
                        "section": get_section(f_num),
                        "hand": get_hand(f_num),
                        "quire": get_quire(f_num),
                        "recto_verso": "r" if "r" in current_folio else "v",
                    })
                current_line = []
            current_line.append(clean)
            current_folio = folio_id
            current_line_idx = line_idx
            last_line_id = line_id

        if current_line:
            f_num = get_folio_num(current_folio)
            lines.append({
                "tokens": current_line,
                "folio_id": current_folio,
                "folio_num": f_num,
                "line_index": current_line_idx,
                "section": get_section(f_num),
                "hand": get_hand(f_num),
                "quire": get_quire(f_num),
                "recto_verso": "r" if "r" in current_folio else "v",
            })
        return lines
    finally:
        session.close()


def load_palette(path):
    """Load lattice_map and window_contents from a palette JSON."""
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    lm_key = (
        "reordered_lattice_map"
        if "reordered_lattice_map" in results
        else "lattice_map"
    )
    wc_key = (
        "reordered_window_contents"
        if "reordered_window_contents" in results
        else "window_contents"
    )
    lattice_map = results[lm_key]
    window_contents = {int(k): v for k, v in results[wc_key].items()}
    return lattice_map, window_contents


def score_line_with_offset(
    line_tokens, offset, lattice_map, window_contents, num_wins
):
    """Score a single line's admissibility under a given mask offset.

    Reuses the same logic as run_14x_mask_inference.py.
    """
    admissible = 0
    total = 0
    current_window = 0

    for word in line_tokens:
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


def infer_oracle_offsets(line_data, lattice_map, window_contents, num_wins):
    """Find optimal per-line mask offsets (oracle)."""
    offsets = []
    for entry in line_data:
        best_offset = 0
        best_score = -1
        for offset in range(num_wins):
            adm, total = score_line_with_offset(
                entry["tokens"], offset,
                lattice_map, window_contents, num_wins,
            )
            if total > 0 and adm > best_score:
                best_score = adm
                best_offset = offset
        offsets.append(best_offset)
    return offsets


def measure_with_offsets(line_data, offsets, lattice_map, window_contents, num_wins):
    """Measure total admissibility using given per-line offsets."""
    total_adm = 0
    total_tok = 0
    for entry, offset in zip(line_data, offsets, strict=False):
        adm, tok = score_line_with_offset(
            entry["tokens"], offset,
            lattice_map, window_contents, num_wins,
        )
        total_adm += adm
        total_tok += tok
    return total_adm, total_tok


def compute_mode(values):
    """Return the most common value."""
    if not values:
        return 0
    return Counter(values).most_common(1)[0][0]


def main():
    console.print(
        "[bold magenta]Phase 14Z2: Mask Rotation Prediction[/bold magenta]"
    )

    if not REORDERED_PATH.exists():
        console.print(f"[red]Error: {REORDERED_PATH} not found.[/red]")
        return

    # 1. Load palette
    lattice_map, window_contents = load_palette(REORDERED_PATH)
    num_wins = len(window_contents)

    # 2. Load lines with metadata
    store = MetadataStore(DB_PATH)
    line_data = load_lines_with_metadata(store)
    console.print(f"Loaded {len(line_data)} lines with metadata.")

    # 3. Baseline (no mask)
    baseline_offsets = [0] * len(line_data)
    base_adm, base_tok = measure_with_offsets(
        line_data, baseline_offsets, lattice_map, window_contents, num_wins,
    )
    base_rate = base_adm / base_tok if base_tok > 0 else 0
    console.print(f"\nBaseline (offset=0): {base_rate * 100:.2f}%")

    # 4. Oracle mask inference
    console.print("Inferring oracle per-line offsets (this takes ~2 min)...")
    oracle_offsets = infer_oracle_offsets(
        line_data, lattice_map, window_contents, num_wins,
    )
    oracle_adm, oracle_tok = measure_with_offsets(
        line_data, oracle_offsets, lattice_map, window_contents, num_wins,
    )
    oracle_rate = oracle_adm / oracle_tok if oracle_tok > 0 else 0
    oracle_gain = oracle_rate - base_rate
    console.print(f"Oracle (per-line): {oracle_rate * 100:.2f}%")
    console.print(f"Oracle gain: {oracle_gain * 100:+.2f}pp")

    # 5. Compute mode offsets for each grouping
    # Group oracle offsets by metadata
    section_offsets = defaultdict(list)
    quire_offsets = defaultdict(list)
    hand_offsets = defaultdict(list)
    page_offsets = defaultdict(list)

    for entry, offset in zip(line_data, oracle_offsets, strict=False):
        section_offsets[entry["section"]].append(offset)
        quire_offsets[entry["quire"]].append(offset)
        hand_offsets[entry["hand"]].append(offset)
        page_offsets[entry["folio_id"]].append(offset)

    global_mode = compute_mode(oracle_offsets)
    section_modes = {s: compute_mode(v) for s, v in section_offsets.items()}
    quire_modes = {q: compute_mode(v) for q, v in quire_offsets.items()}
    hand_modes = {h: compute_mode(v) for h, v in hand_offsets.items()}
    page_modes = {p: compute_mode(v) for p, v in page_offsets.items()}

    console.print(f"\nGlobal mode offset: {global_mode}")
    console.print(f"Section modes: {section_modes}")
    console.print(f"Hand modes: {hand_modes}")

    # 6. Test prediction rules
    rules = {}

    # Rule 1: Global mode
    rules["global_mode"] = [global_mode] * len(line_data)

    # Rule 2: Per-section mode
    rules["per_section"] = [
        section_modes.get(e["section"], global_mode) for e in line_data
    ]

    # Rule 3: Per-quire mode
    rules["per_quire"] = [
        quire_modes.get(e["quire"], global_mode) for e in line_data
    ]

    # Rule 4: Per-hand mode
    rules["per_hand"] = [
        hand_modes.get(e["hand"], global_mode) for e in line_data
    ]

    # Rule 5: Per-page mode
    rules["per_page"] = [
        page_modes.get(e["folio_id"], global_mode) for e in line_data
    ]

    # Rule 6: Previous line carry-forward
    prev_carry = []
    page_modes.get(line_data[0]["folio_id"], global_mode)
    for i, entry in enumerate(line_data):
        if i == 0:
            prev_carry.append(page_modes.get(entry["folio_id"], global_mode))
        elif entry["folio_id"] != line_data[i - 1]["folio_id"]:
            # New page — use page mode
            prev_carry.append(page_modes.get(entry["folio_id"], global_mode))
        else:
            prev_carry.append(oracle_offsets[i - 1])
    rules["prev_line_carry"] = prev_carry

    # 7. Evaluate each rule
    console.print("\n[bold]Evaluating prediction rules...[/bold]")
    results_table = {}

    table = Table(title="Mask Prediction Results")
    table.add_column("Rule", style="cyan")
    table.add_column("Admissibility", justify="right")
    table.add_column("Gain (pp)", justify="right")
    table.add_column("Capture %", justify="right", style="bold green")

    for rule_name, predicted_offsets in sorted(rules.items()):
        adm, tok = measure_with_offsets(
            line_data, predicted_offsets,
            lattice_map, window_contents, num_wins,
        )
        rate = adm / tok if tok > 0 else 0
        gain = rate - base_rate
        capture = (gain / oracle_gain * 100) if oracle_gain > 0 else 0

        results_table[rule_name] = {
            "admissibility": rate,
            "gain_pp": gain * 100,
            "capture_pct": capture,
            "admissible": adm,
            "total": tok,
        }

        table.add_row(
            rule_name,
            f"{rate * 100:.2f}%",
            f"{gain * 100:+.2f}",
            f"{capture:.1f}%",
        )

    # Add oracle and baseline rows
    table.add_row(
        "[dim]baseline (no mask)[/dim]",
        f"{base_rate * 100:.2f}%",
        "—",
        "0.0%",
        style="dim",
    )
    table.add_row(
        "[dim]oracle (per-line)[/dim]",
        f"{oracle_rate * 100:.2f}%",
        f"{oracle_gain * 100:+.2f}",
        "100.0%",
        style="dim",
    )
    console.print(table)

    # 8. Report best rule
    best_rule = max(results_table.items(), key=lambda x: x[1]["capture_pct"])
    console.print(
        f"\n[bold]Best rule:[/bold] {best_rule[0]} "
        f"(captures {best_rule[1]['capture_pct']:.1f}% of oracle gain, "
        f"admissibility {best_rule[1]['admissibility'] * 100:.2f}%)"
    )

    # 9. Section mode detail
    console.print("\n[bold]Per-section mode offsets:[/bold]")
    for section in sorted(section_modes.keys()):
        offsets_in_section = section_offsets[section]
        mode_offset = section_modes[section]
        mode_count = offsets_in_section.count(mode_offset)
        console.print(
            f"  {section}: offset {mode_offset} "
            f"({mode_count}/{len(offsets_in_section)} lines, "
            f"{mode_count / len(offsets_in_section) * 100:.0f}%)"
        )

    # 10. Save results
    output = {
        "baseline_admissibility": base_rate,
        "oracle_admissibility": oracle_rate,
        "oracle_gain_pp": oracle_gain * 100,
        "global_mode_offset": int(global_mode),
        "section_mode_offsets": {
            k: int(v) for k, v in section_modes.items()
        },
        "hand_mode_offsets": {k: int(v) for k, v in hand_modes.items()},
        "rules": results_table,
        "best_rule": best_rule[0],
        "best_capture_pct": best_rule[1]["capture_pct"],
        "num_lines": len(line_data),
        "num_tokens": base_tok,
    }

    ProvenanceWriter.save_results(output, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(
        config={"seed": 42, "command": "run_14z2_mask_prediction"}
    ):
        main()
