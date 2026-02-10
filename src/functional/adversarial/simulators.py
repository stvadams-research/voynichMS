"""
Adversarial Simulators for Phase 6C
"""

import random
from typing import List, Dict, Any, Tuple
from functional.formal_system.simulators import LatticeTraversalSimulator
import logging
logger = logging.getLogger(__name__)

class AdversarialLatticeSimulator(LatticeTraversalSimulator):
    """
    H6C.2: Adversarial Formal System.
    Deliberately structured to frustrate inference.
    - Decoy regularities: rules change between 'sections' of the corpus.
    - Local ambiguity: many states with high-entropy transitions.
    """
    def __init__(self, vocab_size: int = 1000, seed: int = 42):
        super().__init__(vocab_size=vocab_size, seed=seed)
        self.section_rules = {} # section_idx -> rules

    def _get_nexts_adversarial(self, prev: str, curr: str, pos: int, section_idx: int) -> List[str]:
        if section_idx not in self.section_rules:
            self.section_rules[section_idx] = {}
        
        rules = self.section_rules[section_idx]
        state = (prev, curr, pos)
        
        if state not in rules:
            # Generate a rule that might contradict other sections
            num_choices = self.random.choices([1, 2, 5], weights=[0.4, 0.4, 0.2])[0]
            rules[state] = self.random.sample(self.vocab, num_choices)
        return rules[state]

    def generate_corpus_adversarial(self, num_lines: int, line_len: int = 8, sections: int = 5) -> List[List[str]]:
        corpus = []
        lines_per_section = num_lines // sections
        for s in range(sections):
            for _ in range(lines_per_section):
                line = []
                prev = "<START>"
                curr = self.random.choice(self.vocab)
                line.append(curr)
                for pos in range(1, line_len):
                    possible_nexts = self._get_nexts_adversarial(prev, curr, pos-1, s)
                    nxt = self.random.choice(possible_nexts)
                    prev = curr
                    curr = nxt
                    line.append(curr)
                corpus.append(line)
        return corpus
