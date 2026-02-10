"""
Latent State Dimensionality Analyzer

Uses matrix factorization (SVD) on the token transition matrix to estimate 
 the number of latent states required to explain successor constraints.
"""

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds
from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple
import logging
logger = logging.getLogger(__name__)

class LatentStateAnalyzer:
    """
    Estimates the dimensionality of the hidden constraints governing succession.
    """
    def __init__(self, top_n: int = 1000):
        self.top_n = top_n

    def estimate_dimensionality(self, tokens: List[str]) -> Dict[str, Any]:
        """
        Builds transition matrix and performs SVD to find the effective rank.
        """
        if not tokens:
            return {}

        # 1. Map top N tokens to indices
        counts = Counter(tokens)
        vocab = [w for w, c in counts.most_common(self.top_n)]
        token_to_idx = {w: i for i, w in enumerate(vocab)}
        K = len(vocab)

        # 2. Build Sparse Transition Matrix
        row_indices = []
        col_indices = []
        data = []
        
        for i in range(len(tokens) - 1):
            u, v = tokens[i], tokens[i+1]
            if u in token_to_idx and v in token_to_idx:
                row_indices.append(token_to_idx[u])
                col_indices.append(token_to_idx[v])
                data.append(1.0)
                
        if not data:
            return {"error": "no_transitions_found"}

        T = csr_matrix((data, (row_indices, col_indices)), shape=(K, K))
        
        # 3. SVD for Dimensionality
        # We look at singular value decay
        num_vals = min(K - 1, 100)
        u, s, vt = svds(T.astype(float), k=num_vals)
        s = sorted(s, reverse=True)
        
        # Calculate 'Effective Rank' (number of values explaining 90% of variance)
        total_var = np.sum(s)
        cumulative_var = np.cumsum(s) / total_var
        effective_rank_90 = int(np.searchsorted(cumulative_var, 0.90)) + 1
        
        return {
            "vocab_size": K,
            "singular_values": [float(val) for val in s[:20]],
            "effective_rank_90": effective_rank_90,
            "variance_explained": [float(val) for val in cumulative_var[:20]]
        }
