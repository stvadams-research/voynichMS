#!/usr/bin/env python3
"""
Phase 7B: Codicological and Material Constraints Runner
"""

import sys
import json
from pathlib import Path
from collections import defaultdict
from typing import Any, Dict

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import MetadataStore, TranscriptionTokenRecord, TranscriptionLineRecord, PageRecord
from phase1_foundation.core.provenance import ProvenanceWriter
from phase7_human.page_boundary import PageBoundaryAnalyzer
from phase7_human.quire_analysis import QuireAnalyzer
from phase7_human.scribe_coupling import ScribeAnalyzer

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
MULTIMODAL_STATUS_PATH = Path("results/phase5_mechanism/anchor_coupling_confirmatory.json")


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_results(payload: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(payload.get("results"), dict):
        return payload["results"]
    return payload


def summarize_illustration_coupling(status_payload: Dict[str, Any] | None) -> Dict[str, Any]:
    if not status_payload:
        return {
            "status": "MISSING_ARTIFACT",
            "conclusive": False,
            "h1_4_closure_lane": "H1_4_INCONCLUSIVE",
            "h1_5_closure_lane": "H1_5_INCONCLUSIVE",
            "robustness_class": "UNKNOWN",
            "entitlement_robustness_class": "UNKNOWN",
            "statement": (
                "Illustration-coupling artifact is missing; no coupling claim is licensed."
            ),
            "allowed_claim": (
                "No conclusive statement about illustration coupling is available."
            ),
        }

    status = str(status_payload.get("status", "UNKNOWN"))
    h1_4_closure_lane = str(status_payload.get("h1_4_closure_lane", "H1_4_INCONCLUSIVE"))
    raw_h1_5_closure_lane = status_payload.get("h1_5_closure_lane")
    if isinstance(raw_h1_5_closure_lane, str) and raw_h1_5_closure_lane.strip():
        h1_5_closure_lane = raw_h1_5_closure_lane.strip()
    elif "h1_4_closure_lane" in status_payload:
        if h1_4_closure_lane == "H1_4_ALIGNED":
            h1_5_closure_lane = "H1_5_ALIGNED"
        elif h1_4_closure_lane == "H1_4_QUALIFIED":
            h1_5_closure_lane = "H1_5_QUALIFIED"
        elif h1_4_closure_lane == "H1_4_BLOCKED":
            h1_5_closure_lane = "H1_5_BLOCKED"
        else:
            h1_5_closure_lane = "H1_5_INCONCLUSIVE"
    elif status.startswith("CONCLUSIVE_"):
        h1_5_closure_lane = "H1_5_ALIGNED"
    else:
        h1_5_closure_lane = "H1_5_INCONCLUSIVE"
    robustness = status_payload.get("robustness")
    robustness_class = "UNKNOWN"
    entitlement_robustness_class = "UNKNOWN"
    if isinstance(robustness, dict):
        robustness_class = str(robustness.get("robustness_class", "UNKNOWN"))
        entitlement_robustness_class = str(
            robustness.get("entitlement_robustness_class", robustness_class)
        )
    allowed_claim = str(
        status_payload.get(
            "allowed_claim",
            "No conclusive statement about illustration coupling is available.",
        )
    )
    conclusive = status.startswith("CONCLUSIVE_") and h1_5_closure_lane == "H1_5_ALIGNED"

    if status == "CONCLUSIVE_NO_COUPLING":
        if h1_5_closure_lane == "H1_5_BOUNDED":
            statement = (
                "Confirmatory coupling phase2_analysis did not detect a robust illustration/layout "
                "coupling signal in entitlement lanes, robustness remains qualified across "
                "registered lanes, and diagnostic lanes remain non-conclusive monitoring signals; "
                "no claim is allowed beyond bounded entitlement scope."
            )
        elif h1_4_closure_lane == "H1_4_QUALIFIED":
            statement = (
                "Confirmatory coupling phase2_analysis did not detect a robust illustration/layout "
                "coupling signal in the canonical lane, but robustness remains qualified "
                "across registered lanes; no conclusive claim is allowed beyond canonical "
                "lane scope."
            )
        else:
            statement = (
                "Confirmatory coupling phase2_analysis did not detect a robust illustration/layout "
                "coupling signal under configured adequacy criteria."
            )
    elif status == "CONCLUSIVE_COUPLING_PRESENT":
        statement = (
            "Confirmatory coupling phase2_analysis detected a coupling signal; interpretation "
            "must remain structural and non-semantic."
        )
    elif status == "BLOCKED_DATA_GEOMETRY":
        statement = (
            "Coupling phase2_analysis is blocked by cohort geometry/data constraints; "
            "no conclusive claim is allowed."
        )
    elif status == "INCONCLUSIVE_UNDERPOWERED":
        statement = (
            "Coupling phase2_analysis remains underpowered due adequacy constraints; "
            "no conclusive claim is allowed."
        )
    elif status == "INCONCLUSIVE_INFERENTIAL_AMBIGUITY":
        statement = (
            "Coupling phase2_analysis meets adequacy thresholds but remains inferentially ambiguous; "
            "no conclusive claim is allowed."
        )
    else:
        statement = (
            "Coupling status is unknown; no conclusive statement is allowed."
        )

    return {
        "status": status,
        "conclusive": conclusive,
        "h1_4_closure_lane": h1_4_closure_lane,
        "h1_5_closure_lane": h1_5_closure_lane,
        "robustness_class": robustness_class,
        "entitlement_robustness_class": entitlement_robustness_class,
        "statement": statement,
        "allowed_claim": allowed_claim,
    }

def get_pages_data(store, dataset_id="voynich_real"):
    session = store.Session()
    try:
        recs = (
            session.query(
                PageRecord.id, 
                TranscriptionLineRecord.line_index,
                TranscriptionLineRecord.id.label("line_id")
            )
            .join(TranscriptionLineRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == dataset_id)
            .filter(TranscriptionLineRecord.source_id == "zandbergen_landini")
            .order_by(PageRecord.id, TranscriptionLineRecord.line_index)
            .all()
        )
        
        token_recs = (
            session.query(TranscriptionTokenRecord.content, TranscriptionTokenRecord.line_id)
            .join(TranscriptionLineRecord, TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
            .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == dataset_id)
            .filter(TranscriptionLineRecord.source_id == "zandbergen_landini")
            .all()
        )
        
        tokens_by_line = defaultdict(list)
        for content, line_id in token_recs:
            tokens_by_line[line_id].append(content)
            
        pages = defaultdict(list)
        for page_id, line_idx, line_id in recs:
            pages[page_id].append(tokens_by_line[line_id])
            
        return pages
    finally:
        session.close()

def run_phase_7b():
    console.print(Panel.fit(
        "[bold blue]Phase 7B: Codicological and Material Constraints[/bold blue]\n"
        "Testing coupling between text generation and physical manuscript structure.",
        border_style="blue"
    ))

    with active_run(config={"command": "run_7b_codicology", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        
        # 1. Prepare Data
        console.print("\n[bold cyan]Step 1: Preparing Data[/bold cyan]")
        pages = get_pages_data(store)
        console.print(f"Loaded {len(pages)} pages.")
        
        # 2. Page Boundary Adaptation
        console.print("\n[bold cyan]Step 2: Analyzing Page Boundaries[/bold cyan]")
        boundary_analyzer = PageBoundaryAnalyzer()
        boundary_res = boundary_analyzer.analyze_boundary_adaptation(pages)
        layout_res = boundary_analyzer.analyze_layout_obstruction(pages)
        
        # 3. Quire Boundary Analysis
        console.print("\n[bold cyan]Step 3: Analyzing Quire Boundaries[/bold cyan]")
        quire_analyzer = QuireAnalyzer()
        quire_res = quire_analyzer.analyze_continuity(pages)
        
        # 4. Scribal Hand Coupling
        console.print("\n[bold cyan]Step 4: Analyzing Scribal Hands[/bold cyan]")
        scribe_analyzer = ScribeAnalyzer()
        scribe_res = scribe_analyzer.analyze_hand_coupling(pages)

        # 5. Multimodal coupling evidence grade
        console.print("\n[bold cyan]Step 5: Reading Illustration-Coupling Grade[/bold cyan]")
        multimodal_raw = _extract_results(_load_json(MULTIMODAL_STATUS_PATH))
        multimodal_res = summarize_illustration_coupling(multimodal_raw)
        
        # 6. Display Results
        table = Table(title="Phase 7B: Codicological Constraints Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        
        table.add_row("Line Len / Pos Correlation", f"{boundary_res['line_length_pos_correlation']:.4f}")
        table.add_row("Boundary Effect Detected", str(boundary_res['boundary_effect_detected']))
        table.add_row("Layout Coefficient of Var", f"{layout_res['mean_coefficient_of_variation']:.4f}")
        table.add_row("Between-Quire Variance", f"{quire_res['between_quire_variance']:.6f}")
        table.add_row("Illustration Coupling Grade", multimodal_res["status"])
        
        for hand, stats in scribe_res.items():
            table.add_row(f"{hand} Mean TTR (Page)", f"{stats['mean_ttr']:.4f}")
            
        console.print(table)
        
        # 7. Save Artifacts
        output_dir = Path("results/phase7_human")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            "page_boundary": boundary_res,
            "layout": layout_res,
            "quire": quire_res,
            "scribe": scribe_res,
            "illustration_coupling": multimodal_res,
        }
        
        ProvenanceWriter.save_results(results, output_dir / "phase_7b_results.json")
            
        # Generate Report
        report_path = Path("results/reports/phase7_human/PHASE_7B_RESULTS.md")
        with open(report_path, "w") as f:
            f.write("# PHASE 7B RESULTS: CODICOLOGICAL CONSTRAINTS\n\n")
            f.write("## Page Boundary and Layout Adaptation\n\n")
            f.write(f"- **Line Length Position Correlation:** {boundary_res['line_length_pos_correlation']:.4f}\n")
            f.write(f"- **Boundary Effect Detected:** {boundary_res['boundary_effect_detected']}\n")
            f.write(f"- **Layout Coefficient of Variation:** {layout_res['mean_coefficient_of_variation']:.4f}\n")
            f.write("  - *Interpretation:* A correlation suggests in-situ adaptation (H7B.1).\n\n")
            
            f.write("## Quire Continuity\n\n")
            f.write(f"- **Between-Quire Variance (Mean Word Len):** {quire_res['between_quire_variance']:.6f}\n")
            f.write(f"- **Number of Quires Analyzed:** {quire_res['num_quires']}\n\n")
            
            f.write("## Scribal Hand Coupling\n\n")
            for hand, stats in scribe_res.items():
                f.write(f"- **{hand}:** Mean TTR = {stats['mean_ttr']:.4f} (n={stats['sample_size_pages']} pages)\n")

            f.write("\n## Illustration Proximity Evidence Grade\n\n")
            f.write(f"- **Status:** {multimodal_res['status']}\n")
            f.write(f"- **H1.4 Closure Lane:** {multimodal_res['h1_4_closure_lane']}\n")
            f.write(f"- **H1.5 Closure Lane:** {multimodal_res['h1_5_closure_lane']}\n")
            f.write(f"- **Robustness Class:** {multimodal_res['robustness_class']}\n")
            f.write(
                "- **Entitlement Robustness Class:** "
                f"{multimodal_res['entitlement_robustness_class']}\n"
            )
            f.write(f"- **Interpretation:** {multimodal_res['statement']}\n")
            f.write(f"- **Allowed Claim:** {multimodal_res['allowed_claim']}\n")
            
            f.write("\n## Final Determination\n\n")
            if boundary_res['boundary_effect_detected']:
                f.write("- **H7B.1 Supported:** Measurable coupling between text geometry and page boundaries suggests in-situ generation.\n")
            else:
                f.write("- **H7B.2 Supported:** Lack of significant boundary adaptation suggests the text may have been copied from an external source.\n")
            f.write(
                "- **Illustration-Coupling Guardrail:** "
                f"{multimodal_res['statement']}\n"
            )

        store.save_run(run)
        console.print(f"\n[bold green]Run complete. Results saved to {output_dir}[/bold green]")

if __name__ == "__main__":
    run_phase_7b()
