import pytest
from pydantic import ValidationError

pytestmark = pytest.mark.unit

from phase1_foundation.runs.context import RunContext
from phase1_foundation.runs.manager import RunManager, active_run


def test_run_context_requires_run_id() -> None:
    with pytest.raises(ValidationError):
        RunContext()


def test_active_run_unique_run_id_for_same_seed() -> None:
    with active_run(config={"command": "run_1", "seed": 42}, capture_env=False) as run_1:
        run_id_1 = str(run_1.run_id)
        experiment_id_1 = run_1.config.get("experiment_id")
        assert run_1.config.get("run_nonce") is not None

    with active_run(config={"command": "run_2", "seed": 42}, capture_env=False) as run_2:
        run_id_2 = str(run_2.run_id)
        experiment_id_2 = run_2.config.get("experiment_id")
        assert run_2.config.get("run_nonce") is not None

    assert run_id_1 != run_id_2
    assert experiment_id_1 == experiment_id_2
    assert not RunManager.has_active_run()

