import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

pytestmark = pytest.mark.unit

from phase1_foundation.transcription.parsers import ParsedLine, ParsedToken  # noqa: E402
from phase11_stroke.extractor import StrokeExtractor  # noqa: E402
from phase11_stroke.schema import StrokeSchema  # noqa: E402


def _parsed_line(folio: str, line_index: int, tokens: list[str]) -> ParsedLine:
    return ParsedLine(
        folio=folio,
        line_index=line_index,
        content=" ".join(tokens),
        tokens=[ParsedToken(token_index=idx, content=token) for idx, token in enumerate(tokens)],
    )


def test_extractor_known_token_profiles_include_daiin() -> None:
    schema = StrokeSchema()
    extractor = StrokeExtractor(schema)
    parsed_lines = [_parsed_line("f1r", 1, ["daiin"])]
    extracted = extractor.extract_corpus(parsed_lines)

    occurrence = extracted["token_occurrences"][0]
    mean_profile = np.array(occurrence["mean_profile"], dtype=np.float64)
    boundary_profile = np.array(occurrence["boundary_profile"], dtype=np.float64)
    aggregate_profile = np.array(occurrence["aggregate_profile"], dtype=np.float64)

    assert np.allclose(mean_profile, np.array([0.0, 0.4, 0.0, 0.0, 0.4, 1.6]))
    assert np.allclose(
        boundary_profile,
        np.array([0.0, 1.0, 0.0, 0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0]),
    )
    assert np.allclose(aggregate_profile, np.array([0.0, 2.0, 0.0, 0.0, 2.0, 8.0]))


def test_extractor_handles_unknown_tokens_and_counts_skips() -> None:
    schema = StrokeSchema()
    extractor = StrokeExtractor(schema)
    parsed_lines = [
        _parsed_line("f1r", 1, ["daiin", "123"]),
        _parsed_line("f1r", 2, ["c?"]),
    ]
    extracted = extractor.extract_corpus(parsed_lines)

    unknown = next(item for item in extracted["token_occurrences"] if item["token"] == "123")
    assert unknown["recognized_char_count"] == 0
    assert unknown["skipped_char_count"] == 3
    assert np.allclose(np.array(unknown["mean_profile"], dtype=np.float64), np.zeros(6))

    assert extracted["corpus_stats"]["skipped_character_count"] == 4
    assert extracted["skipped_characters"]["by_symbol"]["1"] == 1
    assert extracted["skipped_characters"]["by_symbol"]["2"] == 1
    assert extracted["skipped_characters"]["by_symbol"]["3"] == 1
    assert extracted["skipped_characters"]["by_symbol"]["?"] == 1
