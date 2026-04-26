from fastapi import HTTPException
from sqlmodel import Session

from ..models import Project


def ensure_project_exists(session: Session, project_id: int) -> Project:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project
