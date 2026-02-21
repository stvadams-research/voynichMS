
import matplotlib.pyplot as plt

from support_visualization.core.themes import apply_voynich_theme


class VisualizationEngine:
    """
    Orchestrates figure creation and project-wide styling.
    """

    @staticmethod
    def create_figure(
        figsize: tuple[int, int] = (10, 6),
        title: str | None = None,
        theme: bool = True
    ) -> tuple[plt.Figure, plt.Axes]:
        """
        Initialize a figure and axes with the project theme.
        """
        if theme:
            apply_voynich_theme()

        fig, ax = plt.subplots(figsize=figsize)

        if title:
            ax.set_title(title)

        return fig, ax
