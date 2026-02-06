import re
import uuid
from typing import NewType
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
    """
    def __new__(cls, value: str | None = None):
        if value is None:
            value = str(uuid.uuid4())
        else:
            # Validate it's a UUID
            try:
                uuid.UUID(value)
            except ValueError:
                raise ValueError(f"Invalid RunID: {value}")
        return super().__new__(cls, value)
