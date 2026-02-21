"""
Table and Grille Generator (Rugg style)

Produces text using a grid of prefixes, infixes, and suffixes selected by a grille.
"""

import logging
import random
from typing import Any

from phase1_foundation.controls.interface import ControlGenerator

logger = logging.getLogger(__name__)

class TableGrilleGenerator(ControlGenerator):
    """
    Generates text using a table-and-grille phase5_mechanism.

    Normalization modes:
    - parser: parser-equivalent canonicalization for symmetry.
    - pre_normalized_with_assertions: enforce already-normalized token stream.
    """
    def generate(self, source_dataset_id: str, control_id: str, seed: int = 42, params: dict[str, Any] = None) -> str:
        rng = random.Random(seed)
        params = params or {}
        normalization_mode = self._resolve_normalization_mode(params)

        target_tokens = params.get("target_tokens", 230000)

        # 1. Define table components (Voynich-like)
        prefixes = ["q", "y", "d", "ch", "sh", "s", "o"]
        infixes = ["ol", "or", "al", "ar", "ee", "e", "aiin", "ain"]
        suffixes = ["y", "dy", "ky", "ty", "m", "n", "s"]

        # 2. Build Table
        table_rows = 10
        table_cols = 10
        table = []
        for _ in range(table_rows):
            row = []
            for _ in range(table_cols):
                word = rng.choice(prefixes) + rng.choice(infixes) + rng.choice(suffixes)
                row.append(word)
            table.append(row)

        # 3. Generate tokens by moving a 'grille' over the table
        tokens = []
        grille_x, grille_y = 0, 0

        while len(tokens) < target_tokens:
            # Select word from current grille position
            word = table[grille_y][grille_x]
            tokens.append(word)

            # Move grille
            grille_x = (grille_x + rng.randint(0, 1)) % table_cols
            if grille_x == 0:
                grille_y = (grille_y + 1) % table_rows

            # Periodically jitter the table or grille to simulate page shifts
            if len(tokens) % 500 == 0:
                grille_x = rng.randint(0, table_cols-1)
                grille_y = rng.randint(0, table_rows-1)

        normalized_tokens, normalization = self._normalize_tokens_for_control(
            tokens, mode=normalization_mode
        )

        # 4. Ingest
        metadata = {
            "source_dataset_id": source_dataset_id,
            "params": dict(params),
            "normalization": normalization,
        }
        self._ingest_tokens(control_id, normalized_tokens, seed=seed, metadata=metadata)

        return control_id

    def _ingest_tokens(self, dataset_id: str, tokens: list[str], seed: int, metadata: dict[str, Any]):
        """Helper to register synthetic tokens in the database."""
        from phase1_foundation.core.id_factory import DeterministicIDFactory
        id_factory = DeterministicIDFactory(seed=seed)

        self.store.add_control_dataset(
            id=dataset_id,
            source_dataset_id=str(metadata.get("source_dataset_id", "unknown")),
            type="table_grille",
            params=metadata,
            seed=seed,
        )
        self.store.add_dataset(dataset_id, "generated_table_grille")
        self.store.add_transcription_source("synthetic", "Synthetic Control Generator")

        tokens_per_page = 1000
        for p_idx, start in enumerate(range(0, len(tokens), tokens_per_page)):
            page_id = f"{dataset_id}_p{p_idx}"
            self.store.add_page(page_id, dataset_id, "synthetic", f"hash_{page_id}", 1000, 1500)

            end = start + tokens_per_page
            page_tokens = tokens[start:end]

            trans_line_id = id_factory.next_uuid(f"line:{page_id}")
            self.store.add_transcription_line(trans_line_id, "synthetic", page_id, 0, " ".join(page_tokens))

            for w_idx, token in enumerate(page_tokens):
                token_id = id_factory.next_uuid(f"token:{trans_line_id}:{w_idx}")
                self.store.add_transcription_token(token_id, trans_line_id, w_idx, token)
