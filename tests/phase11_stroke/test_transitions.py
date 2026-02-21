import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

pytestmark = pytest.mark.unit

from phase1_foundation.transcription.parsers import ParsedLine, ParsedToken  # noqa: E402
from phase11_stroke.schema import StrokeSchema  # noqa: E402
from phase11_stroke.transitions import TransitionAnalyzer  # noqa: E402


def _line(idx: int, tokens: list[str]) -> ParsedLine:
    return ParsedLine(
        folio="f1r",
        line_index=idx,
        content=" ".join(tokens),
        tokens=[ParsedToken(token_index=t_idx, content=token) for t_idx, token in enumerate(tokens)],
    )


def test_transitions_detect_deterministic_boundary_structure() -> None:
    lines = []
    lines.extend([_line(i + 1, ["ai", "ta", "ai", "ta"]) for i in range(40)])
    lines.extend([_line(i + 41, ["ag", "ca", "ag", "ca"]) for i in range(40)])

    analyzer = TransitionAnalyzer(schema=StrokeSchema())
    result = analyzer.run(
        parsed_lines=lines,
        schema=StrokeSchema(),
        n_permutations=100,
        rng=np.random.default_rng(42),
    )

    assert result["B1_boundary_mi"] > 0.0
    assert result["B2_intra_mi"] > 0.0


def test_transitions_return_low_boundary_mi_on_randomized_sequences() -> None:
    rng = np.random.default_rng(123)
    token_bank = ["ai", "ta", "ag", "ca"]
    lines = []
    for idx in range(60):
        tokens = [token_bank[int(rng.integers(0, len(token_bank)))] for _ in range(5)]
        lines.append(_line(idx + 1, tokens))

    analyzer = TransitionAnalyzer(schema=StrokeSchema())
    result = analyzer.run(
        parsed_lines=lines,
        schema=StrokeSchema(),
        n_permutations=80,
        rng=np.random.default_rng(7),
    )

    assert result["B1_boundary_mi"] >= 0.0
    assert result["B1_boundary_mi"] < 0.5


def test_information_ratio_helper_is_correct() -> None:
    assert TransitionAnalyzer.information_ratio(0.5, 1.0) == 0.5
    assert TransitionAnalyzer.information_ratio(0.5, 0.0) == 0.0
