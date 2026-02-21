import contextlib
import os
import sys
import threading
import time
import json
from pathlib import Path
from typing import Any, Dict, Generator, Optional

from phase1_foundation.runs.context import RunContext
from phase1_foundation.core.ids import RunID
from phase1_foundation.core.id_factory import DeterministicIDFactory
from phase1_foundation.config import get_tracker
import logging
logger = logging.getLogger(__name__)


def capture_environment() -> Dict[str, Any]:
    """
    Capture environment details for reproducibility tracking.

    Returns a dict containing Python version and installed package versions.
    """
    env = {
        "python_version": sys.version,
        "platform": sys.platform,
    }

    # Try to get package versions
    try:
        import importlib.metadata
        packages = {}
        for dist in importlib.metadata.distributions():
            try:
                packages[dist.metadata["Name"]] = dist.version
            except Exception:
                logger.debug("Failed to capture package metadata entry", exc_info=True)
        env["packages"] = packages
    except ImportError:
        # Fallback for older Python versions
        try:
            import pkg_resources
            env["packages"] = {p.key: p.version for p in pkg_resources.working_set}
        except Exception:
            logger.debug("Failed to capture package metadata via pkg_resources", exc_info=True)
            env["packages"] = {}

    return env


class RunManager:
    """
    Thread-safe manager for run lifecycle.

    Uses thread-local storage to ensure each thread has its own run context,
    preventing race conditions in concurrent execution.
    """
    _thread_local = threading.local()

    @classmethod
    def _get_current_run(cls) -> Optional[RunContext]:
        """Get the current run for this thread."""
        return getattr(cls._thread_local, 'current_run', None)

    @classmethod
    def _set_current_run(cls, run: Optional[RunContext]) -> None:
        """Set the current run for this thread."""
        cls._thread_local.current_run = run

    @classmethod
    def start_run(cls, config: dict = None, capture_env: bool = True) -> RunContext:
        """
        Start a new run in the current thread.

        Args:
            config: Configuration dict for the run.
            capture_env: Whether to capture environment details (default True).

        Returns:
            The new RunContext.

        Raises:
            RuntimeError: If a run is already active in this thread.
        """
        if cls._get_current_run() is not None:
            raise RuntimeError("Run already active in this thread")

        run_config = config or {}

        # Capture environment if requested
        if capture_env:
            run_config["environment"] = capture_environment()

        # Generate deterministic RunID from seed or timestamp
        seed = run_config.get("seed")
        if seed is None:
            if os.environ.get("REQUIRE_COMPUTED", "0") == "1":
                raise RuntimeError(
                    "No seed provided to RunManager.start_run() while "
                    "REQUIRE_COMPUTED=1 is set. All runs must be explicitly "
                    "seeded for reproducibility. Pass config={'seed': <int>}."
                )
            # Fallback to timestamp-based seed for "unseeded" runs
            # This ensures we always have a RunID but it's traceable
            seed = int(time.time() * 1000)
            run_config["seed"] = seed
            run_config["unseeded_run"] = True

        # Run IDs must be unique per execution to prevent run record overwrite.
        # Keep deterministic experiment linkage separate via experiment_id.
        run_nonce = int(run_config.get("run_nonce", time.time_ns()))
        run_config["run_nonce"] = run_nonce
        run_config["experiment_id"] = str(RunID(seed=seed))
        run_factory = DeterministicIDFactory(seed=seed)
        run_id = RunID(value=run_factory.next_uuid(f"run:{run_nonce}:{threading.get_ident()}"))
        run = RunContext(run_id=run_id, config=run_config)
        cls._set_current_run(run)
        
        # Start computation tracking
        get_tracker().start_run(str(run_id))
        
        return run

    @classmethod
    def end_run(cls, status: str = "success") -> None:
        """
        End the current run in this thread.

        Args:
            status: Final status of the run ("success" or "failed").
        """
        current = cls._get_current_run()
        if current is None:
            return
            
        # End computation tracking and save report
        report = get_tracker().end_run()
        if report:
            run_dir = Path("runs") / str(current.run_id)
            run_dir.mkdir(parents=True, exist_ok=True)
            with open(run_dir / "coverage.json", "w") as f:
                json.dump(report.to_dict(), f, indent=2)
        
        current.complete(status)
        # Here we would save the run to storage if needed, but Context handles manifest writing
        cls._set_current_run(None)

    @classmethod
    def get_current_run(cls) -> RunContext:
        """
        Get the current run for this thread.

        Returns:
            The current RunContext.

        Raises:
            RuntimeError: If no run is active in this thread.
        """
        current = cls._get_current_run()
        if current is None:
            raise RuntimeError("No active run in this thread")
        return current

    @classmethod
    def has_active_run(cls) -> bool:
        """Check if there's an active run in this thread."""
        return cls._get_current_run() is not None


@contextlib.contextmanager
def active_run(config: dict = None, capture_env: bool = True) -> Generator[RunContext, None, None]:
    """
    Context manager for managing run lifecycle.

    Args:
        config: Configuration dict for the run.
        capture_env: Whether to capture environment details (default True).

    Yields:
        The RunContext for this run.
    """
    run = RunManager.start_run(config, capture_env=capture_env)
    try:
        yield run
        RunManager.end_run(status="success")
    except Exception:
        RunManager.end_run(status="failed")
        raise
