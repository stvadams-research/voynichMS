#!/usr/bin/env python3
"""Sprint D2: Generic Corpus Ingestion.

Tokenizes and prepares comparison texts for the signature battery.
Produces standardized token sequences from:
  1. Shuffled Voynich (null control — same vocabulary, destroyed sequence)
  2. Latin (De Bello Gallico — natural language baseline)
  3. Reversed Voynich (line-reversed word order — partial structure control)
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402

IVTFF_PATH = project_root / "data/raw/transliterations/ivtff2.0/ZL3b-n.txt"
LATIN_PATH = project_root / "data/external_corpora/latin_corpus.txt"
OUTPUT_PATH = project_root / "results/data/phase18_comparative/ingested_corpora.json"

console = Console()


def load_ivtff_lines(path):
    """Load manuscript lines from IVTFF file."""
    lines = []
    with open(path, encoding="utf-8-sig") as f:
        for raw in f:
            raw = raw.strip()
            if not raw or raw.startswith("#"):
                continue
            if "\t" in raw:
                content = raw.split("\t", 1)[1]
            else:
                content = raw
            content = content.replace("<%>", "").replace("{", "").replace("}", "")
            content = re.sub(r"\[[^\]]*:[^\]]*\]", "", content)
            content = re.sub(r"[!*?]", "", content)
            tokens = [t.strip() for t in content.replace(".", " ").split() if t.strip()]
            if tokens:
                lines.append(tokens)
    return lines


def load_latin_corpus(path, min_tokens=3):
    """Load Latin text as tokenized lines."""
    lines = []
    with open(path, encoding="utf-8-sig") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            # Skip Gutenberg header/footer
            if raw.startswith("***") or raw.startswith("The Project Gutenberg"):
                continue
            if raw.startswith("This ebook") or raw.startswith("Most people"):
                continue
            # Tokenize: lowercase, split on whitespace and punctuation
            clean = re.sub(r"[^a-zA-Z\s]", "", raw.lower())
            tokens = [t for t in clean.split() if len(t) > 0]
            if len(tokens) >= min_tokens:
                lines.append(tokens)
    return lines


def make_shuffled_voynich(voynich_lines, seed=42):
    """Create null control by shuffling word order within each line."""
    rng = np.random.default_rng(seed)
    shuffled = []
    for line in voynich_lines:
        perm = list(line)
        rng.shuffle(perm)
        shuffled.append(perm)
    return shuffled


def make_reversed_voynich(voynich_lines):
    """Create partial control by reversing word order within each line."""
    return [list(reversed(line)) for line in voynich_lines]


def corpus_stats(lines, name):
    """Compute and display basic corpus statistics."""
    all_tokens = [t for line in lines for t in line]
    vocab = set(all_tokens)
    counts = Counter(all_tokens)
    hapax = sum(1 for c in counts.values() if c == 1)

    stats = {
        "name": name,
        "n_lines": len(lines),
        "n_tokens": len(all_tokens),
        "vocab_size": len(vocab),
        "hapax_count": hapax,
        "hapax_fraction": round(hapax / len(vocab), 4) if vocab else 0,
        "mean_line_length": round(np.mean([len(l) for l in lines]), 2),
        "ttr": round(len(vocab) / len(all_tokens), 4) if all_tokens else 0,
    }
    return stats


def main():
    console.rule("[bold magenta]Sprint D2: Generic Corpus Ingestion")

    # 1. Load Voynich
    voynich_lines = load_ivtff_lines(IVTFF_PATH)
    console.print(f"Voynich: {len(voynich_lines)} lines loaded")

    # 2. Create controls
    shuffled = make_shuffled_voynich(voynich_lines)
    reversed_v = make_reversed_voynich(voynich_lines)

    # 3. Load Latin
    if LATIN_PATH.exists():
        latin_lines = load_latin_corpus(LATIN_PATH)
        console.print(f"Latin: {len(latin_lines)} lines loaded")
    else:
        console.print("[yellow]Latin corpus not found — skipping[/yellow]")
        latin_lines = []

    # 4. Compute stats
    corpora = {
        "voynich": {"lines": voynich_lines},
        "shuffled_voynich": {"lines": shuffled},
        "reversed_voynich": {"lines": reversed_v},
    }
    if latin_lines:
        corpora["latin"] = {"lines": latin_lines}

    table = Table(title="Ingested Corpora")
    table.add_column("Corpus", style="cyan")
    table.add_column("Lines", justify="right")
    table.add_column("Tokens", justify="right")
    table.add_column("Vocab", justify="right")
    table.add_column("Hapax %", justify="right")
    table.add_column("TTR", justify="right")

    all_stats = {}
    for name, data in corpora.items():
        stats = corpus_stats(data["lines"], name)
        all_stats[name] = stats
        table.add_row(
            name,
            str(stats["n_lines"]),
            f"{stats['n_tokens']:,}",
            f"{stats['vocab_size']:,}",
            f"{stats['hapax_fraction']:.1%}",
            f"{stats['ttr']:.4f}",
        )

    console.print(table)

    # 5. Save — lines as lists of token lists
    results = {
        "corpora": {},
        "stats": all_stats,
    }
    for name, data in corpora.items():
        results["corpora"][name] = {
            "lines": data["lines"],
            "n_lines": len(data["lines"]),
            "n_tokens": sum(len(l) for l in data["lines"]),
        }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_18b_corpus_ingestion"}):
        main()
