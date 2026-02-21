#!/usr/bin/env python3
"""
Phase 3: Pharmaceutical Section Continuation Synthesis

Gap-Constrained Structural Indistinguishability Study

Executes all tracks of Phase 3:
- Extract pharmaceutical section profile
- Define codicologically defensible gaps
- Generate multiple non-unique continuations per gap
- Run indistinguishability testing
- Evaluate success criteria

All synthetic outputs are explicitly labeled SYNTHETIC.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from typing import Any  # noqa: E402

import typer  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.progress import Progress, SpinnerColumn, TextColumn  # noqa: E402
from rich.table import Table  # noqa: E402

from phase3_synthesis.gap_continuation import MultiGapContinuation  # noqa: E402
from phase3_synthesis.indistinguishability import FullIndistinguishabilityTest  # noqa: E402
from phase3_synthesis.interface import Phase3Findings  # noqa: E402
from phase3_synthesis.profile_extractor import PharmaceuticalProfileExtractor  # noqa: E402

app = typer.Typer()
console = Console()


def display_section_profile(profile_summary: dict[str, Any]):
    """Display the extracted section profile."""
    console.print(Panel(
        f"[bold]Section:[/bold] {profile_summary['section_id']}\n"
        f"[bold]Pages:[/bold] {profile_summary['page_count']}\n\n"
        f"[bold]Jar Count:[/bold] {profile_summary['jar_count_range']}\n"
        f"[bold]Text Blocks per Jar:[/bold] {profile_summary['text_blocks_per_jar']}\n"
        f"[bold]Lines per Block:[/bold] {profile_summary['lines_per_block']}\n"
        f"[bold]Words per Line:[/bold] {profile_summary['words_per_line']}\n\n"
        f"[bold]Locality Range:[/bold] {profile_summary['locality_range']}\n"
        f"[bold]Info Density Range:[/bold] {profile_summary['info_density_range']}\n"
        f"[bold]Repetition Rate:[/bold] {profile_summary['repetition_rate_range']}",
        title="Pharmaceutical Section Structural Profile",
        border_style="cyan",
    ))


def display_gaps(gaps: list[dict[str, Any]]):
    """Display gap definitions."""
    table = Table(title="Codicologically Defensible Gaps", show_header=True)
    table.add_column("Gap ID", style="cyan")
    table.add_column("Strength")
    table.add_column("Between")
    table.add_column("Likely Loss")
    table.add_column("Evidence")

    for gap in gaps:
        strength_color = {
            "strong": "green",
            "moderate": "yellow",
            "weak": "red",
        }.get(gap["strength"], "white")

        table.add_row(
            gap["gap_id"],
            f"[{strength_color}]{gap['strength'].upper()}[/{strength_color}]",
            f"{gap['preceding_page']} → {gap['following_page']}",
            f"{gap['likely_pages_lost']}",
            str(gap["evidence_count"]),
        )

    console.print(table)


def display_continuation_results(results: dict[str, Any]):
    """Display continuation generation results."""
    table = Table(title="Continuation Results per Gap", show_header=True)
    table.add_column("Gap ID", style="cyan")
    table.add_column("Generated", justify="right")
    table.add_column("Accepted", justify="right")
    table.add_column("Rejected", justify="right")
    table.add_column("Unique", justify="right")
    table.add_column("Non-Unique?", justify="center")

    for gap_id, result in results.items():
        non_unique = "[green]YES[/green]" if result.demonstrates_non_uniqueness else "[red]NO[/red]"
        table.add_row(
            gap_id,
            str(len(result.pages) + result.pages_rejected),
            f"[green]{len(result.pages)}[/green]",
            f"[red]{result.pages_rejected}[/red]",
            str(result.unique_pages),
            non_unique,
        )

    console.print(table)


def display_indistinguishability_results(results: dict[str, Any]):
    """Display indistinguishability test results."""
    console.print("\n[bold cyan]Indistinguishability Testing[/bold cyan]")

    table = Table(title="Separation Metrics", show_header=True)
    table.add_column("Gap ID", style="cyan")
    table.add_column("Real vs Scrambled", justify="right")
    table.add_column("Synthetic vs Scrambled", justify="right")
    table.add_column("Real vs Synthetic", justify="right")
    table.add_column("Success?", justify="center")

    for gap_id, data in results["per_gap"].items():
        success = "[green]YES[/green]" if data["success"] else "[red]NO[/red]"

        # Color code separations
        rs_color = "green" if data["real_vs_scrambled"] > 0.7 else "yellow"
        ss_color = "green" if data["synthetic_vs_scrambled"] > 0.7 else "yellow"
        rl_color = "green" if data["real_vs_synthetic"] < 0.3 else "red"

        table.add_row(
            gap_id,
            f"[{rs_color}]{data['real_vs_scrambled']:.3f}[/{rs_color}]",
            f"[{ss_color}]{data['synthetic_vs_scrambled']:.3f}[/{ss_color}]",
            f"[{rl_color}]{data['real_vs_synthetic']:.3f}[/{rl_color}]",
            success,
        )

    console.print(table)

    console.print("\n[bold]Interpretation:[/bold]")
    console.print("  Real vs Scrambled: Should be HIGH (>0.7) - real pages differ from noise")
    console.print("  Synthetic vs Scrambled: Should be HIGH (>0.7) - synthetic pages differ from noise")
    console.print("  Real vs Synthetic: Should be LOW (<0.3) - synthetic pages resemble real pages")


def display_synthetic_samples(results: dict[str, Any], max_samples: int = 2):
    """Display sample synthetic pages."""
    console.print("\n[bold yellow]Sample Synthetic Pages[/bold yellow]")
    console.print("[dim](All outputs are explicitly labeled SYNTHETIC)[/dim]\n")

    for gap_id, result in results.items():
        console.print(f"[cyan]Gap: {gap_id}[/cyan]")

        for page in result.pages[:max_samples]:
            console.print(Panel(
                f"[bold]{page.get_label()}[/bold]\n\n"
                f"Jar Count: {page.jar_count}\n"
                f"Content Hash: {page.content_hash}\n"
                f"Constraints Satisfied: {page.constraints_satisfied}\n\n"
                f"[dim]Sample text (first jar):[/dim]\n"
                f"{' '.join(page.text_blocks[0][:15]) if page.text_blocks else 'N/A'}...",
                border_style="yellow",
            ))


def display_success_evaluation(findings: Phase3Findings):
    """Display Phase 3 success evaluation."""
    success = findings.phase_3_successful

    if success:
        console.print(Panel(
            "[bold green]Phase 3 SUCCESS[/bold green]\n\n"
            f"At least one gap filled: {findings.at_least_one_gap_filled}\n"
            f"Non-uniqueness demonstrated: {findings.non_uniqueness_demonstrated}\n"
            f"No semantics required: {findings.no_semantics_required}\n\n"
            "[dim]Structurally admissible pages can be generated for insertion windows\n"
            "using only non-semantic constraints. Multiple distinct continuations\n"
            "satisfy all constraints, demonstrating that missing pages are not\n"
            "privileged carriers of meaning.[/dim]",
            title="Phase 3 Evaluation",
            border_style="green",
        ))
    else:
        console.print(Panel(
            "[bold yellow]Phase 3 INCONCLUSIVE[/bold yellow]\n\n"
            f"At least one gap filled: {findings.at_least_one_gap_filled}\n"
            f"Non-uniqueness demonstrated: {findings.non_uniqueness_demonstrated}\n"
            f"No semantics required: {findings.no_semantics_required}\n\n"
            "[dim]Some success criteria were not fully met.[/dim]",
            title="Phase 3 Evaluation",
            border_style="yellow",
        ))


@app.command()
def main(
    pages_per_gap: int = typer.Option(
        15, "--pages", "-p",
        help="Number of synthetic pages to generate per gap"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v",
        help="Show detailed output including sample pages"
    ),
):
    """Execute Phase 3: Pharmaceutical Section Continuation Synthesis."""

    console.print(Panel.fit(
        "[bold blue]Phase 3: Pharmaceutical Section Continuation Synthesis[/bold blue]\n"
        "[dim]Gap-Constrained Structural Indistinguishability Study[/dim]\n\n"
        "[yellow]All synthetic outputs are explicitly labeled SYNTHETIC[/yellow]",
        border_style="blue"
    ))

    findings = Phase3Findings()

    # ============================================================
    # EXTRACT SECTION PROFILE
    # ============================================================
    console.print("\n[bold yellow]Step 1: Extracting Section Profile[/bold yellow]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Extracting pharmaceutical section profile...", total=None)

        extractor = PharmaceuticalProfileExtractor()
        section_profile = extractor.extract_section_profile()
        gaps = extractor.define_gaps()

        findings.section_profile = section_profile
        findings.gaps = gaps

        progress.update(task, completed=True)

    profile_summary = extractor.get_profile_summary()
    display_section_profile(profile_summary)

    # ============================================================
    # DEFINE GAPS
    # ============================================================
    console.print("\n[bold yellow]Step 2: Defining Insertion Windows[/bold yellow]")

    gap_summaries = []
    for gap in gaps:
        gap_summaries.append({
            "gap_id": gap.gap_id,
            "strength": gap.strength.value,
            "preceding_page": gap.preceding_page,
            "following_page": gap.following_page,
            "likely_pages_lost": gap.likely_pages_lost,
            "evidence_count": len(gap.evidence),
        })

    display_gaps(gap_summaries)

    # ============================================================
    # TRACK 3A & 3B: GENERATE CONTINUATIONS
    # ============================================================
    console.print("\n[bold yellow]Step 3: Generating Continuations (Track 3A & 3B)[/bold yellow]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating synthetic pages...", total=None)

        multi_gap = MultiGapContinuation(section_profile, gaps)
        continuation_results = multi_gap.run_all(pages_per_gap=pages_per_gap)

        findings.continuation_results = continuation_results

        progress.update(task, completed=True)

    display_continuation_results(continuation_results)

    if verbose:
        display_synthetic_samples(continuation_results)

    # ============================================================
    # INDISTINGUISHABILITY TESTING
    # ============================================================
    console.print("\n[bold yellow]Step 4: Indistinguishability Testing[/bold yellow]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running indistinguishability tests...", total=None)

        # Prepare pages for testing
        gap_pages = {
            gap_id: result.pages
            for gap_id, result in continuation_results.items()
        }

        tester = FullIndistinguishabilityTest(section_profile)
        indist_results = tester.run(gap_pages)

        findings.indistinguishability_results = indist_results

        progress.update(task, completed=True)

    indist_summary = tester.get_summary()
    display_indistinguishability_results(indist_summary)

    # ============================================================
    # EVALUATE SUCCESS
    # ============================================================
    console.print("\n[bold yellow]Step 5: Evaluating Success Criteria[/bold yellow]")

    findings.evaluate_success()
    display_success_evaluation(findings)

    # ============================================================
    # SUMMARY
    # ============================================================
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]Phase 3 Summary[/bold green]",
        border_style="green"
    ))

    summary = findings.generate_summary()

    console.print(f"\n[bold]Section:[/bold] {summary['section']}")
    console.print(f"[bold]Gaps Analyzed:[/bold] {summary['gaps_analyzed']}")
    console.print(f"[bold]Gaps Successfully Filled:[/bold] {summary['gaps_filled']}")
    console.print(f"[bold]Total Synthetic Pages:[/bold] {summary['total_synthetic_pages']}")
    console.print(f"[bold]Non-Uniqueness Demonstrated:[/bold] {summary['non_uniqueness_demonstrated']}")
    console.print(f"[bold]No Semantics Required:[/bold] {summary['no_semantics_required']}")
    console.print(f"\n[bold]Phase 3 Successful:[/bold] {summary['phase_3_successful']}")

    console.print("\n[dim]Phase 3 Complete[/dim]")

    return {
        "summary": summary,
        "continuation_results": {
            gap_id: {
                "pages_generated": len(r.pages),
                "unique_pages": r.unique_pages,
                "demonstrates_non_uniqueness": r.demonstrates_non_uniqueness,
            }
            for gap_id, r in continuation_results.items()
        },
        "indistinguishability": indist_summary,
    }


if __name__ == "__main__":
    app()
