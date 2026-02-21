import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from phase1_foundation.runs.manager import RunManager

logger = logging.getLogger(__name__)

class ProvenanceWriter:
    """Standardized result writer that includes execution provenance.

    Outputs are written to:
    1) an immutable run-scoped snapshot under ``<parent>/by_run/``
    2) the caller-provided path as a backward-compatible "latest" pointer file.
    """

    @staticmethod
    def _get_provenance() -> dict[str, Any]:
        """Capture provenance for the active run, if available."""
        try:
            run = RunManager.get_current_run()
            provenance: dict[str, Any] = {
                "run_id": str(run.run_id),
                "git_commit": run.git_commit,
                "timestamp": run.timestamp_start.isoformat(),
            }
            for key in ("seed", "experiment_id", "run_nonce", "command"):
                if key in run.config:
                    provenance[key] = run.config[key]
            return provenance
        except RuntimeError:
            # Fallback if no active run
            return {
                "run_id": "none",
                "timestamp": datetime.now(UTC).isoformat(),
            }

    @staticmethod
    def _build_snapshot_path(output_path: Path, snapshot_id: str) -> Path:
        """Return run-scoped output path for immutable history."""
        history_dir = output_path.parent / "by_run"
        history_dir.mkdir(parents=True, exist_ok=True)
        return history_dir / f"{output_path.stem}.{snapshot_id}{output_path.suffix}"

    @staticmethod
    def save_results(results: Any, output_path: str | Path, write_latest: bool = True) -> dict[str, str]:
        """Save results with provenance and immutable run-scoped history."""
        try:
            json.dumps(results)
        except TypeError as exc:
            raise ValueError(f"Results must be JSON-serializable: {exc}") from exc

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        provenance = ProvenanceWriter._get_provenance()
        data = {
            "provenance": provenance,
            "results": results
        }

        snapshot_id = str(provenance.get("run_id", "none"))
        if snapshot_id == "none":
            snapshot_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        snapshot_path = ProvenanceWriter._build_snapshot_path(output_path, snapshot_id)

        with open(snapshot_path, "w") as f:
            json.dump(data, f, indent=2)

        if write_latest:
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)

        return {
            "snapshot_path": str(snapshot_path),
            "latest_path": str(output_path),
        }
