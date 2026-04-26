from typing import Any

import httpx

from .settings import settings


class AppwriteError(Exception):
    pass


def _headers() -> dict[str, str]:
    return {
        "X-Appwrite-Project": settings.appwrite_project_id,
        "X-Appwrite-Key": settings.appwrite_api_key,
        "Content-Type": "application/json",
    }


def appwrite_request(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if not settings.appwrite_ready():
        raise AppwriteError("Appwrite env vars are not fully configured.")

    url = f"{settings.appwrite_endpoint}{path}"
    with httpx.Client(timeout=20.0) as client:
        response = client.request(method=method, url=url, headers=_headers(), json=payload)
    if response.status_code >= 400:
        raise AppwriteError(f"Appwrite API error {response.status_code}: {response.text}")
    if not response.text:
        return {}
    return response.json()


def appwrite_health() -> dict[str, Any]:
    # Public health endpoint to verify endpoint reachability.
    url = f"{settings.appwrite_endpoint}/health"
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url)
    response.raise_for_status()
    return response.json()
