#!/usr/bin/env python3
"""Build Phase 18 page-generation assets for workbench.

Generates:
1) folio_state_schedule.json
2) page_priors.json
"""

import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase18_comparative.assets import FolioAssetBuilder  # noqa: E402

MASK_INFERENCE_PATH = (
    project_root / "results/data/phase14_machine/mask_inference.json"
)
MASK_PREDICTION_PATH = (
    project_root / "results/data/phase14_machine/mask_prediction.json"
)
FOLIO_SOURCE_PATH = (
    project_root / "data/raw/transliterations/ivtff2.0/ZL3b-n.txt"
)
OUTPUT_DIR = project_root / "results/data/phase18_comparative"
SCHEDULE_OUT = OUTPUT_DIR / "folio_state_schedule.json"
PRIORS_OUT = OUTPUT_DIR / "page_priors.json"

def load_results(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload.get("results"), dict):
        return payload["results"]
    return payload

def main() -> None:
    for required in [MASK_INFERENCE_PATH, MASK_PREDICTION_PATH, FOLIO_SOURCE_PATH]:
        if not required.exists():
            raise FileNotFoundError(f"Missing required input: {required}")

    mask_inference = load_results(MASK_INFERENCE_PATH)
    mask_prediction = load_results(MASK_PREDICTION_PATH)
    
    builder = FolioAssetBuilder()
    folio_lines = builder.parse_folio_lines(FOLIO_SOURCE_PATH)

    schedule_payload = builder.build_folio_schedule(
        folio_lines=folio_lines,
        mask_inference=mask_inference,
        mask_prediction=mask_prediction,
        folio_source_path=str(FOLIO_SOURCE_PATH.relative_to(project_root))
    )
    priors_payload = builder.build_page_priors(
        folio_lines=folio_lines,
        folio_source_path=str(FOLIO_SOURCE_PATH.relative_to(project_root))
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ProvenanceWriter.save_results(schedule_payload, SCHEDULE_OUT)
    ProvenanceWriter.save_results(priors_payload, PRIORS_OUT)

    print("Built Phase 18 assets:")
    print(f"  - {SCHEDULE_OUT}")
    print(f"  - {PRIORS_OUT}")
    print(
        "Summary: "
        f"folios={schedule_payload['summary']['folio_count']}, "
        f"lines={schedule_payload['summary']['line_count']}, "
        f"global_fallback_folios={schedule_payload['summary']['global_fallback_folios']}"
    )

if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "build_page_generation_assets"}):
        main()
