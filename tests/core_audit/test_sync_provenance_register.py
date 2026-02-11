import importlib.util
from pathlib import Path


def _load_sync_module():
    module_path = Path("scripts/core_audit/sync_provenance_register.py")
    spec = importlib.util.spec_from_file_location("sync_provenance_register", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sync_provenance_register_emits_sync_artifact_and_register(tmp_path) -> None:
    mod = _load_sync_module()
    register_path = tmp_path / "SK_M4_PROVENANCE_REGISTER.md"
    sync_status_path = tmp_path / "provenance_register_sync_status.json"
    payload = mod.sync_provenance_register(
        provenance_health_path=Path("core_status/core_audit/provenance_health_status.json").resolve(),
        repair_report_path=Path("core_status/core_audit/run_status_repair_report.json").resolve(),
        gate_health_path=Path("core_status/core_audit/release_gate_health_status.json").resolve(),
        db_path=Path("data/voynich.db").resolve(),
        register_path=register_path,
        sync_status_path=sync_status_path,
    )

    assert register_path.exists()
    assert sync_status_path.exists()
    assert payload.get("status") in {"IN_SYNC", "DRIFT_DETECTED"}
    assert "drift_detected" in payload
    assert "contract_coupling_state" in payload
    assert "provenance_health_lane" in payload
    assert "provenance_health_residual_reason" in payload
    assert "provenance_health_m4_5_lane" in payload
    assert "provenance_health_m4_5_residual_reason" in payload
    assert "provenance_health_m4_5_data_availability_linkage" in payload
    assert "health_orphaned_rows" in payload
    assert "register_orphaned_rows" in payload
