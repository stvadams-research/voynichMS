from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
import matplotlib.pyplot as plt
import logging

from foundation.storage.metadata import MetadataStore
from foundation.runs.manager import RunManager

logger = logging.getLogger(__name__)

class BaseVisualizer(ABC):
    """
    Abstract base class for all visualizers in the Voynich Manuscript project.
    """

    def __init__(
        self, 
        store: MetadataStore, 
        output_dir: Optional[Path] = None,
        run_id: Optional[str] = None
    ):
        self.store = store
        self._output_dir = output_dir or Path("results/reports/visuals")
        
        # Determine RunID for provenance
        if run_id:
            self.run_id = run_id
        elif RunManager.has_active_run():
            self.run_id = str(RunManager.get_current_run().run_id)
        else:
            self.run_id = "independent"

    @property
    def output_dir(self) -> Path:
        """Return the base output directory for this visualizer's phase."""
        phase_dir = self._output_dir / self.phase_name
        return phase_dir

    @property
    @abstractmethod
    def phase_name(self) -> str:
        """Return the name of the phase (e.g., 'foundation', 'analysis')."""
        pass

    def _get_output_path(self, filename: str) -> Path:
        """Construct the full output path including run_id prefix."""
        full_filename = f"{self.run_id}_{filename}"
        path = self.output_dir / full_filename
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _save_figure(
        self, 
        fig: plt.Figure, 
        filename: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Save a matplotlib figure to the appropriate location.
        """
        output_path = self._get_output_path(filename)
        
        # Add project-standard metadata if possible
        # (Note: Standard PNG metadata support in matplotlib is limited,
        # but we can save sidecar files or just rely on the naming/directory structure)
        
        fig.savefig(output_path, bbox_inches='tight', dpi=300)
        logger.info(f"Saved visualization to {output_path}")
        
        if metadata:
            meta_path = output_path.with_suffix(".json")
            import json
            with open(meta_path, "w") as f:
                json.dump({
                    "run_id": self.run_id,
                    "filename": filename,
                    "metadata": metadata
                }, f, indent=2)
                
        return output_path
