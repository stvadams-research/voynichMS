#!/usr/bin/env python3
"""Phase 14K: Emulator Calibration with Offset Corrections.

Learns canonical per-window offset corrections from the full corpus,
then generates two synthetic corpora (with and without corrections)
and compares their statistical profiles to the real manuscript.

Metrics compared:
  1. Unigram and bigram entropy
  2. N-gram overgeneration (2-5 gram)
  3. Signed offset distribution + KL divergence from real
  4. Admissibility of synthetic text through the lattice
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

from phase1_foundation.core.data_loading import sanitize_token  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import (  # noqa: E402
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)
from phase14_machine.high_fidelity_emulator import HighFidelityVolvelle  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = (
    project_root / "results/data/phase14_machine/full_palette_grid.json"
)
OUTPUT_PATH = (
    project_root / "results/data/phase14_machine/emulator_calibration.json"
)
OFFSETS_PATH = (
    project_root / "results/data/phase14_machine/canonical_offsets.json"
)
console = Console()

NUM_WINDOWS = 50
SEED = 42
NUM_SYNTHETIC_LINES = 5000


# ── Helpers ──────────────────────────────────────────────────────────────

def entropy_from_counts(counts):
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


def signed_circular_offset(a, b, n=NUM_WINDOWS):
    """Signed circular distance from window a to window b."""
    raw = (b - a) % n
    if raw > n // 2:
        raw -= n
    return raw


def kl_divergence(p_counts, q_counts, all_keys):
    """KL(P || Q) in bits, with Laplace smoothing."""
    p_total = sum(p_counts.values()) + len(all_keys)
    q_total = sum(q_counts.values()) + len(all_keys)
    kl = 0.0
    for k in all_keys:
        p = (p_counts.get(k, 0) + 1) / p_total
        q = (q_counts.get(k, 0) + 1) / q_total
        if p > 0:
            kl += p * math.log2(p / q)
    return kl


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


def get_folio_num(folio_id):
    match = re.search(r"f(\d+)", folio_id)
    return int(match.group(1)) if match else 0


def load_all_lines(store):
    """Load all canonical ZL lines as plain token lists."""
    session = store.Session()
    try:
        rows = (
            session.query(
                TranscriptionTokenRecord.content,
                TranscriptionLineRecord.id,
            )
            .join(
                TranscriptionLineRecord,
                TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id,
            )
            .join(
                PageRecord,
                TranscriptionLineRecord.page_id == PageRecord.id,
            )
            .filter(PageRecord.dataset_id == "voynich_real")
            .filter(TranscriptionLineRecord.source_id == "zandbergen_landini")
            .order_by(
                PageRecord.id,
                TranscriptionLineRecord.line_index,
                TranscriptionTokenRecord.token_index,
            )
            .all()
        )

        lines = []
        current_tokens = []
        current_line_id = None

        for content, line_id in rows:
            clean = sanitize_token(content)
            if not clean:
                continue
            if current_line_id is not None and line_id != current_line_id:
                if current_tokens:
                    lines.append(current_tokens)
                current_tokens = []
            current_tokens.append(clean)
            current_line_id = line_id

        if current_tokens:
            lines.append(current_tokens)

        return lines
    finally:
        session.close()


def learn_offset_corrections(lines, lattice_map, min_obs=5):
    """Learn per-window mode offset corrections from training data."""
    groups = defaultdict(list)
    for line in lines:
        for i in range(1, len(line)):
            prev_word = line[i - 1]
            curr_word = line[i]
            if prev_word not in lattice_map or curr_word not in lattice_map:
                continue
            prev_win = lattice_map[prev_word]
            curr_win = lattice_map[curr_word]
            offset = signed_circular_offset(prev_win, curr_win)
            groups[prev_win].append(offset)

    corrections = {}
    for win, offsets in groups.items():
        if len(offsets) >= min_obs:
            corrections[win] = Counter(offsets).most_common(1)[0][0]

    return corrections


# ── Analysis Functions ───────────────────────────────────────────────────

def compute_entropy_profile(lines):
    """Compute unigram and bigram entropy for a corpus."""
    # Unigram
    word_counts = Counter()
    bigram_counts = Counter()
    total_tokens = 0

    for line in lines:
        for word in line:
            word_counts[word] += 1
            total_tokens += 1
        for i in range(1, len(line)):
            bigram_counts[(line[i - 1], line[i])] += 1

    h_unigram = entropy_from_counts(list(word_counts.values()))

    # Conditional entropy H(word | prev_word)
    prev_word_groups = defaultdict(list)
    for (pw, cw), count in bigram_counts.items():
        prev_word_groups[pw].append(count)

    total_bigrams = sum(bigram_counts.values())
    h_conditional = 0.0
    for pw, counts in prev_word_groups.items():
        pw_total = sum(counts)
        p_pw = pw_total / total_bigrams
        h_conditional += p_pw * entropy_from_counts(counts)

    h_bigram = entropy_from_counts(list(bigram_counts.values()))

    return {
        "total_tokens": total_tokens,
        "vocab_size": len(word_counts),
        "h_unigram": round(h_unigram, 4),
        "h_bigram": round(h_bigram, 4),
        "h_conditional": round(h_conditional, 4),
    }


def compute_ngram_overlap(real_lines, syn_lines, max_n=5):
    """Compute n-gram overlap and overgeneration for n=2..max_n."""
    results = {}
    for n in range(2, max_n + 1):
        real_ngrams = set()
        syn_ngrams = set()
        for line in real_lines:
            for i in range(len(line) - n + 1):
                real_ngrams.add(tuple(line[i:i + n]))
        for line in syn_lines:
            for i in range(len(line) - n + 1):
                syn_ngrams.add(tuple(line[i:i + n]))

        overlap = real_ngrams & syn_ngrams
        syn_only = syn_ngrams - real_ngrams

        results[f"{n}-gram"] = {
            "real_unique": len(real_ngrams),
            "syn_unique": len(syn_ngrams),
            "overlap": len(overlap),
            "overlap_frac_of_real": round(len(overlap) / len(real_ngrams), 4) if real_ngrams else 0,
            "syn_unattested": len(syn_only),
            "unattested_frac": round(len(syn_only) / len(syn_ngrams), 4) if syn_ngrams else 0,
            "overgeneration_ratio": round(len(syn_ngrams) / len(real_ngrams), 2) if real_ngrams else 0,
        }
    return results


def compute_offset_profile(lines, lattice_map):
    """Compute signed offset distribution for consecutive token pairs."""
    offset_counts = Counter()
    total = 0
    admissible = 0
    extended = 0

    for line in lines:
        for i in range(1, len(line)):
            prev_word = line[i - 1]
            curr_word = line[i]
            if prev_word not in lattice_map or curr_word not in lattice_map:
                continue
            prev_win = lattice_map[prev_word]
            curr_win = lattice_map[curr_word]
            offset = signed_circular_offset(prev_win, curr_win)
            offset_counts[offset] += 1
            total += 1
            if abs(offset) <= 1:
                admissible += 1
            if abs(offset) <= 3:
                extended += 1

    return {
        "total_transitions": total,
        "admissible_strict": admissible,
        "admissible_rate": round(admissible / total, 4) if total else 0,
        "extended_drift": extended,
        "extended_rate": round(extended / total, 4) if total else 0,
        "offset_counts": dict(sorted(offset_counts.items())),
    }


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    console.print("[bold magenta]Phase 14K: Emulator Calibration with Offset Corrections[/bold magenta]")

    # 1. Load data
    console.print("Loading palette...")
    lattice_map, window_contents = load_palette(PALETTE_PATH)
    console.print(f"  Palette: {len(lattice_map)} words, {len(window_contents)} windows")

    console.print("Loading corpus...")
    store = MetadataStore(DB_PATH)
    real_lines = load_all_lines(store)
    total_tokens = sum(len(l) for l in real_lines)
    console.print(f"  Corpus: {len(real_lines)} lines, {total_tokens} tokens")

    # 2. Learn canonical offset corrections (full corpus)
    console.print("\n[bold]Learning canonical offset corrections...[/bold]")
    corrections = learn_offset_corrections(real_lines, lattice_map, min_obs=5)
    console.print(f"  Corrections: {len(corrections)} windows")
    nonzero = sum(1 for v in corrections.values() if v != 0)
    console.print(f"  Non-zero corrections: {nonzero}/{len(corrections)}")

    # Save canonical offsets
    offsets_data = {
        "corrections": {str(k): v for k, v in sorted(corrections.items())},
        "num_corrections": len(corrections),
        "nonzero_count": nonzero,
        "training_data": "full_corpus",
        "min_obs": 5,
    }
    with active_run(config={"seed": SEED, "command": "run_14zc_emulator_calibration"}):
        ProvenanceWriter.save_results(offsets_data, OFFSETS_PATH)
    console.print(f"  Saved to {OFFSETS_PATH}")

    # 3. Generate synthetic corpora
    console.print(f"\n[bold]Generating {NUM_SYNTHETIC_LINES} synthetic lines...[/bold]")

    # Corpus A: without corrections (baseline)
    console.print("  Corpus A (no corrections)...")
    emulator_a = HighFidelityVolvelle(
        lattice_map, window_contents, seed=SEED, log_choices=False
    )
    corpus_a = emulator_a.generate_mirror_corpus(NUM_SYNTHETIC_LINES)
    tokens_a = sum(len(l) for l in corpus_a)
    console.print(f"    {len(corpus_a)} lines, {tokens_a} tokens")

    # Corpus B: with corrections
    console.print("  Corpus B (with offset corrections)...")
    emulator_b = HighFidelityVolvelle(
        lattice_map, window_contents, seed=SEED, log_choices=False,
        offset_corrections=corrections
    )
    corpus_b = emulator_b.generate_mirror_corpus(NUM_SYNTHETIC_LINES)
    tokens_b = sum(len(l) for l in corpus_b)
    console.print(f"    {len(corpus_b)} lines, {tokens_b} tokens")

    # 4. Entropy comparison
    console.print("\n[bold]Entropy comparison...[/bold]")
    ent_real = compute_entropy_profile(real_lines)
    ent_a = compute_entropy_profile(corpus_a)
    ent_b = compute_entropy_profile(corpus_b)

    ent_table = Table(title="Entropy Comparison")
    ent_table.add_column("Metric", style="cyan")
    ent_table.add_column("Real", justify="right")
    ent_table.add_column("Synthetic A\n(no corr.)", justify="right")
    ent_table.add_column("Synthetic B\n(with corr.)", justify="right")
    ent_table.add_column("A fit %", justify="right")
    ent_table.add_column("B fit %", justify="right")

    for metric in ["h_unigram", "h_conditional", "vocab_size"]:
        r_val = ent_real[metric]
        a_val = ent_a[metric]
        b_val = ent_b[metric]
        if metric == "vocab_size":
            ent_table.add_row(
                metric, str(r_val), str(a_val), str(b_val), "—", "—"
            )
        else:
            a_fit = round(min(r_val, a_val) / max(r_val, a_val) * 100, 1) if max(r_val, a_val) > 0 else 0
            b_fit = round(min(r_val, b_val) / max(r_val, b_val) * 100, 1) if max(r_val, b_val) > 0 else 0
            ent_table.add_row(
                metric,
                f"{r_val:.4f}",
                f"{a_val:.4f}",
                f"{b_val:.4f}",
                f"{a_fit}%",
                f"{b_fit}%",
            )
    console.print(ent_table)

    # Mirror entropy fit (unigram)
    a_mirror_fit = round(min(ent_real["h_unigram"], ent_a["h_unigram"]) /
                         max(ent_real["h_unigram"], ent_a["h_unigram"]) * 100, 2) if ent_real["h_unigram"] > 0 else 0
    b_mirror_fit = round(min(ent_real["h_unigram"], ent_b["h_unigram"]) /
                         max(ent_real["h_unigram"], ent_b["h_unigram"]) * 100, 2) if ent_real["h_unigram"] > 0 else 0
    console.print(f"  Mirror entropy fit (unigram): A={a_mirror_fit}%, B={b_mirror_fit}%")

    # 5. N-gram overlap
    console.print("\n[bold]N-gram overlap...[/bold]")
    ngram_a = compute_ngram_overlap(real_lines, corpus_a)
    ngram_b = compute_ngram_overlap(real_lines, corpus_b)

    ng_table = Table(title="N-gram Comparison")
    ng_table.add_column("N-gram", style="cyan")
    ng_table.add_column("Real unique", justify="right")
    ng_table.add_column("A unique", justify="right")
    ng_table.add_column("B unique", justify="right")
    ng_table.add_column("A overlap %", justify="right")
    ng_table.add_column("B overlap %", justify="right")
    ng_table.add_column("A overgen", justify="right")
    ng_table.add_column("B overgen", justify="right")

    for n in range(2, 6):
        key = f"{n}-gram"
        na = ngram_a[key]
        nb = ngram_b[key]
        ng_table.add_row(
            key,
            str(na["real_unique"]),
            str(na["syn_unique"]),
            str(nb["syn_unique"]),
            f"{na['overlap_frac_of_real']*100:.1f}%",
            f"{nb['overlap_frac_of_real']*100:.1f}%",
            f"{na['overgeneration_ratio']:.1f}×",
            f"{nb['overgeneration_ratio']:.1f}×",
        )
    console.print(ng_table)

    # 6. Offset distribution comparison
    console.print("\n[bold]Transition offset profiles...[/bold]")
    off_real = compute_offset_profile(real_lines, lattice_map)
    off_a = compute_offset_profile(corpus_a, lattice_map)
    off_b = compute_offset_profile(corpus_b, lattice_map)

    off_table = Table(title="Offset Profile Comparison")
    off_table.add_column("Metric", style="cyan")
    off_table.add_column("Real", justify="right")
    off_table.add_column("Synthetic A", justify="right")
    off_table.add_column("Synthetic B", justify="right")
    off_table.add_row(
        "Transitions",
        str(off_real["total_transitions"]),
        str(off_a["total_transitions"]),
        str(off_b["total_transitions"]),
    )
    off_table.add_row(
        "Admissible (±1)",
        f"{off_real['admissible_rate']*100:.1f}%",
        f"{off_a['admissible_rate']*100:.1f}%",
        f"{off_b['admissible_rate']*100:.1f}%",
    )
    off_table.add_row(
        "Extended (±3)",
        f"{off_real['extended_rate']*100:.1f}%",
        f"{off_a['extended_rate']*100:.1f}%",
        f"{off_b['extended_rate']*100:.1f}%",
    )
    console.print(off_table)

    # KL divergence
    all_offsets = set(off_real["offset_counts"].keys()) | set(off_a["offset_counts"].keys()) | set(off_b["offset_counts"].keys())
    kl_a = kl_divergence(off_real["offset_counts"], off_a["offset_counts"], all_offsets)
    kl_b = kl_divergence(off_real["offset_counts"], off_b["offset_counts"], all_offsets)
    console.print(f"  KL(Real || Synthetic A): {kl_a:.4f} bits")
    console.print(f"  KL(Real || Synthetic B): {kl_b:.4f} bits")

    if kl_b < kl_a:
        console.print(f"  [green]→ Corrected emulator is closer to real ({kl_a - kl_b:.4f} bits improvement)[/green]")
    else:
        console.print(f"  [yellow]→ Corrected emulator is farther from real ({kl_b - kl_a:.4f} bits worse)[/yellow]")

    # 7. Summary
    console.print("\n[bold yellow]Summary:[/bold yellow]")

    improvements = 0
    total_metrics = 0

    # Entropy closeness
    for metric in ["h_unigram", "h_conditional"]:
        r = ent_real[metric]
        a_gap = abs(r - ent_a[metric])
        b_gap = abs(r - ent_b[metric])
        total_metrics += 1
        if b_gap < a_gap:
            improvements += 1
            console.print(f"  {metric}: B closer ({b_gap:.4f} vs {a_gap:.4f} gap) [green]✓[/green]")
        else:
            console.print(f"  {metric}: A closer ({a_gap:.4f} vs {b_gap:.4f} gap) [red]✗[/red]")

    # KL divergence
    total_metrics += 1
    if kl_b < kl_a:
        improvements += 1
        console.print(f"  KL divergence: B closer ({kl_b:.4f} vs {kl_a:.4f}) [green]✓[/green]")
    else:
        console.print(f"  KL divergence: A closer ({kl_a:.4f} vs {kl_b:.4f}) [red]✗[/red]")

    # Admissibility closeness to real
    total_metrics += 1
    r_adm = off_real["admissible_rate"]
    a_adm_gap = abs(r_adm - off_a["admissible_rate"])
    b_adm_gap = abs(r_adm - off_b["admissible_rate"])
    if b_adm_gap < a_adm_gap:
        improvements += 1
        console.print(f"  Admissibility closeness: B closer ({b_adm_gap:.4f} vs {a_adm_gap:.4f} gap) [green]✓[/green]")
    else:
        console.print(f"  Admissibility closeness: A closer ({a_adm_gap:.4f} vs {b_adm_gap:.4f} gap) [red]✗[/red]")

    console.print(f"\n  Metrics where B (corrected) wins: {improvements}/{total_metrics}")

    # 8. Save results
    results = {
        "entropy": {
            "real": ent_real,
            "synthetic_a": ent_a,
            "synthetic_b": ent_b,
            "mirror_fit_a": a_mirror_fit,
            "mirror_fit_b": b_mirror_fit,
        },
        "ngrams": {
            "synthetic_a": ngram_a,
            "synthetic_b": ngram_b,
        },
        "offset_profiles": {
            "real": {
                "admissible_rate": off_real["admissible_rate"],
                "extended_rate": off_real["extended_rate"],
                "total_transitions": off_real["total_transitions"],
            },
            "synthetic_a": {
                "admissible_rate": off_a["admissible_rate"],
                "extended_rate": off_a["extended_rate"],
                "total_transitions": off_a["total_transitions"],
            },
            "synthetic_b": {
                "admissible_rate": off_b["admissible_rate"],
                "extended_rate": off_b["extended_rate"],
                "total_transitions": off_b["total_transitions"],
            },
        },
        "kl_divergence": {
            "synthetic_a": round(kl_a, 4),
            "synthetic_b": round(kl_b, 4),
            "improvement_bits": round(kl_a - kl_b, 4),
        },
        "corrections_used": {
            "num_corrections": len(corrections),
            "nonzero": nonzero,
        },
        "generation_params": {
            "seed": SEED,
            "num_lines": NUM_SYNTHETIC_LINES,
        },
        "summary": {
            "metrics_improved": improvements,
            "metrics_total": total_metrics,
        },
    }

    with active_run(config={"seed": SEED, "command": "run_14zc_emulator_calibration"}):
        ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Results saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    main()
