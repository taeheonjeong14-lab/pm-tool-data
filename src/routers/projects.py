from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..database import get_session
from ..models import Evidence, Project, Vendor
from ..schemas import ProjectCreate, VendorCreate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("")
def create_project(payload: ProjectCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(Project).where(Project.code == payload.code)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Project code already exists.")
    project = Project(**payload.model_dump())
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.get("")
def list_projects(session: Session = Depends(get_session)):
    projects = session.exec(select(Project)).all()
    response = []
    for project in projects:
        total_cost = sum(
            e.amount_total
            for e in session.exec(select(Evidence).where(Evidence.project_id == project.id)).all()
        )
        response.append(
            {
                "id": project.id,
                "name": project.name,
                "code": project.code,
                "start_date": project.start_date,
                "end_date": project.end_date,
                "manager_name": project.manager_name,
                "status": project.status,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
                "cumulative_cost": total_cost,
            }
        )
    return response


@router.post("/vendors")
def create_vendor(payload: VendorCreate, session: Session = Depends(get_session)):
    vendor = Vendor(**payload.model_dump())
    session.add(vendor)
    session.commit()
    session.refresh(vendor)
    return vendor


@router.get("/vendors")
def list_vendors(session: Session = Depends(get_session)):
    return session.exec(select(Vendor)).all()
