from datetime import timedelta

from sqlmodel import Session, select

from ..models import (
    BankTransaction,
    Evidence,
    EvidenceMatch,
    EvidenceStatus,
    MatchStatus,
)


def _vendor_similarity(left: str, right: str) -> float:
    left_tokens = set(left.upper().split())
    right_tokens = set(right.upper().split())
    if not left_tokens or not right_tokens:
        return 0
    intersection = len(left_tokens.intersection(right_tokens))
    union = len(left_tokens.union(right_tokens))
    return intersection / union


def _score(evidence: Evidence, transaction: BankTransaction) -> tuple[float, str]:
    amount_gap = abs(evidence.amount_total - transaction.amount)
    amount_score = 1.0 if amount_gap == 0 else max(0.0, 1.0 - (amount_gap / max(transaction.amount, 1)))
    date_gap = abs((evidence.issue_date - transaction.transfer_date).days)
    date_score = 1.0 if date_gap <= 1 else (0.7 if date_gap <= 7 else 0.0)
    vendor_score = _vendor_similarity(evidence.vendor_name, transaction.vendor_name)
    total = (0.5 * amount_score) + (0.3 * date_score) + (0.2 * vendor_score)
    reason = f"amount_gap={amount_gap}, date_gap={date_gap}, vendor_similarity={vendor_score:.2f}"
    return total, reason


def classify(score: float) -> MatchStatus:
    if score >= 0.9:
        return MatchStatus.MATCHED
    if score >= 0.6:
        return MatchStatus.POSSIBLE_MATCH
    return MatchStatus.UNMATCHED


def run_auto_match(session: Session, project_id: int) -> int:
    evidences = session.exec(
        select(Evidence).where(Evidence.project_id == project_id, Evidence.status != EvidenceStatus.MATCHED)
    ).all()
    transactions = session.exec(select(BankTransaction).where(BankTransaction.project_id == project_id)).all()

    created_count = 0
    for evidence in evidences:
        for tx in transactions:
            # Hard pruning for runtime and relevance.
            if abs((evidence.issue_date - tx.transfer_date).days) > 14:
                continue
            if abs(evidence.amount_total - tx.amount) > (0.2 * max(tx.amount, 1)):
                continue
            score, reason = _score(evidence, tx)
            status = classify(score)
            match = EvidenceMatch(
                evidence_id=evidence.id,
                bank_transaction_id=tx.id,
                match_status=status,
                score=round(score, 4),
                reason=reason,
                reviewed=False,
            )
            session.add(match)
            created_count += 1

    session.commit()
    return created_count
