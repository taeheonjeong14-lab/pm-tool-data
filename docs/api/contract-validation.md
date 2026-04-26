# Contract Validation Report

This report validates the implemented endpoints against `docs/api/contract.md`.

## Result

All contract-critical endpoints are implemented and reachable via registered routers in `src/main.py`.

## Checklist

- Projects
  - `POST /projects`: implemented in `src/routers/projects.py`
  - `GET /projects`: implemented in `src/routers/projects.py`
- Ingestion
  - `POST /ingestion/hometax`: implemented in `src/routers/ingestion.py`
  - `POST /ingestion/ocr-receipt`: implemented in `src/routers/ingestion.py`
  - `POST /ingestion/bank-csv`: implemented in `src/routers/ingestion.py`
- Matching and review
  - `POST /matching/run/{project_id}`: implemented in `src/routers/matching.py`
  - `GET /matching/review-queue/{project_id}`: implemented in `src/routers/matching.py`
  - `POST /matching/review-decision`: implemented in `src/routers/matching.py`
  - `POST /matching/manual-link`: implemented in `src/routers/matching.py`
- Dashboard and exports
  - `GET /dashboard/project/{project_id}`: implemented in `src/routers/dashboard.py`
  - `GET /dashboard/project/{project_id}/pnl-statement`: implemented in `src/routers/dashboard.py`
  - `GET /dashboard/project/{project_id}/pnl-charts`: implemented in `src/routers/dashboard.py`
  - `GET /dashboard/project/{project_id}/export.csv`: implemented in `src/routers/dashboard.py`
  - `GET /dashboard/project/{project_id}/pnl-statement.csv`: implemented in `src/routers/dashboard.py`

## Contract Rule Validation

- Project-scoped guard:
  - Enforced via `ensure_project_exists()` in ingestion, matching, and dashboard routers.
- Date and period formats:
  - Accepted as `YYYY-MM-DD`, `YYYY-MM`, and `YYYY-Qn` by current route handlers.
- Enum ownership:
  - Centralized in `src/models.py`.

## Follow-up (Non-blocking)

- Add explicit response models for all endpoints for stricter schema stability.
- Add contract tests that assert sample payloads from `docs/api/sample-payloads.json`.
