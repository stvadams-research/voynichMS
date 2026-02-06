from typing import Dict, Any, Optional
from voynich.storage.metadata import MetadataStore, StructureRecord

class StructureRegistry:
    def __init__(self, store: MetadataStore):
        self.store = store

    def register_structure(self, id: str, name: str, description: str, origin_level: str) -> str:
        """
        Register a new candidate structure.
        """
        self.store.add_structure(
            id=id,
            name=name,
            description=description,
            origin_level=origin_level,
            status="candidate"
        )
        return id

    def record_decision(self, structure_id: str, decision: str, reasoning: str, run_id: str, evidence: Dict[str, Any] = None, controls_applied: Dict[str, Any] = None):
        """
        Record a decision for a structure.
        decision: ACCEPT, REJECT, HOLD
        """
        if decision not in ["ACCEPT", "REJECT", "HOLD"]:
            raise ValueError("Decision must be ACCEPT, REJECT, or HOLD")
            
        self.store.add_decision(
            structure_id=structure_id,
            decision=decision,
            reasoning=reasoning,
            run_id=run_id,
            evidence=evidence,
            controls_applied=controls_applied
        )

    def get_structure_status(self, structure_id: str) -> Optional[str]:
        """
        Get current status of a structure.
        """
        session = self.store.Session()
        try:
            structure = session.query(StructureRecord).filter_by(id=structure_id).first()
            return structure.status if structure else None
        finally:
            session.close()
