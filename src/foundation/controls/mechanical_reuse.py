"""
Mechanical Reuse Generator (Phase 3.3 style)

Produces text by selecting from a small pool of grammar-compliant tokens per page.
"""

import random
from typing import List, Dict, Any, Optional
from foundation.controls.interface import ControlGenerator
from synthesis.generators.grammar_based import GrammarBasedGenerator
from pathlib import Path

class MechanicalReuseGenerator(ControlGenerator):
    """
    Generates text using a rigid grammar and bounded token pools.
    """
    def generate(self, source_dataset_id: str, control_id: str, seed: int = 42, params: Dict[str, Any] = None) -> str:
        random.seed(seed)
        params = params or {}
        
        target_tokens = params.get("target_tokens", 230000)
        pool_size = params.get("pool_size", 25)
        tokens_per_page = params.get("tokens_per_page", 72)
        
        grammar_path = Path("data/derived/voynich_grammar.json")
        if not grammar_path.exists():
            raise FileNotFoundError("Grammar file not found. Run extract_grammar.py first.")
            
        generator = GrammarBasedGenerator(grammar_path)
        
        tokens = []
        page_count = 0
        
        while len(tokens) < target_tokens:
            # Generate pool for this 'page'
            page_pool = [generator.generate_word() for _ in range(pool_size)]
            
            # Fill 'page'
            for _ in range(tokens_per_page):
                if len(tokens) >= target_tokens:
                    break
                tokens.append(random.choice(page_pool))
            
            page_count += 1
            
        # Ingest
        self._ingest_tokens(control_id, tokens)
        
        return control_id

    def _ingest_tokens(self, dataset_id: str, tokens: List[str]):
        """Helper to register synthetic tokens in the database."""
        from foundation.core.id_factory import DeterministicIDFactory
        id_factory = DeterministicIDFactory(seed=42)
        
        self.store.add_dataset(dataset_id, "generated_mechanical_reuse")
        
        tokens_per_page = 1000
        num_pages = len(tokens) // tokens_per_page
        
        session = self.store.Session()
        try:
            for p_idx in range(num_pages):
                page_id = f"{dataset_id}_p{p_idx}"
                self.store.add_page(page_id, dataset_id, "synthetic", f"hash_{page_id}", 1000, 1500)
                
                start = p_idx * tokens_per_page
                end = start + tokens_per_page
                page_tokens = tokens[start:end]
                
                trans_line_id = id_factory.next_uuid(f"line:{page_id}")
                self.store.add_transcription_line(trans_line_id, "synthetic", page_id, 0, " ".join(page_tokens))
                
                for w_idx, token in enumerate(page_tokens):
                    token_id = id_factory.next_uuid(f"token:{trans_line_id}:{w_idx}")
                    self.store.add_transcription_token(token_id, trans_line_id, w_idx, token)
            session.commit()
        finally:
            session.close()
