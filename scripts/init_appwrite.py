import json

from src.appwrite_client import AppwriteError, appwrite_request
from src.settings import settings


def ensure_database() -> None:
    payload = {"databaseId": settings.appwrite_database_id, "name": "PM Tool Data"}
    try:
        appwrite_request("POST", "/databases", payload)
        print(f"Created database: {settings.appwrite_database_id}")
    except AppwriteError as exc:
        if "already exists" in str(exc).lower():
            print(f"Database already exists: {settings.appwrite_database_id}")
            return
        raise


def ensure_collection(collection_id: str, name: str) -> None:
    payload = {
        "collectionId": collection_id,
        "databaseId": settings.appwrite_database_id,
        "name": name,
        "permissions": [],
        "documentSecurity": False,
        "enabled": True,
    }
    try:
        appwrite_request("POST", f"/databases/{settings.appwrite_database_id}/collections", payload)
        print(f"Created collection: {collection_id}")
    except AppwriteError as exc:
        if "already exists" in str(exc).lower():
            print(f"Collection already exists: {collection_id}")
            return
        raise


def apply_schema() -> None:
    collections = [
        ("projects", "Projects"),
        ("vendors", "Vendors"),
        ("evidences", "Evidences"),
        ("bank_transactions", "Bank Transactions"),
        ("evidence_matches", "Evidence Matches"),
        ("review_actions", "Review Actions"),
    ]
    for collection_id, name in collections:
        ensure_collection(collection_id, name)

    print("Collection bootstrap complete.")


def main() -> None:
    if not settings.appwrite_ready():
        raise RuntimeError("APPWRITE_ENDPOINT, APPWRITE_PROJECT_ID, APPWRITE_API_KEY are required.")

    print(
        json.dumps(
            {
                "endpoint": settings.appwrite_endpoint,
                "project_id": settings.appwrite_project_id,
                "database_id": settings.appwrite_database_id,
            },
            indent=2,
        )
    )
    ensure_database()
    apply_schema()
    print("Appwrite initialization complete.")


if __name__ == "__main__":
    main()
