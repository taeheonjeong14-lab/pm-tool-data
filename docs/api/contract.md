# API Contract (UI Integration)

Base URL: `/`
Content type: `application/json` unless multipart is specified.

## Enum Values

- `project.status`: `ongoing` | `closed`
- `evidence_type`: `tax_invoice` | `cash_receipt` | `ocr_receipt` | `simple_receipt`
- `source_system`: `hometax` | `ocr` | `bank_csv` | `manual`
- `evidence.status`: `collected` | `needs_review` | `reviewed` | `matched`
- `match_status`: `matched` | `possible_match` | `unmatched` | `rejected`
- `review_action_type`: `approve` | `reject` | `manual_link`

## 1) Projects

### POST `/projects`
Request:
```json
{
  "name": "Tower A Renovation",
  "code": "PRJ-2026-001",
  "start_date": "2026-01-01",
  "end_date": "2026-12-31",
  "manager_name": "Lee PM",
  "status": "ongoing"
}
```

Response `200`:
```json
{
  "id": 1,
  "name": "Tower A Renovation",
  "code": "PRJ-2026-001",
  "start_date": "2026-01-01",
  "end_date": "2026-12-31",
  "manager_name": "Lee PM",
  "status": "ongoing",
  "created_at": "2026-04-26T05:00:00.000000",
  "updated_at": "2026-04-26T05:00:00.000000"
}
```

### GET `/projects`
Response `200`:
```json
[
  {
    "id": 1,
    "name": "Tower A Renovation",
    "code": "PRJ-2026-001",
    "start_date": "2026-01-01",
    "end_date": "2026-12-31",
    "manager_name": "Lee PM",
    "status": "ongoing",
    "created_at": "2026-04-26T05:00:00.000000",
    "updated_at": "2026-04-26T05:00:00.000000",
    "cumulative_cost": 12400000.0
  }
]
```

## 2) Ingestion

### POST `/ingestion/hometax` (multipart)
Fields:
- `project_id` (number)
- `evidence_type` (`tax_invoice` or `cash_receipt`)
- `payload_file` (json file)

Response:
```json
{"inserted": 4}
```

### POST `/ingestion/ocr-receipt` (multipart)
Fields:
- `project_id`, `vendor_name`, `issue_date`, `amount_total`, `ocr_confidence`, `receipt_image`

Response:
```json
{"id": 10, "needs_review": true}
```

### POST `/ingestion/bank-csv` (multipart)
Fields:
- `project_id`
- `csv_file`

Response:
```json
{"inserted": 12}
```

## 3) Matching And Review

### POST `/matching/run/{project_id}`
Response:
```json
{"created_match_candidates": 16}
```

### GET `/matching/review-queue/{project_id}`
Response:
```json
[
  {
    "evidence_id": 3,
    "bank_transaction_id": 14,
    "match_status": "possible_match",
    "score": 0.83,
    "reason": "amount_gap=2000.0, date_gap=2, vendor_similarity=0.67"
  }
]
```

### POST `/matching/review-decision`
Request:
```json
{
  "evidence_match_id": 7,
  "action_type": "approve",
  "actor_name": "reviewer@company.com",
  "note": "verified with receipt image"
}
```

Response:
```json
{"ok": true}
```

### POST `/matching/manual-link`
Request:
```json
{
  "evidence_id": 8,
  "bank_transaction_id": 31,
  "actor_name": "reviewer@company.com",
  "note": "manual linking by PM"
}
```

Response:
```json
{"ok": true}
```

## 4) Dashboard And P&L

### GET `/dashboard/project/{project_id}`
Query:
- `month=YYYY-MM`
- `quarter=YYYY-Qn`
- `cumulative=true|false`
- `vendor=ABC STEEL`
- `evidence_type=tax_invoice`

Response:
```json
{
  "project_id": 1,
  "total_cost": 1500000.0,
  "unmatched_cost": 200000.0,
  "needs_review_count": 3,
  "missing_evidence_suspected": 2,
  "evidence_count": 18,
  "bank_transaction_count": 20
}
```

### GET `/dashboard/project/{project_id}/pnl-statement`
Query:
- `month`, `quarter`, `cumulative`, `revenue`

Response:
```json
{
  "project_id": 1,
  "period": {
    "month": "2026-04",
    "quarter": null,
    "cumulative": false
  },
  "statement": {
    "sales": 2500000.0,
    "total_cost": 1500000.0,
    "cost_supply": 1363636.0,
    "cost_vat": 136364.0,
    "net_profit": 1000000.0
  },
  "adjustments": {
    "unmatched_amount": 200000.0,
    "needs_review_amount": 85000.0
  }
}
```

### GET `/dashboard/project/{project_id}/pnl-charts`
Query:
- `top_n` (default: 5)

Response:
```json
{
  "project_id": 1,
  "generated_at": "2026-04-26T05:10:11.000000",
  "charts": {
    "monthly_cost_trend": [{"month": "2026-03", "cost": 900000.0}],
    "vendor_cost_share_top_n": [{"vendor_name": "ABC STEEL", "cost": 400000.0}],
    "evidence_type_distribution": [{"evidence_type": "tax_invoice", "count": 10}]
  }
}
```

## CSV Endpoints

- `GET /dashboard/project/{project_id}/export.csv`
- `GET /dashboard/project/{project_id}/pnl-statement.csv`

## Contract Rules

- Project-scoped writes fail when `project_id` is missing or invalid.
- Date formats:
  - Day: `YYYY-MM-DD`
  - Month: `YYYY-MM`
  - Quarter: `YYYY-Qn`
- Backend is the source of truth for enum values.
