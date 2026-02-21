"""
Phase 4 Inference — Unit Tests

Tests the 5 main analyzers and projection_diagnostics sub-modules.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Shared synthetic data
# ---------------------------------------------------------------------------

TOKENS_SMALL = ["a", "b", "c", "a", "b", "d", "a", "c", "b", "e"]
TOKENS_MEDIUM = (["alpha", "beta", "gamma", "delta", "epsilon"] * 40)
TOKENS_REPEAT = ["x"] * 50
TOKENS_EMPTY: list[str] = []

LINES_SMALL = [["a", "b", "c", "d"], ["e", "f", "g", "h"], ["a", "b", "e", "f"]]
LINES_MEDIUM = [["w" + str(j) for j in range(6)] for _ in range(30)]


# ===================================================================
# MontemurroAnalyzer (info_clustering)
# ===================================================================

class TestMontemurroAnalyzer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase4_inference.info_clustering.analyzer import MontemurroAnalyzer
        self.analyzer = MontemurroAnalyzer(num_sections=5)

    def test_empty_tokens_returns_no_data(self):
        result = self.analyzer.calculate_information(TOKENS_EMPTY)
        assert result.get("status") == "no_data" or result.get("num_tokens", 0) == 0

    def test_basic_output_keys(self):
        tokens = TOKENS_MEDIUM
        result = self.analyzer.calculate_information(tokens)
        assert "num_tokens" in result
        assert "num_unique" in result
        assert "word_info" in result

    def test_num_tokens_matches_input(self):
        tokens = TOKENS_MEDIUM
        result = self.analyzer.calculate_information(tokens)
        assert result["num_tokens"] == len(tokens)

    def test_num_unique_correct(self):
        result = self.analyzer.calculate_information(TOKENS_MEDIUM)
        assert result["num_unique"] == 5

    def test_word_info_is_sorted_descending(self):
        result = self.analyzer.calculate_information(TOKENS_MEDIUM)
        infos = [v for _, v in result["word_info"]]
        assert infos == sorted(infos, reverse=True)

    def test_uniform_tokens_low_information(self):
        # Uniform distribution => info per word should be near 0
        result = self.analyzer.calculate_information(TOKENS_REPEAT)
        if result.get("word_info"):
            assert all(v < 0.01 for _, v in result["word_info"])

    def test_summary_metrics_keys(self):
        info = self.analyzer.calculate_information(TOKENS_MEDIUM)
        summary = self.analyzer.get_summary_metrics(info)
        assert "avg_info" in summary
        assert "max_info" in summary
        assert "num_keywords" in summary

    def test_summary_max_geq_avg(self):
        info = self.analyzer.calculate_information(TOKENS_MEDIUM)
        summary = self.analyzer.get_summary_metrics(info)
        assert summary["max_info"] >= summary["avg_info"]

    def test_custom_num_sections(self):
        from phase4_inference.info_clustering.analyzer import MontemurroAnalyzer
        a = MontemurroAnalyzer(num_sections=2)
        result = a.calculate_information(TOKENS_MEDIUM)
        assert result["num_tokens"] == len(TOKENS_MEDIUM)


# ===================================================================
# NetworkAnalyzer (network_features)
# ===================================================================

class TestNetworkAnalyzer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase4_inference.network_features.analyzer import NetworkAnalyzer
        self.analyzer = NetworkAnalyzer(max_tokens=500)

    def test_empty_returns_no_data(self):
        result = self.analyzer.analyze(TOKENS_EMPTY)
        assert result["status"] == "no_data"
        assert result["num_nodes"] == 0

    def test_basic_output_keys(self):
        result = self.analyzer.analyze(TOKENS_SMALL)
        for key in ("num_nodes", "num_edges", "avg_degree", "avg_clustering",
                     "assortativity", "zipf_alpha", "vocabulary_size", "ttr"):
            assert key in result, f"Missing key: {key}"

    def test_vocabulary_size_correct(self):
        result = self.analyzer.analyze(TOKENS_SMALL)
        assert result["vocabulary_size"] == len(set(TOKENS_SMALL))

    def test_ttr_range(self):
        result = self.analyzer.analyze(TOKENS_MEDIUM)
        assert 0.0 <= result["ttr"] <= 1.0

    def test_all_same_tokens_graph(self):
        result = self.analyzer.analyze(TOKENS_REPEAT)
        assert result["num_nodes"] == 1
        assert result["num_edges"] == 1

    def test_max_tokens_limits_network(self):
        from phase4_inference.network_features.analyzer import NetworkAnalyzer
        analyzer = NetworkAnalyzer(max_tokens=5)
        tokens = list("abcdefghij")
        result = analyzer.analyze(tokens)
        # Should build graph on first 5 tokens only
        assert result["num_nodes"] <= 5

    def test_zipf_alpha_positive_for_natural_dist(self):
        # Create Zipf-like distribution
        tokens = (["a"] * 100 + ["b"] * 50 + ["c"] * 25 + ["d"] * 12 +
                  ["e"] * 6 + ["f"] * 3 + ["g"] * 2 + ["h"] * 1)
        result = self.analyzer.analyze(tokens)
        assert result["zipf_alpha"] > 0

    def test_clustering_range(self):
        result = self.analyzer.analyze(TOKENS_MEDIUM)
        assert 0.0 <= result["avg_clustering"] <= 1.0


# ===================================================================
# LanguageIDAnalyzer (lang_id_transforms)
# ===================================================================

class TestLanguageIDAnalyzer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase4_inference.lang_id_transforms.analyzer import LanguageIDAnalyzer
        self.analyzer = LanguageIDAnalyzer()

    def test_build_profile_stores_language(self):
        self.analyzer.build_profile("english", "the quick brown fox jumps over the lazy dog")
        assert "english" in self.analyzer.language_profiles

    def test_score_match_self_similarity(self):
        text = "the quick brown fox jumps over the lazy dog"
        self.analyzer.build_profile("english", text)
        score = self.analyzer.score_match(text, "english")
        assert score > 0.9  # Self-match should be high

    def test_score_match_empty_returns_zero(self):
        self.analyzer.build_profile("english", "test text here")
        score = self.analyzer.score_match("", "english")
        assert score == 0.0

    def test_score_match_range(self):
        self.analyzer.build_profile("english", "the quick brown fox")
        score = self.analyzer.score_match("another text entirely different", "english")
        assert 0.0 <= score <= 1.0

    def test_find_best_transform_returns_tuple(self):
        self.analyzer.build_profile("english", "the quick brown fox")
        transforms = [{"a": "t", "b": "h"}, {"x": "z"}]
        score, mapping = self.analyzer.find_best_transform("abe abe", "english", transforms)
        assert isinstance(score, float)
        assert isinstance(mapping, dict)

    def test_different_languages_different_profiles(self):
        self.analyzer.build_profile("english", "the quick brown fox jumps")
        self.analyzer.build_profile("spanish", "el rapido zorro marron salta")
        assert self.analyzer.language_profiles["english"] != self.analyzer.language_profiles["spanish"]


# ===================================================================
# MorphologyAnalyzer (morph_induction)
# ===================================================================

class TestMorphologyAnalyzer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase4_inference.morph_induction.analyzer import MorphologyAnalyzer
        self.analyzer = MorphologyAnalyzer(min_affix_len=1, max_affix_len=3)

    def test_empty_returns_no_data(self):
        result = self.analyzer.analyze(TOKENS_EMPTY)
        assert result.get("status") == "no_data"

    def test_basic_output_keys(self):
        result = self.analyzer.analyze(TOKENS_MEDIUM)
        assert "num_unique_tokens" in result
        assert "top_suffixes" in result
        assert "morph_consistency" in result

    def test_num_unique_tokens_correct(self):
        result = self.analyzer.analyze(TOKENS_MEDIUM)
        assert result["num_unique_tokens"] == len(set(TOKENS_MEDIUM))

    def test_suffix_extraction(self):
        # Tokens with shared suffixes
        tokens = ["walking", "talking", "running", "jumping"] * 10
        result = self.analyzer.analyze(tokens)
        suffixes = [s for s, _ in result["top_suffixes"]]
        assert "g" in suffixes  # -g is suffix of all words

    def test_consistency_range(self):
        result = self.analyzer.analyze(TOKENS_MEDIUM)
        assert 0.0 <= result["morph_consistency"] <= 1.0

    def test_custom_affix_lengths(self):
        from phase4_inference.morph_induction.analyzer import MorphologyAnalyzer
        analyzer = MorphologyAnalyzer(min_affix_len=2, max_affix_len=2)
        tokens = ["walking", "talking", "running"] * 20
        result = analyzer.analyze(tokens)
        suffixes = [s for s, _ in result["top_suffixes"]]
        # All suffixes should be length 2
        assert all(len(s) == 2 for s in suffixes)


# ===================================================================
# TopicAnalyzer (topic_models)
# ===================================================================

class TestTopicAnalyzer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase4_inference.topic_models.analyzer import TopicAnalyzer
        self.analyzer = TopicAnalyzer(num_topics=3, num_sections=4)

    def test_empty_returns_no_data(self):
        result = self.analyzer.analyze(TOKENS_EMPTY)
        assert result.get("status") == "no_data"

    def test_basic_output_keys(self):
        # Need enough tokens for meaningful LDA
        tokens = (["cat", "dog", "fish"] * 30 + ["car", "bus", "train"] * 30 +
                  ["tree", "flower", "grass"] * 30)
        result = self.analyzer.analyze(tokens)
        assert "num_topics" in result
        assert "num_sections" in result
        assert "topic_words" in result

    def test_num_topics_matches_config(self):
        tokens = (["cat", "dog", "fish"] * 30 + ["car", "bus", "train"] * 30 +
                  ["tree", "flower", "grass"] * 30)
        result = self.analyzer.analyze(tokens)
        if result.get("status") != "no_data":
            assert result["num_topics"] == 3

    def test_topic_words_are_lists_of_strings(self):
        tokens = (["cat", "dog", "fish"] * 50 + ["car", "bus", "train"] * 50)
        result = self.analyzer.analyze(tokens)
        if "topic_words" in result:
            for topic in result["topic_words"]:
                assert isinstance(topic, list)
                for word in topic:
                    assert isinstance(word, str)


# ===================================================================
# LineResetMarkovGenerator (projection_diagnostics)
# ===================================================================

class TestLineResetMarkovGenerator:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase4_inference.projection_diagnostics.line_reset_markov import (
            LineResetMarkovConfig,
            LineResetMarkovGenerator,
        )
        self.GeneratorClass = LineResetMarkovGenerator
        self.ConfigClass = LineResetMarkovConfig

    def test_fit_on_empty_raises(self):
        gen = self.GeneratorClass()
        with pytest.raises(ValueError):
            gen.fit([])

    def test_generate_before_fit_raises(self):
        gen = self.GeneratorClass()
        with pytest.raises(RuntimeError):
            gen.generate(100)

    def test_fit_and_generate_produces_tokens(self):
        gen = self.GeneratorClass(config=self.ConfigClass(random_state=42))
        gen.fit(LINES_SMALL)
        result = gen.generate(20)
        assert "tokens" in result
        assert "lines" in result
        assert len(result["tokens"]) >= 20

    def test_reproducibility_with_same_seed(self):
        gen1 = self.GeneratorClass(config=self.ConfigClass(random_state=42))
        gen1.fit(LINES_SMALL)
        r1 = gen1.generate(50)

        gen2 = self.GeneratorClass(config=self.ConfigClass(random_state=42))
        gen2.fit(LINES_SMALL)
        r2 = gen2.generate(50)

        assert r1["tokens"] == r2["tokens"]

    def test_different_seeds_differ(self):
        # Use varied lines so the Markov model has non-trivial distributions
        varied_lines = [
            ["a", "b", "c", "d", "e"],
            ["b", "c", "a", "e", "d"],
            ["c", "a", "d", "b", "e"],
            ["d", "e", "b", "a", "c"],
            ["a", "d", "c", "e", "b"],
            ["e", "b", "a", "d", "c"],
        ]
        gen1 = self.GeneratorClass(config=self.ConfigClass(random_state=42))
        gen1.fit(varied_lines)
        r1 = gen1.generate(100)

        gen2 = self.GeneratorClass(config=self.ConfigClass(random_state=99))
        gen2.fit(varied_lines)
        r2 = gen2.generate(100)

        assert r1["tokens"] != r2["tokens"]

    def test_fit_stats_keys(self):
        gen = self.GeneratorClass(config=self.ConfigClass(random_state=42))
        gen.fit(LINES_SMALL)
        stats = gen.fit_stats()
        for key in ("num_lines", "vocab_size", "start_vocab_size",
                     "transition_states", "avg_line_length"):
            assert key in stats

    def test_fit_stats_num_lines(self):
        gen = self.GeneratorClass(config=self.ConfigClass(random_state=42))
        gen.fit(LINES_SMALL)
        assert gen.fit_stats()["num_lines"] == len(LINES_SMALL)


# ===================================================================
# LineResetBackoffGenerator (projection_diagnostics)
# ===================================================================

class TestLineResetBackoffGenerator:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase4_inference.projection_diagnostics.line_reset_backoff import (
            LineResetBackoffConfig,
            LineResetBackoffGenerator,
        )
        self.GeneratorClass = LineResetBackoffGenerator
        self.ConfigClass = LineResetBackoffConfig

    def test_fit_and_generate(self):
        gen = self.GeneratorClass(config=self.ConfigClass(random_state=42))
        gen.fit(LINES_SMALL)
        result = gen.generate(30)
        assert len(result["tokens"]) >= 30

    def test_fit_stats_has_trigram_states(self):
        gen = self.GeneratorClass(config=self.ConfigClass(random_state=42))
        gen.fit(LINES_MEDIUM)
        stats = gen.fit_stats()
        assert "trigram_states" in stats
        assert "bigram_states" in stats

    def test_reproducibility(self):
        gen1 = self.GeneratorClass(config=self.ConfigClass(random_state=7))
        gen1.fit(LINES_MEDIUM)
        r1 = gen1.generate(80)

        gen2 = self.GeneratorClass(config=self.ConfigClass(random_state=7))
        gen2.fit(LINES_MEDIUM)
        r2 = gen2.generate(80)

        assert r1["tokens"] == r2["tokens"]


# ===================================================================
# LineResetPersistenceGenerator (projection_diagnostics)
# ===================================================================

class TestLineResetPersistenceGenerator:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase4_inference.projection_diagnostics.line_reset_persistence import (
            LineResetPersistenceConfig,
            LineResetPersistenceGenerator,
        )
        self.GeneratorClass = LineResetPersistenceGenerator
        self.ConfigClass = LineResetPersistenceConfig

    def test_fit_and_generate(self):
        gen = self.GeneratorClass(config=self.ConfigClass(random_state=42))
        gen.fit(LINES_SMALL)
        result = gen.generate(30)
        assert len(result["tokens"]) >= 30

    def test_fit_stats_has_boundary_states(self):
        gen = self.GeneratorClass(config=self.ConfigClass(random_state=42))
        gen.fit(LINES_MEDIUM)
        stats = gen.fit_stats()
        assert "boundary_bigram_states" in stats
        assert "boundary_trigram_states" in stats


# ===================================================================
# KolmogorovProxyAnalyzer (projection_diagnostics)
# ===================================================================

class TestKolmogorovProxyAnalyzer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase4_inference.projection_diagnostics.kolmogorov_proxy import (
            KolmogorovProxyAnalyzer,
            KolmogorovProxyConfig,
        )
        self.analyzer = KolmogorovProxyAnalyzer(
            config=KolmogorovProxyConfig(
                token_limit=200, permutations=5, random_state=42
            )
        )

    def test_basic_output_keys(self):
        dataset_tokens = {"ds1": TOKENS_MEDIUM, "ds2": TOKENS_REPEAT}
        result = self.analyzer.analyze(dataset_tokens)
        assert result["status"] == "ok"
        assert "datasets" in result

    def test_per_dataset_results(self):
        dataset_tokens = {"ds1": TOKENS_MEDIUM}
        result = self.analyzer.analyze(dataset_tokens)
        ds = result["datasets"]["ds1"]
        assert "codec_results" in ds
        assert "token_count" in ds

    def test_compression_ratio_positive(self):
        dataset_tokens = {"ds1": TOKENS_MEDIUM}
        result = self.analyzer.analyze(dataset_tokens)
        ds = result["datasets"]["ds1"]
        for codec, cr in ds["codec_results"].items():
            assert cr["observed_compression_ratio"] > 0

    def test_repeated_tokens_compress_well(self):
        dataset_tokens = {
            "repeat": TOKENS_REPEAT,
            "varied": list("abcdefghijklmnopqrstuvwxyz") * 5,
        }
        result = self.analyzer.analyze(dataset_tokens)
        repeat_ratio = None
        varied_ratio = None
        for codec in result["datasets"]["repeat"]["codec_results"]:
            repeat_ratio = result["datasets"]["repeat"]["codec_results"][codec]["observed_compression_ratio"]
            varied_ratio = result["datasets"]["varied"]["codec_results"][codec]["observed_compression_ratio"]
            break
        assert repeat_ratio < varied_ratio  # Repeated text compresses better


# ===================================================================
# NCDAnalyzer (projection_diagnostics)
# ===================================================================

class TestNCDAnalyzer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase4_inference.projection_diagnostics.ncd import NCDAnalyzer, NCDConfig
        self.analyzer = NCDAnalyzer(
            config=NCDConfig(
                token_limit=200, bootstraps=5, block_size=10,
                random_state=42, focus_dataset_id="ds1",
            )
        )

    def test_basic_output(self):
        dataset_tokens = {
            "ds1": TOKENS_MEDIUM,
            "ds2": ["x", "y", "z"] * 60,
        }
        result = self.analyzer.analyze(dataset_tokens)
        assert result["status"] == "ok"
        assert "point_estimate_ncd" in result

    def test_ncd_self_distance_low(self):
        dataset_tokens = {
            "ds1": TOKENS_MEDIUM,
            "ds2": ["x", "y", "z"] * 60,
        }
        result = self.analyzer.analyze(dataset_tokens)
        ncd = result["point_estimate_ncd"]
        # Self-NCD should be 0 or very small
        assert ncd["ds1"]["ds1"] < 0.1

    def test_ncd_range(self):
        dataset_tokens = {
            "ds1": TOKENS_MEDIUM,
            "ds2": ["x", "y", "z"] * 60,
        }
        result = self.analyzer.analyze(dataset_tokens)
        ncd = result["point_estimate_ncd"]
        for a in ncd:
            for b in ncd[a]:
                assert 0.0 <= ncd[a][b] <= 1.5  # NCD is usually [0, 1+epsilon]


# ===================================================================
# OrderConstraintAnalyzer (projection_diagnostics)
# ===================================================================

class TestOrderConstraintAnalyzer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase4_inference.projection_diagnostics.order_constraints import (
            OrderConstraintAnalyzer,
            OrderConstraintConfig,
        )
        self.analyzer = OrderConstraintAnalyzer(
            config=OrderConstraintConfig(
                token_limit=200, vocab_limit=50, permutations=5, random_state=42,
            )
        )

    def test_basic_output(self):
        dataset_tokens = {"ds1": TOKENS_MEDIUM}
        result = self.analyzer.analyze(dataset_tokens)
        assert result["status"] == "ok"
        assert "datasets" in result

    def test_metrics_present(self):
        dataset_tokens = {"ds1": TOKENS_MEDIUM}
        result = self.analyzer.analyze(dataset_tokens)
        ds = result["datasets"]["ds1"]
        assert "metrics" in ds
        metrics = ds["metrics"]
        assert "bigram_cond_entropy" in metrics

    def test_permutation_p_value_range(self):
        dataset_tokens = {"ds1": TOKENS_MEDIUM}
        result = self.analyzer.analyze(dataset_tokens)
        ds = result["datasets"]["ds1"]
        for metric_name, m in ds["metrics"].items():
            assert 0.0 <= m["p_directional"] <= 1.0


# ===================================================================
# MusicStreamControlBuilder (projection_diagnostics)
# ===================================================================

class TestMusicStreamControlBuilder:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase4_inference.projection_diagnostics.music_stream_controls import (
            MusicStreamConfig,
            MusicStreamControlBuilder,
        )
        self.builder = MusicStreamControlBuilder(
            config=MusicStreamConfig(target_tokens=500, random_state=42)
        )

    def test_build_control_status(self):
        reference = TOKENS_MEDIUM
        result = self.builder.build_control(reference)
        assert result["status"] == "ok"

    def test_output_token_count(self):
        reference = TOKENS_MEDIUM
        result = self.builder.build_control(reference)
        assert result["generated_tokens"] == 500

    def test_tokens_are_strings(self):
        reference = TOKENS_MEDIUM
        result = self.builder.build_control(reference)
        assert all(isinstance(t, str) for t in result["tokens"])

    def test_reproducibility(self):
        from phase4_inference.projection_diagnostics.music_stream_controls import (
            MusicStreamConfig,
            MusicStreamControlBuilder,
        )
        b1 = MusicStreamControlBuilder(config=MusicStreamConfig(target_tokens=100, random_state=42))
        b2 = MusicStreamControlBuilder(config=MusicStreamConfig(target_tokens=100, random_state=42))
        r1 = b1.build_control(TOKENS_MEDIUM)
        r2 = b2.build_control(TOKENS_MEDIUM)
        assert r1["tokens"] == r2["tokens"]
