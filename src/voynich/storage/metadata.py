from sqlalchemy import create_engine, Column, String, DateTime, JSON, Boolean, Integer, ForeignKey, Text, Float, LargeBinary
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class RunRecord(Base):
    __tablename__ = 'runs'

    id = Column(String, primary_key=True)
    timestamp_start = Column(DateTime, nullable=False)
    timestamp_end = Column(DateTime, nullable=True)
    git_commit = Column(String, nullable=False)
    git_dirty = Column(Boolean, nullable=False)
    command_line = Column(JSON, nullable=False)
    config = Column(JSON, nullable=False)
    status = Column(String, nullable=False)
    
    # Relationships
    artifacts = relationship("ArtifactRecord", back_populates="run")
    anomalies = relationship("AnomalyRecord", back_populates="run")

class DatasetRecord(Base):
    __tablename__ = 'datasets'

    id = Column(String, primary_key=True) # e.g., "yale_high_res"
    path = Column(String, nullable=False)
    checksum = Column(String, nullable=True) # Checksum of the directory content
    created_at = Column(DateTime, default=datetime.utcnow)
    
    pages = relationship("PageRecord", back_populates="dataset")

class PageRecord(Base):
    __tablename__ = 'pages'

    id = Column(String, primary_key=True) # PageID string (e.g. "f1r")
    dataset_id = Column(String, ForeignKey('datasets.id'), nullable=False)
    image_path = Column(String, nullable=False)
    checksum = Column(String, nullable=False) # SHA256 of the image file
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    dataset = relationship("DatasetRecord", back_populates="pages")
    objects = relationship("ObjectRecord", back_populates="page")
    lines = relationship("LineRecord", back_populates="page")
    transcription_lines = relationship("TranscriptionLineRecord", back_populates="page")
    regions = relationship("RegionRecord", back_populates="page")
    anchors = relationship("AnchorRecord", back_populates="page")

class ArtifactRecord(Base):
    __tablename__ = 'artifacts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey('runs.id'), nullable=False)
    path = Column(String, nullable=False)
    type = Column(String, nullable=False) # e.g., "manifest", "image", "json"
    checksum = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    run = relationship("RunRecord", back_populates="artifacts")

class AnomalyRecord(Base):
    __tablename__ = 'anomalies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey('runs.id'), nullable=False)
    severity = Column(String, nullable=False) # "warning", "error", "critical"
    category = Column(String, nullable=False) # e.g., "geometry", "integrity"
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    run = relationship("RunRecord", back_populates="anomalies")

class ObjectRecord(Base):
    __tablename__ = 'objects'

    id = Column(String, primary_key=True) # UUID or deterministic ID
    page_id = Column(String, ForeignKey('pages.id'), nullable=False)
    scale = Column(String, nullable=False) # from Scale enum
    geometry = Column(JSON, nullable=False) # serialized geometry
    created_at = Column(DateTime, default=datetime.utcnow)
    
    page = relationship("PageRecord", back_populates="objects")

# --- Level 2A: Segmentation Tables ---

class LineRecord(Base):
    __tablename__ = 'lines'
    id = Column(String, primary_key=True) # UUID
    page_id = Column(String, ForeignKey('pages.id'), nullable=False)
    line_index = Column(Integer, nullable=False)
    bbox = Column(JSON, nullable=False) # Serialized Box
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    page = relationship("PageRecord", back_populates="lines")
    words = relationship("WordRecord", back_populates="line")

class WordRecord(Base):
    __tablename__ = 'words'
    id = Column(String, primary_key=True) # UUID
    line_id = Column(String, ForeignKey('lines.id'), nullable=False)
    word_index = Column(Integer, nullable=False)
    bbox = Column(JSON, nullable=False)
    features = Column(JSON, nullable=True) # ink, cc, etc.
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    line = relationship("LineRecord", back_populates="words")
    glyphs = relationship("GlyphCandidateRecord", back_populates="word")
    alignments = relationship("WordAlignmentRecord", back_populates="word")

class GlyphCandidateRecord(Base):
    __tablename__ = 'glyph_candidates'
    id = Column(String, primary_key=True) # UUID
    word_id = Column(String, ForeignKey('words.id'), nullable=False)
    glyph_index = Column(Integer, nullable=False)
    bbox = Column(JSON, nullable=False)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    word = relationship("WordRecord", back_populates="glyphs")
    alignments = relationship("GlyphAlignmentRecord", back_populates="glyph")

# --- Level 2A: Transcription Tables ---

class TranscriptionSourceRecord(Base):
    __tablename__ = 'transcription_sources'
    id = Column(String, primary_key=True) # e.g. "eva_v1"
    name = Column(String, nullable=False)
    citation = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    lines = relationship("TranscriptionLineRecord", back_populates="source")

class TranscriptionLineRecord(Base):
    __tablename__ = 'transcription_lines'
    id = Column(String, primary_key=True) # UUID
    source_id = Column(String, ForeignKey('transcription_sources.id'), nullable=False)
    page_id = Column(String, ForeignKey('pages.id'), nullable=False)
    line_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("TranscriptionSourceRecord", back_populates="lines")
    page = relationship("PageRecord", back_populates="transcription_lines")
    tokens = relationship("TranscriptionTokenRecord", back_populates="line")

class TranscriptionTokenRecord(Base):
    __tablename__ = 'transcription_tokens'
    id = Column(String, primary_key=True) # UUID
    line_id = Column(String, ForeignKey('transcription_lines.id'), nullable=False)
    token_index = Column(Integer, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    line = relationship("TranscriptionLineRecord", back_populates="tokens")
    alignments = relationship("WordAlignmentRecord", back_populates="token")

# --- Level 2A: Alignment Tables ---

class WordAlignmentRecord(Base):
    __tablename__ = 'word_alignments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    word_id = Column(String, ForeignKey('words.id'), nullable=True) # Nullable for transcript-only
    token_id = Column(String, ForeignKey('transcription_tokens.id'), nullable=True) # Nullable for image-only
    type = Column(String, nullable=False) # 1:1, 1:N, N:1, null
    score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    word = relationship("WordRecord", back_populates="alignments")
    token = relationship("TranscriptionTokenRecord", back_populates="alignments")

class GlyphAlignmentRecord(Base):
    __tablename__ = 'glyph_alignments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    glyph_id = Column(String, ForeignKey('glyph_candidates.id'), nullable=False)
    symbol = Column(String, nullable=False)
    score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    glyph = relationship("GlyphCandidateRecord", back_populates="alignments")

# --- Level 2B: Region Tables ---

class RegionRecord(Base):
    __tablename__ = 'regions'
    id = Column(String, primary_key=True) # UUID
    page_id = Column(String, ForeignKey('pages.id'), nullable=False)
    scale = Column(String, nullable=False) # primitive, mid, large
    method = Column(String, nullable=False) # e.g. "grid", "connected_components"
    bbox = Column(JSON, nullable=False) # Serialized Box
    features = Column(JSON, nullable=True) # area, aspect_ratio, etc.
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    page = relationship("PageRecord", back_populates="regions")
    embeddings = relationship("RegionEmbeddingRecord", back_populates="region")
    
    # Adjacency list relationships could be complex in SQLAlchemy, 
    # usually better to query Edge table directly.

class RegionEdgeRecord(Base):
    __tablename__ = 'region_edges'
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_region_id = Column(String, ForeignKey('regions.id'), nullable=False)
    target_region_id = Column(String, ForeignKey('regions.id'), nullable=False)
    type = Column(String, nullable=False) # contains, overlaps, near
    weight = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class RegionEmbeddingRecord(Base):
    __tablename__ = 'region_embeddings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    region_id = Column(String, ForeignKey('regions.id'), nullable=False)
    model_name = Column(String, nullable=False)
    vector = Column(LargeBinary, nullable=False) # Binary blob of numpy array
    created_at = Column(DateTime, default=datetime.utcnow)

    region = relationship("RegionRecord", back_populates="embeddings")

# --- Level 3: Control Tables ---

class ControlDatasetRecord(Base):
    __tablename__ = 'control_datasets'
    id = Column(String, primary_key=True) # e.g. "scrambled_v1"
    source_dataset_id = Column(String, ForeignKey('datasets.id'), nullable=False)
    type = Column(String, nullable=False) # synthetic_null, scrambled
    params = Column(JSON, nullable=False) # generation parameters
    seed = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class MetricResultRecord(Base):
    __tablename__ = 'metric_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey('runs.id'), nullable=False)
    dataset_id = Column(String, nullable=False) # Can be real or control dataset ID
    metric_name = Column(String, nullable=False)
    scope = Column(String, nullable=False) # page, region, global
    value = Column(Float, nullable=True) # Single scalar value
    details = Column(JSON, nullable=True) # Complex value (distribution, etc.)
    created_at = Column(DateTime, default=datetime.utcnow)

class MetricComparisonRecord(Base):
    __tablename__ = 'metric_comparisons'
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String, nullable=False)
    real_dataset_id = Column(String, nullable=False)
    control_dataset_id = Column(String, nullable=False)
    difference_score = Column(Float, nullable=True)
    significance = Column(Float, nullable=True)
    classification = Column(String, nullable=True) # SURVIVES, PARTIAL, FAILS
    created_at = Column(DateTime, default=datetime.utcnow)

# --- Level 4: Anchor Tables ---

class AnchorMethodRecord(Base):
    __tablename__ = 'anchor_methods'
    id = Column(String, primary_key=True) # e.g. "geometric_v1"
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    parameters = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    anchors = relationship("AnchorRecord", back_populates="method")

class AnchorRecord(Base):
    __tablename__ = 'anchors'
    id = Column(String, primary_key=True) # UUID
    run_id = Column(String, ForeignKey('runs.id'), nullable=False)
    page_id = Column(String, ForeignKey('pages.id'), nullable=False)
    source_type = Column(String, nullable=False) # word, line, glyph
    source_id = Column(String, nullable=False) # generic ID
    target_type = Column(String, nullable=False) # region
    target_id = Column(String, nullable=False) # generic ID
    relation_type = Column(String, nullable=False) # overlaps, near, inside, touches
    score = Column(Float, nullable=True) # e.g. IoU
    method_id = Column(String, ForeignKey('anchor_methods.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    method = relationship("AnchorMethodRecord", back_populates="anchors")
    page = relationship("PageRecord", back_populates="anchors")

class AnchorMetricRecord(Base):
    __tablename__ = 'anchor_metrics'
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey('runs.id'), nullable=False)
    dataset_id = Column(String, nullable=False)
    metric_name = Column(String, nullable=False) # e.g. "anchor_stability"
    value = Column(Float, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# --- Level 5: Decision Tables ---

class StructureRecord(Base):
    __tablename__ = 'structures'
    id = Column(String, primary_key=True) # e.g. "currier_a_b_distinction"
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    origin_level = Column(String, nullable=False) # 2A, 2B, 4
    status = Column(String, nullable=False) # candidate, accepted, rejected, inconclusive
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    decisions = relationship("DecisionRecord", back_populates="structure")
    sensitivity_results = relationship("SensitivityResultRecord", back_populates="structure")
    hypotheses = relationship("HypothesisRecord", secondary="hypothesis_structures", back_populates="structures")

class DecisionRecord(Base):
    __tablename__ = 'decisions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    structure_id = Column(String, ForeignKey('structures.id'), nullable=False)
    decision = Column(String, nullable=False) # ACCEPT, REJECT, HOLD
    reasoning = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=True)
    controls_applied = Column(JSON, nullable=True)
    run_id = Column(String, ForeignKey('runs.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    structure = relationship("StructureRecord", back_populates="decisions")

class SensitivityResultRecord(Base):
    __tablename__ = 'sensitivity_results'
    id = Column(Integer, primary_key=True, autoincrement=True)
    structure_id = Column(String, ForeignKey('structures.id'), nullable=False)
    parameter_name = Column(String, nullable=False)
    parameter_value = Column(String, nullable=False) # Store as string to handle various types
    metric_value = Column(Float, nullable=True)
    run_id = Column(String, ForeignKey('runs.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    structure = relationship("StructureRecord", back_populates="sensitivity_results")

# --- Level 6: Hypothesis Tables ---

class HypothesisRecord(Base):
    __tablename__ = 'hypotheses'
    id = Column(String, primary_key=True) # e.g. "glyph_core_modifier_structure"
    description = Column(Text, nullable=False)
    assumptions = Column(Text, nullable=True)
    falsification_criteria = Column(Text, nullable=True)
    status = Column(String, nullable=False) # active, supported, falsified, inconclusive
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    runs = relationship("HypothesisRunRecord", back_populates="hypothesis")
    metrics = relationship("HypothesisMetricRecord", back_populates="hypothesis")
    structures = relationship("StructureRecord", secondary="hypothesis_structures", back_populates="hypotheses")

class HypothesisStructure(Base):
    __tablename__ = 'hypothesis_structures'
    hypothesis_id = Column(String, ForeignKey('hypotheses.id'), primary_key=True)
    structure_id = Column(String, ForeignKey('structures.id'), primary_key=True)

class HypothesisRunRecord(Base):
    __tablename__ = 'hypothesis_runs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    hypothesis_id = Column(String, ForeignKey('hypotheses.id'), nullable=False)
    run_id = Column(String, ForeignKey('runs.id'), nullable=False)
    result_summary = Column(JSON, nullable=True)
    outcome = Column(String, nullable=False) # SUPPORTED, WEAKLY_SUPPORTED, NOT_SUPPORTED, FALSIFIED
    created_at = Column(DateTime, default=datetime.utcnow)

    hypothesis = relationship("HypothesisRecord", back_populates="runs")

class HypothesisMetricRecord(Base):
    __tablename__ = 'hypothesis_metrics'
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey('runs.id'), nullable=False)
    hypothesis_id = Column(String, ForeignKey('hypotheses.id'), nullable=False)
    dataset_id = Column(String, nullable=False) # Real or Control
    metric_name = Column(String, nullable=False)
    value = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    hypothesis = relationship("HypothesisRecord", back_populates="metrics")


class MetadataStore:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def save_run(self, run_context):
        session = self.Session()
        try:
            record = RunRecord(
                id=run_context.run_id,
                timestamp_start=run_context.timestamp_start,
                timestamp_end=run_context.timestamp_end,
                git_commit=run_context.git_commit,
                git_dirty=run_context.git_dirty,
                command_line=run_context.command_line,
                config=run_context.config,
                status=run_context.status
            )
            session.merge(record)
            session.commit()
        finally:
            session.close()
    
    def add_dataset(self, dataset_id: str, path: str, checksum: str = None):
        session = self.Session()
        try:
            record = DatasetRecord(
                id=dataset_id,
                path=str(path),
                checksum=checksum
            )
            session.merge(record)
            session.commit()
        finally:
            session.close()

    def add_page(self, page_id: str, dataset_id: str, image_path: str, checksum: str, width: int = None, height: int = None):
        session = self.Session()
        try:
            record = PageRecord(
                id=page_id,
                dataset_id=dataset_id,
                image_path=str(image_path),
                checksum=checksum,
                width=width,
                height=height
            )
            session.merge(record)
            session.commit()
        finally:
            session.close()

    def add_artifact(self, run_id: str, path: str, type: str, checksum: str):
        session = self.Session()
        try:
            record = ArtifactRecord(
                run_id=run_id,
                path=str(path),
                type=type,
                checksum=checksum
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

    def add_anomaly(self, run_id: str, severity: str, category: str, message: str, details: dict = None):
        session = self.Session()
        try:
            record = AnomalyRecord(
                run_id=run_id,
                severity=severity,
                category=category,
                message=message,
                details=details
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

    # --- Level 2A Helpers ---

    def add_line(self, id: str, page_id: str, line_index: int, bbox: dict, confidence: float = None):
        session = self.Session()
        try:
            record = LineRecord(
                id=id,
                page_id=page_id,
                line_index=line_index,
                bbox=bbox,
                confidence=confidence
            )
            session.merge(record)
            session.commit()
        finally:
            session.close()

    def add_word(self, id: str, line_id: str, word_index: int, bbox: dict, features: dict = None, confidence: float = None):
        session = self.Session()
        try:
            record = WordRecord(
                id=id,
                line_id=line_id,
                word_index=word_index,
                bbox=bbox,
                features=features,
                confidence=confidence
            )
            session.merge(record)
            session.commit()
        finally:
            session.close()

    def add_glyph_candidate(self, id: str, word_id: str, glyph_index: int, bbox: dict, confidence: float = None):
        session = self.Session()
        try:
            record = GlyphCandidateRecord(
                id=id,
                word_id=word_id,
                glyph_index=glyph_index,
                bbox=bbox,
                confidence=confidence
            )
            session.merge(record)
            session.commit()
        finally:
            session.close()

    def add_transcription_source(self, id: str, name: str, citation: str = None):
        session = self.Session()
        try:
            record = TranscriptionSourceRecord(
                id=id,
                name=name,
                citation=citation
            )
            session.merge(record)
            session.commit()
        finally:
            session.close()

    def add_transcription_line(self, id: str, source_id: str, page_id: str, line_index: int, content: str):
        session = self.Session()
        try:
            record = TranscriptionLineRecord(
                id=id,
                source_id=source_id,
                page_id=page_id,
                line_index=line_index,
                content=content
            )
            session.merge(record)
            session.commit()
        finally:
            session.close()

    def add_transcription_token(self, id: str, line_id: str, token_index: int, content: str):
        session = self.Session()
        try:
            record = TranscriptionTokenRecord(
                id=id,
                line_id=line_id,
                token_index=token_index,
                content=content
            )
            session.merge(record)
            session.commit()
        finally:
            session.close()

    def add_word_alignment(self, word_id: str, token_id: str, type: str, score: float = None):
        session = self.Session()
        try:
            record = WordAlignmentRecord(
                word_id=word_id,
                token_id=token_id,
                type=type,
                score=score
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

    # --- Level 2B Helpers ---

    def add_region(self, id: str, page_id: str, scale: str, method: str, bbox: dict, features: dict = None, confidence: float = None):
        session = self.Session()
        try:
            record = RegionRecord(
                id=id,
                page_id=page_id,
                scale=scale,
                method=method,
                bbox=bbox,
                features=features,
                confidence=confidence
            )
            session.merge(record)
            session.commit()
        finally:
            session.close()

    def add_region_edge(self, source_id: str, target_id: str, type: str, weight: float = None):
        session = self.Session()
        try:
            record = RegionEdgeRecord(
                source_region_id=source_id,
                target_region_id=target_id,
                type=type,
                weight=weight
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

    def add_region_embedding(self, region_id: str, model_name: str, vector: bytes):
        session = self.Session()
        try:
            record = RegionEmbeddingRecord(
                region_id=region_id,
                model_name=model_name,
                vector=vector
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

    # --- Level 3 Helpers ---

    def add_control_dataset(self, id: str, source_dataset_id: str, type: str, params: dict, seed: int):
        session = self.Session()
        try:
            record = ControlDatasetRecord(
                id=id,
                source_dataset_id=source_dataset_id,
                type=type,
                params=params,
                seed=seed
            )
            session.merge(record)
            session.commit()
        finally:
            session.close()

    def add_metric_result(self, run_id: str, dataset_id: str, metric_name: str, scope: str, value: float, details: dict = None):
        session = self.Session()
        try:
            record = MetricResultRecord(
                run_id=run_id,
                dataset_id=dataset_id,
                metric_name=metric_name,
                scope=scope,
                value=value,
                details=details
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

    def add_metric_comparison(self, metric_name: str, real_dataset_id: str, control_dataset_id: str, difference_score: float, classification: str):
        session = self.Session()
        try:
            record = MetricComparisonRecord(
                metric_name=metric_name,
                real_dataset_id=real_dataset_id,
                control_dataset_id=control_dataset_id,
                difference_score=difference_score,
                classification=classification
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

    # --- Level 4 Helpers ---

    def add_anchor_method(self, id: str, name: str, description: str = None, parameters: dict = None):
        session = self.Session()
        try:
            record = AnchorMethodRecord(
                id=id,
                name=name,
                description=description,
                parameters=parameters
            )
            session.merge(record)
            session.commit()
        finally:
            session.close()

    def add_anchor(self, id: str, run_id: str, page_id: str, source_type: str, source_id: str, target_type: str, target_id: str, relation_type: str, method_id: str, score: float = None):
        session = self.Session()
        try:
            record = AnchorRecord(
                id=id,
                run_id=run_id,
                page_id=page_id,
                source_type=source_type,
                source_id=source_id,
                target_type=target_type,
                target_id=target_id,
                relation_type=relation_type,
                score=score,
                method_id=method_id
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

    def add_anchor_metric(self, run_id: str, dataset_id: str, metric_name: str, value: float, details: dict = None):
        session = self.Session()
        try:
            record = AnchorMetricRecord(
                run_id=run_id,
                dataset_id=dataset_id,
                metric_name=metric_name,
                value=value,
                details=details
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

    # --- Level 5 Helpers ---

    def add_structure(self, id: str, name: str, description: str, origin_level: str, status: str = "candidate"):
        session = self.Session()
        try:
            record = StructureRecord(
                id=id,
                name=name,
                description=description,
                origin_level=origin_level,
                status=status
            )
            session.merge(record)
            session.commit()
        finally:
            session.close()

    def add_decision(self, structure_id: str, decision: str, reasoning: str, run_id: str, evidence: dict = None, controls_applied: dict = None):
        session = self.Session()
        try:
            record = DecisionRecord(
                structure_id=structure_id,
                decision=decision,
                reasoning=reasoning,
                evidence=evidence,
                controls_applied=controls_applied,
                run_id=run_id
            )
            session.add(record)
            
            # Update structure status
            structure = session.query(StructureRecord).filter_by(id=structure_id).first()
            if structure:
                if decision == "ACCEPT":
                    structure.status = "accepted"
                elif decision == "REJECT":
                    structure.status = "rejected"
                elif decision == "HOLD":
                    structure.status = "inconclusive"
            
            session.commit()
        finally:
            session.close()

    def add_sensitivity_result(self, structure_id: str, parameter_name: str, parameter_value: str, metric_value: float, run_id: str):
        session = self.Session()
        try:
            record = SensitivityResultRecord(
                structure_id=structure_id,
                parameter_name=parameter_name,
                parameter_value=str(parameter_value),
                metric_value=metric_value,
                run_id=run_id
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

    # --- Level 6 Helpers ---

    def add_hypothesis(self, id: str, description: str, assumptions: str, falsification_criteria: str, status: str = "active"):
        session = self.Session()
        try:
            record = HypothesisRecord(
                id=id,
                description=description,
                assumptions=assumptions,
                falsification_criteria=falsification_criteria,
                status=status
            )
            session.merge(record)
            session.commit()
        finally:
            session.close()

    def add_hypothesis_run(self, hypothesis_id: str, run_id: str, outcome: str, result_summary: dict = None):
        session = self.Session()
        try:
            record = HypothesisRunRecord(
                hypothesis_id=hypothesis_id,
                run_id=run_id,
                outcome=outcome,
                result_summary=result_summary
            )
            session.add(record)
            
            # Update hypothesis status based on latest run
            hypothesis = session.query(HypothesisRecord).filter_by(id=hypothesis_id).first()
            if hypothesis:
                if outcome == "SUPPORTED":
                    hypothesis.status = "supported"
                elif outcome == "FALSIFIED":
                    hypothesis.status = "falsified"
                elif outcome == "NOT_SUPPORTED":
                    hypothesis.status = "inconclusive"
            
            session.commit()
        finally:
            session.close()

    def add_hypothesis_metric(self, run_id: str, hypothesis_id: str, dataset_id: str, metric_name: str, value: float):
        session = self.Session()
        try:
            record = HypothesisMetricRecord(
                run_id=run_id,
                hypothesis_id=hypothesis_id,
                dataset_id=dataset_id,
                metric_name=metric_name,
                value=value
            )
            session.add(record)
            session.commit()
        finally:
            session.close()
