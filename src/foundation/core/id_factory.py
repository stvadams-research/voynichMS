"""
Deterministic ID Factory

Provides reproducible ID generation for analytical code paths.
Replaces random uuid4() calls to enable reproducibility.
"""

import hashlib
import uuid
from typing import Optional
import logging
logger = logging.getLogger(__name__)
from foundation.config import DEFAULT_SEED


class DeterministicIDFactory:
    """
    Factory for generating deterministic IDs based on a seed.

    Usage:
        factory = DeterministicIDFactory(seed=DEFAULT_SEED)
        id1 = factory.next_id("region")  # Deterministic based on seed + prefix + counter
        id2 = factory.next_id("anchor")  # Different prefix, still deterministic

    For reproducibility:
        factory1 = DeterministicIDFactory(seed=DEFAULT_SEED)
        factory2 = DeterministicIDFactory(seed=DEFAULT_SEED)
        assert factory1.next_id("test") == factory2.next_id("test")  # True
    """

    def __init__(self, seed: int = DEFAULT_SEED):
        """
        Initialize the factory with a seed.

        Args:
            seed: Integer seed for deterministic generation. Same seed produces
                  same sequence of IDs.
        """
        self.seed = seed
        self.counter = 0

    def next_id(self, prefix: str = "") -> str:
        """
        Generate the next deterministic ID.

        Args:
            prefix: Optional prefix for namespacing (e.g., "region", "anchor").
                    Different prefixes with the same counter will produce different IDs.

        Returns:
            A 32-character hexadecimal string (UUID-length without hyphens).
        """
        self.counter += 1
        data = f"{self.seed}:{prefix}:{self.counter}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def next_uuid(self, prefix: str = "") -> str:
        """
        Generate the next deterministic ID in UUID format.

        Args:
            prefix: Optional prefix for namespacing.

        Returns:
            A UUID-formatted string (with hyphens).
        """
        hex_id = self.next_id(prefix)
        # Format as UUID: 8-4-4-4-12
        return f"{hex_id[:8]}-{hex_id[8:12]}-{hex_id[12:16]}-{hex_id[16:20]}-{hex_id[20:32]}"

    def reset(self):
        """Reset the counter to start the sequence over."""
        self.counter = 0

    def fork(self, namespace: str) -> "DeterministicIDFactory":
        """
        Create a new factory with a derived seed for a specific namespace.

        Useful for creating isolated ID sequences within a larger run.

        Args:
            namespace: String to derive the new seed from.

        Returns:
            A new DeterministicIDFactory with a deterministically derived seed.
        """
        derived_seed_data = f"{self.seed}:{namespace}"
        derived_seed = int(hashlib.sha256(derived_seed_data.encode()).hexdigest()[:8], 16)
        return DeterministicIDFactory(seed=derived_seed)


# Global factory for convenience (can be reset for reproducibility)
_global_factory: Optional[DeterministicIDFactory] = None


def get_global_factory(seed: Optional[int] = None) -> DeterministicIDFactory:
    """
    Get the global ID factory, optionally reinitializing with a seed.

    Args:
        seed: If provided, reinitializes the global factory with this seed.
              If None, returns the existing factory or creates one with seed=0.

    Returns:
        The global DeterministicIDFactory instance.
    """
    global _global_factory

    if seed is not None:
        _global_factory = DeterministicIDFactory(seed=seed)
    elif _global_factory is None:
        _global_factory = DeterministicIDFactory(seed=0)

    return _global_factory


def deterministic_id(prefix: str = "", seed: Optional[int] = None) -> str:
    """
    Convenience function to generate a deterministic ID.

    Args:
        prefix: Optional prefix for namespacing.
        seed: If provided, reinitializes the global factory with this seed first.

    Returns:
        A 32-character hexadecimal string.
    """
    factory = get_global_factory(seed)
    return factory.next_id(prefix)


def deterministic_uuid(prefix: str = "", seed: Optional[int] = None) -> str:
    """
    Convenience function to generate a deterministic UUID.

    Args:
        prefix: Optional prefix for namespacing.
        seed: If provided, reinitializes the global factory with this seed first.

    Returns:
        A UUID-formatted string.
    """
    factory = get_global_factory(seed)
    return factory.next_uuid(prefix)
