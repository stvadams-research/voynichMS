#!/usr/bin/env python3
"""
Step 3.2.4: The Indistinguishability Challenge (The Turing Test)

Generates a synthetic pharmaceutical section and tests if it
is statistically indistinguishable from the real manuscript.
"""

import argparse
import math
import os
import re
import sys
from time import perf_counter
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from foundation.runs.manager import active_run
from foundation.storage.metadata import MetadataStore
from foundation.storage.metadata import PageRecord
from foundation.core.id_factory import DeterministicIDFactory
from foundation.config import DEFAULT_SEED

from synthesis.profile_extractor import PharmaceuticalProfileExtractor
from synthesis.text_generator import TextContinuationGenerator

# Metrics
from foundation.metrics.library import RepetitionRate
from foundation.core.provenance import ProvenanceWriter
from analysis.stress_tests.information_preservation import InformationPreservationTest
from analysis.stress_tests.locality import LocalityTest

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
REAL_DATASET_ID = "voynich_real"
SYNTHETIC_DATASET_ID = "voynich_synthetic_grammar"
EXPLANATION_CLASS = "constructed_system"
REPETITION_TOLERANCE = 0.10
INFO_DENSITY_TOLERANCE = 0.10
LOCALITY_RADIUS_TOLERANCE = 1.0
SPLIT_PAGE_ID_PATTERN = re.compile(r"^(f\d+[rv])\d+$")


class RealProfilePreflightError(RuntimeError):
    """Structured preflight error with machine-readable reason metadata."""

    def __init__(self, message: str, *, reason_code: str, preflight: dict):
        super().__init__(message)
        self.reason_code = reason_code
        self.preflight = preflight


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
    findings = {
        "status": "BLOCKED",
        "strict_computed": strict_computed,
        "reason_code": reason_code,
        "error": error,
    }
    if preflight is not None:
        findings["preflight"] = preflight
    ProvenanceWriter.save_results(findings, "status/synthesis/TURING_TEST_RESULTS.json")


def run_turing_test(*, strict_computed: bool, preflight_only: bool = False) -> None:
    console.print(Panel.fit(
        "[bold blue]Step 3.2.4: The Algorithmic Turing Test[/bold blue]\n"
        "Testing indistinguishability of grammar-based generator",
        border_style="blue"
    ))

    with active_run(config={"command": "turing_test", "seed": DEFAULT_SEED}) as run:
        store = MetadataStore(DB_PATH)
        id_factory = DeterministicIDFactory(seed=DEFAULT_SEED)
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
            findings = {
                "status": "PREFLIGHT_OK",
                "strict_computed": strict_computed,
                "preflight": preflight,
            }
            ProvenanceWriter.save_results(findings, "status/synthesis/TURING_TEST_RESULTS.json")
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
                    store.add_line(line_id, page_id, line_idx, {"x":0,"y":0,"w":0,"h":0}, 1.0)
                    
                    trans_line_id = id_factory.next_uuid(f"trans_line:{page_id}:{line_idx}")
                    store.add_transcription_line(trans_line_id, "synthetic", page_id, line_idx, " ".join(block))
                    
                    for w_idx, token in enumerate(block):
                        word_id = id_factory.next_uuid(f"word:{line_id}:{w_idx}")
                        store.add_word(word_id, line_id, w_idx, {"x":0,"y":0,"w":0,"h":0}, {}, 1.0)
                        
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
        
        console.print(table)
        console.print(f"[dim]Analysis complete in {perf_counter() - analysis_start:.2f}s[/dim]")
        
        success = repetition_pass and info_pass and locality_pass
        
        if success:
            console.print("\n[bold green]SUCCESS: Synthetic text is statistically indistinguishable from Real Voynichese.[/bold green]")
            findings_status = "SUCCESS"
        else:
            console.print("\n[bold yellow]INCONCLUSIVE: Gaps remain in structural similarity.[/bold yellow]")
            findings_status = "INCONCLUSIVE"
            
        # Save results
        findings = {
            "status": findings_status,
            "strict_computed": strict_computed,
            "preflight": preflight,
            "dataset_ids": {
                "real": REAL_DATASET_ID,
                "synthetic": dataset_id,
            },
            "tolerances": {
                "repetition": REPETITION_TOLERANCE,
                "info_density": INFO_DENSITY_TOLERANCE,
                "locality_radius": LOCALITY_RADIUS_TOLERANCE,
            },
            "metrics": {
                "repetition": {"real": real_rep, "syn": syn_rep},
                "info_density": {"real": real_info_density, "syn": syn_info_density},
                "locality_radius": {"real": real_radius, "syn": syn_radius},
            },
            "pass_flags": {
                "repetition": repetition_pass,
                "info_density": info_pass,
                "locality_radius": locality_pass,
            },
        }
        ProvenanceWriter.save_results(findings, "status/synthesis/TURING_TEST_RESULTS.json")
            
        store.save_run(run)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the synthesis indistinguishability challenge."
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
