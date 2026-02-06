from typing import List, Dict, Any
from voynich.storage.metadata import MetadataStore, WordRecord, TranscriptionTokenRecord, WordAlignmentRecord, GlyphCandidateRecord, RegionRecord, RegionEdgeRecord, AnchorRecord

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
        Mock similarity search. In real implementation, would use vector search.
        """
        session = self.store.Session()
        try:
            # Just return random other regions for Level 2B demo
            # Real impl: cosine similarity on embeddings
            import random
            all_regions = session.query(RegionRecord).filter(RegionRecord.id != region_id).limit(limit).all()
            return [{"region_id": r.id, "score": random.random(), "page_id": r.page_id} for r in all_regions]
        finally:
            session.close()

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
