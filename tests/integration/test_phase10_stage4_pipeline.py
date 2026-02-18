from __future__ import annotations

from phase10_admissibility.stage4_pipeline import (
    Stage4Config,
    interpret_priority_urgent,
    synthesize_stage4,
)


def test_stage4_synthesis_mixed_results_in_tension() -> None:
    synthesis = synthesize_stage4(
        config=Stage4Config(),
        stage1_summary={
            "method_decisions": {
                "H": "closure_strengthened",
                "J": "closure_weakened",
                "K": "closure_weakened",
            }
        },
        stage1b_replication={
            "method_j_status_after_gate": "closure_weakened",
            "method_k_status_after_gate": "closure_weakened",
        },
        stage2_summary={
            "method_decisions": {
                "G": "indeterminate",
                "I": "closure_strengthened",
            }
        },
        stage3_summary={"method_decisions": {"F": "indeterminate"}},
        stage3_priority_gate={"priority": "urgent", "reason": "mixed early-stage signals"},
    )
    assert synthesis["aggregate_class"] == "mixed_results_tension"
    assert synthesis["closure_status"] == "in_tension"
    assert synthesis["method_decisions"]["F"] == "indeterminate"


def test_urgent_interpretation_is_priority_not_verdict() -> None:
    urgency = interpret_priority_urgent(
        stage3_priority_gate={"priority": "urgent", "reason": "gate"},
        stage1_summary={"method_decisions": {"J": "closure_weakened"}},
        stage2_summary={"method_decisions": {"G": "indeterminate", "I": "closure_strengthened"}},
    )
    assert urgency["priority"] == "urgent"
    assert "not itself evidence" in urgency["meaning"]
