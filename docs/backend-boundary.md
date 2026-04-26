# Backend Boundary

This repository is dedicated to the data backend only.

## Scope

- Data ingestion APIs (HomeTax, OCR receipt metadata, bank CSV)
- Data normalization and project-context validation
- Matching engine and review workflow
- Project-level P&L aggregation APIs and CSV export
- Database schema and data policies for Supabase

## Out Of Scope

- Frontend UI implementation and routing
- Client-side visualization components
- UI state management and design system

## Integration Contract

- UI connects to this backend over HTTP APIs only.
- Backend owns enum/status values and response schema contracts.
- All project-bound writes require `project_id`.
