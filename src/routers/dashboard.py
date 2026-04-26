import csv
import io
from calendar import monthrange
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from ..database import get_session
from ..models import BankTransaction, Evidence, EvidenceMatch, MatchStatus
from ..services.project_context import ensure_project_exists

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _filter_evidences(
    evidences: list[Evidence],
    month: str | None = None,
    quarter: str | None = None,
    cumulative: bool = False,
    vendor: str | None = None,
    evidence_type: str | None = None,
):
    filtered = evidences
    if vendor:
        filtered = [e for e in filtered if e.vendor_name == vendor.upper()]
    if evidence_type:
        filtered = [e for e in filtered if e.evidence_type.value == evidence_type]
    if month and not cumulative:
        year, month_num = month.split("-")
        year_int = int(year)
        month_int = int(month_num)
        last_day = monthrange(year_int, month_int)[1]
        filtered = [
            e
            for e in filtered
            if e.issue_date >= date(year_int, month_int, 1)
            and e.issue_date <= date(year_int, month_int, last_day)
        ]
    if quarter and not cumulative:
        quarter_year, quarter_num = quarter.split("-Q")
        y = int(quarter_year)
        q = int(quarter_num)
        start_month = (q - 1) * 3 + 1
        end_month = start_month + 2
        quarter_start = date(y, start_month, 1)
        quarter_end = date(y, end_month, monthrange(y, end_month)[1])
        filtered = [e for e in filtered if quarter_start <= e.issue_date <= quarter_end]
    return filtered


@router.get("/project/{project_id}")
def project_dashboard(
    project_id: int,
    month: str | None = Query(default=None),
    quarter: str | None = Query(default=None),
    cumulative: bool = Query(default=False),
    vendor: str | None = Query(default=None),
    evidence_type: str | None = Query(default=None),
    session: Session = Depends(get_session),
):
    ensure_project_exists(session, project_id)
    evidences = session.exec(select(Evidence).where(Evidence.project_id == project_id)).all()
    evidences = _filter_evidences(evidences, month, quarter, cumulative, vendor, evidence_type)

    total_cost = sum(e.amount_total for e in evidences)
    needs_review_count = sum(1 for e in evidences if e.needs_review)

    matches = session.exec(
        select(EvidenceMatch, Evidence)
        .join(Evidence, Evidence.id == EvidenceMatch.evidence_id)
        .where(Evidence.project_id == project_id)
    ).all()
    unmatched_cost = sum(
        e.amount_total for m, e in matches if m.match_status in [MatchStatus.UNMATCHED, MatchStatus.POSSIBLE_MATCH]
    )

    bank_count = len(session.exec(select(BankTransaction).where(BankTransaction.project_id == project_id)).all())
    missing_evidence_suspected = max(0, bank_count - len(evidences))

    return {
        "project_id": project_id,
        "total_cost": total_cost,
        "unmatched_cost": unmatched_cost,
        "needs_review_count": needs_review_count,
        "missing_evidence_suspected": missing_evidence_suspected,
        "evidence_count": len(evidences),
        "bank_transaction_count": bank_count,
    }


@router.get("/project/{project_id}/pnl-statement")
def project_pnl_statement(
    project_id: int,
    month: str | None = Query(default=None),
    quarter: str | None = Query(default=None),
    cumulative: bool = Query(default=False),
    revenue: float | None = Query(default=None),
    session: Session = Depends(get_session),
):
    ensure_project_exists(session, project_id)
    evidences = session.exec(select(Evidence).where(Evidence.project_id == project_id)).all()
    evidences = _filter_evidences(evidences, month, quarter, cumulative)

    total_supply = sum(e.amount_supply for e in evidences)
    total_vat = sum(e.amount_vat for e in evidences)
    total_cost = sum(e.amount_total for e in evidences)
    needs_review_amount = sum(e.amount_total for e in evidences if e.needs_review)

    matches = session.exec(
        select(EvidenceMatch, Evidence)
        .join(Evidence, Evidence.id == EvidenceMatch.evidence_id)
        .where(Evidence.project_id == project_id)
    ).all()
    unmatched_amount = sum(
        e.amount_total for m, e in matches if m.match_status in [MatchStatus.POSSIBLE_MATCH, MatchStatus.UNMATCHED]
    )

    sales = revenue if revenue is not None else 0.0
    net_profit = sales - total_cost

    return {
        "project_id": project_id,
        "period": {"month": month, "quarter": quarter, "cumulative": cumulative},
        "statement": {
            "sales": sales,
            "total_cost": total_cost,
            "cost_supply": total_supply,
            "cost_vat": total_vat,
            "net_profit": net_profit,
        },
        "adjustments": {
            "unmatched_amount": unmatched_amount,
            "needs_review_amount": needs_review_amount,
        },
    }


@router.get("/project/{project_id}/pnl-charts")
def project_pnl_charts(project_id: int, top_n: int = Query(default=5), session: Session = Depends(get_session)):
    ensure_project_exists(session, project_id)
    evidences = session.exec(select(Evidence).where(Evidence.project_id == project_id)).all()

    monthly_cost: dict[str, float] = {}
    vendor_cost: dict[str, float] = {}
    type_distribution: dict[str, int] = {}
    for e in evidences:
        month_key = e.issue_date.strftime("%Y-%m")
        monthly_cost[month_key] = monthly_cost.get(month_key, 0) + e.amount_total
        vendor_cost[e.vendor_name] = vendor_cost.get(e.vendor_name, 0) + e.amount_total
        type_key = e.evidence_type.value
        type_distribution[type_key] = type_distribution.get(type_key, 0) + 1

    monthly_series = [{"month": k, "cost": monthly_cost[k]} for k in sorted(monthly_cost.keys())]
    top_vendors = sorted(vendor_cost.items(), key=lambda item: item[1], reverse=True)[:top_n]
    vendor_series = [{"vendor_name": v, "cost": c} for v, c in top_vendors]
    type_series = [{"evidence_type": k, "count": v} for k, v in sorted(type_distribution.items())]

    return {
        "project_id": project_id,
        "generated_at": datetime.utcnow().isoformat(),
        "charts": {
            "monthly_cost_trend": monthly_series,
            "vendor_cost_share_top_n": vendor_series,
            "evidence_type_distribution": type_series,
        },
    }


@router.get("/project/{project_id}/export.csv")
def export_project_csv(project_id: int, session: Session = Depends(get_session)):
    ensure_project_exists(session, project_id)
    evidences = session.exec(select(Evidence).where(Evidence.project_id == project_id)).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["evidence_id", "issue_date", "vendor_name", "amount_total", "status", "source_system"])
    for evidence in evidences:
        writer.writerow(
            [
                evidence.id,
                evidence.issue_date.isoformat(),
                evidence.vendor_name,
                evidence.amount_total,
                evidence.status,
                evidence.source_system,
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=project_{project_id}_evidence.csv"},
    )


@router.get("/project/{project_id}/pnl-statement.csv")
def export_pnl_statement_csv(
    project_id: int,
    month: str | None = Query(default=None),
    quarter: str | None = Query(default=None),
    cumulative: bool = Query(default=False),
    revenue: float | None = Query(default=None),
    session: Session = Depends(get_session),
):
    pnl = project_pnl_statement(project_id, month, quarter, cumulative, revenue, session)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["metric", "value"])
    writer.writerow(["sales", pnl["statement"]["sales"]])
    writer.writerow(["total_cost", pnl["statement"]["total_cost"]])
    writer.writerow(["cost_supply", pnl["statement"]["cost_supply"]])
    writer.writerow(["cost_vat", pnl["statement"]["cost_vat"]])
    writer.writerow(["net_profit", pnl["statement"]["net_profit"]])
    writer.writerow(["unmatched_amount", pnl["adjustments"]["unmatched_amount"]])
    writer.writerow(["needs_review_amount", pnl["adjustments"]["needs_review_amount"]])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=project_{project_id}_pnl_statement.csv"},
    )
