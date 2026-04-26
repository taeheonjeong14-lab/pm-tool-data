from datetime import datetime

from ..models import EvidenceStatus


def normalize_vendor_name(name: str) -> str:
    normalized = " ".join(name.strip().upper().split())
    return normalized


def normalize_amount(value: str | float | int) -> float:
    if isinstance(value, (float, int)):
        return float(value)
    sanitized = value.replace(",", "").strip()
    return float(sanitized or 0)


def infer_needs_review(ocr_confidence: float | None) -> bool:
    if ocr_confidence is None:
        return False
    return ocr_confidence < 0.85


def infer_evidence_status(needs_review: bool) -> EvidenceStatus:
    return EvidenceStatus.NEEDS_REVIEW if needs_review else EvidenceStatus.COLLECTED


def iso_to_date(raw: str):
    return datetime.fromisoformat(raw).date()
