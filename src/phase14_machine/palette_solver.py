"""
Global Palette Solver (Phase 14)

Reconstructs the full physical grid for the entire Voynich vocabulary 
using a graph-based constraint satisfaction approach.
"""

from collections import Counter, defaultdict
from typing import Any

import networkx as nx
import numpy as np


class GlobalPaletteSolver:
    """
    Infers 2D coordinates for every word in the vocabulary based on 
    physical adjacency signals (slips and transitions).
    
    Attributes:
        G: A networkx Graph where nodes are words and edges represent 
           physical proximity signals (slips or transitions).
    """
    def __init__(self) -> None:
        """Initializes an empty adjacency graph."""
        self.G = nx.Graph()

    def ingest_data(self, 
                    slips: list[dict[str, Any]], 
                    lines: list[list[str]], 
                    top_n: int | None = 8000) -> None:
        """
        Builds the global physical adjacency graph with frequency filtering.
        
        Args:
            slips: A list of detected mechanical slips (with actual contexts).
            lines: A list of manuscript lines (tokenized).
            top_n: The maximum number of frequent tokens to include in the graph.
        """
        # Standardize: Always cap at 8,000 to avoid long-tail noise
        target_n = top_n if top_n else 8000
        
        all_tokens = [t for l in lines for t in l]
        counts = Counter(all_tokens)
        keep_tokens = set([w for w, c in counts.most_common(target_n)])
        print(f"Building graph for top {target_n} tokens...")

        # 1. Signal from Slips (Weight = 10.0)
        # Slips are high-confidence signals of vertical adjacency
        for s in slips:
            word_a = s['word']
            # actual_context[0] is the word physically above the slip
            word_b = s['actual_context'][0]
            if word_a in keep_tokens and word_b in keep_tokens:
                self.G.add_edge(word_a, word_b, weight=10.0, type='slip')
            
        # 2. Signal from Transitions (Weight = 1.0)
        # Transitions are signals of horizontal/state adjacency
        for line in lines:
            for i in range(len(line) - 1):
                u, v = line[i], line[i+1]
                if u in keep_tokens and v in keep_tokens:
                    self.G.add_edge(u, v, weight=1.0, type='transition')

    def solve_grid(self, iterations: int = 30) -> dict[str, tuple[float, float]]:
        """
        Infers 2D coordinates using an iterative force-directed layout.
        
        Args:
            iterations: Total number of optimization steps.
            
        Returns:
            A dictionary mapping each word to its (x, y) coordinates.
        """
        num_nodes = self.G.number_of_nodes()
        if num_nodes == 0:
            return {}
            
        print(f"Solving physical grid for {num_nodes} tokens...")
        
        # We run iterations in batches to provide status heartbeats
        batch_size = 5
        current_pos = None
        
        for i in range(0, iterations, batch_size):
            actual_iter = min(batch_size, iterations - i)
            # Use fixed seed for first batch, then use previous positions for stability
            current_pos = nx.spring_layout(
                self.G, 
                weight='weight', 
                iterations=actual_iter, 
                pos=current_pos,
                seed=42 if i == 0 else None
            )
            print(f"  [HEARTBEAT] Completed {i + actual_iter}/{iterations} iterations...")
        
        print("Layout optimization complete.")
        return {word: (float(coord[0]), float(coord[1])) for word, coord in current_pos.items()}

    def cluster_lattice(self, 
                        solved_pos: dict[str, tuple[float, float]], 
                        num_windows: int = 50) -> dict[str, Any]:
        """
        Groups words into discrete functional windows based on their 2D coordinates.
        
        Args:
            solved_pos: Mapping from word to its physical coordinates.
            num_windows: The number of clusters (windows) to create.
            
        Returns:
            A dictionary containing the word-to-window map and the window-to-words list.
        """
        if not solved_pos:
            return {"word_to_window": {}, "window_contents": {}}
            
        from sklearn.cluster import KMeans
        words = list(solved_pos.keys())
        coords = np.array([solved_pos[w] for w in words])
        
        # KMeans finds the most natural 'windows' in the physical space
        print(f"Clustering {len(words)} tokens into {num_windows} physical windows...")
        kmeans = KMeans(n_clusters=num_windows, random_state=42, n_init=10)
        labels = kmeans.fit_predict(coords)
        
        word_to_window = {words[i]: int(labels[i]) for i in range(len(words))}
        
        # Build the 'Window Contents' map
        # window_id -> list of words in that window
        window_contents = defaultdict(list)
        for w, wid in word_to_window.items():
            window_contents[wid].append(w)
            
        return {
            "word_to_window": word_to_window,
            "window_contents": dict(window_contents)
        }

    @staticmethod
    def reorder_windows(
        word_to_window: dict[str, int],
        window_contents: dict[int, list[str]],
        lines: list[list[str]],
    ) -> dict[str, Any]:
        """Reorder window IDs via spectral ordering on the transition graph.

        KMeans assigns arbitrary window IDs that don't reflect sequential
        access patterns.  This method builds a window-to-window transition
        matrix from the real corpus and uses the Fiedler vector of its
        graph Laplacian to find the optimal circular ordering.

        Args:
            word_to_window: Current word-to-window mapping.
            window_contents: Current window-to-word-list mapping.
            lines: Real manuscript lines (for building the transition matrix).

        Returns:
            A dictionary with reordered ``word_to_window`` and
            ``window_contents``.
        """
        num_wins = len(window_contents)
        if num_wins < 3:
            return {
                "word_to_window": word_to_window,
                "window_contents": window_contents,
            }

        # 1. Build transition matrix
        matrix = np.zeros((num_wins, num_wins), dtype=int)
        for line in lines:
            prev_win = None
            for word in line:
                if word in word_to_window:
                    cur_win = word_to_window[word]
                    if prev_win is not None:
                        matrix[prev_win][cur_win] += 1
                    prev_win = cur_win

        # 2. Spectral ordering via Fiedler vector
        sym = matrix + matrix.T
        D = np.diag(sym.sum(axis=1).astype(float))
        L = D - sym.astype(float)
        eigenvalues, eigenvectors = np.linalg.eigh(L)
        fiedler = eigenvectors[:, 1]
        order = [int(x) for x in np.argsort(fiedler)]

        # 3. Apply reordering
        old_to_new = {old_id: new_id for new_id, old_id in enumerate(order)}

        new_w2w = {
            word: int(old_to_new[old_win])
            for word, old_win in word_to_window.items()
            if old_win in old_to_new
        }

        new_wc: dict[int, list[str]] = {}
        for old_id, words in window_contents.items():
            new_id = old_to_new.get(old_id)
            if new_id is not None:
                new_wc[new_id] = words

        print(f"Spectral reordering applied to {num_wins} windows.")
        return {"word_to_window": new_w2w, "window_contents": new_wc}
