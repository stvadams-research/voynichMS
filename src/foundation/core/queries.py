import struct
from typing import List, Dict, Any
import numpy as np
from foundation.storage.metadata import MetadataStore, WordRecord, TranscriptionTokenRecord, WordAlignmentRecord, GlyphCandidateRecord, RegionRecord, RegionEdgeRecord, AnchorRecord, RegionEmbeddingRecord

class QueryEngine:
    def __init__(self, store: MetadataStore):
        self.store = store

    def get_words_for_token(self, token_content: str) -> List[Dict[str, Any]]:
        session = self.store.Session()
        try:
            # Join Word -> Alignment -> Token
            results = session.query(WordRecord, TranscriptionTokenRecord).\
                join(WordAlignmentRecord, WordRecord.id == WordAlignmentRecord.word_id).\
                join(TranscriptionTokenRecord, TranscriptionTokenRecord.id == WordAlignmentRecord.token_id).\
                filter(TranscriptionTokenRecord.content == token_content).all()
            
            return [{"word_id": w.id, "bbox": w.bbox, "token": t.content, "page_id": w.line.page_id} for w, t in results]
        finally:
            session.close()

    def get_glyphs_for_word(self, word_id: str) -> List[Dict[str, Any]]:
        session = self.store.Session()
        try:
            glyphs = session.query(GlyphCandidateRecord).filter_by(word_id=word_id).order_by(GlyphCandidateRecord.glyph_index).all()
            return [{"glyph_id": g.id, "bbox": g.bbox, "index": g.glyph_index} for g in glyphs]
        finally:
            session.close()

    # --- Level 2B Queries ---

    def get_related_regions(self, region_id: str, relation_type: str = None) -> List[Dict[str, Any]]:
        session = self.store.Session()
        try:
            query = session.query(RegionEdgeRecord, RegionRecord).\
                join(RegionRecord, RegionEdgeRecord.target_region_id == RegionRecord.id).\
                filter(RegionEdgeRecord.source_region_id == region_id)
            
            if relation_type:
                query = query.filter(RegionEdgeRecord.type == relation_type)
            
            results = query.all()
            return [{"region_id": r.id, "type": e.type, "weight": e.weight, "bbox": r.bbox} for e, r in results]
        finally:
            session.close()

    def find_similar_regions(self, region_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find regions similar to the given region using embedding cosine similarity.

        Uses stored region embeddings to compute real similarity scores.
        Returns empty list if source region has no embedding.
        """
        session = self.store.Session()
        try:
            # Get source region embedding
            source_embedding = (
                session.query(RegionEmbeddingRecord)
                .filter_by(region_id=region_id)
                .first()
            )

            if not source_embedding or not source_embedding.vector:
                return []  # No embedding available for source region

            source_vector = self._bytes_to_vector(source_embedding.vector)
            if source_vector is None:
                return []

            # Get all other regions
            all_regions = (
                session.query(RegionRecord)
                .filter(RegionRecord.id != region_id)
                .all()
            )

            # Score each region by cosine similarity
            scored = []
            for region in all_regions:
                embedding = (
                    session.query(RegionEmbeddingRecord)
                    .filter_by(region_id=region.id)
                    .first()
                )
                if embedding and embedding.vector:
                    target_vector = self._bytes_to_vector(embedding.vector)
                    if target_vector is not None:
                        score = self._cosine_similarity(source_vector, target_vector)
                        scored.append({
                            "region_id": region.id,
                            "score": score,
                            "page_id": region.page_id
                        })

            # Sort by score descending and return top results
            scored.sort(key=lambda x: x["score"], reverse=True)
            return scored[:limit]
        finally:
            session.close()

    def _bytes_to_vector(self, data: bytes) -> np.ndarray:
        """Convert binary blob to numpy array."""
        try:
            return np.frombuffer(data, dtype=np.float32)
        except (ValueError, struct.error):
            return None

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors."""
        if vec1.shape != vec2.shape:
            return 0.0

        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    # --- Level 4 Queries ---

    def get_anchors_for_text(self, text_id: str) -> List[Dict[str, Any]]:
        """
        Get all regions anchored to a specific text object (word, line, etc.)
        """
        session = self.store.Session()
        try:
            anchors = session.query(AnchorRecord).filter_by(source_id=text_id).all()
            results = []
            for a in anchors:
                results.append({
                    "anchor_id": a.id,
                    "target_type": a.target_type,
                    "target_id": a.target_id,
                    "relation": a.relation_type,
                    "score": a.score
                })
            return results
        finally:
            session.close()

    def get_anchors_for_region(self, region_id: str) -> List[Dict[str, Any]]:
        """
        Get all text objects anchored to a specific region.
        """
        session = self.store.Session()
        try:
            anchors = session.query(AnchorRecord).filter_by(target_id=region_id).all()
            results = []
            for a in anchors:
                results.append({
                    "anchor_id": a.id,
                    "source_type": a.source_type,
                    "source_id": a.source_id,
                    "relation": a.relation_type,
                    "score": a.score
                })
            return results
        finally:
            session.close()

    def get_anchors_by_type(self, relation_type: str, min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Get all anchors of a specific type with a minimum score.
        """
        session = self.store.Session()
        try:
            anchors = session.query(AnchorRecord).\
                filter(AnchorRecord.relation_type == relation_type).\
                filter(AnchorRecord.score >= min_score).all()
            
            results = []
            for a in anchors:
                results.append({
                    "anchor_id": a.id,
                    "source_id": a.source_id,
                    "target_id": a.target_id,
                    "score": a.score,
                    "page_id": a.page_id
                })
            return results
        finally:
            session.close()
