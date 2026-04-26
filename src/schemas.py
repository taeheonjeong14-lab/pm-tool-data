from datetime import date
from typing import Optional

from pydantic import BaseModel

from .models import (
    EvidenceStatus,
    EvidenceType,
    MatchStatus,
    ProjectStatus,
    ReviewActionType,
    SourceSystem,
)


class ProjectCreate(BaseModel):
    name: str
    code: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    manager_name: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ONGOING


class VendorCreate(BaseModel):
    name: str
    alias: Optional[str] = None
    business_number: Optional[str] = None


class EvidenceCreate(BaseModel):
    project_id: int
    vendor_name: str
    issue_date: date
    amount_supply: float = 0
    amount_vat: float = 0
    amount_total: float
    payment_method: Optional[str] = None
    evidence_type: EvidenceType
    source_system: SourceSystem
    status: EvidenceStatus = EvidenceStatus.COLLECTED
    ocr_confidence: Optional[float] = None
    needs_review: bool = False
    raw_payload: Optional[str] = None
    image_path: Optional[str] = None


class BankTransactionCreate(BaseModel):
    project_id: int
    transfer_date: date
    vendor_name: str
    description: Optional[str] = None
    amount: float
    account_number_masked: Optional[str] = None


class ManualMatchDecision(BaseModel):
    evidence_match_id: int
    action_type: ReviewActionType
    actor_name: str
    note: Optional[str] = None


class ManualLinkRequest(BaseModel):
    evidence_id: int
    bank_transaction_id: int
    actor_name: str
    note: Optional[str] = None


class MatchResponse(BaseModel):
    evidence_id: int
    bank_transaction_id: int
    match_status: MatchStatus
    score: float
    reason: Optional[str] = None
