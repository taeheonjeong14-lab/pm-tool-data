import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session

from ..database import get_session
from ..models import Evidence, EvidenceType, SourceSystem, BankTransaction
from ..services.project_context import ensure_project_exists
from ..services.normalization import (
    infer_evidence_status,
    infer_needs_review,
    normalize_amount,
    normalize_vendor_name,
)

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/hometax")
async def ingest_hometax(
    project_id: int = Form(...),
    evidence_type: EvidenceType = Form(...),
    payload_file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    ensure_project_exists(session, project_id)
    raw = await payload_file.read()
    try:
        records = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="hometax payload must be valid UTF-8 JSON.")

    if not isinstance(records, list):
        raise HTTPException(status_code=400, detail="hometax payload should be a JSON array.")

    inserted = 0
    for row in records:
        vendor = normalize_vendor_name(str(row.get("vendor_name", "")))
        issue_date_raw = str(row.get("issue_date", ""))
        if not vendor or not issue_date_raw:
            continue
        evidence = Evidence(
            project_id=project_id,
            vendor_name=vendor,
            issue_date=datetime.fromisoformat(issue_date_raw).date(),
            amount_supply=normalize_amount(row.get("amount_supply", 0)),
            amount_vat=normalize_amount(row.get("amount_vat", 0)),
            amount_total=normalize_amount(row.get("amount_total", 0)),
            payment_method=row.get("payment_method"),
            evidence_type=evidence_type,
            source_system=SourceSystem.HOMETAX,
            status=infer_evidence_status(False),
            needs_review=False,
            raw_payload=json.dumps(row, ensure_ascii=True),
        )
        session.add(evidence)
        inserted += 1

    session.commit()
    return {"inserted": inserted}


@router.post("/bank-csv")
async def ingest_bank_csv(
    project_id: int = Form(...),
    csv_file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    ensure_project_exists(session, project_id)
    raw = await csv_file.read()
    decoded = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))
    inserted = 0

    for row in reader:
        transfer_date = datetime.fromisoformat(row["transfer_date"]).date()
        transaction = BankTransaction(
            project_id=project_id,
            transfer_date=transfer_date,
            vendor_name=normalize_vendor_name(row.get("vendor_name", "")),
            description=row.get("description"),
            amount=normalize_amount(row.get("amount", 0)),
            account_number_masked=row.get("account_number_masked"),
            source_system=SourceSystem.BANK_CSV,
        )
        session.add(transaction)
        inserted += 1

    session.commit()
    return {"inserted": inserted}


@router.post("/ocr-receipt")
async def ingest_ocr_receipt(
    project_id: int = Form(...),
    vendor_name: str = Form(...),
    issue_date: str = Form(...),
    amount_total: float = Form(...),
    ocr_confidence: float = Form(...),
    receipt_image: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    ensure_project_exists(session, project_id)
    # MVP: store metadata and filename. Worker/OCR connector can later replace this with async pipeline.
    _ = await receipt_image.read()
    normalized_vendor = normalize_vendor_name(vendor_name)
    needs_review = infer_needs_review(ocr_confidence)
    evidence = Evidence(
        project_id=project_id,
        vendor_name=normalized_vendor,
        issue_date=datetime.fromisoformat(issue_date).date(),
        amount_total=amount_total,
        amount_supply=amount_total,
        amount_vat=0,
        evidence_type=EvidenceType.OCR_RECEIPT,
        source_system=SourceSystem.OCR,
        ocr_confidence=ocr_confidence,
        needs_review=needs_review,
        status=infer_evidence_status(needs_review),
        image_path=receipt_image.filename,
    )
    session.add(evidence)
    session.commit()
    session.refresh(evidence)
    return {"id": evidence.id, "needs_review": evidence.needs_review}
