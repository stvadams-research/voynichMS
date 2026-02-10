import random
from typing import Any, Dict, List

from foundation.controls.interface import ControlGenerator
from foundation.core.id_factory import DeterministicIDFactory
from foundation.storage.metadata import (
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)
import logging

logger = logging.getLogger(__name__)


class SyntheticNullGenerator(ControlGenerator):
    """
    Generates a synthetic null dataset using flat sampling over source vocabulary.

    Normalization modes:
    - parser: parser-equivalent canonicalization for symmetry.
    - pre_normalized_with_assertions: enforce already-normalized token stream.
    """

    def generate(
        self,
        source_dataset_id: str,
        control_id: str,
        seed: int = 42,
        params: Dict[str, Any] = None,
    ) -> str:
        rng = random.Random(seed)
        params = params or {}
        normalization_mode = self._resolve_normalization_mode(params)

        vocabulary = self._load_source_vocabulary(source_dataset_id)
        if not vocabulary:
            vocabulary = self._fallback_vocabulary(rng)
            logger.warning(
                "No source vocabulary found for %s; using deterministic fallback vocabulary (%d tokens).",
                source_dataset_id,
                len(vocabulary),
            )
        vocabulary, normalization = self._normalize_tokens_for_control(
            vocabulary, mode=normalization_mode
        )

        # Register control dataset with normalization provenance.
        params_with_policy = dict(params)
        params_with_policy["normalization"] = normalization
        self.store.add_control_dataset(
            id=control_id,
            source_dataset_id=source_dataset_id,
            type="synthetic_null",
            params=params_with_policy,
            seed=seed,
        )
        self.store.add_transcription_source("synthetic", "Synthetic Control Generator")

        num_pages = int(params.get("num_pages", 5))
        lines_per_page = int(params.get("lines_per_page", 24))
        tokens_per_line = int(params.get("tokens_per_line", 8))
        id_factory = DeterministicIDFactory(seed=seed)

        for i in range(num_pages):
            page_id = f"{control_id}_p{i+1}"
            self.store.add_page(
                page_id=page_id,
                dataset_id=control_id,
                image_path="synthetic_path",
                checksum=f"synthetic_checksum_{page_id}",
                width=1000,
                height=1500,
            )

            for line_index in range(lines_per_page):
                line_tokens = [rng.choice(vocabulary) for _ in range(tokens_per_line)]
                line_content = " ".join(line_tokens)

                line_id = id_factory.next_uuid(f"line:{page_id}:{line_index}")
                self.store.add_transcription_line(
                    id=line_id,
                    source_id="synthetic",
                    page_id=page_id,
                    line_index=line_index,
                    content=line_content,
                )

                for token_index, token in enumerate(line_tokens):
                    token_id = id_factory.next_uuid(
                        f"token:{page_id}:{line_index}:{token_index}"
                    )
                    self.store.add_transcription_token(
                        id=token_id,
                        line_id=line_id,
                        token_index=token_index,
                        content=token,
                    )

        return control_id

    def _load_source_vocabulary(self, source_dataset_id: str) -> List[str]:
        """Load unique token vocabulary from the source dataset."""
        session = self.store.Session()
        try:
            rows = (
                session.query(TranscriptionTokenRecord.content)
                .join(
                    TranscriptionLineRecord,
                    TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id,
                )
                .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
                .filter(PageRecord.dataset_id == source_dataset_id)
                .all()
            )
            return sorted({row[0] for row in rows if row and row[0]})
        finally:
            session.close()

    def _fallback_vocabulary(self, rng: random.Random, size: int = 500) -> List[str]:
        """Build deterministic pseudo-vocabulary when source tokens are unavailable."""
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        vocab = set()
        while len(vocab) < size:
            length = rng.randint(3, 8)
            token = "".join(rng.choice(alphabet) for _ in range(length))
            vocab.add(token)
        return sorted(vocab)
