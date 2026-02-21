"""
Mechanical Slip Detection

Identifies 'Vertical Offsets' where a scribe may have accidentally 
used the constraints of an adjacent line.
"""

from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)

class MechanicalSlipDetector:
    """
    Analyzes the corpus for transition violations that are satisfied by 
    vertical context shifts.
    
    Attributes:
        min_transition_count: Minimum number of times a transition must appear 
                             to be considered 'legal'.
        legal_transitions: Dictionary mapping (prev_word, position) to a set 
                          of observed next words.
        transition_counts: Frequency count of all transitions for filtering.
    """
    def __init__(self, min_transition_count: int = 2) -> None:
        """
        Initializes the detector with a sensitivity threshold.
        
        Args:
            min_transition_count: Sensitivity threshold for transition legality.
        """
        self.min_transition_count = min_transition_count
        # Context: (prev_word, position) -> Set of valid next words
        self.legal_transitions: Dict[Tuple[str, int], Set[str]] = defaultdict(set)
        # Counts for significance
        self.transition_counts: Counter[Tuple[Tuple[str, int], str]] = Counter()

    def build_model(self, lines: List[List[str]]) -> None:
        """
        Builds the global empirical lattice from all lines.
        
        Args:
            lines: A list of tokenized manuscript lines.
        """
        for line in lines:
            for i in range(len(line) - 1):
                prev = line[i]
                curr = line[i+1]
                pos = i + 1
                ctx = (prev, pos)
                self.transition_counts[(ctx, curr)] += 1
                
        # Filter by min_transition_count to avoid single-occurrence noise
        for (ctx, curr), count in self.transition_counts.items():
            if count >= self.min_transition_count:
                self.legal_transitions[ctx].add(curr)

    def detect_slips(self, lines: List[List[str]]) -> List[Dict[str, Any]]:
        """
        Scans lines for vertical offsets (eye-slips).
        
        A slip occurs if Word(i, j) is ILLEGAL for Context(i, j-1) 
        but LEGAL for Context(i-1, j-1).
        
        Args:
            lines: A list of tokenized manuscript lines.
            
        Returns:
            A list of detected slip events with context metadata.
        """
        slips = []
        for i in range(1, len(lines)): # Start from second line
            curr_line = lines[i]
            prev_line = lines[i-1]
            
            # We only check tokens where BOTH lines have a predecessor at j-1
            min_len = min(len(curr_line), len(prev_line))
            
            for j in range(1, min_len):
                word = curr_line[j]
                
                # Contexts: (previous_word, current_position)
                ctx_actual = (curr_line[j-1], j)
                ctx_vertical = (prev_line[j-1], j)
                
                # 1. Is it illegal in current line?
                is_legal_actual = word in self.legal_transitions[ctx_actual]
                
                # 2. Is it legal in vertical context? (Eye slipped up one row)
                is_legal_vertical = word in self.legal_transitions[ctx_vertical]
                
                if not is_legal_actual and is_legal_vertical:
                    # Potential Slip!
                    slips.append({
                        "line_index": i,
                        "token_index": j,
                        "word": word,
                        "actual_context": ctx_actual,
                        "vertical_context": ctx_vertical,
                        "type": "vertical_offset_down"
                    })
                    
        return slips
