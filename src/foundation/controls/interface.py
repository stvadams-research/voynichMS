from abc import ABC, abstractmethod
import re
from typing import Any, Dict, List, Tuple

from foundation.storage.metadata import MetadataStore
import logging

logger = logging.getLogger(__name__)

_NORMALIZED_TOKEN_PATTERN = re.compile(r"^[a-z]+$")

class ControlGenerator(ABC):
    VALID_NORMALIZATION_MODES = ("parser", "pre_normalized_with_assertions")

    def __init__(self, store: MetadataStore):
        self.store = store

    @abstractmethod
    def generate(self, source_dataset_id: str, control_id: str, seed: int = 42, params: Dict[str, Any] = None) -> str:
        """
        Generate a control dataset.
        Returns the ID of the generated control dataset.
        """
        pass

    def _resolve_normalization_mode(self, params: Dict[str, Any] | None) -> str:
        params = params or {}
        mode = str(params.get("normalization_mode", "parser"))
        if mode not in self.VALID_NORMALIZATION_MODES:
            raise ValueError(
                f"Invalid normalization_mode={mode!r}. "
                f"Allowed: {self.VALID_NORMALIZATION_MODES}"
            )
        return mode

    def _normalize_token(self, token: str, mode: str) -> str:
        token_str = str(token or "").strip()
        if mode == "parser":
            # Parser mode canonicalizes tokens for symmetry with real-data path.
            normalized = re.sub(r"[^a-z]", "", token_str.lower())
            if not normalized:
                raise ValueError(f"Token cannot be normalized in parser mode: {token!r}")
            return normalized

        if not _NORMALIZED_TOKEN_PATTERN.fullmatch(token_str):
            raise ValueError(
                "Token violates pre_normalized_with_assertions mode; "
                f"expected lowercase alpha token, got {token!r}"
            )
        return token_str

    def _normalize_tokens_for_control(
        self, tokens: List[str], *, mode: str
    ) -> Tuple[List[str], Dict[str, Any]]:
        normalized = [self._normalize_token(token, mode) for token in tokens]
        provenance = {
            "normalization_mode": mode,
            "token_count": len(normalized),
            "normalization_symmetry": (
                "parser-equivalent canonicalization"
                if mode == "parser"
                else "pre-normalized token assertion"
            ),
        }
        return normalized, provenance
