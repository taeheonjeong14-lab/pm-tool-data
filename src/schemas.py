from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

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


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PnlProjectStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class Currency(str, Enum):
    KRW = "KRW"


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class PnlValues(StrictModel):
    contractAmount: int = Field(ge=0)
    changeOrderAmount: int = Field(ge=0)
    otherRevenue: int = Field(ge=0)
    materialCost: int = Field(ge=0)
    laborCost: int = Field(ge=0)
    subcontractCost: int = Field(ge=0)
    equipmentCost: int = Field(ge=0)
    expenseCost: int = Field(ge=0)
    siteOverhead: int = Field(ge=0)
    hqAllocation: int = Field(ge=0)
    contingency: int = Field(ge=0)
    otherCost: int = Field(ge=0)


class PnlSummary(StrictModel):
    totalRevenue: int
    totalCost: int
    profit: int
    profitMargin: float


class ProjectListItem(StrictModel):
    id: str
    name: str
    code: str
    status: PnlProjectStatus
    pnlSummary: PnlSummary
    updatedAt: datetime


class ProjectListResponse(StrictModel):
    items: list[ProjectListItem]
    page: int = Field(ge=1)
    limit: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class PnlDetailResponse(StrictModel):
    projectId: str
    currency: Currency = Currency.KRW
    values: PnlValues
    summary: PnlSummary
    updatedAt: datetime


class PnlSaveRequest(StrictModel):
    values: PnlValues
    clientUpdatedAt: datetime


class ErrorBody(StrictModel):
    code: ErrorCode
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorEnvelope(StrictModel):
    error: ErrorBody
