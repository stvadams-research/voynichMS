#!/usr/bin/env python3
"""Phase 20, Sprint 6: Manuscript Layout vs Codebook Structure.

6.1: Per-folio window usage profiles (dominant window, entropy)
6.2: Folio clustering by window profile (within- vs between-section similarity)
6.3: Window ordering vs folio sequence (Spearman rank correlation)

Tests whether the manuscript's internal structure shows codebook-like
organization — i.e., whether folios cluster by window usage.
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
from scipy import stats

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
DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OUTPUT_PATH = project_root / "results/data/phase20_state_machine/layout_analysis.json"

SECTIONS = {
    "Herbal A": (1, 57),
    "Herbal B": (58, 66),
    "Astro": (67, 74),
    "Biological": (75, 84),
    "Cosmo": (85, 86),
    "Pharma": (87, 102),
    "Stars": (103, 116),
}


# ── Helpers ───────────────────────────────────────────────────────────

def load_palette(path):
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    lm_key = ("reordered_lattice_map" if "reordered_lattice_map" in results
              else "lattice_map")
    return results[lm_key]


def extract_folio_num(page_id):
    """Extract folio number from page ID like 'f1r', 'f2v', 'f85v2'."""
    m = re.match(r"f(\d+)", page_id)
    return int(m.group(1)) if m else None


def get_section(folio_num):
    for name, (lo, hi) in SECTIONS.items():
        if lo <= folio_num <= hi:
            return name
    return "Other"


def load_folio_lines(store, lattice_map):
    """Load corpus tokens grouped by folio, with window assignments."""
    session = store.Session()
    try:
        rows = (
            session.query(
                TranscriptionTokenRecord.content,
                PageRecord.id,
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

        # Group tokens by folio
        folio_tokens = defaultdict(list)
        for content, page_id in rows:
            clean = sanitize_token(content)
            if not clean:
                continue
            folio_num = extract_folio_num(page_id)
            if folio_num is None:
                continue
            w = lattice_map.get(clean)
            if w is not None:
                folio_tokens[folio_num].append((clean, int(w)))

        return dict(folio_tokens)
    finally:
        session.close()


def cosine_similarity(v1, v2):
    """Cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    n1 = math.sqrt(sum(a * a for a in v1))
    n2 = math.sqrt(sum(b * b for b in v2))
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot / (n1 * n2)


def shannon_entropy(counts):
    """Shannon entropy of a count distribution."""
    total = sum(counts)
    if total == 0:
        return 0.0
    probs = [c / total for c in counts if c > 0]
    return -sum(p * math.log2(p) for p in probs)


# ── Sprint Functions ─────────────────────────────────────────────────

def sprint_6_1(folio_tokens):
    """6.1: Per-folio window usage profiles."""
    console.rule("[bold blue]6.1: Per-Folio Window Usage Profiles")

    folio_profiles = {}
    for folio_num in sorted(folio_tokens.keys()):
        tokens = folio_tokens[folio_num]
        window_counts = Counter(w for _, w in tokens)

        # Build vector (length NUM_WINDOWS)
        vec = [window_counts.get(i, 0) for i in range(NUM_WINDOWS)]
        dominant = max(window_counts, key=window_counts.get) if window_counts else -1
        entropy = shannon_entropy(list(window_counts.values()))
        n_windows_used = len(window_counts)

        folio_profiles[folio_num] = {
            "token_count": len(tokens),
            "n_windows_used": n_windows_used,
            "dominant_window": dominant,
            "dominant_fraction": (window_counts[dominant] / len(tokens)
                                 if tokens else 0),
            "entropy": round(entropy, 3),
            "vector": vec,
            "section": get_section(folio_num),
        }

    # Display summary table (top 15 by token count)
    table = Table(title="Folio Window Profiles (top 15 by tokens)")
    table.add_column("Folio", justify="right")
    table.add_column("Section")
    table.add_column("Tokens", justify="right")
    table.add_column("Windows", justify="right")
    table.add_column("Dominant", justify="right")
    table.add_column("Dom %", justify="right")
    table.add_column("Entropy", justify="right")

    sorted_folios = sorted(folio_profiles.items(),
                           key=lambda x: x[1]["token_count"], reverse=True)
    for folio_num, p in sorted_folios[:15]:
        table.add_row(
            f"f{folio_num}",
            p["section"],
            str(p["token_count"]),
            str(p["n_windows_used"]),
            str(p["dominant_window"]),
            f"{p['dominant_fraction']:.1%}",
            f"{p['entropy']:.2f}",
        )
    console.print(table)

    # Summary stats
    entropies = [p["entropy"] for p in folio_profiles.values()]
    dom_fracs = [p["dominant_fraction"] for p in folio_profiles.values()]
    console.print(f"\n  Folios analyzed: {len(folio_profiles)}")
    console.print(f"  Mean entropy: {np.mean(entropies):.3f} "
                  f"(range {min(entropies):.3f}–{max(entropies):.3f})")
    console.print(f"  Mean dominant fraction: {np.mean(dom_fracs):.3f}")

    # Check: how many folios have W18 as dominant?
    w18_dominant = sum(1 for p in folio_profiles.values()
                       if p["dominant_window"] == 18)
    console.print(f"  Folios with W18 dominant: {w18_dominant}/{len(folio_profiles)}")

    return folio_profiles


def sprint_6_2(folio_profiles):
    """6.2: Folio clustering by window profile."""
    console.rule("[bold blue]6.2: Folio Clustering by Window Profile")

    # Group folios by section
    section_folios = defaultdict(list)
    for folio_num, p in folio_profiles.items():
        section_folios[p["section"]].append(folio_num)

    # Compute all pairwise cosine similarities
    folio_list = sorted(folio_profiles.keys())
    vectors = {f: folio_profiles[f]["vector"] for f in folio_list}

    within_sims = []
    between_sims = []

    for i, f1 in enumerate(folio_list):
        for f2 in folio_list[i + 1:]:
            sim = cosine_similarity(vectors[f1], vectors[f2])
            if folio_profiles[f1]["section"] == folio_profiles[f2]["section"]:
                within_sims.append(sim)
            else:
                between_sims.append(sim)

    within_mean = np.mean(within_sims) if within_sims else 0
    between_mean = np.mean(between_sims) if between_sims else 0

    # Mann-Whitney U test
    if within_sims and between_sims:
        u_stat, p_value = stats.mannwhitneyu(
            within_sims, between_sims, alternative="greater")
    else:
        u_stat, p_value = 0.0, 1.0

    console.print(f"  Within-section similarity: {within_mean:.4f} "
                  f"(n={len(within_sims)})")
    console.print(f"  Between-section similarity: {between_mean:.4f} "
                  f"(n={len(between_sims)})")
    console.print(f"  Difference: {within_mean - between_mean:+.4f}")
    console.print(f"  Mann-Whitney U: {u_stat:.0f}, p={p_value:.2e}")

    if p_value < 0.001:
        verdict = "SIGNIFICANT"
        console.print(f"  [green]Verdict: {verdict} — sections have distinct "
                      "window profiles[/green]")
    elif p_value < 0.05:
        verdict = "MARGINAL"
        console.print(f"  [yellow]Verdict: {verdict}[/yellow]")
    else:
        verdict = "NOT SIGNIFICANT"
        console.print(f"  [red]Verdict: {verdict} — no codebook-like "
                      "clustering by section[/red]")

    # Per-section mean within similarity
    table = Table(title="Per-Section Window Profile Coherence")
    table.add_column("Section")
    table.add_column("Folios", justify="right")
    table.add_column("Mean Within-Sim", justify="right")

    for section_name in SECTIONS:
        folios = section_folios.get(section_name, [])
        if len(folios) < 2:
            table.add_row(section_name, str(len(folios)), "—")
            continue
        sims = []
        for i, f1 in enumerate(folios):
            for f2 in folios[i + 1:]:
                sims.append(cosine_similarity(vectors[f1], vectors[f2]))
        table.add_row(section_name, str(len(folios)),
                      f"{np.mean(sims):.4f}" if sims else "—")
    console.print(table)

    return {
        "within_section_mean": round(float(within_mean), 4),
        "between_section_mean": round(float(between_mean), 4),
        "difference": round(float(within_mean - between_mean), 4),
        "mann_whitney_u": round(float(u_stat)),
        "p_value": float(p_value),
        "verdict": verdict,
        "n_within_pairs": len(within_sims),
        "n_between_pairs": len(between_sims),
    }


def sprint_6_3(folio_tokens):
    """6.3: Window ordering vs folio sequence."""
    console.rule("[bold blue]6.3: Window Ordering vs Folio Sequence")

    # For each token, record (folio_num, window_id)
    folio_window_pairs = []
    for folio_num in sorted(folio_tokens.keys()):
        for _, w in folio_tokens[folio_num]:
            folio_window_pairs.append((folio_num, w))

    if len(folio_window_pairs) < 10:
        console.print("  [red]Insufficient data[/red]")
        return {"spearman_r": 0.0, "p_value": 1.0, "n_tokens": 0}

    folio_vals = [p[0] for p in folio_window_pairs]
    window_vals = [p[1] for p in folio_window_pairs]

    rho, p_value = stats.spearmanr(folio_vals, window_vals)

    console.print(f"  Tokens analyzed: {len(folio_window_pairs)}")
    console.print(f"  Spearman ρ: {rho:.4f}")
    console.print(f"  p-value: {p_value:.2e}")

    if abs(rho) < 0.1:
        verdict = "NO CORRELATION"
        console.print(f"  [green]Verdict: {verdict} — window order is "
                      "independent of folio order[/green]")
    elif abs(rho) < 0.3:
        verdict = "WEAK CORRELATION"
        console.print(f"  [yellow]Verdict: {verdict}[/yellow]")
    else:
        verdict = "MODERATE+ CORRELATION"
        console.print(f"  [red]Verdict: {verdict} — manuscript layout "
                      "partially mirrors device traversal[/red]")

    # Per-section correlation
    table = Table(title="Per-Section Folio-Window Correlation")
    table.add_column("Section")
    table.add_column("Tokens", justify="right")
    table.add_column("Spearman ρ", justify="right")
    table.add_column("p-value", justify="right")

    section_corrs = {}
    for section_name, (lo, hi) in SECTIONS.items():
        pairs = [(f, w) for f, w in folio_window_pairs if lo <= f <= hi]
        if len(pairs) < 10:
            table.add_row(section_name, str(len(pairs)), "—", "—")
            continue
        fs = [p[0] for p in pairs]
        ws = [p[1] for p in pairs]
        sr, sp = stats.spearmanr(fs, ws)
        section_corrs[section_name] = {"rho": round(float(sr), 4),
                                       "p_value": float(sp),
                                       "n": len(pairs)}
        table.add_row(section_name, str(len(pairs)),
                      f"{sr:.4f}", f"{sp:.2e}")
    console.print(table)

    return {
        "spearman_r": round(float(rho), 4),
        "p_value": float(p_value),
        "n_tokens": len(folio_window_pairs),
        "verdict": verdict,
        "per_section": section_corrs,
    }


# ── Main ──────────────────────────────────────────────────────────────

def main():
    console.rule("[bold magenta]Phase 20, Sprint 6: Manuscript Layout vs "
                 "Codebook Structure")

    console.print("Loading data...")
    lattice_map = load_palette(PALETTE_PATH)
    store = MetadataStore(DB_PATH)
    folio_tokens = load_folio_lines(store, lattice_map)
    console.print(f"  Folios: {len(folio_tokens)}")
    console.print(f"  Total tokens: {sum(len(t) for t in folio_tokens.values())}")

    # 6.1
    folio_profiles = sprint_6_1(folio_tokens)

    # 6.2
    clustering = sprint_6_2(folio_profiles)

    # 6.3
    correlation = sprint_6_3(folio_tokens)

    # Assemble results (strip vectors from profiles for JSON size)
    profile_summary = {}
    for f, p in folio_profiles.items():
        profile_summary[str(f)] = {k: v for k, v in p.items() if k != "vector"}

    results = {
        "folio_profiles": profile_summary,
        "clustering": clustering,
        "folio_window_correlation": correlation,
        "summary": {
            "n_folios": len(folio_profiles),
            "codebook_like_organization": clustering["verdict"] == "SIGNIFICANT",
            "layout_mirrors_device": abs(correlation["spearman_r"]) >= 0.3,
        },
    }

    # Sanitize
    def _sanitize(obj):
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

    results = _sanitize(results)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_20d_layout_analysis"}):
        main()
