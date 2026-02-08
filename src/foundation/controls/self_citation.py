"""
Self-Citation Generator (Timm & Schinner style)

Produces text by selecting a 'kernel' and mutating/extending it.
Simulates a non-semantic process that generates Zipf-like distributions.
"""

import random
from typing import List, Dict, Any
from foundation.controls.interface import ControlGenerator

class SelfCitationGenerator(ControlGenerator):
    """
    Generates text using a self-citation (kernel-based) mechanism.
    """
    def generate(self, source_dataset_id: str, control_id: str, seed: int = 42, params: Dict[str, Any] = None) -> str:
        random.seed(seed)
        params = params or {}
        
        target_tokens = params.get("target_tokens", 230000)
        pool_size = params.get("pool_size", 500)
        mutation_rate = params.get("mutation_rate", 0.1)
        
        # 1. Initialize kernel pool
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        pool = []
        for _ in range(pool_size):
            word_len = random.randint(3, 8)
            word = "".join(random.choice(alphabet) for _ in range(word_len))
            pool.append(word)
            
        # 2. Generate tokens
        tokens = []
        while len(tokens) < target_tokens:
            # Select from pool
            kernel = random.choice(pool)
            
            # Mutate
            if random.random() < mutation_rate:
                # Add/Change a character
                idx = random.randint(0, len(kernel)-1)
                kernel = kernel[:idx] + random.choice(alphabet) + kernel[idx+1:]
                # Update pool? 
                # Timm style: sometimes update pool with new variant
                if random.random() < 0.5:
                    pool[random.randint(0, pool_size-1)] = kernel
            
            tokens.append(kernel)
            
        # 3. Register and ingest
        # (For this simplified implementation, we'll return the token list or handle ingestion)
        # To match the pipeline, we should save to DB.
        self._ingest_tokens(control_id, tokens)
        
        return control_id

    def _ingest_tokens(self, dataset_id: str, tokens: List[str]):
        """Helper to register synthetic tokens in the database."""
        # Using simplified ingestion for Phase 4 controls
        from foundation.core.id_factory import DeterministicIDFactory
        id_factory = DeterministicIDFactory(seed=42)
        
        self.store.add_dataset(dataset_id, "generated_self_citation")
        
        # Partition into dummy pages
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
