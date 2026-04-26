from fastapi import FastAPI

from .appwrite_client import AppwriteError, appwrite_health
from .database import init_db
from .routers.dashboard import router as dashboard_router
from .routers.ingestion import router as ingestion_router
from .routers.matching import router as matching_router
from .routers.projects import router as projects_router
from .settings import settings

app = FastAPI(title="Construction PM P&L MVP", version="0.1.0")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/health/appwrite")
def health_appwrite():
    if not settings.appwrite_ready():
        return {"ok": False, "configured": False, "message": "Missing APPWRITE_* env vars."}
    try:
        status = appwrite_health()
        return {"ok": True, "configured": True, "status": status}
    except AppwriteError as exc:
        return {"ok": False, "configured": True, "message": str(exc)}
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "configured": True, "message": f"Unexpected error: {exc}"}


app.include_router(projects_router)
app.include_router(ingestion_router)
app.include_router(matching_router)
app.include_router(dashboard_router)
