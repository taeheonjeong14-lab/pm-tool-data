from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..database import get_session
from ..models import (
    BankTransaction,
    Evidence,
    EvidenceMatch,
    EvidenceStatus,
    MatchStatus,
    ReviewAction,
    ReviewActionType,
)
from ..schemas import ManualLinkRequest, MatchResponse, ManualMatchDecision
from ..services.matching import run_auto_match
from ..services.project_context import ensure_project_exists

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post("/run/{project_id}")
def execute_matching(project_id: int, session: Session = Depends(get_session)):
    ensure_project_exists(session, project_id)
    created_count = run_auto_match(session, project_id)
    return {"created_match_candidates": created_count}


@router.get("/review-queue/{project_id}", response_model=list[MatchResponse])
def get_review_queue(project_id: int, session: Session = Depends(get_session)):
    ensure_project_exists(session, project_id)
    query = (
        select(EvidenceMatch, Evidence)
        .join(Evidence, Evidence.id == EvidenceMatch.evidence_id)
        .where(
            Evidence.project_id == project_id,
            EvidenceMatch.match_status.in_([MatchStatus.POSSIBLE_MATCH, MatchStatus.UNMATCHED]),
            EvidenceMatch.reviewed.is_(False),
        )
        .order_by(EvidenceMatch.score.desc())
    )
    rows = session.exec(query).all()
    return [
        MatchResponse(
            evidence_id=evidence_match.evidence_id,
            bank_transaction_id=evidence_match.bank_transaction_id,
            match_status=evidence_match.match_status,
            score=evidence_match.score,
            reason=evidence_match.reason,
        )
        for evidence_match, _evidence in rows
    ]


@router.post("/review-decision")
def review_decision(payload: ManualMatchDecision, session: Session = Depends(get_session)):
    evidence_match = session.get(EvidenceMatch, payload.evidence_match_id)
    if not evidence_match:
        raise HTTPException(status_code=404, detail="Match record not found.")

    if payload.action_type.value == "approve":
        evidence_match.match_status = MatchStatus.MATCHED
        evidence = session.get(Evidence, evidence_match.evidence_id)
        if evidence:
            evidence.status = EvidenceStatus.MATCHED
    elif payload.action_type.value == "reject":
        evidence_match.match_status = MatchStatus.REJECTED

    evidence_match.reviewed = True
    action = ReviewAction(
        evidence_match_id=evidence_match.id,
        action_type=payload.action_type,
        actor_name=payload.actor_name,
        note=payload.note,
    )
    session.add(action)
    session.commit()
    return {"ok": True}


@router.post("/manual-link")
def manual_link(payload: ManualLinkRequest, session: Session = Depends(get_session)):
    evidence = session.get(Evidence, payload.evidence_id)
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found.")
    transaction = session.get(BankTransaction, payload.bank_transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Bank transaction not found.")

    match = EvidenceMatch(
        evidence_id=payload.evidence_id,
        bank_transaction_id=payload.bank_transaction_id,
        match_status=MatchStatus.MATCHED,
        score=1.0,
        reason="manual_link",
        reviewed=True,
    )
    session.add(match)
    session.flush()
    evidence.status = EvidenceStatus.MATCHED
    action = ReviewAction(
        evidence_match_id=match.id,
        action_type=ReviewActionType.MANUAL_LINK,
        actor_name=payload.actor_name,
        note=payload.note,
    )
    session.add(action)
    session.commit()
    return {"ok": True}
