import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from foundation.runs.manager import RunManager
import logging
logger = logging.getLogger(__name__)

class ProvenanceWriter:
    """Standardized result writer that includes execution provenance."""
    
    @staticmethod
    def save_results(results: Any, output_path: str | Path):
        """Save results to JSON with run_id, git_commit, and timestamp."""
        try:
            json.dumps(results)
        except TypeError as exc:
            raise ValueError(f"Results must be JSON-serializable: {exc}") from exc

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        provenance = {}
        try:
            run = RunManager.get_current_run()
            provenance["run_id"] = str(run.run_id)
            provenance["git_commit"] = run.git_commit
            provenance["timestamp"] = run.timestamp_start.isoformat()
        except RuntimeError:
            # Fallback if no active run
            provenance["run_id"] = "none"
            provenance["timestamp"] = datetime.now(timezone.utc).isoformat()
            
        data = {
            "provenance": provenance,
            "results": results
        }
        
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
