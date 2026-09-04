import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.app.schemas.regulatory import RegulatoryDocumentCreate, RegulatoryRuleCreate
from backend.app.repositories.regulatory_repository import get_regulatory_repository
from backend.app.core.logging import get_logger

logger = get_logger("services.regulatory.ingestion")

class RegulatoryIngestionService:
    """
    Ingestion service for official Department of Consumer Affairs (DCA) regulatory publications.
    Extracts structured rule proposals and places them in PENDING_REVIEW status.
    AI/automated pipelines are NEVER permitted to activate legal rules directly into production.
    """

    @classmethod
    def ingest_official_document(
        cls,
        document_name: str,
        document_type: str,
        notification_number: str,
        publication_date: str,
        effective_date: str,
        source_url: str,
        source_reference: str,
        version: str,
        document_text: Optional[str] = None
    ) -> Dict[str, Any]:
        repo = get_regulatory_repository()
        content_hash = hashlib.sha256(document_text.encode("utf-8") if document_text else document_name.encode("utf-8")).hexdigest()

        doc_create = RegulatoryDocumentCreate(
            document_name=document_name,
            document_type=document_type,
            notification_number=notification_number,
            publication_date=publication_date,
            effective_date=effective_date,
            source_url=source_url,
            source_reference=source_reference,
            content_hash=content_hash,
            version=version,
            status="PENDING_REVIEW"
        )
        stored_doc = repo.create_document(doc_create)
        logger.info(f"Ingested official document '{document_name}' as '{stored_doc.id}' (status: PENDING_REVIEW)")

        candidate_rules = []
        if document_text:
            candidate_rules = cls._extract_candidate_rules_from_text(document_text, stored_doc.id, version, effective_date, source_url)
            for cr in candidate_rules:
                repo.create_rule(cr)

        return {
            "document": stored_doc,
            "candidate_rules_count": len(candidate_rules),
            "status": "PENDING_REVIEW",
            "message": "Document and candidate rules ingested successfully into administrative staging. Requires human review and approval before becoming active."
        }

    @classmethod
    def _extract_candidate_rules_from_text(
        cls,
        text: str,
        doc_id: str,
        version: str,
        effective_date: str,
        source_url: str
    ) -> List[RegulatoryRuleCreate]:
        """Heuristic extractor parsing legal sections into candidate rule proposals."""
        candidates = []
        if "Maximum Retail Price" in text or "MRP" in text:
            candidates.append(RegulatoryRuleCreate(
                rule_id=f"PCR-AMEND-MRP-{version.replace('.', '_')}",
                rule_version=version,
                title="MRP Declaration Proposal",
                section="Rule 6",
                sub_rule="6(1)(e)",
                requirement="Proposed amendment requirement for Maximum Retail Price declaration.",
                applicable_categories=["all", "packaged_commodity"],
                field_to_validate="mrp",
                validation_type="REQUIRED",
                validation_expression={"confidence_threshold": 0.70},
                severity="CRITICAL",
                effective_from=effective_date,
                source_document_id=doc_id,
                source_url=source_url,
                source_excerpt=text[:250],
                status="PENDING_REVIEW"
            ))
        return candidates
