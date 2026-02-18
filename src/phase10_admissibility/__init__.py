"""Phase 10 admissibility workflows."""

from .stage1_pipeline import (
    CorpusBundle,
    Stage1Config,
    build_reference_generators,
    build_stage1_markdown,
    load_dataset_bundle,
    now_utc_iso,
    run_method_h,
    run_method_j,
    run_method_k,
    summarize_stage1,
)
from .stage2_pipeline import (
    Stage2Config,
    build_cross_linguistic_manifest,
    build_illustration_features,
    build_stage2_markdown,
    run_method_g,
    run_method_i,
    scan_data_resource_inventory,
    summarize_stage2,
)
from .stage3_pipeline import (
    Stage3Config,
    build_stage3_markdown,
    evaluate_stage3_priority_gate,
    run_method_f,
    summarize_stage3,
)
from .stage4_pipeline import (
    Stage4Config,
    build_phase10_closure_update_markdown,
    build_phase10_results_markdown,
    interpret_priority_urgent,
    synthesize_stage4,
)

__all__ = [
    "CorpusBundle",
    "Stage1Config",
    "build_reference_generators",
    "build_stage1_markdown",
    "load_dataset_bundle",
    "now_utc_iso",
    "run_method_h",
    "run_method_j",
    "run_method_k",
    "summarize_stage1",
    "Stage2Config",
    "scan_data_resource_inventory",
    "build_illustration_features",
    "build_cross_linguistic_manifest",
    "run_method_g",
    "run_method_i",
    "summarize_stage2",
    "build_stage2_markdown",
    "Stage3Config",
    "evaluate_stage3_priority_gate",
    "run_method_f",
    "summarize_stage3",
    "build_stage3_markdown",
    "Stage4Config",
    "synthesize_stage4",
    "interpret_priority_urgent",
    "build_phase10_results_markdown",
    "build_phase10_closure_update_markdown",
]
