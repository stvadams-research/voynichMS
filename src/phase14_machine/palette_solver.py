"""
Global Palette Solver (Phase 14)

Reconstructs the full physical grid for the entire Voynich vocabulary 
using a graph-based constraint satisfaction approach.
"""

from typing import List, Dict, Any, Tuple, Optional
from collections import Counter, defaultdict
import networkx as nx
import numpy as np

class GlobalPaletteSolver:
    """
    Infers 2D coordinates for every word in the vocabulary based on 
    physical adjacency signals (slips and transitions).
    """
    def __init__(self):
        self.G = nx.Graph()

    def ingest_data(self, slips: List[Dict[str, Any]], lines: List[List[str]], top_n: Optional[int] = 8000):
        """Builds the global physical adjacency graph with frequency filtering."""
        # Standardize: Always cap at 8,000 to avoid long-tail noise
        target_n = top_n if top_n else 8000
        
        all_tokens = [t for l in lines for t in l]
        counts = Counter(all_tokens)
        keep_tokens = set([w for w, c in counts.most_common(target_n)])
        print(f"Building graph for top {target_n} tokens...")

        # 1. Signal from Slips (Weight = 10.0)
        for s in slips:
            word_a = s['word']
            word_b = s['actual_context'][0]
            if word_a in keep_tokens and word_b in keep_tokens:
                self.G.add_edge(word_a, word_b, weight=10.0, type='slip')
            
        # 2. Signal from Transitions (Weight = 1.0)
        for line in lines:
            for i in range(len(line) - 1):
                u, v = line[i], line[i+1]
                if u in keep_tokens and v in keep_tokens:
                    self.G.add_edge(u, v, weight=1.0, type='transition')

    def solve_grid(self, iterations: int = 30) -> Dict[str, Tuple[float, float]]:
        """
        Uses an iterative force-directed layout with heartbeats to prevent timeouts.
        """
        num_nodes = self.G.number_of_nodes()
        print(f"Solving physical grid for {num_nodes} tokens...")
        
        # We run iterations in batches of 5 to provide status updates
        batch_size = 5
        current_pos = None
        
        for i in range(0, iterations, batch_size):
            actual_iter = min(batch_size, iterations - i)
            # Use fixed seed for first batch, then use previous positions
            current_pos = nx.spring_layout(
                self.G, 
                weight='weight', 
                iterations=actual_iter, 
                pos=current_pos,
                seed=42 if i == 0 else None
            )
            print(f"  [HEARTBEAT] Completed {i + actual_iter}/{iterations} iterations...")
        
        print("Layout optimization complete.")
        return {word: tuple(coord) for word, coord in current_pos.items()}

    def cluster_columns(self, solved_pos: Dict[str, Tuple[float, float]], num_columns: int = 15) -> Dict[int, List[str]]:
        """
        Groups words into discrete vertical stacks (windows).
        """
        # Sort words by X-coordinate
        words = sorted(solved_pos.keys(), key=lambda w: solved_pos[w][0])
        
        # Divide into even chunks (columns)
        chunk_size = len(words) // num_columns
        columns = {}
        for i in range(num_columns):
            start = i * chunk_size
            end = (i + 1) * chunk_size if i < num_columns - 1 else len(words)
            columns[i+1] = words[start:end]
            
        return columns
