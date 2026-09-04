from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, status
from backend.app.schemas.regulatory import (
    RegulatoryDocumentDTO,
    RegulatoryDocumentCreate,
    RegulatoryRuleDTO,
    RegulatoryRuleCreate,
    RuleAmendmentDTO,
    RuleStatusTransitionRequest,
    RegulatoryCatalogSummaryResponse
)
from backend.app.repositories.regulatory_repository import get_regulatory_repository
from backend.app.services.regulatory.ingestion import RegulatoryIngestionService
from backend.app.core.logging import get_logger

logger = get_logger("api.regulatory")
router = APIRouter()

@router.get(
    "/regulatory/summary",
    response_model=RegulatoryCatalogSummaryResponse,
    summary="Get regulatory database overview and governance counts",
    description="Returns aggregate counts of active, pending, and superseded statutory rules, official documents, and amendments."
)
async def get_regulatory_summary():
    repo = get_regulatory_repository()
    return repo.get_summary()

@router.get(
    "/regulatory/documents",
    response_model=List[RegulatoryDocumentDTO],
    summary="List official government regulatory publications",
    description="Returns official Department of Consumer Affairs documents, notifications, and gazette references."
)
async def list_regulatory_documents():
    repo = get_regulatory_repository()
    return repo.list_documents()

@router.post(
    "/regulatory/documents",
    status_code=status.HTTP_201_CREATED,
    summary="Ingest an official government regulatory document",
    description="Submits an official notification to administrative staging in PENDING_REVIEW status."
)
async def ingest_document(payload: RegulatoryDocumentCreate, document_text: Optional[str] = None):
    res = RegulatoryIngestionService.ingest_official_document(
        document_name=payload.document_name,
        document_type=payload.document_type,
        notification_number=payload.notification_number or "",
        publication_date=payload.publication_date,
        effective_date=payload.effective_date,
        source_url=payload.source_url or "",
        source_reference=payload.source_reference,
        version=payload.version,
        document_text=document_text
    )
    return res

@router.get(
    "/regulatory/rules",
    response_model=List[RegulatoryRuleDTO],
    summary="List versioned statutory rules",
    description="Returns data-driven rules with category, field, version, and status filters."
)
async def list_regulatory_rules(
    version: Optional[str] = Query(None, description="Statutory rule version (e.g. '2026.1', '2011')"),
    category: Optional[str] = Query(None, description="Category filter (e.g. 'packaged_commodity')"),
    field: Optional[str] = Query(None, description="Declaration field filter (e.g. 'mrp', 'net_quantity')"),
    status: Optional[str] = Query(None, description="Status filter (ACTIVE, PENDING_REVIEW, SUPERSEDED)")
):
    repo = get_regulatory_repository()
    return repo.list_rules(version=version, category=category, field=field, status=status)

@router.get(
    "/regulatory/rules/{rule_id}",
    response_model=RegulatoryRuleDTO,
    summary="Get single statutory rule by ID",
    description="Returns complete rule requirement, validation expression, and official DCA citations."
)
async def get_regulatory_rule(rule_id: str, version: Optional[str] = None):
    repo = get_regulatory_repository()
    rule = repo.get_rule_by_id(rule_id, version=version)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule with ID '{rule_id}' not found."
        )
    return rule

@router.post(
    "/regulatory/rules",
    response_model=RegulatoryRuleDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new statutory rule candidate",
    description="Creates a candidate rule in PENDING_REVIEW status awaiting admin authorization."
)
async def create_regulatory_rule(payload: RegulatoryRuleCreate):
    repo = get_regulatory_repository()
    return repo.create_rule(payload)

@router.post(
    "/regulatory/rules/{rule_id}/transition",
    summary="Admin lifecycle governance for statutory rules",
    description="Transitions rule status: APPROVE, ACTIVATE, SUPERSEDE, or REJECT."
)
async def transition_rule_status(rule_id: str, req: RuleStatusTransitionRequest):
    repo = get_regulatory_repository()
    action = req.action.upper().strip()
    valid_actions = {
        "APPROVE": "APPROVED",
        "ACTIVATE": "ACTIVE",
        "SUPERSEDE": "SUPERSEDED",
        "REJECT": "REJECTED"
    }
    if action not in valid_actions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action '{action}'. Valid actions: {list(valid_actions.keys())}"
        )

    target_status = valid_actions[action]
    success = repo.set_rule_status(rule_id, target_status, effective_until=req.effective_until)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule '{rule_id}' not found for status update."
        )

    return {
        "rule_id": rule_id,
        "new_status": target_status,
        "message": f"Rule successfully transitioned to {target_status} status."
    }

@router.get(
    "/regulatory/amendments",
    response_model=List[RuleAmendmentDTO],
    summary="List legislative amendment history and chronology",
    description="Returns chronological audit trail of statutory modifications under the Packaged Commodities Rules."
)
async def list_rule_amendments(rule_id: Optional[str] = None):
    repo = get_regulatory_repository()
    return repo.list_amendments(rule_id=rule_id)

from backend.app.services.regulatory.synchronizer import RegulatorySynchronizer

@router.post(
    "/regulatory/sync",
    summary="Synchronize regulatory database with official Department of Consumer Affairs publications",
    description="Connects to https://consumeraffairs.gov.in/pages/legal-metrology-act, discovers publications, computes hashes, and syncs statutory rule catalogs."
)
async def sync_official_regulatory_sources():
    try:
        return await RegulatorySynchronizer.sync_official_sources()
    except Exception as e:
        logger.error(f"Official regulatory synchronization failed: {e}", exc_info=True)
        return {
            "status": "FALLBACK",
            "source_authority": "Department of Consumer Affairs, Government of India",
            "source_url": "https://consumeraffairs.gov.in/pages/legal-metrology-act",
            "message": f"Source synchronization failed ({str(e)}) — using last successfully synchronized regulatory dataset.",
            "error_detail": str(e)
        }
