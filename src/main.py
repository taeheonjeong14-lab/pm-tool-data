from fastapi import FastAPI

from .database import init_db
from .routers.dashboard import router as dashboard_router
from .routers.ingestion import router as ingestion_router
from .routers.matching import router as matching_router
from .routers.projects import router as projects_router

app = FastAPI(title="Construction PM P&L MVP", version="0.1.0")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"ok": True}


app.include_router(projects_router)
app.include_router(ingestion_router)
app.include_router(matching_router)
app.include_router(dashboard_router)
