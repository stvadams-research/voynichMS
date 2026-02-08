"""
Foundation Metrics Library

Real implementations that compute metrics from actual database records.
"""

import math
from typing import List, Dict, Any
from collections import Counter
from sqlalchemy import func

from foundation.metrics.interface import Metric, MetricResult
from foundation.storage.metadata import (
    PageRecord,
    LineRecord,
    WordRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
    WordAlignmentRecord,
    RegionRecord,
    RegionEmbeddingRecord,
)
from foundation.config import use_real_computation


class RepetitionRate(Metric):
    """
    Calculates the repetition rate of tokens/words.

    Real implementation queries TranscriptionTokenRecord to count
    repeated tokens vs total tokens.
    """

    def calculate(self, dataset_id: str) -> List[MetricResult]:
        if not use_real_computation("metrics"):
            return self._calculate_simulated(dataset_id)

        return self._calculate_real(dataset_id)

    def _calculate_real(self, dataset_id: str) -> List[MetricResult]:
        """
        Calculate repetition rate from actual token frequencies.

        Formula: repeated_tokens / total_tokens
        where repeated_tokens counts tokens that appear more than once.
        """
        session = self.store.Session()
        try:
            # Get all pages for this dataset
            pages = session.query(PageRecord).filter_by(dataset_id=dataset_id).all()

            if not pages:
                return [MetricResult(
                    metric_name="RepetitionRate",
                    dataset_id=dataset_id,
                    scope="global",
                    value=0.0,
                    details={"error": "no_pages_found"}
                )]

            page_ids = [p.id for p in pages]

            # Get all transcription tokens for these pages
            tokens = (
                session.query(TranscriptionTokenRecord.content)
                .join(TranscriptionLineRecord, TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
                .filter(TranscriptionLineRecord.page_id.in_(page_ids))
                .all()
            )

            if not tokens:
                # Fallback: try to get tokens via word alignments
                tokens = self._get_tokens_via_alignments(session, page_ids)

            if not tokens:
                return [MetricResult(
                    metric_name="RepetitionRate",
                    dataset_id=dataset_id,
                    scope="global",
                    value=0.0,
                    details={"error": "no_tokens_found"}
                )]

            # Count token frequencies
            token_contents = [t[0] if isinstance(t, tuple) else t for t in tokens]
            token_counts = Counter(token_contents)

            total_tokens = len(token_contents)
            unique_tokens = len(token_counts)

            # Repetition rate: tokens that appear more than once / total occurrences
            repeated_occurrences = sum(count for count in token_counts.values() if count > 1)
            repetition_rate = repeated_occurrences / total_tokens if total_tokens > 0 else 0.0

            # Alternative metric: 1 - (unique / total) measures how non-unique the vocabulary is
            vocabulary_repetition = 1 - (unique_tokens / total_tokens) if total_tokens > 0 else 0.0

            return [MetricResult(
                metric_name="RepetitionRate",
                dataset_id=dataset_id,
                scope="global",
                value=repetition_rate,
                details={
                    "total_tokens": total_tokens,
                    "unique_tokens": unique_tokens,
                    "vocabulary_repetition": vocabulary_repetition,
                    "top_5_tokens": dict(token_counts.most_common(5)),
                }
            )]

        finally:
            session.close()

    def _get_tokens_via_alignments(self, session, page_ids: List[str]) -> List[str]:
        """Get token content via word alignments if direct transcription path fails."""
        tokens = (
            session.query(TranscriptionTokenRecord.content)
            .join(WordAlignmentRecord, TranscriptionTokenRecord.id == WordAlignmentRecord.token_id)
            .join(WordRecord, WordAlignmentRecord.word_id == WordRecord.id)
            .join(LineRecord, WordRecord.line_id == LineRecord.id)
            .filter(LineRecord.page_id.in_(page_ids))
            .all()
        )
        return [t[0] for t in tokens] if tokens else []

    def _calculate_simulated(self, dataset_id: str) -> List[MetricResult]:
        """Legacy simulated implementation for backward compatibility."""
        import random
        # Use a deterministic local RNG for simulated results
        # Deriving seed from dataset_id ensures stability across runs
        import hashlib
        seed_hash = int(hashlib.sha256(dataset_id.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed_hash)

        dataset_type = "real"
        if "scrambled" in dataset_id:
            dataset_type = "scrambled"
        elif "synthetic" in dataset_id:
            dataset_type = "synthetic"

        if dataset_type == "real":
            val = 0.15 + rng.uniform(-0.02, 0.02)
        elif dataset_type == "scrambled":
            val = 0.02 + rng.uniform(0.0, 0.01)
        else:
            val = 0.05 + rng.uniform(-0.01, 0.01)

        return [MetricResult(
            metric_name="RepetitionRate",
            dataset_id=dataset_id,
            scope="global",
            value=val,
            details={"type": dataset_type, "simulated": True}
        )]


class ClusterTightness(Metric):
    """
    Calculates tightness of visual clusters.

    Real implementation computes from RegionEmbeddingRecord vectors
    using the formula: 1 / (1 + mean_distance_from_centroid)
    """

    def calculate(self, dataset_id: str) -> List[MetricResult]:
        if not use_real_computation("metrics"):
            return self._calculate_simulated(dataset_id)

        return self._calculate_real(dataset_id)

    def _calculate_real(self, dataset_id: str) -> List[MetricResult]:
        """
        Compute cluster tightness from region embedding vectors.

        Formula: 1 / (1 + mean_distance_from_centroid)
        """
        session = self.store.Session()
        try:
            import numpy as np

            # Get all pages for this dataset
            pages = session.query(PageRecord).filter_by(dataset_id=dataset_id).all()

            if not pages:
                return [MetricResult(
                    metric_name="ClusterTightness",
                    dataset_id=dataset_id,
                    scope="global",
                    value=0.5,
                    details={"error": "no_pages_found"}
                )]

            page_ids = [p.id for p in pages]

            # Get all region embeddings for these pages
            embeddings = (
                session.query(RegionEmbeddingRecord)
                .join(RegionRecord, RegionEmbeddingRecord.region_id == RegionRecord.id)
                .filter(RegionRecord.page_id.in_(page_ids))
                .all()
            )

            if not embeddings:
                # Fallback: compute from region bounding boxes if no embeddings
                return self._compute_from_bboxes(session, page_ids, dataset_id)

            # Convert binary vectors to numpy arrays
            vectors = []
            for emb in embeddings:
                try:
                    vec = np.frombuffer(emb.vector, dtype=np.float32)
                    vectors.append(vec)
                except Exception:
                    continue

            if len(vectors) < 2:
                return [MetricResult(
                    metric_name="ClusterTightness",
                    dataset_id=dataset_id,
                    scope="global",
                    value=0.5,
                    details={"error": "insufficient_embeddings", "count": len(vectors)}
                )]

            # Stack into matrix
            vectors = np.array(vectors)

            # Compute centroid
            centroid = np.mean(vectors, axis=0)

            # Compute distances from centroid
            distances = np.linalg.norm(vectors - centroid, axis=1)
            mean_distance = float(np.mean(distances))

            # Compute tightness: 1 / (1 + mean_distance)
            tightness = 1.0 / (1.0 + mean_distance)

            return [MetricResult(
                metric_name="ClusterTightness",
                dataset_id=dataset_id,
                scope="global",
                value=tightness,
                details={
                    "embedding_count": len(vectors),
                    "mean_distance": mean_distance,
                    "std_distance": float(np.std(distances)),
                    "min_distance": float(np.min(distances)),
                    "max_distance": float(np.max(distances)),
                }
            )]

        except ImportError:
            # numpy not available, use fallback
            return self._compute_from_bboxes(session, page_ids, dataset_id)
        finally:
            session.close()

    def _compute_from_bboxes(self, session, page_ids: List[str], dataset_id: str) -> List[MetricResult]:
        """
        Compute cluster tightness from region bounding boxes.

        Uses centroid positions of regions to compute tightness.
        """
        regions = (
            session.query(RegionRecord)
            .filter(RegionRecord.page_id.in_(page_ids))
            .filter(RegionRecord.scale == "mid")  # Use mid-scale regions
            .all()
        )

        if len(regions) < 2:
            return [MetricResult(
                metric_name="ClusterTightness",
                dataset_id=dataset_id,
                scope="global",
                value=0.5,
                details={"error": "insufficient_regions", "count": len(regions)}
            )]

        # Extract centroids from bboxes
        centroids = []
        for r in regions:
            bbox = r.bbox
            if bbox:
                cx = (bbox.get("x_min", 0) + bbox.get("x_max", 1)) / 2
                cy = (bbox.get("y_min", 0) + bbox.get("y_max", 1)) / 2
                centroids.append((cx, cy))

        if len(centroids) < 2:
            return [MetricResult(
                metric_name="ClusterTightness",
                dataset_id=dataset_id,
                scope="global",
                value=0.5,
                details={"error": "invalid_bboxes"}
            )]

        # Compute mean centroid
        mean_x = sum(c[0] for c in centroids) / len(centroids)
        mean_y = sum(c[1] for c in centroids) / len(centroids)

        # Compute distances
        distances = [
            math.sqrt((c[0] - mean_x) ** 2 + (c[1] - mean_y) ** 2)
            for c in centroids
        ]
        mean_distance = sum(distances) / len(distances)

        # Compute tightness
        tightness = 1.0 / (1.0 + mean_distance)

        return [MetricResult(
            metric_name="ClusterTightness",
            dataset_id=dataset_id,
            scope="global",
            value=tightness,
            details={
                "region_count": len(regions),
                "mean_distance": mean_distance,
                "computed_from": "bboxes",
            }
        )]

    def _calculate_simulated(self, dataset_id: str) -> List[MetricResult]:
        """Legacy simulated implementation for backward compatibility."""
        import random
        import hashlib
        seed_hash = int(hashlib.sha256(dataset_id.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed_hash)
        
        val = rng.uniform(0.5, 0.8)
        return [MetricResult(
            metric_name="ClusterTightness",
            dataset_id=dataset_id,
            scope="global",
            value=val,
            details={"simulated": True}
        )]
