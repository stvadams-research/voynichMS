#!/usr/bin/env python3
"""
Step 3.2.4: The Indistinguishability Challenge (The Turing Test)

Generates a synthetic pharmaceutical section and tests if it
is statistically indistinguishable from the real manuscript.
"""

import argparse
import json
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import Any

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from phase1_foundation.config import DEFAULT_SEED
from phase1_foundation.core.id_factory import DeterministicIDFactory
from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.metrics.library import RepetitionRate
from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import MetadataStore, PageRecord
from phase2_analysis.stress_tests.information_preservation import InformationPreservationTest
from phase2_analysis.stress_tests.locality import LocalityTest
from phase3_synthesis.profile_extractor import PharmaceuticalProfileExtractor
from phase3_synthesis.text_generator import TextContinuationGenerator

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
REAL_DATASET_ID = "voynich_real"
SYNTHETIC_DATASET_ID = "voynich_synthetic_grammar"
EXPLANATION_CLASS = "constructed_system"
REPETITION_TOLERANCE = 0.10
INFO_DENSITY_TOLERANCE = 0.10
LOCALITY_RADIUS_TOLERANCE = 1.0
MEAN_WORD_LENGTH_TOLERANCE = 0.60
POSITIONAL_ENTROPY_TOLERANCE = 0.12
SPLIT_PAGE_ID_PATTERN = re.compile(r"^(f\d+[rv])\d+$")

SK_H3_POLICY_PATH = project_root / "configs/core_skeptic/sk_h3_control_comparability_policy.json"
CONTROL_COMPARABILITY_STATUS_PATH = "core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json"


class RealProfilePreflightError(RuntimeError):
    """Structured preflight error with machine-readable reason metadata."""

    def __init__(self, message: str, *, reason_code: str, preflight: dict):
        super().__init__(message)
        self.reason_code = reason_code
        self.preflight = preflight


def _load_sk_h3_policy() -> dict[str, Any]:
    if SK_H3_POLICY_PATH.exists():
        return json.loads(SK_H3_POLICY_PATH.read_text(encoding="utf-8"))
    return {
        "metric_partition_policy": {
            "matching_metrics": ["repetition_rate", "information_density", "locality_radius"],
            "holdout_evaluation_metrics": ["mean_word_length", "positional_entropy"],
        },
        "normalization_policy": {"default_mode": "parser"},
    }


def _partition_policy(policy: dict[str, Any]) -> dict[str, Any]:
    partition = dict(policy.get("metric_partition_policy", {}))
    matching_metrics = [str(v) for v in partition.get("matching_metrics", [])]
    holdout_metrics = [str(v) for v in partition.get("holdout_evaluation_metrics", [])]
    metric_overlap = sorted(set(matching_metrics) & set(holdout_metrics))
    return {
        "matching_metrics": matching_metrics,
        "holdout_evaluation_metrics": holdout_metrics,
        "metric_overlap": metric_overlap,
    }


def _status_allowed_claim(status: str) -> str:
    if status == "COMPARABLE_CONFIRMED":
        return "Control comparability supports bounded structural phase4_inference under SK-H3 policy."
    if status == "COMPARABLE_QUALIFIED":
        return "Control comparability is acceptable with explicit caveats."
    if status == "INCONCLUSIVE_DATA_LIMITED":
        return "Control comparability remains inconclusive pending additional evidence volume."
    return "Control-based inferential claims are blocked pending SK-H3 remediation."


def _build_comparability_summary(
    *,
    policy: dict[str, Any],
    status: str,
    reason_code: str,
    matching_pass: bool,
    holdout_pass: bool,
    pass_flags: dict[str, bool] | None = None,
) -> dict[str, Any]:
    partition = _partition_policy(policy)
    normalization_policy = dict(policy.get("normalization_policy", {}))
    metric_overlap = list(partition["metric_overlap"])
    leakage_detected = len(metric_overlap) > 0
    return {
        "status": status,
        "reason_code": reason_code,
        "matching_metrics": list(partition["matching_metrics"]),
        "holdout_evaluation_metrics": list(partition["holdout_evaluation_metrics"]),
        "metric_overlap": metric_overlap,
        "leakage_detected": leakage_detected,
        "matching_pass": matching_pass,
        "holdout_pass": holdout_pass,
        "normalization_mode": str(normalization_policy.get("default_mode", "parser")),
        "allowed_claim": _status_allowed_claim(status),
        "pass_flags": dict(pass_flags or {}),
    }


def _write_control_comparability_status(summary: dict[str, Any]) -> None:
    grade_map = {
        "COMPARABLE_CONFIRMED": "A",
        "COMPARABLE_QUALIFIED": "B",
        "INCONCLUSIVE_DATA_LIMITED": "C",
        "NON_COMPARABLE_BLOCKED": "D",
    }
    payload = {
        "status": summary.get("status"),
        "reason_code": summary.get("reason_code"),
        "comparability_grade": grade_map.get(str(summary.get("status")), "D"),
        "allowed_claim": summary.get("allowed_claim"),
        "matching_metrics": summary.get("matching_metrics", []),
        "holdout_evaluation_metrics": summary.get("holdout_evaluation_metrics", []),
        "metric_overlap": summary.get("metric_overlap", []),
        "leakage_detected": bool(summary.get("leakage_detected", False)),
        "normalization_mode": summary.get("normalization_mode", "parser"),
    }
    ProvenanceWriter.save_results(payload, CONTROL_COMPARABILITY_STATUS_PATH)


def _normalize_pharma_page_id(page_id: str) -> str:
    """Normalize split folio ids (e.g., f89r1 -> f89r) for preflight matching."""
    match = SPLIT_PAGE_ID_PATTERN.match(page_id)
    if match:
        return match.group(1)
    return page_id


def _index_available_pages(page_ids: set[str]) -> dict[str, list[str]]:
    """Map normalized page ids to all raw variants present in the dataset."""
    by_base: dict[str, list[str]] = {}
    for page_id in sorted(page_ids):
        base = _normalize_pharma_page_id(page_id)
        by_base.setdefault(base, []).append(page_id)
    return by_base


def _require_scalar(value, metric_name: str, dataset_id: str) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            f"{metric_name} for dataset '{dataset_id}' is not numeric: {value!r}"
        ) from exc
    if not math.isfinite(numeric):
        raise RuntimeError(
            f"{metric_name} for dataset '{dataset_id}' is not finite: {numeric!r}"
        )
    return numeric


def _require_metric_result(metric_results, metric_name: str, dataset_id: str) -> float:
    if not metric_results:
        raise RuntimeError(
            f"{metric_name} is unavailable for dataset '{dataset_id}'. "
            "Verify dataset/transcription artifacts are present."
        )
    return _require_scalar(metric_results[0].value, metric_name, dataset_id)


def _require_stress_metric(
    metrics: dict,
    key: str,
    metric_name: str,
    dataset_id: str,
) -> float:
    if key not in metrics:
        raise RuntimeError(
            f"{metric_name} metric '{key}' missing for dataset '{dataset_id}'."
        )
    return _require_scalar(metrics[key], metric_name, dataset_id)


def _mean(values: list[float], *, fallback: float = 0.0) -> float:
    if not values:
        return fallback
    return sum(values) / len(values)


def _compute_token_positional_entropy(text_blocks: list[list[str]]) -> float:
    counts = {"start": Counter(), "mid": Counter(), "end": Counter()}
    tokens = [token for block in text_blocks for token in block if token]
    if not tokens:
        return 0.0

    for token in tokens:
        counts["start"][token[0]] += 1
        counts["end"][token[-1]] += 1
        for char in token[1:-1]:
            counts["mid"][char] += 1

    entropies = []
    for counter in counts.values():
        if not counter:
            continue
        total = sum(counter.values())
        entropy = 0.0
        for count in counter.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        max_entropy = math.log2(len(counter)) if len(counter) > 1 else 1.0
        entropies.append(entropy / max_entropy if max_entropy > 0 else 0.0)

    return _mean(entropies)


def _preflight_real_profile_inputs(
    store: MetadataStore, strict_computed: bool
) -> dict:
    expected_pages = list(PharmaceuticalProfileExtractor.SECTION_PAGES)
    session = store.Session()
    try:
        available = {
            row[0]
            for row in session.query(PageRecord.id)
            .filter(PageRecord.dataset_id == REAL_DATASET_ID)
            .all()
        }
    finally:
        session.close()

    available_by_base = _index_available_pages(available)
    available_normalized = set(available_by_base.keys())
    missing_pages = [
        page
        for page in expected_pages
        if _normalize_pharma_page_id(page) not in available_normalized
    ]
    split_variants = {
        page: variants
        for page, variants in available_by_base.items()
        if page in expected_pages and any(variant != page for variant in variants)
    }
    preflight = {
        "dataset_id": REAL_DATASET_ID,
        "expected_pages": expected_pages,
        "available_pages": sorted(available),
        "available_pages_normalized": sorted(available_normalized),
        "split_page_variants": split_variants,
        "missing_pages": missing_pages,
        "missing_count": len(missing_pages),
    }
    if not missing_pages:
        return preflight

    preview = ", ".join(missing_pages[:8])
    suffix = "..." if len(missing_pages) > 8 else ""
    message = (
        f"Real profile preflight: missing {len(missing_pages)}/"
        f"{len(expected_pages)} pharmaceutical pages in dataset "
        f"'{REAL_DATASET_ID}' ({preview}{suffix})."
    )
    if strict_computed:
        raise RealProfilePreflightError(
            f"{message} REQUIRE_COMPUTED=1 forbids simulated/fallback profile paths.",
            reason_code="DATA_AVAILABILITY",
            preflight=preflight,
        )
    console.print(f"[yellow]Warning:[/yellow] {message}")
    return preflight


def _write_blocked_results(
    *,
    strict_computed: bool,
    error: str,
    reason_code: str,
    preflight: dict | None = None,
) -> None:
    policy = _load_sk_h3_policy()
    comparability = _build_comparability_summary(
        policy=policy,
        status="NON_COMPARABLE_BLOCKED",
        reason_code=reason_code,
        matching_pass=False,
        holdout_pass=False,
    )
    findings = {
        "status": "BLOCKED",
        "strict_computed": strict_computed,
        "reason_code": reason_code,
        "error": error,
        "comparability": comparability,
    }
    if preflight is not None:
        findings["preflight"] = preflight
    ProvenanceWriter.save_results(findings, "core_status/phase3_synthesis/TURING_TEST_RESULTS.json")
    _write_control_comparability_status(comparability)


def run_turing_test(*, strict_computed: bool, preflight_only: bool = False) -> None:
    console.print(Panel.fit(
        "[bold blue]Step 3.2.4: The Algorithmic Turing Test[/bold blue]\n"
        "Testing indistinguishability of grammar-based generator",
        border_style="blue"
    ))

    with active_run(config={"command": "turing_test", "seed": DEFAULT_SEED}) as run:
        store = MetadataStore(DB_PATH)
        id_factory = DeterministicIDFactory(seed=DEFAULT_SEED)
        policy = _load_sk_h3_policy()

        try:
            preflight = _preflight_real_profile_inputs(store, strict_computed)
        except RealProfilePreflightError as exc:
            _write_blocked_results(
                strict_computed=strict_computed,
                error=str(exc),
                reason_code=exc.reason_code,
                preflight=exc.preflight,
            )
            raise
        except RuntimeError as exc:
            _write_blocked_results(
                strict_computed=strict_computed,
                error=str(exc),
                reason_code="RUNTIME_ERROR",
            )
            raise

        if preflight_only:
            comparability = _build_comparability_summary(
                policy=policy,
                status="INCONCLUSIVE_DATA_LIMITED",
                reason_code="PREFLIGHT_ONLY",
                matching_pass=False,
                holdout_pass=False,
            )
            findings = {
                "status": "PREFLIGHT_OK",
                "strict_computed": strict_computed,
                "preflight": preflight,
                "comparability": comparability,
            }
            ProvenanceWriter.save_results(findings, "core_status/phase3_synthesis/TURING_TEST_RESULTS.json")
            _write_control_comparability_status(comparability)
            store.save_run(run)
            console.print("[green]Preflight complete.[/green]")
            return

        # 1. Setup
        setup_start = perf_counter()
        extractor = PharmaceuticalProfileExtractor(store)
        profile = extractor.extract_section_profile()
        generator = TextContinuationGenerator(profile)
        console.print(f"[dim]Setup complete in {perf_counter() - setup_start:.2f}s[/dim]")

        # Ensure source id used for synthetic transcription lines exists.
        store.add_transcription_source("synthetic", "Synthetic Generator")

        # 2. Generate full synthetic section (2 pages)
        console.print("\n[bold yellow]Step 1: Generating Synthetic Section (2 pages)[/bold yellow]")
        generation_start = perf_counter()
        dataset_id = SYNTHETIC_DATASET_ID
        store.add_dataset(dataset_id, "generated")

        synthetic_pages = generator.generate_multiple(gap_id="full_section", count=2)
        if not synthetic_pages:
            raise RuntimeError("Synthetic generation produced zero pages.")

        # Ingest
        session = store.Session()
        try:
            for i, page in enumerate(synthetic_pages):
                page_id = f"syn_grammar_{i}"
                store.add_page(page_id, dataset_id, "placeholder.jpg", f"hash_{i}", 1000, 1500)

                for line_idx, block in enumerate(page.text_blocks):
                    line_id = id_factory.next_uuid(f"line:{page_id}:{line_idx}")
                    store.add_line(line_id, page_id, line_idx, {"x": 0, "y": 0, "w": 0, "h": 0}, 1.0)

                    trans_line_id = id_factory.next_uuid(f"trans_line:{page_id}:{line_idx}")
                    store.add_transcription_line(
                        trans_line_id, "synthetic", page_id, line_idx, " ".join(block)
                    )

                    for w_idx, token in enumerate(block):
                        word_id = id_factory.next_uuid(f"word:{line_id}:{w_idx}")
                        store.add_word(word_id, line_id, w_idx, {"x": 0, "y": 0, "w": 0, "h": 0}, {}, 1.0)

                        token_id = id_factory.next_uuid(f"trans_token:{trans_line_id}:{w_idx}")
                        store.add_transcription_token(token_id, trans_line_id, w_idx, token)
            session.commit()
        finally:
            session.close()

        console.print(f"Generated and registered {len(synthetic_pages)} pages to {dataset_id}")
        console.print(
            f"[dim]Generation and ingest complete in {perf_counter() - generation_start:.2f}s[/dim]"
        )

        # 3. Benchmark against REAL data
        console.print("\n[bold yellow]Step 2: Analysis Blind Test[/bold yellow]")
        analysis_start = perf_counter()

        # Repetition
        rep_metric = RepetitionRate(store)
        real_rep = _require_metric_result(
            rep_metric.calculate(REAL_DATASET_ID),
            "repetition_rate",
            REAL_DATASET_ID,
        )
        syn_rep = _require_metric_result(
            rep_metric.calculate(dataset_id),
            "repetition_rate",
            dataset_id,
        )

        # Information density from computed stress-test metrics (no hardcoded values).
        info_test = InformationPreservationTest(store)
        real_info_result = info_test.run(EXPLANATION_CLASS, REAL_DATASET_ID, [])
        syn_info_result = info_test.run(EXPLANATION_CLASS, dataset_id, [])
        real_info_density = _require_stress_metric(
            real_info_result.metrics,
            "real_information_density",
            "information_density",
            REAL_DATASET_ID,
        )
        syn_info_density = _require_stress_metric(
            syn_info_result.metrics,
            "real_information_density",
            "information_density",
            dataset_id,
        )

        # Locality radius from computed stress-test metrics (no hardcoded values).
        loc_test = LocalityTest(store)
        real_loc_result = loc_test.run(EXPLANATION_CLASS, REAL_DATASET_ID, [])
        syn_loc_result = loc_test.run(EXPLANATION_CLASS, dataset_id, [])
        real_radius = _require_stress_metric(
            real_loc_result.metrics,
            "locality_radius",
            "locality_radius",
            REAL_DATASET_ID,
        )
        syn_radius = _require_stress_metric(
            syn_loc_result.metrics,
            "locality_radius",
            "locality_radius",
            dataset_id,
        )

        # Holdout metrics are intentionally separated from matching metrics.
        real_mean_word_length = _mean(
            [float(page.mean_word_length) for page in profile.pages if float(page.mean_word_length) > 0.0],
            fallback=0.0,
        )
        real_positional_entropy = _mean(
            [float(page.positional_entropy) for page in profile.pages if float(page.positional_entropy) > 0.0],
            fallback=0.0,
        )

        syn_mean_word_length_values: list[float] = []
        syn_positional_entropy_values: list[float] = []
        for page in synthetic_pages:
            if "mean_word_length" in page.metrics:
                syn_mean_word_length_values.append(float(page.metrics["mean_word_length"]))
            else:
                blocks = [token for line in page.text_blocks for token in line]
                if blocks:
                    syn_mean_word_length_values.append(
                        sum(len(token) for token in blocks) / len(blocks)
                    )
            if "positional_entropy" in page.metrics:
                syn_positional_entropy_values.append(float(page.metrics["positional_entropy"]))
            else:
                syn_positional_entropy_values.append(
                    _compute_token_positional_entropy(page.text_blocks)
                )

        syn_mean_word_length = _mean(syn_mean_word_length_values, fallback=0.0)
        syn_positional_entropy = _mean(syn_positional_entropy_values, fallback=0.0)

        # 4. Display Comparison
        table = Table(title="The Algorithmic Turing Test Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Real (Target)", style="green")
        table.add_column("Synthetic (Grammar)", style="yellow")
        table.add_column("Pass?", justify="center")

        def check_pass(val, target, tolerance=0.5):
            return "[green]PASS[/green]" if abs(val - target) <= tolerance else "[red]FAIL[/red]"

        repetition_pass = abs(syn_rep - real_rep) <= REPETITION_TOLERANCE
        info_pass = abs(syn_info_density - real_info_density) <= INFO_DENSITY_TOLERANCE
        locality_pass = abs(syn_radius - real_radius) <= LOCALITY_RADIUS_TOLERANCE
        mean_word_length_pass = abs(syn_mean_word_length - real_mean_word_length) <= MEAN_WORD_LENGTH_TOLERANCE
        positional_entropy_pass = abs(syn_positional_entropy - real_positional_entropy) <= POSITIONAL_ENTROPY_TOLERANCE

        table.add_row(
            "Repetition Rate",
            f"{real_rep:.3f}",
            f"{syn_rep:.3f}",
            check_pass(syn_rep, real_rep, REPETITION_TOLERANCE),
        )
        table.add_row(
            "Info Density",
            f"{real_info_density:.3f}",
            f"{syn_info_density:.3f}",
            check_pass(syn_info_density, real_info_density, INFO_DENSITY_TOLERANCE),
        )
        table.add_row(
            "Locality Radius",
            f"{real_radius:.2f}",
            f"{syn_radius:.2f}",
            check_pass(syn_radius, real_radius, LOCALITY_RADIUS_TOLERANCE),
        )
        table.add_row(
            "Holdout: Mean Word Length",
            f"{real_mean_word_length:.3f}",
            f"{syn_mean_word_length:.3f}",
            check_pass(syn_mean_word_length, real_mean_word_length, MEAN_WORD_LENGTH_TOLERANCE),
        )
        table.add_row(
            "Holdout: Positional Entropy",
            f"{real_positional_entropy:.3f}",
            f"{syn_positional_entropy:.3f}",
            check_pass(syn_positional_entropy, real_positional_entropy, POSITIONAL_ENTROPY_TOLERANCE),
        )

        console.print(table)
        console.print(f"[dim]Analysis complete in {perf_counter() - analysis_start:.2f}s[/dim]")

        success = repetition_pass and info_pass and locality_pass

        if success:
            console.print("\n[bold green]SUCCESS: Synthetic text is statistically indistinguishable from Real Voynichese.[/bold green]")
            findings_status = "SUCCESS"
        else:
            console.print("\n[bold yellow]INCONCLUSIVE: Gaps remain in structural similarity.[/bold yellow]")
            findings_status = "INCONCLUSIVE"

        pass_flags = {
            "repetition_rate": repetition_pass,
            "information_density": info_pass,
            "locality_radius": locality_pass,
            "mean_word_length": mean_word_length_pass,
            "positional_entropy": positional_entropy_pass,
        }
        partition = _partition_policy(policy)
        matching_pass = all(pass_flags.get(metric, False) for metric in partition["matching_metrics"])
        holdout_pass = all(pass_flags.get(metric, False) for metric in partition["holdout_evaluation_metrics"])

        if partition["metric_overlap"]:
            comparability_status = "NON_COMPARABLE_BLOCKED"
            comparability_reason = "TARGET_LEAKAGE"
        elif matching_pass and holdout_pass:
            comparability_status = "COMPARABLE_CONFIRMED"
            comparability_reason = "MATCH_AND_HOLDOUT_PASS"
        elif matching_pass:
            comparability_status = "COMPARABLE_QUALIFIED"
            comparability_reason = "MATCH_PASS_HOLDOUT_CAVEAT"
        else:
            comparability_status = "INCONCLUSIVE_DATA_LIMITED"
            comparability_reason = "MATCH_INSUFFICIENT"

        comparability = _build_comparability_summary(
            policy=policy,
            status=comparability_status,
            reason_code=comparability_reason,
            matching_pass=matching_pass,
            holdout_pass=holdout_pass,
            pass_flags=pass_flags,
        )

        # Save results
        findings = {
            "status": findings_status,
            "strict_computed": strict_computed,
            "preflight": preflight,
            "dataset_ids": {
                "real": REAL_DATASET_ID,
                "synthetic": dataset_id,
            },
            "matching_metrics": list(partition["matching_metrics"]),
            "holdout_evaluation_metrics": list(partition["holdout_evaluation_metrics"]),
            "metric_overlap": list(partition["metric_overlap"]),
            "leakage_detected": bool(partition["metric_overlap"]),
            "tolerances": {
                "repetition_rate": REPETITION_TOLERANCE,
                "information_density": INFO_DENSITY_TOLERANCE,
                "locality_radius": LOCALITY_RADIUS_TOLERANCE,
                "mean_word_length": MEAN_WORD_LENGTH_TOLERANCE,
                "positional_entropy": POSITIONAL_ENTROPY_TOLERANCE,
            },
            "metrics": {
                "repetition_rate": {"real": real_rep, "syn": syn_rep},
                "information_density": {"real": real_info_density, "syn": syn_info_density},
                "locality_radius": {"real": real_radius, "syn": syn_radius},
                "mean_word_length": {"real": real_mean_word_length, "syn": syn_mean_word_length},
                "positional_entropy": {"real": real_positional_entropy, "syn": syn_positional_entropy},
            },
            "pass_flags": pass_flags,
            "comparability": comparability,
        }
        ProvenanceWriter.save_results(findings, "core_status/phase3_synthesis/TURING_TEST_RESULTS.json")
        _write_control_comparability_status(comparability)

        store.save_run(run)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the phase3_synthesis indistinguishability challenge."
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Only validate real-profile prerequisites and write status output.",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--strict-computed",
        action="store_true",
        help="Force strict computed mode (equivalent to REQUIRE_COMPUTED=1).",
    )
    mode_group.add_argument(
        "--allow-fallback",
        action="store_true",
        help=(
            "Allow non-strict fallback behavior for exploratory runs. "
            "Release-evidentiary runs should not use this flag."
        ),
    )
    return parser.parse_args()


def _resolve_strict_mode(args: argparse.Namespace) -> bool:
    """
    Resolve strict-mode policy.

    Precedence:
    1) Explicit CLI mode flags.
    2) REQUIRE_COMPUTED environment variable.
    3) Strict-by-default fallback for release safety.
    """
    if args.allow_fallback:
        return False
    if args.strict_computed:
        return True

    env_value = os.environ.get("REQUIRE_COMPUTED")
    if env_value is not None:
        return env_value == "1"

    # Default to strict mode when no explicit override is provided.
    return True


if __name__ == "__main__":
    args = _parse_args()
    strict_mode = _resolve_strict_mode(args)
    run_turing_test(strict_computed=strict_mode, preflight_only=args.preflight_only)
