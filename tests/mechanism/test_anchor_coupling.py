from mechanism.anchor_coupling import (
    STATUS_BLOCKED_DATA_GEOMETRY,
    STATUS_CONCLUSIVE_COUPLING_PRESENT,
    STATUS_CONCLUSIVE_NO_COUPLING,
    STATUS_INCONCLUSIVE_UNDERPOWERED,
    classify_line_cohort,
    decide_status,
    evaluate_adequacy,
    evaluate_inference,
)


def test_classify_line_cohort_respects_ratio_thresholds() -> None:
    assert (
        classify_line_cohort(
            [True, True, False, True],
            anchored_ratio_min=0.5,
            unanchored_ratio_max=0.1,
        )
        == "anchored"
    )
    assert (
        classify_line_cohort(
            [False, False, False, True],
            anchored_ratio_min=0.8,
            unanchored_ratio_max=0.25,
        )
        == "unanchored"
    )
    assert (
        classify_line_cohort(
            [True, False, True, False],
            anchored_ratio_min=0.75,
            unanchored_ratio_max=0.10,
        )
        == "ambiguous"
    )


def test_evaluate_adequacy_blocks_when_required_cohort_missing() -> None:
    adequacy = evaluate_adequacy(
        available_anchor_line_count=120,
        available_unanchored_line_count=0,
        anchored_page_count=20,
        unanchored_page_count=0,
        anchored_recurring_contexts=200,
        unanchored_recurring_contexts=0,
        policy={
            "min_lines_per_cohort": 40,
            "min_pages_per_cohort": 8,
            "min_recurring_contexts_per_cohort": 80,
            "min_balance_ratio": 0.2,
        },
    )
    assert adequacy["pass"] is False
    assert adequacy["blocked"] is True
    assert "no_unanchored_lines" in adequacy["reasons"]


def test_evaluate_adequacy_passes_when_thresholds_met() -> None:
    adequacy = evaluate_adequacy(
        available_anchor_line_count=150,
        available_unanchored_line_count=120,
        anchored_page_count=25,
        unanchored_page_count=19,
        anchored_recurring_contexts=250,
        unanchored_recurring_contexts=210,
        policy={
            "min_lines_per_cohort": 40,
            "min_pages_per_cohort": 8,
            "min_recurring_contexts_per_cohort": 80,
            "min_balance_ratio": 0.2,
        },
    )
    assert adequacy["pass"] is True
    assert adequacy["blocked"] is False
    assert adequacy["reasons"] == []


def test_inference_decision_and_status_mapping() -> None:
    no_coupling_inference = evaluate_inference(
        delta_mean_consistency=0.003,
        delta_ci_low=-0.012,
        delta_ci_high=0.011,
        p_value=0.42,
        policy={
            "alpha": 0.05,
            "coupling_delta_abs_min": 0.03,
            "no_coupling_delta_abs_max": 0.015,
        },
    )
    assert no_coupling_inference["decision"] == "NO_COUPLING"
    status_payload = decide_status(
        adequacy={"pass": True, "blocked": False},
        inference=no_coupling_inference,
    )
    assert status_payload["status"] == STATUS_CONCLUSIVE_NO_COUPLING

    coupling_inference = evaluate_inference(
        delta_mean_consistency=0.08,
        delta_ci_low=0.04,
        delta_ci_high=0.12,
        p_value=0.003,
        policy={
            "alpha": 0.05,
            "coupling_delta_abs_min": 0.03,
            "no_coupling_delta_abs_max": 0.015,
        },
    )
    assert coupling_inference["decision"] == "COUPLING_PRESENT"
    status_payload = decide_status(
        adequacy={"pass": True, "blocked": False},
        inference=coupling_inference,
    )
    assert status_payload["status"] == STATUS_CONCLUSIVE_COUPLING_PRESENT

    blocked_status = decide_status(
        adequacy={"pass": False, "blocked": True},
        inference={"decision": "INCONCLUSIVE"},
    )
    assert blocked_status["status"] == STATUS_BLOCKED_DATA_GEOMETRY

    underpowered_status = decide_status(
        adequacy={"pass": False, "blocked": False},
        inference={"decision": "INCONCLUSIVE"},
    )
    assert underpowered_status["status"] == STATUS_INCONCLUSIVE_UNDERPOWERED
