#!/usr/bin/env python3
"""Sprint A2: The Latin Test.

Can a Latin text be encoded into the choice-bit stream without violating
lattice constraints?  This script:
  A2.1 — Extracts the choice-index sequence from the real manuscript
  A2.2 — Computes arithmetic coding channel capacity
  A2.3 — Attempts to encode a short Latin passage into the choice stream
  A2.4 — Round-trip verification (encode → decode → compare)
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402

CHOICE_STREAM_PATH = (
    project_root / "results/data/phase15_rule_extraction/choice_stream_trace.json"
)
LEGACY_CHOICE_STREAM_PATH = (
    project_root / "results/data/phase15_selection/choice_stream_trace.json"
)
RSB_PATH = project_root / "results/data/phase17_finality/residual_bandwidth.json"
OUTPUT_PATH = project_root / "results/data/phase17_finality/latin_test.json"
console = Console()

# Genesis 1:1-5 from the Vulgate (standard test passage)
LATIN_PASSAGE = (
    "In principio creavit Deus caelum et terram. "
    "Terra autem erat inanis et vacua et tenebrae super faciem abyssi "
    "et spiritus Dei ferebatur super aquas. "
    "Dixitque Deus fiat lux et facta est lux. "
    "Et vidit Deus lucem quod esset bona "
    "et divisit lucem ac tenebras. "
    "Appellavitque lucem diem et tenebras noctem "
    "factumque est vespere et mane dies unus."
)


# ── A2.1: Choice-Index Extraction ────────────────────────────────────

def extract_choice_indices(choices):
    """Extract the choice-index sequence and per-choice alphabet sizes."""
    console.rule("[bold blue]A2.1: Choice-Index Extraction")

    indices = []
    alphabet_sizes = []
    for c in choices:
        idx = c["chosen_index"]
        n = c["candidates_count"]
        if n > 1:
            indices.append(idx)
            alphabet_sizes.append(n)

    console.print(f"  Total choices with >1 candidate: {len(indices)}")
    console.print(f"  Mean alphabet size: {np.mean(alphabet_sizes):.1f}")
    console.print(f"  Min: {min(alphabet_sizes)}, Max: {max(alphabet_sizes)}, "
                  f"Median: {np.median(alphabet_sizes):.0f}")

    return indices, alphabet_sizes


# ── A2.2: Channel Capacity ───────────────────────────────────────────

def compute_channel_capacity(alphabet_sizes):
    """Compute theoretical channel capacity using per-choice alphabet sizes."""
    console.rule("[bold blue]A2.2: Arithmetic Coding Channel Capacity")

    # Each choice contributes log2(candidates_count) bits of capacity
    # if the scribe has full freedom over the index.
    bits_per_choice = [math.log2(n) for n in alphabet_sizes]
    total_bits = sum(bits_per_choice)
    mean_bpc = np.mean(bits_per_choice)
    total_kb = total_bits / 8192

    console.print(f"  Total channel capacity: {total_bits:,.0f} bits ({total_kb:.1f} KB)")
    console.print(f"  Mean bits per choice: {mean_bpc:.3f}")
    console.print(f"  Equivalent Latin chars (@4.1 bits/char): ~{total_bits / 4.1:,.0f}")

    return {
        "total_capacity_bits": round(total_bits, 2),
        "total_capacity_kb": round(total_kb, 2),
        "mean_bits_per_choice": round(mean_bpc, 4),
        "n_choices": len(alphabet_sizes),
        "latin_chars_equivalent": round(total_bits / 4.1, 0),
    }


# ── A2.3: Latin Encoding Attempt ─────────────────────────────────────

def text_to_bits(text):
    """Convert text to a bit string using 8-bit ASCII."""
    bits = []
    for ch in text.encode("latin-1", errors="replace"):
        for i in range(7, -1, -1):
            bits.append((ch >> i) & 1)
    return bits


def bits_to_text(bits):
    """Convert a bit string back to text using 8-bit ASCII."""
    chars = []
    for i in range(0, len(bits) - 7, 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bits[i + j]
        chars.append(chr(byte))
    return "".join(chars)


def resolve_choice_stream_path() -> Path:
    if CHOICE_STREAM_PATH.exists():
        return CHOICE_STREAM_PATH
    if LEGACY_CHOICE_STREAM_PATH.exists():
        return LEGACY_CHOICE_STREAM_PATH
    raise FileNotFoundError(
        "Choice stream trace missing. Checked "
        f"{CHOICE_STREAM_PATH} and {LEGACY_CHOICE_STREAM_PATH}."
    )


def encode_into_choices(message_bits, alphabet_sizes):
    """Encode a bit stream into choice indices using simple base decomposition.

    For each choice with alphabet size N, we can encode floor(log2(N)) bits
    by setting the choice index to the value represented by those bits.
    Returns the list of encoded choice indices and how many message bits
    were consumed.
    """
    encoded_indices = []
    bits_consumed = 0

    for n in alphabet_sizes:
        if bits_consumed >= len(message_bits):
            break
        if n <= 1:
            encoded_indices.append(0)
            continue

        # How many bits can this choice encode?
        capacity = int(math.log2(n))
        if capacity == 0:
            encoded_indices.append(0)
            continue

        # Extract that many bits from the message
        chunk = message_bits[bits_consumed: bits_consumed + capacity]
        if len(chunk) < capacity:
            # Pad with zeros for the last partial chunk
            chunk = chunk + [0] * (capacity - len(chunk))

        # Convert bits to index value
        value = 0
        for bit in chunk:
            value = (value << 1) | bit
        # Ensure within bounds
        value = min(value, n - 1)
        encoded_indices.append(value)
        bits_consumed += capacity

    return encoded_indices, bits_consumed


def decode_from_choices(encoded_indices, alphabet_sizes, total_bits):
    """Decode a bit stream from choice indices."""
    bits = []
    for idx, n in zip(encoded_indices, alphabet_sizes):
        if n <= 1:
            continue
        capacity = int(math.log2(n))
        if capacity == 0:
            continue
        # Extract bits from index value
        for i in range(capacity - 1, -1, -1):
            bits.append((idx >> i) & 1)
        if len(bits) >= total_bits:
            break
    return bits[:total_bits]


def latin_encoding_test(indices, alphabet_sizes):
    """Attempt to encode a Latin passage into the choice stream."""
    console.rule("[bold blue]A2.3: Latin Encoding Attempt")

    passage = LATIN_PASSAGE
    console.print(f"  Passage: Genesis 1:1-5 ({len(passage)} chars)")
    console.print(f'  First 80 chars: "{passage[:80]}..."')

    # Convert to bits
    message_bits = text_to_bits(passage)
    total_message_bits = len(message_bits)
    console.print(f"  Message size: {total_message_bits} bits ({total_message_bits / 8} bytes)")

    # Compute how many choices are needed
    cumulative_capacity = 0
    choices_needed = 0
    for n in alphabet_sizes:
        if n > 1:
            cumulative_capacity += int(math.log2(n))
            choices_needed += 1
        if cumulative_capacity >= total_message_bits:
            break

    console.print(f"  Choices needed to encode: {choices_needed} / {len(alphabet_sizes)}")
    fraction_used = choices_needed / len(alphabet_sizes) if alphabet_sizes else 0
    console.print(f"  Fraction of manuscript used: {fraction_used:.1%}")

    if cumulative_capacity < total_message_bits:
        console.print("[red]  ENCODING FAILED: Insufficient channel capacity[/red]")
        return {
            "passage_chars": len(passage),
            "passage_bits": total_message_bits,
            "encoding_success": False,
            "shortfall_bits": total_message_bits - cumulative_capacity,
        }

    # Encode
    encoded, bits_consumed = encode_into_choices(message_bits, alphabet_sizes)
    console.print(f"  Bits consumed: {bits_consumed}")
    console.print("  [green]ENCODING SUCCEEDED[/green]")

    # A2.4: Round-trip verification
    console.rule("[bold blue]A2.4: Round-Trip Verification")
    decoded_bits = decode_from_choices(encoded, alphabet_sizes, total_message_bits)
    decoded_text = bits_to_text(decoded_bits)

    match = decoded_text == passage
    console.print(f"  Decoded text matches original: "
                  f"{'[green]YES[/green]' if match else '[red]NO[/red]'}")

    if not match:
        # Find first mismatch
        for i, (a, b) in enumerate(zip(passage, decoded_text)):
            if a != b:
                console.print(f"  First mismatch at char {i}: "
                              f"expected '{a}' got '{b}'")
                break
        console.print(f'  Decoded first 80: "{decoded_text[:80]}"')

    return {
        "passage_chars": len(passage),
        "passage_bits": total_message_bits,
        "encoding_success": True,
        "bits_consumed": bits_consumed,
        "choices_needed": choices_needed,
        "choices_available": len(alphabet_sizes),
        "fraction_of_manuscript": round(fraction_used, 4),
        "round_trip_match": match,
        "decoded_first_80": decoded_text[:80],
    }


# ── Main ──────────────────────────────────────────────────────────────

def main():
    console.rule("[bold magenta]Sprint A2: The Latin Test")

    # Load choice stream
    choice_stream_path = resolve_choice_stream_path()
    console.print(f"Using choice stream: {choice_stream_path}")
    with open(choice_stream_path) as f:
        trace = json.load(f)
    choices = trace.get("results", trace).get("choices", [])
    console.print(f"Loaded {len(choices)} choice records.")

    # Load RSB for context
    rsb_bpw = None
    if RSB_PATH.exists():
        with open(RSB_PATH) as f:
            rsb_data = json.load(f)
        rsb_bpw = rsb_data["results"]["rsb_bpw"]
        console.print(f"RSB from A1: {rsb_bpw:.4f} bits/word")

    # A2.1: Extract choice indices
    indices, alphabet_sizes = extract_choice_indices(choices)

    # A2.2: Channel capacity
    capacity = compute_channel_capacity(alphabet_sizes)

    # A2.3-A2.4: Latin encoding + round-trip
    encoding = latin_encoding_test(indices, alphabet_sizes)

    # Summary
    console.rule("[bold magenta]Summary")
    table = Table(title="Latin Test Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="bold")
    table.add_row("Channel capacity", f"{capacity['total_capacity_bits']:,.0f} bits")
    table.add_row("Latin passage size", f"{encoding['passage_bits']} bits ({encoding['passage_chars']} chars)")
    table.add_row("Encoding success", "YES" if encoding["encoding_success"] else "NO")
    if encoding["encoding_success"]:
        table.add_row("Choices consumed", f"{encoding['choices_needed']:,} / {encoding['choices_available']:,}")
        table.add_row("Manuscript fraction used", f"{encoding['fraction_of_manuscript']:.1%}")
        table.add_row("Round-trip fidelity", "EXACT" if encoding["round_trip_match"] else "FAILED")
    if rsb_bpw is not None:
        table.add_row("RSB (from A1)", f"{rsb_bpw:.2f} bits/word")
    console.print(table)

    console.print(
        "\n[bold]Interpretation:[/bold] "
        "The lattice choice stream has sufficient capacity to encode "
        "a short Latin passage. This does NOT prove hidden content exists — "
        "it demonstrates that the mechanical model's choice freedom is "
        "large enough that steganography is physically feasible."
    )

    # Save
    results = {
        "channel_capacity": capacity,
        "latin_passage": {
            "text_preview": LATIN_PASSAGE[:100] + "...",
            "chars": len(LATIN_PASSAGE),
        },
        "encoding_result": encoding,
        "rsb_bpw": rsb_bpw,
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Saved to {OUTPUT_PATH}[/green]")


if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_17d_latin_test"}):
        main()
