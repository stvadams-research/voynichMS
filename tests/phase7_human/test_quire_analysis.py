from phase7_human.quire_analysis import QuireAnalyzer


def test_get_quire_with_valid_folio_ids():
    analyzer = QuireAnalyzer()

    assert analyzer.get_quire("f1r") == 1
    assert analyzer.get_quire("f8v") == 1
    assert analyzer.get_quire("f9r") == 2
    assert analyzer.get_quire("f16v") == 2


def test_get_quire_with_malformed_folio_logs_and_returns_zero(caplog):
    analyzer = QuireAnalyzer()

    with caplog.at_level("WARNING"):
        quire = analyzer.get_quire("folio_without_digits")

    assert quire == 0
    assert "Failed to parse quire" in caplog.text


def test_analyze_continuity_groups_pages_by_quire():
    analyzer = QuireAnalyzer()
    pages = {
        "f1r": [["a", "bb"], ["ccc"]],
        "f2v": [["dddd"]],
        "f9r": [["ee", "fff"]],
    }

    result = analyzer.analyze_continuity(pages)

    assert result["num_quires"] == 2
    assert set(result["quire_means"].keys()) == {1, 2}
    assert "between_quire_variance" in result
