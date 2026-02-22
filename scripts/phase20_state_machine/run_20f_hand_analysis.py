#!/usr/bin/env python3
"""Phase 20, Sprint 8: Scribal Hand × Device Correspondence.

8.1: Per-hand window usage profiles (token count, entropy, top windows)
8.2: Hand-specific consultation patterns (shared vs hand-specific vocabulary)
8.3: Hand-specific drift admissibility
8.4: Hand × device interaction synthesis

Tests whether the two scribal hands use the production device differently,
or whether differences are limited to suffix preferences.
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
OFFSETS_PATH = project_root / "results/data/phase14_machine/canonical_offsets.json"
OUTPUT_PATH = project_root / "results/data/phase20_state_machine/hand_analysis.json"

WORDS_PER_PAGE = 60  # codebook capacity (from Sprint 1)

# Scribal hand boundaries (Currier/D'Imperio consensus)
HAND_RANGES = {
    "Hand 1": [(1, 66)],
    "Hand 2": [(75, 84), (103, 116)],
}

# Stylometry profiles from Phase 14 high_fidelity_emulator
EMULATOR_PROFILES = {
    "Hand 1": {"drift": 15, "suffix_weights": {"dy": 12.0, "in": 4.0, "y": 8.0, "m": 3.0}},
    "Hand 2": {"drift": 25, "suffix_weights": {"in": 20.0, "dy": 2.0, "m": 10.0, "y": 5.0}},
}


# ── Helpers ───────────────────────────────────────────────────────────

def load_palette(path):
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    lm_key = ("reordered_lattice_map" if "reordered_lattice_map" in results
              else "lattice_map")
    return results[lm_key]


def load_corrections(path):
    with open(path) as f:
        data = json.load(f)
    results = data.get("results", data)
    return {int(k): v for k, v in results["corrections"].items()}


def extract_folio_num(page_id):
    m = re.match(r"f(\d+)", page_id)
    return int(m.group(1)) if m else None


def get_hand(folio_num):
    for hand, ranges in HAND_RANGES.items():
        for lo, hi in ranges:
            if lo <= folio_num <= hi:
                return hand
    return "Unknown"


def load_corpus_by_hand(store, lattice_map):
    """Load corpus tokens grouped by scribal hand."""
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

        hand_tokens = defaultdict(list)  # hand → [(token, window)]
        for content, page_id in rows:
            clean = sanitize_token(content)
            if not clean:
                continue
            folio_num = extract_folio_num(page_id)
            if folio_num is None:
                continue
            w = lattice_map.get(clean)
            if w is None:
                continue
            hand = get_hand(folio_num)
            hand_tokens[hand].append((clean, int(w)))

        return dict(hand_tokens)
    finally:
        session.close()


def shannon_entropy(counts):
    total = sum(counts)
    if total == 0:
        return 0.0
    probs = [c / total for c in counts if c > 0]
    return -sum(p * math.log2(p) for p in probs)


# ── Sprint Functions ─────────────────────────────────────────────────

def sprint_8_1(hand_tokens):
    """8.1: Per-hand window usage profiles."""
    console.rule("[bold blue]8.1: Per-Hand Window Usage Profiles")

    profiles = {}

    for hand in ["Hand 1", "Hand 2", "Unknown"]:
        tokens = hand_tokens.get(hand, [])
        if not tokens:
            continue

        window_counts = Counter(w for _, w in tokens)
        vocab = set(t for t, _ in tokens)

        # Window usage vector
        vec = [window_counts.get(i, 0) for i in range(NUM_WINDOWS)]
        entropy = shannon_entropy(list(window_counts.values()))
        n_windows_used = len(window_counts)

        # Top 10 windows
        top_windows = window_counts.most_common(10)

        profiles[hand] = {
            "token_count": len(tokens),
            "vocab_size": len(vocab),
            "n_windows_used": n_windows_used,
            "window_entropy": round(entropy, 3),
            "top_10_windows": [
                {"window": w, "tokens": c, "fraction": round(c / len(tokens), 4)}
                for w, c in top_windows
            ],
            "vector": vec,
        }

    # Display
    table = Table(title="Per-Hand Window Usage Profiles")
    table.add_column("Hand")
    table.add_column("Tokens", justify="right")
    table.add_column("Vocab", justify="right")
    table.add_column("Windows", justify="right")
    table.add_column("Entropy", justify="right")
    table.add_column("W18 %", justify="right")
    table.add_column("Top-3 Windows")

    for hand in ["Hand 1", "Hand 2", "Unknown"]:
        p = profiles.get(hand)
        if not p:
            continue
        w18_frac = p["vector"][18] / p["token_count"] if p["token_count"] else 0
        top3 = ", ".join(f"W{tw['window']}({tw['fraction']:.0%})"
                         for tw in p["top_10_windows"][:3])
        table.add_row(
            hand,
            str(p["token_count"]),
            str(p["vocab_size"]),
            str(p["n_windows_used"]),
            f"{p['window_entropy']:.2f}",
            f"{w18_frac:.1%}",
            top3,
        )
    console.print(table)

    # Statistical comparison: Hand 1 vs Hand 2 window distributions
    if "Hand 1" in profiles and "Hand 2" in profiles:
        v1 = profiles["Hand 1"]["vector"]
        v2 = profiles["Hand 2"]["vector"]
        # Normalize to proportions
        t1 = sum(v1)
        t2 = sum(v2)
        p1 = [c / t1 for c in v1]
        p2 = [c / t2 for c in v2]

        # Jensen-Shannon divergence
        m = [(a + b) / 2 for a, b in zip(p1, p2)]
        kl_1m = sum(a * math.log2(a / b) for a, b in zip(p1, m)
                    if a > 0 and b > 0)
        kl_2m = sum(a * math.log2(a / b) for a, b in zip(p2, m)
                    if a > 0 and b > 0)
        jsd = (kl_1m + kl_2m) / 2

        # Cosine similarity
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = math.sqrt(sum(a * a for a in v1))
        n2 = math.sqrt(sum(b * b for b in v2))
        cosine = dot / (n1 * n2) if n1 > 0 and n2 > 0 else 0

        console.print("\n  Hand 1 vs Hand 2:")
        console.print(f"    Jensen-Shannon divergence: {jsd:.4f}")
        console.print(f"    Cosine similarity: {cosine:.4f}")

        if jsd < 0.01:
            verdict = "IDENTICAL"
        elif jsd < 0.05:
            verdict = "SIMILAR"
        else:
            verdict = "DISTINCT"
        console.print(f"    Verdict: {verdict}")

        profiles["comparison"] = {
            "jsd": round(jsd, 4),
            "cosine_similarity": round(cosine, 4),
            "verdict": verdict,
        }

    return profiles


def sprint_8_2(hand_tokens):
    """8.2: Hand-specific consultation patterns."""
    console.rule("[bold blue]8.2: Hand-Specific Consultation Patterns")

    hand_vocabs = {}
    for hand in ["Hand 1", "Hand 2"]:
        tokens = hand_tokens.get(hand, [])
        hand_vocabs[hand] = set(t for t, _ in tokens)

    if not all(hand_vocabs.values()):
        console.print("  [red]Insufficient data for both hands[/red]")
        return {}

    v1 = hand_vocabs["Hand 1"]
    v2 = hand_vocabs["Hand 2"]
    shared = v1 & v2
    only_h1 = v1 - v2
    only_h2 = v2 - v1

    console.print(f"  Hand 1 vocabulary: {len(v1)} words")
    console.print(f"  Hand 2 vocabulary: {len(v2)} words")
    console.print(f"  Shared vocabulary: {len(shared)} words "
                  f"({len(shared) / len(v1 | v2):.1%} of union)")
    console.print(f"  Hand 1 only: {len(only_h1)} words")
    console.print(f"  Hand 2 only: {len(only_h2)} words")

    # Token coverage from shared vocabulary
    for hand in ["Hand 1", "Hand 2"]:
        tokens = hand_tokens[hand]
        shared_tokens = sum(1 for t, _ in tokens if t in shared)
        console.print(f"  {hand}: {shared_tokens / len(tokens):.1%} of tokens "
                      f"from shared vocabulary")

    # Per-hand codebook pages
    for hand in ["Hand 1", "Hand 2"]:
        vocab_size = len(hand_vocabs[hand])
        pages = math.ceil(vocab_size / WORDS_PER_PAGE)
        console.print(f"  {hand} codebook: {vocab_size} words → {pages} pages")

    # Shared codebook pages
    shared_pages = math.ceil(len(shared) / WORDS_PER_PAGE)
    console.print(f"  Shared codebook: {len(shared)} words → {shared_pages} pages")

    # Window-specific overlap
    h1_window_vocab = defaultdict(set)
    h2_window_vocab = defaultdict(set)
    for t, w in hand_tokens.get("Hand 1", []):
        h1_window_vocab[w].add(t)
    for t, w in hand_tokens.get("Hand 2", []):
        h2_window_vocab[w].add(t)

    window_overlaps = {}
    for w in range(NUM_WINDOWS):
        wv1 = h1_window_vocab[w]
        wv2 = h2_window_vocab[w]
        if not wv1 and not wv2:
            continue
        union = wv1 | wv2
        inter = wv1 & wv2
        jaccard = len(inter) / len(union) if union else 0
        window_overlaps[w] = {
            "hand1_words": len(wv1),
            "hand2_words": len(wv2),
            "shared": len(inter),
            "jaccard": round(jaccard, 3),
        }

    # Display top windows by divergence
    table = Table(title="Per-Window Vocabulary Overlap (Top 10 by size)")
    table.add_column("Window", justify="right")
    table.add_column("Hand 1", justify="right")
    table.add_column("Hand 2", justify="right")
    table.add_column("Shared", justify="right")
    table.add_column("Jaccard", justify="right")

    sorted_wo = sorted(window_overlaps.items(),
                       key=lambda x: x[1]["hand1_words"] + x[1]["hand2_words"],
                       reverse=True)
    for w, wo in sorted_wo[:10]:
        table.add_row(
            f"W{w}",
            str(wo["hand1_words"]),
            str(wo["hand2_words"]),
            str(wo["shared"]),
            f"{wo['jaccard']:.3f}",
        )
    console.print(table)

    # Mean Jaccard across active windows
    active_jaccards = [wo["jaccard"] for wo in window_overlaps.values()
                       if wo["hand1_words"] > 0 and wo["hand2_words"] > 0]
    mean_jaccard = np.mean(active_jaccards) if active_jaccards else 0

    console.print(f"\n  Mean Jaccard (active windows): {mean_jaccard:.3f}")

    return {
        "hand1_vocab": len(v1),
        "hand2_vocab": len(v2),
        "shared_vocab": len(shared),
        "union_vocab": len(v1 | v2),
        "shared_fraction": round(len(shared) / len(v1 | v2), 4),
        "hand1_only": len(only_h1),
        "hand2_only": len(only_h2),
        "hand1_shared_token_coverage": round(
            sum(1 for t, _ in hand_tokens["Hand 1"] if t in shared)
            / len(hand_tokens["Hand 1"]), 4),
        "hand2_shared_token_coverage": round(
            sum(1 for t, _ in hand_tokens["Hand 2"] if t in shared)
            / len(hand_tokens["Hand 2"]), 4),
        "hand1_codebook_pages": math.ceil(len(v1) / WORDS_PER_PAGE),
        "hand2_codebook_pages": math.ceil(len(v2) / WORDS_PER_PAGE),
        "shared_codebook_pages": shared_pages,
        "mean_window_jaccard": round(float(mean_jaccard), 3),
        "per_window_overlap": {
            str(w): wo for w, wo in sorted(window_overlaps.items())
        },
    }


def sprint_8_3(hand_tokens, corrections, lattice_map):
    """8.3: Hand-specific drift admissibility."""
    console.rule("[bold blue]8.3: Hand-Specific Drift Admissibility")

    results = {}

    for hand in ["Hand 1", "Hand 2"]:
        tokens = hand_tokens.get(hand, [])
        if len(tokens) < 2:
            continue

        # Build bigram transitions
        admissible = 0
        total = 0

        for i in range(len(tokens) - 1):
            _, w_curr = tokens[i]
            _, w_next = tokens[i + 1]

            # Corrected next window
            corr = corrections.get(w_curr, 0)
            expected = (w_curr + 1 + corr) % NUM_WINDOWS

            # ±1 drift band
            neighbors = {
                expected,
                (expected - 1) % NUM_WINDOWS,
                (expected + 1) % NUM_WINDOWS,
            }

            if w_next in neighbors:
                admissible += 1
            total += 1

        rate = admissible / total if total else 0

        results[hand] = {
            "transitions": total,
            "admissible": admissible,
            "rate": round(rate, 4),
        }

        console.print(f"  {hand}: {admissible}/{total} admissible "
                      f"({rate:.1%})")

    # Compare rates
    if "Hand 1" in results and "Hand 2" in results:
        r1 = results["Hand 1"]["rate"]
        r2 = results["Hand 2"]["rate"]
        diff = r1 - r2

        # Z-test for proportions
        n1 = results["Hand 1"]["transitions"]
        n2 = results["Hand 2"]["transitions"]
        p_pool = ((results["Hand 1"]["admissible"]
                   + results["Hand 2"]["admissible"]) / (n1 + n2))
        se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
        z = diff / se if se > 0 else 0
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))

        console.print(f"\n  Difference (H1 - H2): {diff:+.4f}")
        console.print(f"  Z-statistic: {z:.2f}, p-value: {p_value:.2e}")

        if p_value < 0.001:
            verdict = "SIGNIFICANTLY DIFFERENT"
        elif p_value < 0.05:
            verdict = "MARGINALLY DIFFERENT"
        else:
            verdict = "NOT SIGNIFICANTLY DIFFERENT"
        console.print(f"  Verdict: {verdict}")

        # Compare with emulator drift parameters
        console.print("\n  Emulator drift parameters:")
        for hand in ["Hand 1", "Hand 2"]:
            ep = EMULATOR_PROFILES[hand]
            console.print(f"    {hand}: drift={ep['drift']}, "
                          f"measured admissibility={results[hand]['rate']:.1%}")

        # Correlation check: higher drift parameter → different admissibility?
        console.print(f"\n  Hand 2 has higher drift ({EMULATOR_PROFILES['Hand 2']['drift']} "
                      f"vs {EMULATOR_PROFILES['Hand 1']['drift']})")
        if r2 < r1:
            console.print("  → Higher drift correlates with LOWER admissibility ✓")
        elif r2 > r1:
            console.print("  → Higher drift correlates with HIGHER admissibility")
        else:
            console.print("  → No difference in admissibility")

        results["comparison"] = {
            "difference": round(diff, 4),
            "z_statistic": round(z, 2),
            "p_value": float(p_value),
            "verdict": verdict,
        }

    return results


def sprint_8_4(profiles, consultation, admissibility):
    """8.4: Hand × device interaction synthesis."""
    console.rule("[bold blue]8.4: Hand × Device Interaction Synthesis")

    # Gather evidence
    evidence = []

    # Window profile similarity
    if "comparison" in profiles:
        jsd = profiles["comparison"]["jsd"]
        evidence.append(("Window profile similarity",
                         profiles["comparison"]["verdict"],
                         f"JSD={jsd:.4f}"))

    # Vocabulary overlap
    if consultation:
        shared_frac = consultation.get("shared_fraction", 0)
        evidence.append(("Vocabulary overlap",
                         "HIGH" if shared_frac > 0.5 else "LOW",
                         f"{shared_frac:.1%} shared"))

    # Admissibility difference
    if "comparison" in admissibility:
        evidence.append(("Admissibility difference",
                         admissibility["comparison"]["verdict"],
                         f"Δ={admissibility['comparison']['difference']:+.4f}"))

    # Suffix preferences (from emulator profiles)
    h1_suffixes = EMULATOR_PROFILES["Hand 1"]["suffix_weights"]
    h2_suffixes = EMULATOR_PROFILES["Hand 2"]["suffix_weights"]
    top_h1 = max(h1_suffixes, key=h1_suffixes.get)
    top_h2 = max(h2_suffixes, key=h2_suffixes.get)
    evidence.append(("Top suffix preference",
                     "DIFFERENT" if top_h1 != top_h2 else "SAME",
                     f"H1: -{top_h1}, H2: -{top_h2}"))

    # Display
    table = Table(title="Hand × Device Interaction Evidence")
    table.add_column("Dimension")
    table.add_column("Finding")
    table.add_column("Detail")

    for dim, finding, detail in evidence:
        table.add_row(dim, finding, detail)
    console.print(table)

    # Synthesis verdict
    console.print("\n  [bold]Synthesis:[/bold]")

    # Count dimensions of difference
    different_dims = sum(1 for _, finding, _ in evidence
                         if finding in ("DISTINCT", "LOW",
                                        "SIGNIFICANTLY DIFFERENT",
                                        "DIFFERENT"))

    if different_dims >= 3:
        verdict = "SPECIALIST PROFILES"
        console.print("  The two hands use the device in fundamentally different ways:")
        console.print("  different window focus, different vocabulary, different drift.")
    elif different_dims >= 1:
        verdict = "MINOR VARIATION"
        console.print("  The hands share the same device usage pattern with minor")
        console.print("  differences in suffix preferences and/or drift rate.")
    else:
        verdict = "IDENTICAL USAGE"
        console.print("  Both hands use the device identically — differences are")
        console.print("  limited to handwriting style, not production method.")

    console.print(f"  Verdict: [bold]{verdict}[/bold]")

    return {
        "evidence": [
            {"dimension": dim, "finding": finding, "detail": detail}
            for dim, finding, detail in evidence
        ],
        "different_dimensions": different_dims,
        "verdict": verdict,
    }


# ── Main ──────────────────────────────────────────────────────────────

def main():
    console.rule("[bold magenta]Phase 20, Sprint 8: Scribal Hand × Device "
                 "Correspondence")

    console.print("Loading data...")
    lattice_map = load_palette(PALETTE_PATH)
    corrections = load_corrections(OFFSETS_PATH)
    store = MetadataStore(DB_PATH)
    hand_tokens = load_corpus_by_hand(store, lattice_map)

    for hand in ["Hand 1", "Hand 2", "Unknown"]:
        tokens = hand_tokens.get(hand, [])
        console.print(f"  {hand}: {len(tokens)} tokens")

    # 8.1: Per-hand window usage
    profiles = sprint_8_1(hand_tokens)

    # 8.2: Consultation patterns
    consultation = sprint_8_2(hand_tokens)

    # 8.3: Drift admissibility
    admissibility = sprint_8_3(hand_tokens, corrections, lattice_map)

    # 8.4: Synthesis
    synthesis = sprint_8_4(profiles, consultation, admissibility)

    # Strip vectors from profiles for output
    profile_out = {}
    for hand, p in profiles.items():
        if isinstance(p, dict) and "vector" in p:
            profile_out[hand] = {k: v for k, v in p.items() if k != "vector"}
        else:
            profile_out[hand] = p

    results = {
        "profiles": profile_out,
        "consultation": consultation,
        "admissibility": admissibility,
        "synthesis": synthesis,
        "summary": {
            "hand1_tokens": profiles.get("Hand 1", {}).get("token_count", 0),
            "hand2_tokens": profiles.get("Hand 2", {}).get("token_count", 0),
            "shared_vocab_fraction": consultation.get("shared_fraction", 0),
            "admissibility_verdict": admissibility.get("comparison", {}).get(
                "verdict", "N/A"),
            "overall_verdict": synthesis["verdict"],
        },
    }

    # Sanitize numpy types
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
    with active_run(config={"seed": 42, "command": "run_20f_hand_analysis"}):
        main()
