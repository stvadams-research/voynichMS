import math
import zlib
from collections import Counter, defaultdict
import numpy as np

def calculate_entropy(data):
    """Calculates the Shannon entropy of a dataset."""
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((c/total) * math.log2(c/total) for c in counts.values())

class BiasAnalyzer:
    """Analyzes selection bias and compressibility in choice streams."""

    def __init__(self, choices):
        """
        Args:
            choices (list): List of choice dictionaries containing 'window_id', 
                            'chosen_index', and 'candidates_count'.
        """
        self.choices = choices

    def analyze_window_bias(self, min_samples=50):
        """
        Analyzes bias within windows based on entropy reduction.
        
        Args:
            min_samples (int): Minimum number of choices in a window to include it.
            
        Returns:
            list: List of dictionaries containing stats for each window.
        """
        win_choices = defaultdict(list)
        win_candidate_counts = {}
        
        for c in self.choices:
            wid = c.get('window_id')
            if wid is None: 
                continue
            win_choices[wid].append(c.get('chosen_index', 0))
            if wid not in win_candidate_counts:
                win_candidate_counts[wid] = c.get('candidates_count', 0)

        window_stats = []
        for wid, idxs in win_choices.items():
            if len(idxs) < min_samples:
                continue
                
            ent = calculate_entropy(idxs)
            candidates = win_candidate_counts.get(wid, len(set(idxs)))
            # Avoid log(0)
            max_ent = math.log2(candidates) if candidates > 1 else 0.0
            
            # Skew is percentage reduction in entropy from max
            if max_ent > 0:
                skew = max(0.0, (max_ent - ent) / max_ent)
            else:
                skew = 0.0
                
            window_stats.append({
                "window_id": wid,
                "count": len(idxs),
                "candidates": candidates,
                "entropy": ent,
                "max_entropy": max_ent,
                "skew": skew
            })
            
        return window_stats

    def analyze_compressibility(self, seed=42):
        """
        Compares compressibility of the actual choice stream vs a uniform random baseline.
        
        Returns:
            dict: Compression statistics.
        """
        # Real compression
        raw_indices = [c.get('chosen_index', 0) % 256 for c in self.choices]
        raw_bytes = bytes(raw_indices)
        compressed_size = len(zlib.compress(raw_bytes))
        uncompressed_size = len(raw_bytes)
        
        if uncompressed_size == 0:
             return {
                "real_ratio": 0.0,
                "sim_ratio": 0.0,
                "improvement": 0.0
            }

        ratio = compressed_size / uncompressed_size

        # Simulated Uniform Baseline
        rng = np.random.default_rng(seed=seed)
        sim_indices = [
            rng.integers(0, max(c.get('candidates_count', 1), 1)) % 256
            for c in self.choices
        ]
        sim_bytes = bytes(sim_indices)
        sim_compressed_size = len(zlib.compress(sim_bytes))
        sim_ratio = sim_compressed_size / len(sim_bytes)

        improvement = (sim_ratio - ratio) / sim_ratio if sim_ratio > 0 else 0.0

        return {
            "real_ratio": ratio,
            "sim_ratio": sim_ratio,
            "improvement": improvement
        }
