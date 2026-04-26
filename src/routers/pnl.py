from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlmodel import Session, select

from ..database import get_session
from ..models import Project, ProjectPnlSnapshot, ProjectStatus
from ..schemas import (
    ErrorCode,
    ErrorEnvelope,
    PnlDetailResponse,
    PnlProjectStatus,
    PnlSaveRequest,
    PnlSummary,
    PnlValues,
    ProjectListItem,
    ProjectListResponse,
)

router = APIRouter(tags=["Projects", "PnL"])


def _to_external_project_id(project_id: int) -> str:
    return f"prj_{project_id:03d}"


def _to_internal_project_id(project_id: str) -> int:
    if not project_id.startswith("prj_"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": ErrorCode.NOT_FOUND, "message": "Project not found", "details": {}}},
        )
    suffix = project_id.removeprefix("prj_")
    if not suffix.isdigit():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": ErrorCode.NOT_FOUND, "message": "Project not found", "details": {}}},
        )
    return int(suffix)


def _status_to_external(status_value: ProjectStatus) -> PnlProjectStatus:
    if status_value == ProjectStatus.CLOSED:
        return PnlProjectStatus.CLOSED
    return PnlProjectStatus.ACTIVE


def _snapshot_to_values(snapshot: ProjectPnlSnapshot) -> PnlValues:
    return PnlValues(
        contractAmount=snapshot.contract_amount,
        changeOrderAmount=snapshot.change_order_amount,
        otherRevenue=snapshot.other_revenue,
        materialCost=snapshot.material_cost,
        laborCost=snapshot.labor_cost,
        subcontractCost=snapshot.subcontract_cost,
        equipmentCost=snapshot.equipment_cost,
        expenseCost=snapshot.expense_cost,
        siteOverhead=snapshot.site_overhead,
        hqAllocation=snapshot.hq_allocation,
        contingency=snapshot.contingency,
        otherCost=snapshot.other_cost,
    )


def build_summary(values: PnlValues) -> PnlSummary:
    total_revenue = values.contractAmount + values.changeOrderAmount + values.otherRevenue
    total_cost = (
        values.materialCost
        + values.laborCost
        + values.subcontractCost
        + values.equipmentCost
        + values.expenseCost
        + values.siteOverhead
        + values.hqAllocation
        + values.contingency
        + values.otherCost
    )
    profit = total_revenue - total_cost
    margin = round((profit / total_revenue) * 100, 2) if total_revenue > 0 else 0.0
    return PnlSummary(
        totalRevenue=total_revenue,
        totalCost=total_cost,
        profit=profit,
        profitMargin=margin,
    )


def _get_or_init_snapshot(session: Session, project_id: int) -> ProjectPnlSnapshot:
    snapshot = session.get(ProjectPnlSnapshot, project_id)
    if snapshot:
        return snapshot
    snapshot = ProjectPnlSnapshot(project_id=project_id)
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return snapshot


@router.get(
    "/projects",
    response_model=ProjectListResponse,
    responses={500: {"model": ErrorEnvelope, "description": "Internal server error"}},
)
def list_projects(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    all_projects = session.exec(select(Project).order_by(Project.id)).all()
    total = len(all_projects)
    offset = (page - 1) * limit
    projects = all_projects[offset : offset + limit]
    items: list[ProjectListItem] = []
    for project in projects:
        snapshot = _get_or_init_snapshot(session, project.id)
        values = _snapshot_to_values(snapshot)
        items.append(
            ProjectListItem(
                id=_to_external_project_id(project.id),
                name=project.name,
                code=project.code,
                status=_status_to_external(project.status),
                pnlSummary=build_summary(values),
                updatedAt=snapshot.updated_at,
            )
        )
    return ProjectListResponse(items=items, page=page, limit=limit, total=total)


@router.get(
    "/projects/{projectId}/pnl",
    response_model=PnlDetailResponse,
    responses={
        404: {"model": ErrorEnvelope, "description": "Resource not found"},
        500: {"model": ErrorEnvelope, "description": "Internal server error"},
    },
)
def get_project_pnl(
    projectId: str = Path(..., description="Project ID"),
    session: Session = Depends(get_session),
):
    internal_project_id = _to_internal_project_id(projectId)
    project = session.get(Project, internal_project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": ErrorCode.NOT_FOUND, "message": "Project not found", "details": {}}},
        )
    snapshot = _get_or_init_snapshot(session, project.id)
    values = _snapshot_to_values(snapshot)
    return PnlDetailResponse(
        projectId=projectId,
        values=values,
        summary=build_summary(values),
        updatedAt=snapshot.updated_at,
    )


@router.put(
    "/projects/{projectId}/pnl",
    response_model=PnlDetailResponse,
    responses={
        400: {"model": ErrorEnvelope, "description": "Validation failed"},
        404: {"model": ErrorEnvelope, "description": "Resource not found"},
        409: {"model": ErrorEnvelope, "description": "Concurrency conflict"},
        500: {"model": ErrorEnvelope, "description": "Internal server error"},
    },
)
def put_project_pnl(
    payload: PnlSaveRequest,
    projectId: str = Path(..., description="Project ID"),
    session: Session = Depends(get_session),
):
    internal_project_id = _to_internal_project_id(projectId)
    project = session.get(Project, internal_project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": ErrorCode.NOT_FOUND, "message": "Project not found", "details": {}}},
        )

    snapshot = _get_or_init_snapshot(session, project.id)
    client_updated_at = (
        payload.clientUpdatedAt.replace(tzinfo=None)
        if payload.clientUpdatedAt.tzinfo is not None
        else payload.clientUpdatedAt
    )
    if client_updated_at != snapshot.updated_at:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": ErrorCode.CONFLICT,
                    "message": "Resource was updated by another request",
                    "details": {"serverUpdatedAt": snapshot.updated_at.isoformat(timespec="milliseconds") + "Z"},
                }
            },
        )

    values = payload.values
    snapshot.contract_amount = values.contractAmount
    snapshot.change_order_amount = values.changeOrderAmount
    snapshot.other_revenue = values.otherRevenue
    snapshot.material_cost = values.materialCost
    snapshot.labor_cost = values.laborCost
    snapshot.subcontract_cost = values.subcontractCost
    snapshot.equipment_cost = values.equipmentCost
    snapshot.expense_cost = values.expenseCost
    snapshot.site_overhead = values.siteOverhead
    snapshot.hq_allocation = values.hqAllocation
    snapshot.contingency = values.contingency
    snapshot.other_cost = values.otherCost
    snapshot.updated_at = datetime.utcnow()

    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    response_values = _snapshot_to_values(snapshot)
    return PnlDetailResponse(
        projectId=projectId,
        values=response_values,
        summary=build_summary(response_values),
        updatedAt=snapshot.updated_at,
    )
