import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import matplotlib.pyplot as plt
import numpy as np
import logging

from support_visualization.base import BaseVisualizer
from support_visualization.core.themes import apply_voynich_theme, get_color_palette

logger = logging.getLogger(__name__)

class SynthesisVisualizer(BaseVisualizer):
    """
    Visualizers for Layer 3 (Synthesis).
    Focuses on comparing real manuscript data with synthetic reconstructions.
    """

    @property
    def phase_name(self) -> str:
        return "phase3_synthesis"

    def plot_gap_analysis(self, gap_json_path: Path) -> Optional[str]:
        """
        Visualize the gap between real and synthetic metrics.
        """
        apply_voynich_theme()
        
        if not gap_json_path.exists():
            logger.error(f"Gap Analysis JSON not found: {gap_json_path}")
            return None
            
        with open(gap_json_path, "r") as f:
            # Note: ProvenanceWriter saves in a specific format {provenance: ..., results: ...}
            data = json.load(f)
            results = data.get("results", data) # Handle both raw and provenance-wrapped
            
        metrics = list(results.keys())
        target_vals = [results[m]["target"] for m in metrics]
        syn_vals = [results[m]["synthetic"] for m in metrics]
        
        # Filter out None values
        valid_indices = [i for i, v in enumerate(target_vals) if v is not None and syn_vals[i] is not None]
        metrics = [metrics[i] for i in valid_indices]
        target_vals = [target_vals[i] for i in valid_indices]
        syn_vals = [syn_vals[i] for i in valid_indices]
        
        if not metrics:
            logger.warning("No valid metric pairs found for gap phase2_analysis plot")
            return None
            
        x = np.arange(len(metrics))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = get_color_palette()
        
        ax.bar(x - width/2, target_vals, width, label='Real (Target)', color=colors[0])
        ax.bar(x + width/2, syn_vals, width, label='Synthetic', color=colors[2])
        
        ax.set_ylabel('Metric Value')
        ax.set_title('Synthesis Gap Analysis: Real vs Synthetic')
        ax.set_xticks(x)
        ax.set_xticklabels([m.replace('_', ' ').title() for m in metrics])
        ax.legend()
        
        # Add text labels for the gap percentage
        for i in range(len(metrics)):
            gap = target_vals[i] - syn_vals[i]
            pct = (gap / target_vals[i]) * 100 if target_vals[i] != 0 else 0
            ax.text(x[i], max(target_vals[i], syn_vals[i]) * 1.05, 
                    f"Gap: {pct:.1f}%", ha='center', color=colors[1], fontweight='bold')
        
        filename = "synthesis_gap_analysis.png"
        output_path = self._save_figure(fig, filename, metadata={
            "source": str(gap_json_path),
            "metrics": metrics
        })
        plt.close(fig)
        
        return str(output_path)
