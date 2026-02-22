import math

import numpy as np


def dist(p1, p2):
    """Euclidean distance between two 2D points."""
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

class LayoutAnalyzer:
    """Analyzes the physical efficiency of transitions in different geometric layouts."""

    def __init__(self, num_windows=50):
        """
        Args:
            num_windows (int): Total number of windows in the system.
        """
        self.num_windows = num_windows

    def get_grid_coords(self, win_id, cols=10):
        """Maps a window ID to 2D grid coordinates."""
        row = win_id // cols
        col = win_id % cols
        return (float(col), float(row))

    def get_circle_coords(self, win_id, radius=10):
        """Maps a window ID to circular coordinates."""
        angle = (2 * math.pi * win_id) / self.num_windows
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        return (x, y)

    def analyze_transitions(self, window_ids, limit=10000):
        """
        Calculates average travel distance for a sequence of transitions.
        """
        grid_dist = 0.0
        circle_dist = 0.0
        count = 0
        
        for i in range(1, min(len(window_ids), limit)):
            w1 = window_ids[i-1]
            w2 = window_ids[i]
            
            grid_dist += dist(self.get_grid_coords(w1), self.get_grid_coords(w2))
            circle_dist += dist(self.get_circle_coords(w1), self.get_circle_coords(w2))
            count += 1
            
        return {
            "avg_grid_dist": grid_dist / count if count > 0 else 0.0,
            "avg_circle_dist": circle_dist / count if count > 0 else 0.0,
            "num_transitions": count
        }

    def calculate_random_baseline(self, num_samples=1000, seed=42):
        """Calculates a random baseline for travel distance."""
        rng = np.random.default_rng(seed=seed)
        grid_dist = 0.0
        for _ in range(num_samples):
            w1 = rng.integers(0, self.num_windows)
            w2 = rng.integers(0, self.num_windows)
            grid_dist += dist(self.get_grid_coords(w1), self.get_grid_coords(w2))
            
        return grid_dist / num_samples if num_samples > 0 else 0.0
