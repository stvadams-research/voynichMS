"""Tests for DeterministicIDFactory and module-level convenience functions."""

import re

import pytest

from phase1_foundation.core.id_factory import (
    DeterministicIDFactory,
    deterministic_id,
    deterministic_uuid,
    get_global_factory,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# DeterministicIDFactory core behaviour
# ---------------------------------------------------------------------------

class TestDeterministicIDFactory:

    def test_same_seed_produces_same_ids(self):
        f1 = DeterministicIDFactory(seed=42)
        f2 = DeterministicIDFactory(seed=42)
        assert f1.next_id("x") == f2.next_id("x")
        assert f1.next_id("x") == f2.next_id("x")

    def test_different_seeds_produce_different_ids(self):
        f1 = DeterministicIDFactory(seed=1)
        f2 = DeterministicIDFactory(seed=2)
        assert f1.next_id("x") != f2.next_id("x")

    def test_different_prefixes_produce_different_ids(self):
        f = DeterministicIDFactory(seed=42)
        id_a = f.next_id("region")
        f2 = DeterministicIDFactory(seed=42)
        # Advance to same counter position but with different prefix
        id_b = f2.next_id("anchor")
        assert id_a != id_b

    def test_sequential_ids_are_unique(self):
        f = DeterministicIDFactory(seed=0)
        ids = [f.next_id("test") for _ in range(100)]
        assert len(set(ids)) == 100

    def test_id_format_is_32_hex_chars(self):
        f = DeterministicIDFactory(seed=42)
        hex_id = f.next_id("prefix")
        assert len(hex_id) == 32
        assert re.fullmatch(r"[0-9a-f]{32}", hex_id)

    def test_empty_prefix_works(self):
        f = DeterministicIDFactory(seed=42)
        hex_id = f.next_id()
        assert len(hex_id) == 32

    def test_counter_increments(self):
        f = DeterministicIDFactory(seed=42)
        assert f.counter == 0
        f.next_id()
        assert f.counter == 1
        f.next_id()
        assert f.counter == 2


# ---------------------------------------------------------------------------
# next_uuid
# ---------------------------------------------------------------------------

class TestNextUUID:

    def test_uuid_format(self):
        f = DeterministicIDFactory(seed=42)
        uid = f.next_uuid("test")
        # UUID format: 8-4-4-4-12
        assert re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            uid,
        )

    def test_uuid_deterministic(self):
        f1 = DeterministicIDFactory(seed=7)
        f2 = DeterministicIDFactory(seed=7)
        assert f1.next_uuid("a") == f2.next_uuid("a")

    def test_uuid_uses_same_counter_as_next_id(self):
        """next_uuid and next_id share the same counter."""
        f = DeterministicIDFactory(seed=42)
        f.next_uuid("x")
        assert f.counter == 1
        f.next_id("y")
        assert f.counter == 2


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------

class TestReset:

    def test_reset_reproduces_sequence(self):
        f = DeterministicIDFactory(seed=42)
        first_run = [f.next_id("t") for _ in range(5)]
        f.reset()
        second_run = [f.next_id("t") for _ in range(5)]
        assert first_run == second_run

    def test_reset_zeroes_counter(self):
        f = DeterministicIDFactory(seed=42)
        f.next_id()
        f.next_id()
        f.reset()
        assert f.counter == 0


# ---------------------------------------------------------------------------
# fork
# ---------------------------------------------------------------------------

class TestFork:

    def test_fork_produces_different_ids(self):
        parent = DeterministicIDFactory(seed=42)
        child = parent.fork("namespace_a")
        assert parent.next_id("x") != child.next_id("x")

    def test_fork_is_deterministic(self):
        p1 = DeterministicIDFactory(seed=42)
        p2 = DeterministicIDFactory(seed=42)
        c1 = p1.fork("ns")
        c2 = p2.fork("ns")
        assert c1.next_id("t") == c2.next_id("t")

    def test_different_namespaces_produce_different_forks(self):
        parent = DeterministicIDFactory(seed=42)
        c1 = parent.fork("ns_a")
        c2 = parent.fork("ns_b")
        assert c1.next_id("t") != c2.next_id("t")

    def test_fork_does_not_affect_parent_counter(self):
        parent = DeterministicIDFactory(seed=42)
        parent.next_id()
        parent.fork("ns")
        assert parent.counter == 1  # fork should not increment


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

class TestGlobalFactory:

    def test_get_global_factory_creates_singleton(self):
        f1 = get_global_factory(seed=99)
        f2 = get_global_factory()
        assert f1 is f2

    def test_get_global_factory_reinit_with_seed(self):
        f1 = get_global_factory(seed=100)
        f2 = get_global_factory(seed=200)
        assert f1 is not f2
        assert f2.seed == 200

    def test_deterministic_id_returns_hex(self):
        hex_id = deterministic_id("test", seed=42)
        assert len(hex_id) == 32
        assert re.fullmatch(r"[0-9a-f]{32}", hex_id)

    def test_deterministic_uuid_returns_uuid_format(self):
        uid = deterministic_uuid("test", seed=42)
        assert re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            uid,
        )
