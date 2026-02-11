import matplotlib.pyplot as plt

# Voynich-inspired color palette
VOYNICH_COLORS = {
    'parchment': '#F5F5DC',
    'ink': '#2F2F2F',
    'botanical_green': '#4F7942',
    'botanical_red': '#8B0000',
    'botanical_blue': '#4682B4',
    'gold': '#D4AF37',
    'faded_ink': '#555555'
}

def apply_voynich_theme():
    """
    Apply a consistent visual style across all project plots.
    """
    plt.style.use('seaborn-v0_8-paper')
    
    params = {
        'axes.facecolor': VOYNICH_COLORS['parchment'],
        'figure.facecolor': 'white',
        'axes.edgecolor': VOYNICH_COLORS['ink'],
        'axes.labelcolor': VOYNICH_COLORS['ink'],
        'xtick.color': VOYNICH_COLORS['ink'],
        'ytick.color': VOYNICH_COLORS['ink'],
        'text.color': VOYNICH_COLORS['ink'],
        'axes.prop_cycle': plt.cycler(color=[
            VOYNICH_COLORS['botanical_green'],
            VOYNICH_COLORS['botanical_red'],
            VOYNICH_COLORS['botanical_blue'],
            VOYNICH_COLORS['gold'],
            VOYNICH_COLORS['faded_ink']
        ]),
        'font.family': 'serif',
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.color': VOYNICH_COLORS['faded_ink'],
        'figure.autolayout': True
    }
    
    plt.rcParams.update(params)

def get_color_palette():
    """Return the Voynich color palette list."""
    return [
        VOYNICH_COLORS['botanical_green'],
        VOYNICH_COLORS['botanical_red'],
        VOYNICH_COLORS['botanical_blue'],
        VOYNICH_COLORS['gold'],
        VOYNICH_COLORS['faded_ink']
    ]
