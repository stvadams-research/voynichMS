"""
Step 3.2.3: Grammar-Based Glyph Generator

Generates Voynichese text by following extracted glyph-level rules.
Uses transition and positional probabilities from voynich_grammar.json.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from phase1_foundation.config import require_seed_if_strict
import logging
logger = logging.getLogger(__name__)

class GrammarBasedGenerator:
    """
    Generates words glyph-by-glyph using a probabilistic grammar.
    """
    def __init__(self, grammar_path: Path, seed: Optional[int] = None):
        require_seed_if_strict(seed, "GrammarBasedGenerator")
        with open(grammar_path, "r") as f:
            self.grammar = json.load(f)

        self.transitions = self.grammar["transitions"]
        self.positions = self.grammar["positions"]
        self.word_lengths = self.grammar["word_lengths"]

        self.rng = random.Random(seed)
        
        # Pre-process for weighted sampling
        self.len_values, self.len_weights = self._prepare_weights(self.word_lengths)

    def _prepare_weights(self, prob_dict: Dict[str, float]) -> Tuple[List[Any], List[float]]:
        items = list(prob_dict.items())
        values = [i[0] for i in items]
        weights = [i[1] for i in items]
        return values, weights

    def generate_word(self, max_length: int = 15) -> str:
        """
        Generate a single word glyph-by-glyph.
        """
        word = []
        current = "<START>"
        
        while len(word) < max_length:
            if current not in self.transitions:
                break
                
            next_probs = self.transitions[current]
            symbols, weights = self._prepare_weights(next_probs)
            
            next_sym = self.rng.choices(symbols, weights=weights, k=1)[0]
            
            if next_sym == "<END>":
                break
                
            word.append(next_sym)
            current = next_sym
            
        return "".join(word)

    def generate_line(self, target_word_count: int) -> List[str]:
        """
        Generate a line of words.
        """
        return [self.generate_word() for _ in range(target_word_count)]

    def generate_block(self, num_lines: int, words_per_line: int) -> List[List[str]]:
        """
        Generate a block of text.
        """
        return [self.generate_line(words_per_line) for _ in range(num_lines)]
