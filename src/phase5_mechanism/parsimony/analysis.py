"""
Parsimony and Residual Dependency Analysis.
"""

from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict
import math
import logging
logger = logging.getLogger(__name__)

class ParsimonyAnalyzer:
    def __init__(self):
        pass

    def analyze_node_explosion(self, lines: List[List[str]]) -> Dict[str, Any]:
        """
        Estimates the effective state space size of a Position-Indexed DAG.

        explosion_factor = |unique (word, position) states| / |vocabulary|
        Values >>1 indicate positional conditioning inflates the state space.
        """
        unique_words = set()
        unique_states = set() # (word, pos)
        transitions = set() # ((word, pos), successor)
        
        for line in lines:
            for i, word in enumerate(line):
                unique_words.add(word)
                state = (word, i)
                unique_states.add(state)
                
                if i < len(line) - 1:
                    successor = line[i+1]
                    transitions.add((state, successor))
                    
        vocab_size = len(unique_words)
        state_count = len(unique_states)
        
        return {
            "vocab_size": vocab_size,
            "state_count": state_count,
            "explosion_factor": state_count / vocab_size if vocab_size > 0 else 0.0,
            "transition_count": len(transitions)
        }

    def analyze_residual_dependency(self, lines: List[List[str]]) -> Dict[str, Any]:
        """
        Checks if history (prefix) adds information beyond (Word, Position).

        Compares two weighted conditional entropies:
          H_base = H(successor | word, position)
          H_hist = H(successor | word, position, predecessor)

        Each is computed as a weighted average over contexts:
          H = sum_ctx [ N(ctx) * (-sum_s p(s|ctx) * log2(p(s|ctx))) ] / sum_ctx N(ctx)

        entropy_reduction = H_base - H_hist  (>0 means history helps)
        rel_reduction     = reduction / H_base
        """
        # Contexts
        ctx_word_pos = defaultdict(Counter)
        ctx_word_pos_hist = defaultdict(Counter)
        
        for line in lines:
            for i in range(1, len(line) - 1): # Start at 1 to have history
                prev = line[i-1]
                curr = line[i]
                succ = line[i+1]
                
                key_base = (curr, i)
                key_hist = (curr, i, prev)
                
                ctx_word_pos[key_base][succ] += 1
                ctx_word_pos_hist[key_hist][succ] += 1
                
        def calculate_entropy(successors_map):
            entropies = []
            weights = []
            for context, counts in successors_map.items():
                total = sum(counts.values())
                if total == 0: continue
                probs = [c / total for c in counts.values()]
                ent = -sum(p * math.log2(p) for p in probs if p > 0)
                entropies.append(ent)
                weights.append(total)
            
            if not weights: return 0.0
            return sum(e * w for e, w in zip(entropies, weights)) / sum(weights)

        h_base = calculate_entropy(ctx_word_pos)
        h_hist = calculate_entropy(ctx_word_pos_hist)
        
        reduction = h_base - h_hist
        
        return {
            "h_word_pos": float(h_base),
            "h_word_pos_hist": float(h_hist),
            "entropy_reduction": float(reduction),
            "rel_reduction": float(reduction / h_base) if h_base > 0 else 0.0
        }
