import os
from unittest.mock import patch

import pytest

from phase1_foundation.config import ComputationTracker, SimulationViolationError

pytestmark = pytest.mark.unit


def test_enforcement_enabled():
    """Test that REQUIRE_COMPUTED=1 raises error on simulation."""
    with patch.dict(os.environ, {"REQUIRE_COMPUTED": "1"}):
        # Re-initialize tracker to pick up env var
        tracker = ComputationTracker()
        tracker._initialized = False
        tracker.__init__()
        
        assert tracker.require_computed is True
        
        with pytest.raises(SimulationViolationError):
            tracker.record_simulated("test_component", "test_cat", "testing enforcement")

def test_enforcement_disabled():
    """Test that REQUIRE_COMPUTED=0 allows simulation."""
    with patch.dict(os.environ, {"REQUIRE_COMPUTED": "0"}):
        # Re-initialize tracker
        tracker = ComputationTracker()
        tracker._initialized = False
        tracker.__init__()
        
        assert tracker.require_computed is False
        
        # Should not raise
        tracker.record_simulated("test_component", "test_cat", "testing allowed")
