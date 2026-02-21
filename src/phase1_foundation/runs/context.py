import json
import logging
import subprocess
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from phase1_foundation.core.ids import RunID

logger = logging.getLogger(__name__)

def get_git_revision_hash() -> str:
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except Exception:
        logger.debug("Git revision unavailable", exc_info=True)
        return "unknown"

def get_git_status() -> str:
    try:
        return subprocess.check_output(['git', 'status', '--porcelain']).decode('ascii').strip()
    except Exception:
        logger.debug("Git status unavailable", exc_info=True)
        return "unknown"

class RunContext(BaseModel):
    """
    Captures the full provenance context of an execution run.
    """
    # run_id is intentionally required: callers should construct RunContext
    # through RunManager.start_run(), which supplies deterministic seed linkage.
    run_id: RunID
    timestamp_start: datetime = Field(default_factory=lambda: datetime.now(UTC))
    timestamp_end: datetime | None = None
    git_commit: str = Field(default_factory=get_git_revision_hash)
    git_dirty: bool = Field(default_factory=lambda: bool(get_git_status()))
    command_line: list[str] = Field(default_factory=lambda: sys.argv)
    config: dict[str, Any] = Field(default_factory=dict)
    user: str = Field(default="unknown") # Could get from env or os
    status: str = "running"

    input_assets: list[dict[str, str]] = Field(default_factory=list)
    output_assets: list[dict[str, str]] = Field(default_factory=list)
    completion_callbacks: list[Callable[["RunContext"], None]] = Field(
        default_factory=list, exclude=True, repr=False
    )
    completion_callback_keys: list[str] = Field(
        default_factory=list, exclude=True, repr=False
    )

    def add_input_asset(self, path: str, checksum: str):
        self.input_assets.append({"path": path, "checksum": checksum})

    def add_output_asset(self, path: str, checksum: str, type: str):
        self.output_assets.append({"path": path, "checksum": checksum, "type": type})

    def add_completion_callback(
        self, key: str, callback: Callable[["RunContext"], None]
    ) -> None:
        """Register an idempotent callback executed when run status is finalized."""
        if key in self.completion_callback_keys:
            return
        self.completion_callback_keys.append(key)
        self.completion_callbacks.append(callback)

    def complete(self, status: str = "success") -> None:
        self.timestamp_end = datetime.now(UTC)
        self.status = status
        for callback in list(self.completion_callbacks):
            try:
                callback(self)
            except Exception:
                logger.exception("Run completion callback failed")
        self._write_artifacts()

    def _write_artifacts(self):
        """Write provenance artifacts to the run directory."""
        # Ensure runs directory exists
        run_dir = Path("runs") / str(self.run_id)
        run_dir.mkdir(parents=True, exist_ok=True)

        # 1. run.json - Execution metadata
        run_meta = {
            "run_id": str(self.run_id),
            "status": self.status,
            "timestamp_start": self.timestamp_start.isoformat(),
            "timestamp_end": self.timestamp_end.isoformat() if self.timestamp_end else None,
            "git_commit": self.git_commit,
            "git_dirty": self.git_dirty,
            "command_line": self.command_line,
            "user": self.user,
        }
        with open(run_dir / "run.json", "w") as f:
            json.dump(run_meta, f, indent=2)

        # 2. config.json - Configuration used
        with open(run_dir / "config.json", "w") as f:
            json.dump(self.config, f, indent=2)

        # 3. inputs.json - Input provenance
        with open(run_dir / "inputs.json", "w") as f:
            json.dump({"inputs": self.input_assets}, f, indent=2)

        # 4. outputs.json - Output provenance
        with open(run_dir / "outputs.json", "w") as f:
            json.dump({"outputs": self.output_assets}, f, indent=2)

        # 5. manifest.json - Aggregate (for backward compatibility)
        with open(run_dir / "manifest.json", "w") as f:
            f.write(self.model_dump_json(indent=2))

    model_config = ConfigDict(arbitrary_types_allowed=True)
