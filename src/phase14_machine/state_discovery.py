"""
Multi-State State-Space Discovery (Phase 14)

Clusters transition profiles to identify discrete 'Mask' states 
(Volvelle settings) across the manuscript.
"""

from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict
import numpy as np
from sklearn.cluster import KMeans

class StateSpaceSolver:
    """
    Identifies discrete mechanical states by clustering local transition matrices.
    """
    def build_transition_vectors(self, lines: List[List[str]], window_size: int = 500) -> np.ndarray:
        """
        Produces a feature vector for each window representing its transition profile.
        """
        # We focus on the top 50 most common tokens to keep the feature space manageable
        all_tokens = [t for l in lines for t in l]
        top_50 = [w for w, c in Counter(all_tokens).most_common(50)]
        word_to_idx = {w: i for i, w in enumerate(top_50)}
        
        vectors = []
        for start in range(0, len(lines) - window_size, 100):
            window = lines[start:start + window_size]
            # Transition Matrix (50x50) flattened into a vector of 2500
            vec = np.zeros(len(top_50) * len(top_50))
            for line in window:
                for i in range(len(line) - 1):
                    u, v = line[i], line[i+1]
                    if u in word_to_idx and v in word_to_idx:
                        idx = word_to_idx[u] * len(top_50) + word_to_idx[v]
                        vec[idx] += 1
            # Normalize
            if np.sum(vec) > 0:
                vec /= np.sum(vec)
            vectors.append(vec)
            
        return np.array(vectors)

    def solve_states(self, vectors: np.ndarray, num_states: int = 3) -> Dict[str, Any]:
        """
        Clusters the transition vectors into discrete states.
        """
        if vectors.shape[0] < num_states:
            return {"num_states": 0}
            
        kmeans = KMeans(n_clusters=num_states, random_state=42, n_init=10)
        labels = kmeans.fit_predict(vectors)
        
        # Calculate cluster centroids (The 'Prototypes' for each mask state)
        centroids = kmeans.cluster_centers_
        
        return {
            "num_states": num_states,
            "labels": labels.tolist(),
            "state_prototypes": centroids.tolist()
        }
