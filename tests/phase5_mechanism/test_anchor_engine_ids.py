from phase1_foundation.anchors.engine import AnchorEngine


class _StoreStub:
    def __init__(self) -> None:
        self.calls = []

    def add_anchor_method(self, **kwargs):
        self.calls.append(kwargs)


def test_method_id_is_deterministic_for_name_and_parameters() -> None:
    store = _StoreStub()
    engine = AnchorEngine(store=store, seed=42)

    id1 = engine.register_method(
        name="geometric_v1",
        description="test",
        parameters={"distance_threshold": 0.1},
    )
    id2 = engine.register_method(
        name="geometric_v1",
        description="test",
        parameters={"distance_threshold": 0.1},
    )

    assert id1 == id2


def test_method_id_changes_when_parameters_change() -> None:
    store = _StoreStub()
    engine = AnchorEngine(store=store, seed=42)

    id1 = engine.register_method(
        name="geometric_v1",
        description="test",
        parameters={"distance_threshold": 0.1},
    )
    id2 = engine.register_method(
        name="geometric_v1",
        description="test",
        parameters={"distance_threshold": 0.2},
    )

    assert id1 != id2


def test_anchor_id_is_deterministic_for_relation_tuple() -> None:
    engine = AnchorEngine(store=_StoreStub(), seed=42)

    id1 = engine._anchor_id(
        method_id="m1",
        page_id="f1r",
        source_id="w1",
        target_id="reg1",
        relation_type="inside",
    )
    id2 = engine._anchor_id(
        method_id="m1",
        page_id="f1r",
        source_id="w1",
        target_id="reg1",
        relation_type="inside",
    )
    id3 = engine._anchor_id(
        method_id="m1",
        page_id="f1r",
        source_id="w1",
        target_id="reg1",
        relation_type="near",
    )

    assert id1 == id2
    assert id1 != id3
