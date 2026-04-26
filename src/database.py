import os

from sqlmodel import Session, SQLModel, create_engine

DEFAULT_LOCAL_SQLITE = "sqlite:///./pm_tool.db"


def _resolve_database_url() -> str:
    configured = os.getenv("DATABASE_URL")
    if configured:
        return configured

    # Vercel serverless runtime can write only under /tmp.
    if os.getenv("VERCEL"):
        return "sqlite:////tmp/pm_tool.db"
    return DEFAULT_LOCAL_SQLITE


DATABASE_URL = _resolve_database_url()

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
