import hashlib
import re
import uuid
from typing import NewType, Optional
from pydantic import BaseModel, Field, field_validator

class FolioID(str):
    """
    Canonical ID for a folio page (e.g., 'f1r', 'f102v1').
    Format: 'f' + number + 'r'/'v' + optional suffix
    """
    _pattern = re.compile(r"^f\d+[rv]\d*$")

    def __new__(cls, value: str):
        if not cls._pattern.match(value):
            raise ValueError(f"Invalid FolioID format: {value}. Must match {cls._pattern.pattern}")
        return super().__new__(cls, value)

class PageID(BaseModel):
    """
    Structured representation of a page identity.
    """
    folio: str
    
    @field_validator("folio")
    @classmethod
    def validate_folio(cls, v: str) -> str:
        # This will raise ValueError if invalid
        FolioID(v)
        return v

    def __str__(self) -> str:
        return self.folio

    def __hash__(self) -> int:
        return hash(self.folio)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PageID):
            return self.folio == other.folio
        return False

class RunID(str):
    """
    UUID-based identifier for a specific execution run.

    For reproducibility, provide a seed parameter to generate deterministic IDs:
        RunID(seed=42)  # Always produces the same ID for seed=42

    For random (non-reproducible) runs:
        RunID()  # Uses uuid4()

    To reuse an existing ID:
        RunID("existing-uuid-string")
    """
    def __new__(cls, value: Optional[str] = None, seed: Optional[int] = None):
        if value is None:
            if seed is not None:
                # Deterministic generation from seed
                from foundation.core.id_factory import DeterministicIDFactory
                factory = DeterministicIDFactory(seed=seed)
                value = factory.next_uuid("run")
            else:
                # Random generation (no longer allowed for reproducibility)
                raise ValueError("RunID must be provided or generated from a seed for reproducibility")
        else:
            # Validate it's a UUID
            try:
                uuid.UUID(value)
            except ValueError:
                raise ValueError(f"Invalid RunID: {value}")
        return super().__new__(cls, value)
