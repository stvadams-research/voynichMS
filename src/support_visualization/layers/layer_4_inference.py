import json
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from support_visualization.base import BaseVisualizer
from support_visualization.core.themes import apply_voynich_theme, get_color_palette

logger = logging.getLogger(__name__)

class InferenceVisualizer(BaseVisualizer):
    """
    Visualizers for Layer 4 (Inference Evaluation).
    Focuses on the reliability of phase4_inference methods across semantic and non-semantic texts.
    """

    @property
    def phase_name(self) -> str:
        return "phase4_inference"

    def plot_lang_id_comparison(self, results_json_path: Path) -> str | None:
        """
        Visualize Language ID confidence scores across different datasets.
        Shows how non-semantic datasets can still produce high-confidence matches.
        """
        apply_voynich_theme()
        
        if not results_json_path.exists():
            logger.error(f"Inference results JSON not found: {results_json_path}")
            return None
            
        with open(results_json_path) as f:
            data = json.load(f)
            results = data.get("results", data)
            
        datasets = list(results.keys())
        languages = list(next(iter(results.values())).keys())
        
        fig, ax = plt.subplots(figsize=(12, 6))
        colors = get_color_palette()
        
        x = np.arange(len(datasets))
        width = 0.35
        
        for i, lang in enumerate(languages):
            scores = [results[ds][lang] for ds in datasets]
            ax.bar(x + (i - len(languages)/2 + 0.5) * width, 
                   scores, width, label=lang.title(), color=colors[i % len(colors)])
            
        ax.set_ylabel('Best Confidence Score')
        ax.set_title('Language ID False Positive Evaluation')
        ax.set_xticks(x)
        ax.set_xticklabels([ds.replace('_', ' ').title() for ds in datasets])
        ax.legend()
        
        # Add a "Decipherment Threshold" line
        ax.axhline(y=0.7, color='red', linestyle='--', alpha=0.5, label='Inference Threshold (Typical)')
        
        filename = "lang_id_comparison.png"
        output_path = self._save_figure(fig, filename, metadata={
            "source": str(results_json_path),
            "datasets": datasets,
            "languages": languages
        })
        plt.close(fig)
        
        return str(output_path)
