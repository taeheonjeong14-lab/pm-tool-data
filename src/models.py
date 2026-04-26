from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class EvidenceType(str, Enum):
    TAX_INVOICE = "tax_invoice"
    CASH_RECEIPT = "cash_receipt"
    OCR_RECEIPT = "ocr_receipt"
    SIMPLE_RECEIPT = "simple_receipt"


class SourceSystem(str, Enum):
    HOMETAX = "hometax"
    OCR = "ocr"
    BANK_CSV = "bank_csv"
    MANUAL = "manual"


class EvidenceStatus(str, Enum):
    COLLECTED = "collected"
    NEEDS_REVIEW = "needs_review"
    REVIEWED = "reviewed"
    MATCHED = "matched"


class MatchStatus(str, Enum):
    MATCHED = "matched"
    POSSIBLE_MATCH = "possible_match"
    UNMATCHED = "unmatched"
    REJECTED = "rejected"


class ReviewActionType(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    MANUAL_LINK = "manual_link"


class ProjectStatus(str, Enum):
    ONGOING = "ongoing"
    CLOSED = "closed"


class Project(SQLModel, table=True):
    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    code: str = Field(index=True, unique=True)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    manager_name: Optional[str] = None
    status: ProjectStatus = Field(default=ProjectStatus.ONGOING, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Vendor(SQLModel, table=True):
    __tablename__ = "vendors"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    alias: Optional[str] = Field(default=None, index=True)
    business_number: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Evidence(SQLModel, table=True):
    __tablename__ = "evidences"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True, foreign_key="projects.id")
    vendor_id: Optional[int] = Field(default=None, foreign_key="vendors.id")
    vendor_name: str = Field(index=True)
    issue_date: date = Field(index=True)
    amount_supply: float = Field(default=0)
    amount_vat: float = Field(default=0)
    amount_total: float = Field(index=True)
    payment_method: Optional[str] = None
    evidence_type: EvidenceType
    source_system: SourceSystem
    status: EvidenceStatus = Field(default=EvidenceStatus.COLLECTED, index=True)
    ocr_confidence: Optional[float] = None
    needs_review: bool = Field(default=False, index=True)
    raw_payload: Optional[str] = None
    image_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BankTransaction(SQLModel, table=True):
    __tablename__ = "bank_transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True, foreign_key="projects.id")
    transfer_date: date = Field(index=True)
    vendor_name: str = Field(index=True)
    description: Optional[str] = None
    amount: float = Field(index=True)
    account_number_masked: Optional[str] = None
    source_system: SourceSystem = Field(default=SourceSystem.BANK_CSV)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EvidenceMatch(SQLModel, table=True):
    __tablename__ = "evidence_matches"

    id: Optional[int] = Field(default=None, primary_key=True)
    evidence_id: int = Field(index=True, foreign_key="evidences.id")
    bank_transaction_id: int = Field(index=True, foreign_key="bank_transactions.id")
    match_status: MatchStatus = Field(index=True)
    score: float = Field(default=0)
    reason: Optional[str] = None
    reviewed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewAction(SQLModel, table=True):
    __tablename__ = "review_actions"

    id: Optional[int] = Field(default=None, primary_key=True)
    evidence_match_id: int = Field(index=True, foreign_key="evidence_matches.id")
    action_type: ReviewActionType = Field(index=True)
    actor_name: str
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
