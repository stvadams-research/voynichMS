from phase1_foundation.core.ids import RunID, PageID
import json
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

def generate_run_summary(run_id: RunID):
    """
    Generate a summary report for a completed run.
    """
    logger.info("Generating summary for run %s...", run_id)
    run_dir = Path("runs") / str(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    run_meta_path = run_dir / "run.json"
    inputs_path = run_dir / "inputs.json"
    outputs_path = run_dir / "outputs.json"

    run_meta = {}
    inputs = {"inputs": []}
    outputs = {"outputs": []}

    if run_meta_path.exists():
        with open(run_meta_path, "r") as f:
            run_meta = json.load(f)
    if inputs_path.exists():
        with open(inputs_path, "r") as f:
            inputs = json.load(f)
    if outputs_path.exists():
        with open(outputs_path, "r") as f:
            outputs = json.load(f)

    summary_path = run_dir / "summary.md"
    with open(summary_path, "w") as f:
        f.write(f"# Run Summary: {run_id}\n\n")
        f.write(f"- Status: {run_meta.get('status', 'unknown')}\n")
        f.write(f"- Started: {run_meta.get('timestamp_start', 'unknown')}\n")
        f.write(f"- Ended: {run_meta.get('timestamp_end', 'unknown')}\n")
        f.write(f"- Git Commit: {run_meta.get('git_commit', 'unknown')}\n")
        f.write(f"- Inputs: {len(inputs.get('inputs', []))}\n")
        f.write(f"- Outputs: {len(outputs.get('outputs', []))}\n")

    return summary_path

def generate_overlays(page_id: PageID):
    """
    Record overlay-generation intent for a page.
    """
    logger.info("Generating overlays for page %s...", page_id)
    output_dir = Path("core_status/qc/overlays")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{page_id}.json"
    payload = {
        "page_id": str(page_id),
        "status": "not_rendered",
        "reason": "Overlay rendering backend is not part of this repository build.",
    }
    with open(output_path, "w") as f:
        json.dump(payload, f, indent=2)
    return output_path
