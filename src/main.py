import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .appwrite_client import AppwriteError, appwrite_health
from .database import init_db
from .routers.dashboard import router as dashboard_router
from .routers.ingestion import router as ingestion_router
from .routers.matching import router as matching_router
from .routers.pnl import router as pnl_router
from .routers.projects import router as projects_router
from .schemas import ErrorCode
from .settings import settings

app = FastAPI(title="Construction PM P&L MVP", version="0.1.0")
logger = logging.getLogger(__name__)


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


def _error_response(
    status_code: int,
    code: ErrorCode,
    message: str,
    details: dict[str, Any] | None = None,
):
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code.value, "message": message, "details": details or {}}},
    )


@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(_request: Request, exc: RequestValidationError):
    return _error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        code=ErrorCode.VALIDATION_ERROR,
        message="Validation failed",
        details={"issues": exc.errors()},
    )


@app.exception_handler(HTTPException)
async def handle_http_exception(_request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    if exc.status_code == status.HTTP_404_NOT_FOUND:
        code = ErrorCode.NOT_FOUND
        default_message = "Resource not found"
    elif exc.status_code == status.HTTP_409_CONFLICT:
        code = ErrorCode.CONFLICT
        default_message = "Concurrency conflict"
    elif exc.status_code == status.HTTP_400_BAD_REQUEST:
        code = ErrorCode.VALIDATION_ERROR
        default_message = "Validation failed"
    else:
        code = ErrorCode.INTERNAL_ERROR
        default_message = "Unexpected error"

    detail_message = default_message
    detail_payload: dict[str, Any] = {}
    if isinstance(exc.detail, str):
        detail_message = exc.detail
    elif isinstance(exc.detail, dict):
        detail_payload = exc.detail
        if isinstance(exc.detail.get("message"), str):
            detail_message = exc.detail["message"]

    return _error_response(
        status_code=exc.status_code,
        code=code,
        message=detail_message,
        details=detail_payload,
    )


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception):
    logger.exception("Unhandled server error at %s", request.url.path, exc_info=exc)
    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code=ErrorCode.INTERNAL_ERROR,
        message="Unexpected error",
    )


app.include_router(projects_router)
app.include_router(ingestion_router)
app.include_router(matching_router)
app.include_router(dashboard_router)
app.include_router(pnl_router)
