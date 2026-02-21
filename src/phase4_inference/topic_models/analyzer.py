"""
Method C: Topic Modeling Alignment

Uses LDA to identify latent topics and measures their alignment with manuscript sections.
"""

import logging
from typing import Any

import numpy as np
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer

logger = logging.getLogger(__name__)

class TopicAnalyzer:
    """
    Analyzes topical coherence and section alignment using LDA.
    """
    def __init__(self, num_topics: int = 10, num_sections: int = 20):
        self.num_topics = num_topics
        self.num_sections = num_sections

    def analyze(self, tokens: list[str]) -> dict[str, Any]:
        """
        Run LDA and measure topic-section alignment.
        """
        if not tokens:
            logger.warning("TopicAnalyzer.analyze received no tokens")
            return {
                "status": "no_data",
                "metrics": {},
                "num_topics": self.num_topics,
                "num_sections": self.num_sections,
                "unique_dominant_topics": 0,
                "avg_section_topic_kl": 0.0,
                "topic_words": [],
            }

        # 1. Prepare Documents (One per section)
        section_size = len(tokens) // self.num_sections
        docs = []
        for i in range(self.num_sections):
            start = i * section_size
            end = (i + 1) * section_size if i < self.num_sections - 1 else len(tokens)
            docs.append(" ".join(tokens[start:end]))

        # 2. Vectorize
        vectorizer = CountVectorizer(max_features=2000)
        X = vectorizer.fit_transform(docs)

        # 3. Fit LDA
        lda = LatentDirichletAllocation(
            n_components=self.num_topics,
            random_state=42,
            learning_method='online'
        )
        doc_topic_dist = lda.fit_transform(X)

        # 4. Measure Alignment
        # Topic Dominance per section
        dominant_topic_per_section = np.argmax(doc_topic_dist, axis=1)

        # Topic Coherence (Simplified: count of unique dominant topics across sections)
        # Higher count = better discrimination of sections by topics
        unique_dominant = len(set(dominant_topic_per_section))

        # Kullback-Leibler Divergence from uniform topic distribution
        # Higher = topics are more concentrated in specific sections
        uniform = np.full(self.num_topics, 1.0 / self.num_topics)
        kl_divs = []
        for dist in doc_topic_dist:
            # Avoid log(0)
            dist_safe = dist + 1e-10
            dist_safe /= dist_safe.sum()
            kl = np.sum(dist_safe * np.log2(dist_safe / uniform))
            kl_divs.append(kl)

        avg_kl = float(np.mean(kl_divs))

        return {
            "num_topics": self.num_topics,
            "num_sections": self.num_sections,
            "unique_dominant_topics": int(unique_dominant),
            "avg_section_topic_kl": avg_kl,
            "topic_words": self._get_topic_words(lda, vectorizer)
        }

    def _get_topic_words(self, lda, vectorizer, top_n: int = 10) -> list[list[str]]:
        words = vectorizer.get_feature_names_out()
        topic_words = []
        for topic_idx, topic in enumerate(lda.components_):
            top_words_idx = topic.argsort()[:-top_n - 1:-1]
            topic_words.append([words[i] for i in top_words_idx])
        return topic_words
