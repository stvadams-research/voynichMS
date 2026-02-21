"""Tests for RandomnessController — reproducibility enforcement.

Covers: three modes (FORBIDDEN, SEEDED, UNRESTRICTED), random module patching,
seed registration, context managers, decorators, and thread isolation.
"""

import random
import threading

import pytest

from phase1_foundation.core.randomness import (
    RandomnessController,
    RandomnessViolationError,
    SeedRecord,
    get_randomness_controller,
    no_randomness,
    requires_seed,
)

# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSingleton:
    def test_singleton_identity(self):
        a = RandomnessController()
        b = RandomnessController()
        assert a is b

    def test_get_randomness_controller_returns_singleton(self):
        ctrl = get_randomness_controller()
        assert ctrl is RandomnessController()


# ---------------------------------------------------------------------------
# FORBIDDEN mode (default)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestForbiddenMode:
    def test_default_mode_is_forbidden(self, clean_randomness):
        ctrl = clean_randomness
        assert ctrl._get_mode() == RandomnessController.FORBIDDEN

    def test_forbidden_context_raises_on_random(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.patch_random_module()
        with ctrl.forbidden_context("test_analysis"):
            with pytest.raises(RandomnessViolationError) as exc_info:
                random.random()
            assert "test_analysis" in str(exc_info.value)

    def test_forbidden_context_raises_on_randint(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.patch_random_module()
        with ctrl.forbidden_context("test"), pytest.raises(RandomnessViolationError):
            random.randint(1, 10)

    def test_forbidden_context_raises_on_uniform(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.patch_random_module()
        with ctrl.forbidden_context("test"), pytest.raises(RandomnessViolationError):
            random.uniform(0.0, 1.0)

    def test_forbidden_context_raises_on_choice(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.patch_random_module()
        with ctrl.forbidden_context("test"), pytest.raises(RandomnessViolationError):
            random.choice([1, 2, 3])

    def test_forbidden_context_raises_on_shuffle(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.patch_random_module()
        with ctrl.forbidden_context("test"), pytest.raises(RandomnessViolationError):
            random.shuffle([1, 2, 3])


# ---------------------------------------------------------------------------
# SEEDED mode
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSeededMode:
    def test_seeded_context_allows_random(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.patch_random_module()
        with ctrl.seeded_context("gen", seed=42):
            val = random.random()
            assert isinstance(val, float)

    def test_seeded_context_registers_seed(self, clean_randomness):
        ctrl = clean_randomness
        with ctrl.seeded_context("gen", seed=42, purpose="test"):
            pass
        log = ctrl.get_seed_log()
        assert len(log) == 1
        assert log[0].module == "gen"
        assert log[0].seed == 42
        assert log[0].purpose == "test"

    def test_seeded_context_is_reproducible(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.patch_random_module()

        with ctrl.seeded_context("gen", seed=42):
            vals1 = [random.random() for _ in range(5)]

        with ctrl.seeded_context("gen", seed=42):
            vals2 = [random.random() for _ in range(5)]

        assert vals1 == vals2

    def test_different_seeds_produce_different_output(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.patch_random_module()

        with ctrl.seeded_context("gen", seed=42):
            vals1 = [random.random() for _ in range(5)]

        with ctrl.seeded_context("gen", seed=99):
            vals2 = [random.random() for _ in range(5)]

        assert vals1 != vals2


# ---------------------------------------------------------------------------
# UNRESTRICTED mode
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestUnrestrictedMode:
    def test_unrestricted_allows_random(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.patch_random_module()
        with ctrl.unrestricted_context():
            val = random.random()
            assert isinstance(val, float)


# ---------------------------------------------------------------------------
# Patching / unpatching
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPatching:
    def test_patch_is_idempotent(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.patch_random_module()
        ctrl.patch_random_module()  # should not raise
        assert ctrl._patched is True

    def test_unpatch_is_idempotent(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.unpatch_random_module()
        ctrl.unpatch_random_module()  # should not raise
        assert ctrl._patched is False

    def test_unpatch_restores_originals(self, clean_randomness):
        ctrl = clean_randomness
        orig = random.random
        ctrl.patch_random_module()
        assert random.random is not orig
        ctrl.unpatch_random_module()
        assert random.random is orig

    def test_unpatched_random_works_normally(self, clean_randomness):
        """Without patching, random calls work even in FORBIDDEN mode."""
        ctrl = clean_randomness
        # Default mode is FORBIDDEN but random is not patched
        val = random.random()
        assert isinstance(val, float)


# ---------------------------------------------------------------------------
# Context nesting
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestContextNesting:
    def test_nested_contexts_restore_outer_mode(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.patch_random_module()

        with ctrl.seeded_context("outer", seed=1):
            assert ctrl._get_mode() == RandomnessController.SEEDED
            with ctrl.forbidden_context("inner"):
                assert ctrl._get_mode() == RandomnessController.FORBIDDEN
            assert ctrl._get_mode() == RandomnessController.SEEDED

    def test_context_restores_on_exception(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.patch_random_module()

        with ctrl.seeded_context("outer", seed=1):
            try:
                with ctrl.forbidden_context("inner"):
                    raise ValueError("boom")
            except ValueError:
                pass
            # Should be back to SEEDED
            assert ctrl._get_mode() == RandomnessController.SEEDED


# ---------------------------------------------------------------------------
# Seed log
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSeedLog:
    def test_register_seed_returns_seed(self, clean_randomness):
        ctrl = clean_randomness
        result = ctrl.register_seed("mod", 42, "test")
        assert result == 42

    def test_seed_log_returns_copy(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.register_seed("mod", 42)
        log = ctrl.get_seed_log()
        log.clear()
        assert len(ctrl.get_seed_log()) == 1

    def test_clear_seed_log(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.register_seed("mod", 42)
        ctrl.clear_seed_log()
        assert ctrl.get_seed_log() == []

    def test_seed_record_has_timestamp(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.register_seed("mod", 42)
        record = ctrl.get_seed_log()[0]
        assert isinstance(record, SeedRecord)
        assert record.timestamp is not None


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDecorators:
    def test_no_randomness_decorator(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.patch_random_module()

        @no_randomness
        def pure_function(x):
            return x * 2

        # Should work fine (no random calls inside)
        assert pure_function(5) == 10

    def test_no_randomness_decorator_catches_violation(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.patch_random_module()

        @no_randomness
        def impure_function():
            return random.random()

        with pytest.raises(RandomnessViolationError):
            impure_function()

    def test_requires_seed_decorator(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.patch_random_module()

        @requires_seed()
        def generate(seed=None):
            return random.random()

        result = generate(seed=42)
        assert isinstance(result, float)

    def test_requires_seed_without_seed_raises(self, clean_randomness):
        @requires_seed()
        def generate(seed=None):
            return 1

        with pytest.raises(ValueError, match="requires 'seed' parameter"):
            generate()

    def test_requires_seed_custom_param(self, clean_randomness):
        ctrl = clean_randomness
        ctrl.patch_random_module()

        @requires_seed(seed_param="my_seed")
        def generate(my_seed=None):
            return random.random()

        result = generate(my_seed=42)
        assert isinstance(result, float)

    def test_requires_seed_without_custom_param_raises(self, clean_randomness):
        @requires_seed(seed_param="my_seed")
        def generate(my_seed=None):
            return 1

        with pytest.raises(ValueError, match="requires 'my_seed' parameter"):
            generate()


# ---------------------------------------------------------------------------
# RandomnessViolationError
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestViolationError:
    def test_error_attributes(self):
        err = RandomnessViolationError(context="analysis", caller="func")
        assert err.context == "analysis"
        assert err.caller == "func"

    def test_error_message(self):
        err = RandomnessViolationError(context="analysis")
        assert "analysis" in str(err)
        assert "RANDOMNESS VIOLATION" in str(err)

    def test_is_exception_subclass(self):
        assert issubclass(RandomnessViolationError, Exception)


# ---------------------------------------------------------------------------
# Thread isolation
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_thread_isolation(clean_randomness):
    """Each thread has independent mode state."""
    ctrl = clean_randomness
    ctrl.patch_random_module()
    results = {}

    def thread_seeded():
        with ctrl.seeded_context("t1", seed=42):
            results["seeded_mode"] = ctrl._get_mode()
            results["seeded_val"] = random.random()

    def thread_forbidden():
        with ctrl.forbidden_context("t2"):
            results["forbidden_mode"] = ctrl._get_mode()

    t1 = threading.Thread(target=thread_seeded)
    t2 = threading.Thread(target=thread_forbidden)
    t1.start()
    t1.join()
    t2.start()
    t2.join()

    assert results["seeded_mode"] == RandomnessController.SEEDED
    assert results["forbidden_mode"] == RandomnessController.FORBIDDEN
    assert isinstance(results["seeded_val"], float)
