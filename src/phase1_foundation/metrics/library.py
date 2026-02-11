"""
Foundation Metrics Library

Real implementations that compute metrics from actual database records.
"""

import math
import logging
from typing import List
from collections import Counter

from phase1_foundation.metrics.interface import Metric, MetricResult
from phase1_foundation.storage.metadata import (
    PageRecord,
    LineRecord,
    WordRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
    WordAlignmentRecord,
    RegionRecord,
    RegionEmbeddingRecord,
)

logger = logging.getLogger(__name__)


class RepetitionRate(Metric):
    """
    Calculates the repetition rate of tokens.

    Real implementation queries TranscriptionTokenRecord to count
    repeated tokens vs total tokens.
    """

    def calculate(self, dataset_id: str) -> List[MetricResult]:
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
                    value=float("nan"),
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
                logger.warning("No direct transcription tokens found for dataset %s, falling back to word alignments", dataset_id)
                tokens = self._get_tokens_via_alignments(session, page_ids)

            if not tokens:
                return [MetricResult(
                    metric_name="RepetitionRate",
                    dataset_id=dataset_id,
                    scope="global",
                    value=float("nan"),
                    details={"error": "no_tokens_found"}
                )]

            # Count token frequencies
            token_contents = [t[0] if isinstance(t, tuple) else t for t in tokens]
            token_counts = Counter(token_contents)

            total_tokens = len(token_contents)
            unique_tokens = len(token_counts)

            # Repetition rate: tokens that appear more than once / total occurrences
            repeated_occurrences = sum(count for count in token_counts.values() if count > 1)
            token_repetition_rate = repeated_occurrences / total_tokens if total_tokens > 0 else 0.0

            # Supplementary statistic: 1 - type/token ratio.
            vocabulary_coverage = 1 - (unique_tokens / total_tokens) if total_tokens > 0 else 0.0

            return [MetricResult(
                metric_name="RepetitionRate",
                dataset_id=dataset_id,
                scope="global",
                value=token_repetition_rate,
                details={
                    "total_tokens": total_tokens,
                    "unique_tokens": unique_tokens,
                    "token_repetition_rate": token_repetition_rate,
                    "vocabulary_coverage": vocabulary_coverage,
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


class ClusterTightness(Metric):
    """
    Calculates tightness of visual clusters.

    Real implementation computes from RegionEmbeddingRecord vectors
    using the formula: 1 / (1 + mean_distance_from_centroid)
    """

    def calculate(self, dataset_id: str) -> List[MetricResult]:
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
                logger.warning("ClusterTightness: no pages found for dataset %s", dataset_id)
                return [MetricResult(
                    metric_name="ClusterTightness",
                    dataset_id=dataset_id,
                    scope="global",
                    value=float("nan"),
                    details={"status": "no_data", "error": "no_pages_found", "method": "none"}
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
                logger.warning(
                    "ClusterTightness falling back to bbox computation for dataset %s",
                    dataset_id,
                )
                return self._compute_from_bboxes(session, page_ids, dataset_id)

            # Convert binary vectors to numpy arrays
            vectors = []
            for emb in embeddings:
                try:
                    vec = np.frombuffer(emb.vector, dtype=np.float32)
                    vectors.append(vec)
                except Exception as e:
                    logger.warning("Failed to decode embedding %s: %s", emb.id, e)
                    continue

            if len(vectors) < 2:
                logger.warning(
                    "ClusterTightness: insufficient embeddings (%d) for dataset %s",
                    len(vectors),
                    dataset_id,
                )
                return [MetricResult(
                    metric_name="ClusterTightness",
                    dataset_id=dataset_id,
                    scope="global",
                    value=float("nan"),
                    details={
                        "status": "no_data",
                        "error": "insufficient_embeddings",
                        "count": len(vectors),
                        "method": "embeddings",
                    },
                )]

            # Stack into matrix
            vectors = np.array(vectors)
            
            if vectors.ndim != 2:
                raise ValueError(f"Expected 2D embedding array, got {vectors.ndim}D")

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
                    "method": "embeddings",
                    "computation_path": "embeddings",
                    "embedding_count": len(vectors),
                    "mean_distance": mean_distance,
                    "std_distance": float(np.std(distances)),
                    "min_distance": float(np.min(distances)),
                    "max_distance": float(np.max(distances)),
                }
            )]

        except Exception as e:
            # numpy not available or other error, use bbox fallback
            logger.warning(
                "Error in embedding-based ClusterTightness for %s; falling back to bboxes",
                dataset_id,
                exc_info=True,
            )
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
            logger.warning(
                "ClusterTightness bbox fallback: insufficient regions (%d) for dataset %s",
                len(regions),
                dataset_id,
            )
            return [MetricResult(
                metric_name="ClusterTightness",
                dataset_id=dataset_id,
                scope="global",
                value=float("nan"),
                details={
                    "status": "no_data",
                    "error": "insufficient_regions",
                    "count": len(regions),
                    "method": "bboxes",
                },
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
            logger.warning(
                "ClusterTightness bbox fallback: invalid region bboxes for dataset %s",
                dataset_id,
            )
            return [MetricResult(
                metric_name="ClusterTightness",
                dataset_id=dataset_id,
                scope="global",
                value=float("nan"),
                details={"status": "no_data", "error": "invalid_bboxes", "method": "bboxes"}
            )]

        # Compute mean centroid
        mean_x = sum(c[0] for c in centroids) / len(centroids) if len(centroids) > 0 else 0
        mean_y = sum(c[1] for c in centroids) / len(centroids) if len(centroids) > 0 else 0

        # Compute distances
        distances = [
            math.sqrt((c[0] - mean_x) ** 2 + (c[1] - mean_y) ** 2)
            for c in centroids
        ]
        mean_distance = sum(distances) / len(distances) if len(distances) > 0 else 0

        # Compute tightness
        tightness = 1.0 / (1.0 + mean_distance)

        return [MetricResult(
            metric_name="ClusterTightness",
            dataset_id=dataset_id,
            scope="global",
            value=tightness,
            details={
                "method": "bboxes",
                "computation_path": "bboxes",
                "region_count": len(regions),
                "mean_distance": mean_distance,
            }
        )]
