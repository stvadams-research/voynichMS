import matplotlib.pyplot as plt
from typing import Tuple, Optional
from support_visualization.core.themes import apply_voynich_theme

class VisualizationEngine:
    """
    Orchestrates figure creation and project-wide styling.
    """
    
    @staticmethod
    def create_figure(
        figsize: Tuple[int, int] = (10, 6), 
        title: Optional[str] = None,
        theme: bool = True
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Initialize a figure and axes with the project theme.
        """
        if theme:
            apply_voynich_theme()
            
        fig, ax = plt.subplots(figsize=figsize)
        
        if title:
            ax.set_title(title)
            
        return fig, ax
