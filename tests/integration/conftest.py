"""
Integration test configuration.

Ensures the src directory is on the path for all integration tests.
"""

import sys
from pathlib import Path

# Add src directory to path for integration tests
src_path = str(Path(__file__).parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import pytest fixtures that should be available to all integration tests
import pytest
from phase1_foundation.storage.metadata import MetadataStore
from phase1_foundation.config import get_tracker, ComputationTracker
from phase1_foundation.core.randomness import get_randomness_controller, RandomnessController
