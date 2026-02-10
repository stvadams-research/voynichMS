from synthesis.interface import PageProfile, SectionProfile
from synthesis.text_generator import ConstrainedMarkovGenerator


def _sample_section_profile() -> SectionProfile:
    page = PageProfile(
        page_id="f88r",
        jar_count=2,
        total_lines=8,
        total_words=32,
    )
    profile = SectionProfile(
        pages=[page],
        jar_count_range=(2, 3),
        lines_per_block_range=(2, 4),
        words_per_line_range=(3, 6),
    )
    return profile


def test_train_on_known_sequence_builds_expected_transition():
    generator = ConstrainedMarkovGenerator(order=2, seed=42)

    generator._train_on_sequence(["a", "b", "c"])

    assert ("a", "b") in generator.states
    state = generator.states[("a", "b")]
    assert state.transitions["c"] == 1
    assert state.total == 1


def test_generate_line_is_deterministic_with_fixed_seed():
    profile = _sample_section_profile()

    g1 = ConstrainedMarkovGenerator(order=2, seed=123)
    g2 = ConstrainedMarkovGenerator(order=2, seed=123)
    g1.train(profile)
    g2.train(profile)

    line1 = g1.generate_line(target_length=10)
    line2 = g2.generate_line(target_length=10)

    assert line1 == line2


def test_generate_line_handles_zero_length():
    generator = ConstrainedMarkovGenerator(order=2, seed=99)
    line = generator.generate_line(target_length=0)
    assert line == []


def test_generate_line_handles_single_token_request():
    generator = ConstrainedMarkovGenerator(order=2, seed=101)
    line = generator.generate_line(target_length=1)
    assert len(line) == 1
