from __future__ import annotations

from phase10_admissibility.stage3_pipeline import (
    evaluate_stage3_priority_gate,
    summarize_stage3,
)


def test_stage3_priority_gate_is_urgent_when_stage2_not_fully_strengthened() -> None:
    gate = evaluate_stage3_priority_gate(
        stage1_summary={"method_decisions": {"H": "closure_strengthened"}},
        stage2_summary={
            "method_decisions": {"G": "indeterminate", "I": "closure_strengthened"}
        },
    )
    assert gate["priority"] == "urgent"


def test_stage3_priority_gate_is_lower_when_stage2_both_strengthened() -> None:
    gate = evaluate_stage3_priority_gate(
        stage1_summary={"method_decisions": {"H": "closure_strengthened"}},
        stage2_summary={
            "method_decisions": {
                "G": "closure_strengthened",
                "I": "closure_strengthened",
            }
        },
    )
    assert gate["priority"] == "lower"


def test_summarize_stage3_uses_method_f_decision() -> None:
    summary = summarize_stage3(
        priority_gate={"priority": "urgent"},
        method_f_result={"decision": "indeterminate"},
    )
    assert summary["stage"] == "10.3"
    assert summary["priority"] == "urgent"
    assert summary["stage_decision"] == "indeterminate"
    assert summary["method_decisions"]["F"] == "indeterminate"

