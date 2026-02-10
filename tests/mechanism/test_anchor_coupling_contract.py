from pathlib import Path


def test_anchor_coupling_script_emits_required_contract_fields() -> None:
    script = Path("scripts/mechanism/run_5i_anchor_coupling.py").read_text(
        encoding="utf-8"
    )
    module = Path("src/mechanism/anchor_coupling.py").read_text(encoding="utf-8")
    assert "anchor_coupling_confirmatory.json" in script
    assert "\"status\"" in script
    assert "\"status_reason\"" in script
    assert "\"allowed_claim\"" in script
    assert "\"h1_4_closure_lane\"" in script
    assert "\"h1_4_residual_reason\"" in script
    assert "\"h1_4_reopen_conditions\"" in script
    assert "\"h1_5_closure_lane\"" in script
    assert "\"h1_5_residual_reason\"" in script
    assert "\"h1_5_reopen_conditions\"" in script
    assert "\"adequacy\"" in script
    assert "\"inference\"" in script
    assert "\"robustness\"" in script
    assert "\"robustness_matrix\"" in script
    assert "\"p_value\"" in script
    assert "\"delta_ci_low\"" in script
    assert "\"delta_ci_high\"" in script
    assert "CONCLUSIVE_NO_COUPLING" in module
    assert "CONCLUSIVE_COUPLING_PRESENT" in module
    assert "INCONCLUSIVE_UNDERPOWERED" in module
    assert "INCONCLUSIVE_INFERENTIAL_AMBIGUITY" in module
    assert "BLOCKED_DATA_GEOMETRY" in module
    assert "H1_4_ALIGNED" in module
    assert "H1_4_QUALIFIED" in module
    assert "H1_5_ALIGNED" in module
    assert "H1_5_BOUNDED" in module
    assert "H1_5_QUALIFIED" in module
    assert "ROBUSTNESS_CLASS_MIXED" in module


def test_coverage_audit_script_writes_machine_readable_output() -> None:
    script = Path("scripts/mechanism/audit_anchor_coverage.py").read_text(
        encoding="utf-8"
    )
    assert "status/mechanism/anchor_coverage_audit.json" in script
    assert "token_anchor_ratio" in script
    assert "token_balance_ratio" in script
    assert "relation_type_counts" in script
