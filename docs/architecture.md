# Data Backend Architecture

## Modules

- `src/routers/projects.py`: project and vendor endpoints
- `src/routers/ingestion.py`: ingest endpoints
- `src/routers/matching.py`: matching and review endpoints
- `src/routers/dashboard.py`: P&L and CSV endpoints
- `src/services/`: normalization, matching, project-context guard
- `src/models.py`: domain entities and enums
- `src/schemas.py`: request/response models

## Runtime Flow

1. Client sends project-scoped ingestion payload.
2. Backend validates project context.
3. Data is normalized and persisted.
4. Matching engine generates candidate links.
5. Review actions finalize match states.
6. P&L APIs aggregate by period and expose statement/chart data.
