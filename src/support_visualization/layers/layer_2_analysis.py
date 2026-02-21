import json
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from support_visualization.base import BaseVisualizer
from support_visualization.core.themes import apply_voynich_theme, get_color_palette

logger = logging.getLogger(__name__)

class AnalysisVisualizer(BaseVisualizer):
    """
    Visualizers for Layer 2 (Analysis & Admissibility).
    Focuses on sensitivity, stability, and admissibility boundaries.
    """

    @property
    def phase_name(self) -> str:
        return "phase2_analysis"

    def plot_sensitivity_sweep(self, sweep_json_path: Path) -> str | None:
        """
        Generate plots summarizing a sensitivity sweep.
        """
        apply_voynich_theme()
        
        if not sweep_json_path.exists():
            logger.error(f"Sweep JSON not found: {sweep_json_path}")
            return None
            
        with open(sweep_json_path) as f:
            data = json.load(f)
            
        results = data.get("results", {}).get("results", [])
        if not results:
            logger.warning("No results found in sweep JSON")
            return None
            
        df = pd.DataFrame(results)
        
        # Plot 1: Top Score by Scenario
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Group by family
        families = df['family'].unique()
        colors = get_color_palette()
        
        for i, family in enumerate(families):
            family_df = df[df['family'] == family]
            ax.scatter(family_df['id'], family_df['top_score'], 
                       label=family, color=colors[i % len(colors)], s=100)
            
        ax.set_title("Sensitivity Sweep: Top Model Scores")
        ax.set_ylabel("Top Score")
        ax.set_xlabel("Scenario ID")
        ax.set_ylim(0, 1.1)
        plt.xticks(rotation=45, ha='right')
        ax.legend()
        
        filename = "sensitivity_top_scores.png"
        output_path = self._save_figure(fig, filename, metadata={
            "source": str(sweep_json_path),
            "scenario_count": len(results)
        })
        plt.close(fig)
        
        # Plot 2: Surviving vs Falsified Models
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        
        x = range(len(df))
        ax2.bar(x, df['surviving_models'], label='Surviving', color=colors[0], alpha=0.7)
        ax2.bar(x, df['falsified_models'], bottom=df['surviving_models'], 
                label='Falsified', color=colors[1], alpha=0.7)
        
        ax2.set_xticks(x)
        ax2.set_xticklabels(df['id'], rotation=45, ha='right')
        ax2.set_title("Model Survival across Sensitivity Scenarios")
        ax2.set_ylabel("Model Count")
        ax2.legend()
        
        filename2 = "sensitivity_model_survival.png"
        self._save_figure(fig2, filename2)
        plt.close(fig2)
        
        return str(output_path)
