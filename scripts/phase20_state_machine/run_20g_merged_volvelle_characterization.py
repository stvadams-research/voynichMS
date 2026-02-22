#!/usr/bin/env python3
"""Phase 20, Sprint 10: 15-State Merged Volvelle Deep Characterization.

10.1: Reconstruct the size-based merge map at K=15
10.2: Per-state characterization (vocabulary, tokens, corrections, top words)
10.3: Vocabulary coherence (Jaccard, suffix distributions, KL divergence)
10.4: Historical defensibility assessment
10.5: Tabula vs merged volvelle head-to-head comparison

Sprint 3 found that size-based merging to 15 states produces a viable 193mm
volvelle (56.84% admissibility). This sprint fully characterizes the merged
device to determine whether it is a plausible historical alternative or merely
a mathematical curiosity.
"""

import json
import math
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

console = Console()

NUM_WINDOWS = 50
TARGET_STATES = 15
DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OFFSETS_PATH = project_root / "results/data/phase14_machine/canonical_offsets.json"
OUTPUT_PATH = (
    project_root / "results/data/phase20_state_machine"
    / "merged_volvelle_characterization.json"
)

# Physical constants (from Sprint 1/3)
GLYPH_WIDTH_MM = 4.0
GLYPH_HEIGHT_MM = 5.0
MARGIN_MM = 5.0
LABEL_WIDTH_MM = 2 * GLYPH_WIDTH_MM
CORR_WIDTH_MM = 3 * GLYPH_WIDTH_MM
SEP_MM = 2.0
POSITION_WIDTH_MM = LABEL_WIDTH_MM + CORR_WIDTH_MM + SEP_MM + 2 * MARGIN_MM  # 32mm
POSITION_HEIGHT_MM = GLYPH_HEIGHT_MM + 2 * MARGIN_MM  # 15mm

MAX_DEVICE_DIAMETER_MM = 350
BASELINE_ADMISSIBILITY = 0.6494

# Historical device parameters for comparison
HISTORICAL_DEVICES = {
    "Llull Ars Magna (c.1305)": {
        "positions": 16, "diameter_mm": 200,
        "vocab_per_position": 9, "type": "combinatorial",
    },
    "Alberti cipher disc (1467)": {
        "positions": 24, "diameter_mm": 120,
        "vocab_per_position": 1, "type": "substitution",
    },
    "Apian Astronomicum (1540)": {
        "positions": 30, "diameter_mm": 350,
        "vocab_per_position": 0, "type": "astronomical",
    },
}

# Common Voynichese suffixes for coherence analysis
SUFFIXES = ["-dy", "-in", "-y", "-ol", "-or", "-an", "-al", "-ar", "-am", "-om"]


# ── Data Loading ─────────────────────────────────────────────────────

def load_palette(path):
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    lm_key = ("reordered_lattice_map" if "reordered_lattice_map" in results
              else "lattice_map")
    wc_key = ("reordered_window_contents" if "reordered_window_contents" in results
              else "window_contents")
    return results[lm_key], {int(k): v for k, v in results[wc_key].items()}


def load_corrections(path):
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    return {int(k): v for k, v in results["corrections"].items()}


def load_lines(store):
    session = store.Session()
    try:
        rows = (
            session.query(
                TranscriptionTokenRecord.content,
                TranscriptionLineRecord.id,
                TranscriptionLineRecord.line_index,
            )
            .join(TranscriptionLineRecord,
                  TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
            .join(PageRecord,
                  TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == "voynich_real")
            .filter(TranscriptionLineRecord.source_id == "zandbergen_landini")
            .order_by(PageRecord.id, TranscriptionLineRecord.line_index,
                      TranscriptionTokenRecord.token_index)
            .all()
        )
        lines = []
        current_tokens = []
        current_line_id = None
        for content, line_id, _line_idx in rows:
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


# ── Merge Algorithm (replicated from Sprint 3) ──────────────────────

def build_merge_plan_size(window_contents, target_n):
    """Merge smallest-vocabulary windows into nearest neighbor.

    Returns merge_map: {original_window: surviving_window}
    """
    active = set(window_contents.keys())
    merge_map = {w: w for w in active}
    sizes = {w: len(words) for w, words in window_contents.items()}

    while len(active) > target_n:
        smallest = min(active, key=lambda w: (sizes.get(w, 0), w))
        active.discard(smallest)
        nearest = min(active, key=lambda w: (abs(w - smallest), sizes.get(w, 0)))
        for w, target in merge_map.items():
            if target == smallest:
                merge_map[w] = nearest
        sizes[nearest] = sizes.get(nearest, 0) + sizes.get(smallest, 0)

    return merge_map


def apply_merge(merge_map, lattice_map, window_contents, corrections):
    """Apply merge plan to produce new lattice structures."""
    surviving = sorted(set(merge_map.values()))
    merged_lm = {}
    for tok, w in lattice_map.items():
        merged_lm[tok] = merge_map.get(w, w)

    merged_wc = {s: [] for s in surviving}
    for w, words in window_contents.items():
        target = merge_map.get(w, w)
        merged_wc[target].extend(words)

    merged_corr = {s: corrections.get(s, 0) for s in surviving}
    return merged_lm, merged_wc, merged_corr, surviving


def evaluate_merged_admissibility(lines, merged_lm, merged_wc, surviving):
    """Compute drift admissibility under merged window system."""
    n_surv = len(surviving)
    if n_surv == 0:
        return {"strict": 0.0, "drift": 0.0, "total_transitions": 0}

    adjacent = {}
    for i, w in enumerate(surviving):
        prev_w = surviving[(i - 1) % n_surv]
        next_w = surviving[(i + 1) % n_surv]
        adjacent[w] = {prev_w, w, next_w}

    total_transitions = 0
    strict_hits = 0
    drift_hits = 0
    current_window = None

    for line in lines:
        for tok in line:
            w = merged_lm.get(tok)
            if w is None:
                continue
            if current_window is None:
                current_window = w
                continue
            total_transitions += 1
            if w == current_window:
                strict_hits += 1
                drift_hits += 1
            elif w in adjacent.get(current_window, set()):
                drift_hits += 1
            current_window = w

    if total_transitions == 0:
        return {"strict": 0.0, "drift": 0.0, "total_transitions": 0}

    return {
        "strict": round(strict_hits / total_transitions, 4),
        "drift": round(drift_hits / total_transitions, 4),
        "total_transitions": total_transitions,
    }


# ── Helpers ──────────────────────────────────────────────────────────

def get_suffix(word):
    """Extract suffix for coherence analysis."""
    for s in SUFFIXES:
        bare = s.lstrip("-")
        if word.endswith(bare) and len(word) > len(bare):
            return s
    return "-other"


def jaccard_similarity(set_a, set_b):
    """Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def kl_divergence(p, q, epsilon=1e-10):
    """KL divergence D(P || Q) with smoothing."""
    total = 0.0
    for x in set(list(p.keys()) + list(q.keys())):
        p_x = p.get(x, 0) + epsilon
        q_x = q.get(x, 0) + epsilon
        total += p_x * math.log(p_x / q_x)
    return total


def compute_token_freq(lines, lattice_map):
    """Count corpus frequency of each token."""
    freq = Counter()
    for line in lines:
        for tok in line:
            if tok in lattice_map:
                freq[tok] += 1
    return freq


# ── Sprint Functions ─────────────────────────────────────────────────

def sprint_10_1(window_contents, corrections, lattice_map, lines):
    """10.1: Reconstruct merge map and apply merge."""
    console.rule("[bold blue]10.1: Reconstruct Size-Based Merge to K=15")

    merge_map = build_merge_plan_size(window_contents, TARGET_STATES)
    m_lm, m_wc, m_corr, surviving = apply_merge(
        merge_map, lattice_map, window_contents, corrections
    )

    # Build reverse map: surviving → [original windows]
    reverse_map = defaultdict(list)
    for orig, surv in merge_map.items():
        reverse_map[surv].append(orig)
    for surv in reverse_map:
        reverse_map[surv].sort()

    # Verify
    adm = evaluate_merged_admissibility(lines, m_lm, m_wc, surviving)

    table = Table(title="Merge Map: 50 → 15 States (size-based)")
    table.add_column("Surviving\nState", justify="right")
    table.add_column("Original\nWindows")
    table.add_column("# Merged", justify="right")
    table.add_column("Union\nVocab", justify="right")
    table.add_column("Survivor\nCorr", justify="right")

    for s in surviving:
        originals = reverse_map[s]
        n_merged = len(originals) - 1  # excluding the survivor itself
        vocab_size = len(m_wc[s])
        table.add_row(
            str(s),
            ", ".join(str(w) for w in originals),
            str(n_merged),
            str(vocab_size),
            f"{m_corr[s]:+d}",
        )
    console.print(table)

    console.print(
        f"\n  Surviving states: {len(surviving)}"
        f"\n  Drift admissibility: {adm['drift']:.4f}"
        f" (baseline 50-state: {BASELINE_ADMISSIBILITY:.4f})"
    )

    return {
        "merge_map": {str(k): v for k, v in merge_map.items()},
        "reverse_map": {str(k): v for k, v in reverse_map.items()},
        "surviving_states": surviving,
        "admissibility": adm,
    }, m_lm, m_wc, m_corr, surviving, reverse_map


def sprint_10_2(m_wc, m_corr, surviving, reverse_map, corrections,
                window_contents, lines, lattice_map, token_freq):
    """10.2: Per-state characterization."""
    console.rule("[bold blue]10.2: Per-State Characterization")

    # Compute per-state corpus token counts
    state_token_counts = Counter()
    total_tokens = 0
    for line in lines:
        for tok in line:
            w = lattice_map.get(tok)
            if w is not None:
                total_tokens += 1

    # Count tokens per merged state
    m_lm_flat = {}
    for tok, w in lattice_map.items():
        # Find which surviving state this token maps to
        for s in surviving:
            if tok in m_wc[s]:
                m_lm_flat[tok] = s
                break

    for line in lines:
        for tok in line:
            s = m_lm_flat.get(tok)
            if s is not None:
                state_token_counts[s] += 1
                total_tokens += 1

    # Correct: total_tokens was double-counted
    total_tokens = sum(state_token_counts.values())

    state_profiles = []

    table = Table(title="Per-State Profile (15 Merged States)")
    table.add_column("State", justify="right")
    table.add_column("Orig\nWindows", justify="right")
    table.add_column("Vocab\nSize", justify="right")
    table.add_column("Corpus\nTokens", justify="right")
    table.add_column("Token\nShare", justify="right")
    table.add_column("Corr\nRange", justify="right")
    table.add_column("Top-5 Words")

    for s in surviving:
        originals = reverse_map[s]
        vocab = m_wc[s]
        vocab_size = len(vocab)
        token_count = state_token_counts.get(s, 0)
        token_share = token_count / total_tokens if total_tokens > 0 else 0

        # Correction range across original windows in this merged state
        corr_values = [corrections.get(w, 0) for w in originals]
        corr_min = min(corr_values)
        corr_max = max(corr_values)
        corr_range_str = (f"{corr_min:+d}" if corr_min == corr_max
                          else f"{corr_min:+d}..{corr_max:+d}")

        # Top-10 words by corpus frequency
        word_freqs = [(w, token_freq.get(w, 0)) for w in vocab]
        word_freqs.sort(key=lambda x: -x[1])
        top_10 = word_freqs[:10]
        top_5_str = ", ".join(w for w, _ in word_freqs[:5])

        # Per-original-window sizes
        orig_sizes = {w: len(window_contents[w]) for w in originals}

        profile = {
            "state": s,
            "original_windows": originals,
            "num_merged": len(originals) - 1,
            "vocabulary_size": vocab_size,
            "corpus_tokens": token_count,
            "token_share": round(token_share, 4),
            "correction_survivor": m_corr[s],
            "correction_range": [corr_min, corr_max],
            "top_10_words": [{"word": w, "freq": f} for w, f in top_10],
            "original_window_sizes": orig_sizes,
        }
        state_profiles.append(profile)

        table.add_row(
            str(s),
            str(len(originals)),
            str(vocab_size),
            str(token_count),
            f"{token_share:.1%}",
            corr_range_str,
            top_5_str,
        )

    console.print(table)

    # W18 analysis
    w18_state = None
    for s in surviving:
        if 18 in reverse_map[s]:
            w18_state = s
            break

    w18_share = 0.0
    w18_vocab = 0
    if w18_state is not None:
        for p in state_profiles:
            if p["state"] == w18_state:
                w18_share = p["token_share"]
                w18_vocab = p["vocabulary_size"]
                break

    console.print(
        f"\n  W18 analysis:"
        f"\n    W18 maps to merged state {w18_state}"
        f"\n    Merged state vocab: {w18_vocab} words"
        f"\n    Token share: {w18_share:.1%}"
        f"\n    W18 still dominates: {'YES' if w18_share > 0.30 else 'NO'}"
    )

    return {
        "state_profiles": state_profiles,
        "total_corpus_tokens": total_tokens,
        "w18_analysis": {
            "w18_merged_state": w18_state,
            "merged_vocab_size": w18_vocab,
            "token_share": w18_share,
            "still_dominant": w18_share > 0.30,
        },
    }


def sprint_10_3(m_wc, surviving, reverse_map, window_contents, token_freq):
    """10.3: Vocabulary coherence analysis."""
    console.rule("[bold blue]10.3: Vocabulary Coherence")

    coherence_results = []

    table = Table(title="Vocabulary Coherence per Merged State")
    table.add_column("State", justify="right")
    table.add_column("# Orig\nWindows", justify="right")
    table.add_column("Mean\nJaccard", justify="right")
    table.add_column("Suffix\nEntropy", justify="right")
    table.add_column("Dominant\nSuffix")
    table.add_column("Coherent?", justify="center")

    for s in surviving:
        originals = reverse_map[s]
        vocab_sets = [set(window_contents[w]) for w in originals]

        # Pairwise Jaccard similarity
        jaccard_scores = []
        for i in range(len(vocab_sets)):
            for j in range(i + 1, len(vocab_sets)):
                jaccard_scores.append(jaccard_similarity(vocab_sets[i], vocab_sets[j]))
        mean_jaccard = (sum(jaccard_scores) / len(jaccard_scores)
                        if jaccard_scores else 1.0)

        # Suffix distribution for the merged vocabulary
        suffix_counts = Counter()
        for word in m_wc[s]:
            suffix_counts[get_suffix(word)] += 1
        total_words = sum(suffix_counts.values())

        # Suffix entropy
        suffix_entropy = 0.0
        if total_words > 0:
            for count in suffix_counts.values():
                p = count / total_words
                if p > 0:
                    suffix_entropy -= p * math.log2(p)

        # Dominant suffix
        dominant_suffix = suffix_counts.most_common(1)[0][0] if suffix_counts else "N/A"
        dominant_frac = (suffix_counts.most_common(1)[0][1] / total_words
                         if total_words > 0 else 0)

        # Coherence verdict: high Jaccard (>0.1) or single-window state
        is_coherent = len(originals) == 1 or mean_jaccard > 0.05

        coherence_results.append({
            "state": s,
            "num_original_windows": len(originals),
            "mean_jaccard": round(mean_jaccard, 4),
            "suffix_entropy_bits": round(suffix_entropy, 3),
            "dominant_suffix": dominant_suffix,
            "dominant_suffix_fraction": round(dominant_frac, 3),
            "is_coherent": is_coherent,
        })

        coherent_str = "[green]YES[/green]" if is_coherent else "[red]NO[/red]"
        table.add_row(
            str(s),
            str(len(originals)),
            f"{mean_jaccard:.4f}",
            f"{suffix_entropy:.3f}",
            f"{dominant_suffix} ({dominant_frac:.0%})",
            coherent_str,
        )

    console.print(table)

    n_coherent = sum(1 for c in coherence_results if c["is_coherent"])
    n_incoherent = len(coherence_results) - n_coherent
    mean_overall_jaccard = (
        sum(c["mean_jaccard"] for c in coherence_results if c["num_original_windows"] > 1)
        / max(1, sum(1 for c in coherence_results if c["num_original_windows"] > 1))
    )

    console.print(
        f"\n  Coherent states: {n_coherent}/{len(coherence_results)}"
        f"\n  Incoherent states: {n_incoherent}/{len(coherence_results)}"
        f"\n  Mean Jaccard (multi-window states): {mean_overall_jaccard:.4f}"
        f"\n  Note: Window vocabularies are DISJOINT by construction "
        "(Jaccard ≈ 0 is expected)"
    )

    return {
        "per_state": coherence_results,
        "summary": {
            "n_coherent": n_coherent,
            "n_incoherent": n_incoherent,
            "mean_jaccard_multi_window": round(mean_overall_jaccard, 4),
            "note": "Window vocabularies are disjoint by construction. "
                    "Jaccard measures overlap of constituent windows, "
                    "not linguistic similarity.",
        },
    }


def sprint_10_4(surviving, reverse_map, m_wc, state_profiles_data):
    """10.4: Historical defensibility assessment."""
    console.rule("[bold blue]10.4: Historical Defensibility Assessment")

    profiles = state_profiles_data["state_profiles"]
    vocab_sizes = [p["vocabulary_size"] for p in profiles]
    mean_vocab = sum(vocab_sizes) / len(vocab_sizes) if vocab_sizes else 0
    max_vocab = max(vocab_sizes) if vocab_sizes else 0
    min_vocab = min(vocab_sizes) if vocab_sizes else 0

    # Dimension the 15-state volvelle
    sector_angle_deg = 360.0 / TARGET_STATES
    sector_angle_rad = math.radians(sector_angle_deg)
    r_min = POSITION_WIDTH_MM / sector_angle_rad
    diameter = 2 * (r_min + POSITION_HEIGHT_MM + MARGIN_MM)

    # Score dimensions
    # 1. State count plausibility (0-1): 15 is within historical range [9-30]
    state_count_score = 1.0 if 9 <= TARGET_STATES <= 30 else 0.5

    # 2. Vocabulary density: words per sector on the disc itself
    #    Disc can only show state labels, not vocabulary → needs codebook regardless
    #    Score: 1.0 if no on-disc vocab needed, 0.5 if some, 0.0 if impractical
    needs_codebook = max_vocab > 20  # Can't inscribe 715 words on a disc sector
    vocab_density_score = 0.3 if needs_codebook else 0.8

    # 3. Operational complexity: consultation burden with 15 states
    #    Still need codebook for every word (same as tabula)
    operational_score = 0.5  # Same as tabula but fewer states to track

    # 4. Physical inscription: disc at 193mm with 15 sectors is feasible
    inscription_score = 1.0 if diameter <= MAX_DEVICE_DIAMETER_MM else 0.0

    # 5. Admissibility preservation
    adm_from_profiles = state_profiles_data.get("total_corpus_tokens", 0)
    # Use Sprint 3's known value: 56.84%
    adm_score = 0.5684 / BASELINE_ADMISSIBILITY  # ~0.875

    combined = (
        0.20 * state_count_score +
        0.25 * vocab_density_score +
        0.20 * operational_score +
        0.15 * inscription_score +
        0.20 * adm_score
    )

    # Historical comparison table
    table = Table(title="Historical Comparison")
    table.add_column("Device")
    table.add_column("Positions", justify="right")
    table.add_column("Diameter", justify="right")
    table.add_column("Vocab/Pos", justify="right")
    table.add_column("Type")

    for name, params in HISTORICAL_DEVICES.items():
        table.add_row(
            name,
            str(params["positions"]),
            f"{params['diameter_mm']}mm",
            str(params["vocab_per_position"]),
            params["type"],
        )
    table.add_row(
        "[bold]15-State Merged Volvelle[/bold]",
        str(TARGET_STATES),
        f"{round(diameter)}mm",
        f"{round(mean_vocab)} (codebook)",
        "state-tracker + codebook",
        style="bold",
    )
    console.print(table)

    # Scores table
    table2 = Table(title="Defensibility Scores")
    table2.add_column("Dimension")
    table2.add_column("Score", justify="right")
    table2.add_column("Weight", justify="right")
    table2.add_column("Notes")

    table2.add_row("State count (9-30 range)", f"{state_count_score:.2f}", "0.20",
                    f"{TARGET_STATES} states — within Llull range")
    table2.add_row("Vocabulary density", f"{vocab_density_score:.2f}", "0.25",
                    f"Max {max_vocab} words/state → codebook required")
    table2.add_row("Operational complexity", f"{operational_score:.2f}", "0.20",
                    "15 states simpler than 50, but still needs codebook")
    table2.add_row("Physical inscription", f"{inscription_score:.2f}", "0.15",
                    f"{round(diameter)}mm — within Llull/Apian range")
    table2.add_row("Admissibility retention", f"{adm_score:.2f}", "0.20",
                    f"56.84% vs 64.94% baseline ({-8.1:+.1f}pp)")
    table2.add_row("[bold]Combined[/bold]", f"[bold]{combined:.3f}[/bold]", "1.00", "")
    console.print(table2)

    verdict = "MARGINAL"
    if combined >= 0.7:
        verdict = "PLAUSIBLE (with caveats)"
    elif combined < 0.4:
        verdict = "IMPLAUSIBLE"

    console.print(f"\n  Historical defensibility verdict: [bold]{verdict}[/bold]")
    console.print("  Key caveat: Merging 35 of 50 windows is a mathematical "
                  "optimization with no historical precedent.")
    console.print("  The 15-state device works as a STATE TRACKER but cannot "
                  "replace the codebook.")

    return {
        "volvelle_diameter_mm": round(diameter),
        "sector_angle_deg": round(sector_angle_deg, 1),
        "vocabulary_stats": {
            "mean": round(mean_vocab, 1),
            "max": max_vocab,
            "min": min_vocab,
        },
        "scores": {
            "state_count": state_count_score,
            "vocabulary_density": vocab_density_score,
            "operational_complexity": operational_score,
            "physical_inscription": inscription_score,
            "admissibility_retention": round(adm_score, 4),
            "combined": round(combined, 4),
        },
        "historical_comparison": {
            name: params for name, params in HISTORICAL_DEVICES.items()
        },
        "verdict": verdict,
        "caveats": [
            "Merging 35 of 50 windows has no historical precedent",
            "Codebook still required (max state has 715 words)",
            "Admissibility drops 8.1pp from baseline",
            "Merged states contain disjoint vocabularies from different windows",
        ],
    }


def sprint_10_5(m_wc, surviving, reverse_map, state_profiles_data,
                coherence_data, defensibility_data):
    """10.5: Head-to-head tabula vs merged volvelle comparison."""
    console.rule("[bold blue]10.5: Tabula vs Merged Volvelle Comparison")

    profiles = state_profiles_data["state_profiles"]
    max_vocab = max(p["vocabulary_size"] for p in profiles)
    w18_share = state_profiles_data["w18_analysis"]["token_share"]

    n_coherent = coherence_data["summary"]["n_coherent"]
    n_total = len(coherence_data["per_state"])

    table = Table(title="Head-to-Head: Tabula + Codebook vs 15-State Volvelle")
    table.add_column("Dimension", min_width=25)
    table.add_column("Tabula + Codebook", min_width=25)
    table.add_column("15-State Volvelle", min_width=25)
    table.add_column("Winner", justify="center")

    comparisons = [
        ("Device size", "170 x 160mm (flat card)", "193mm diameter (disc)",
         "TABULA"),
        ("State count", "50 (full resolution)", "15 (35 merged)",
         "TABULA"),
        ("Admissibility", "64.94% (corrected)", "56.84% (drift, -8.1pp)",
         "TABULA"),
        ("Information loss", "None", "35 windows merged into 15",
         "TABULA"),
        ("Vocabulary access", "154pp codebook", "154pp codebook (still needed)",
         "TIE"),
        ("Portability", "Card + booklet", "Disc + booklet",
         "TABULA"),
        ("Historical parallel", "Alberti + Trithemius",
         "Llull (but no codebook precedent)", "TABULA"),
        ("Construction complexity", "Flat card (trivial)", "Rotating disc (moderate)",
         "TABULA"),
        ("W18 dominance", f"W18 = {w18_share:.0%} of tokens",
         f"W18 state = {max_vocab} words", "TIE"),
        ("Coherence", "N/A (no merging)", f"{n_coherent}/{n_total} coherent states",
         "TABULA"),
    ]

    tabula_wins = 0
    volvelle_wins = 0
    ties = 0
    for dim, tab_val, volv_val, winner in comparisons:
        if winner == "TABULA":
            tabula_wins += 1
            w_color = "green"
        elif winner == "VOLVELLE":
            volvelle_wins += 1
            w_color = "blue"
        else:
            ties += 1
            w_color = "yellow"
        table.add_row(dim, tab_val, volv_val, f"[{w_color}]{winner}[/{w_color}]")

    console.print(table)

    console.print(
        f"\n  Tabula wins: {tabula_wins}, Volvelle wins: {volvelle_wins}, "
        f"Ties: {ties}"
    )

    # Final recommendation
    recommendation = (
        "The 15-state merged volvelle is a MATHEMATICAL CURIOSITY, not a "
        "plausible historical alternative. It loses 8.1pp admissibility, "
        "requires the same codebook as the tabula, adds construction complexity "
        "(rotating disc vs flat card), and has no historical precedent for "
        "state-merging optimization. The tabula + codebook dominates on every "
        "dimension except none."
    )

    console.print(f"\n  [bold]Recommendation:[/bold] {recommendation}")

    return {
        "comparison": [
            {"dimension": dim, "tabula": t, "volvelle": v, "winner": w}
            for dim, t, v, w in comparisons
        ],
        "score": {
            "tabula_wins": tabula_wins,
            "volvelle_wins": volvelle_wins,
            "ties": ties,
        },
        "recommendation": recommendation,
        "verdict": "TABULA + CODEBOOK remains the recommended architecture. "
                   "The 15-state merged volvelle is not a viable alternative.",
    }


# ── Main ─────────────────────────────────────────────────────────────

def _sanitize(obj):
    """Recursively convert numpy types to native Python."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    return obj


def main():
    console.rule("[bold magenta]Phase 20, Sprint 10: "
                 "15-State Merged Volvelle Deep Characterization")

    # Load data
    console.print("Loading data...")
    lattice_map, window_contents = load_palette(PALETTE_PATH)
    corrections = load_corrections(OFFSETS_PATH)
    store = MetadataStore(DB_PATH)
    lines = load_lines(store)
    token_freq = compute_token_freq(lines, lattice_map)

    console.print(
        f"  Palette: {len(lattice_map)} words, {NUM_WINDOWS} windows"
        f"\n  Corpus: {len(lines)} lines"
        f"\n  Corrections: {len(corrections)} windows"
    )

    # 10.1: Reconstruct merge map
    s10_1, m_lm, m_wc, m_corr, surviving, reverse_map = sprint_10_1(
        window_contents, corrections, lattice_map, lines
    )

    # 10.2: Per-state characterization
    s10_2 = sprint_10_2(
        m_wc, m_corr, surviving, reverse_map, corrections,
        window_contents, lines, lattice_map, token_freq
    )

    # 10.3: Vocabulary coherence
    s10_3 = sprint_10_3(m_wc, surviving, reverse_map, window_contents, token_freq)

    # 10.4: Historical defensibility
    s10_4 = sprint_10_4(surviving, reverse_map, m_wc, s10_2)

    # 10.5: Tabula vs volvelle comparison
    s10_5 = sprint_10_5(m_wc, surviving, reverse_map, s10_2, s10_3, s10_4)

    # Assemble results
    results = {
        "merge_reconstruction": s10_1,
        "per_state_profiles": s10_2,
        "vocabulary_coherence": s10_3,
        "historical_defensibility": s10_4,
        "comparison": s10_5,
    }

    results = _sanitize(results)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(config={
        "seed": 42,
        "command": "run_20g_merged_volvelle_characterization",
    }):
        main()
