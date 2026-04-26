# Construction PM P&L MVP

건설 현장 PM이 프로젝트 단위로 비용증빙을 수집하고 P&L을 빠르게 확인할 수 있도록 하는 MVP 백엔드입니다.

## 포함 기능

- 프로젝트 생성/목록/상세 컨텍스트 관리
- 홈택스 JSON 수집 (세금계산서/현금영수증)
- 영수증 이미지 OCR 결과 수집 (MVP 메타데이터 처리)
- 은행 이체 CSV 수집
- 증빙-거래내역 규칙 기반 자동 매칭 + 검수/수동 연결
- 프로젝트 대시보드 + 손익계산서형/그래프형 P&L + CSV 내보내기

## 실행 방법

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```

API 문서: `http://127.0.0.1:8000/docs`

## Appwrite 설정

1. `.env.example`를 참고해 루트 `.env`를 구성
2. `APPWRITE_ENDPOINT`, `APPWRITE_PROJECT_ID`, `APPWRITE_API_KEY` 설정
3. 필요 시 `APPWRITE_DATABASE_ID` 지정 (기본: `pm_tool`)

Appwrite 초기화:

```bash
python scripts/init_appwrite.py
```

연결 상태 확인:

- `GET /health/appwrite`

## 프로젝트 관리

### 프로젝트 생성 `/projects`

- 필드: `name`, `code`, `start_date`, `end_date`, `manager_name`, `status`
- 상태값: `ongoing`, `closed`
- 모든 수집/매칭/대시보드 API는 존재하는 `project_id`가 필요합니다.

## 데이터 수집 포맷

### 1) 홈택스 `/ingestion/hometax`

- `multipart/form-data`
  - `project_id`: number
  - `evidence_type`: `tax_invoice` | `cash_receipt`
  - `payload_file`: JSON 파일

JSON 배열 예시:

```json
[
  {
    "vendor_name": "ABC STEEL",
    "issue_date": "2026-04-01",
    "amount_supply": 100000,
    "amount_vat": 10000,
    "amount_total": 110000,
    "payment_method": "transfer"
  }
]
```

### 2) 은행 CSV `/ingestion/bank-csv`

- `multipart/form-data`
  - `project_id`: number
  - `csv_file`: CSV 파일

CSV 컬럼:

```text
transfer_date,vendor_name,description,amount,account_number_masked
2026-04-03,ABC STEEL,steel payment,110000,1234-****-****
```

### 3) OCR 영수증 `/ingestion/ocr-receipt`

- `multipart/form-data`
  - `project_id`, `vendor_name`, `issue_date`, `amount_total`, `ocr_confidence`, `receipt_image`

## 매칭/검수 흐름

1. `/matching/run/{project_id}` 실행
2. `/matching/review-queue/{project_id}` 로 후보 확인
3. `/matching/review-decision` 으로 승인/거절
4. `/matching/manual-link` 으로 수동 연결

## 대시보드

- `GET /dashboard/project/{project_id}`
  - 필터: `month=YYYY-MM`, `quarter=YYYY-Qn`, `cumulative=true|false`, `vendor`, `evidence_type`
- `GET /dashboard/project/{project_id}/pnl-statement`
  - 손익계산서형 응답
  - 옵션: `month`, `quarter`, `cumulative`, `revenue`
- `GET /dashboard/project/{project_id}/pnl-charts`
  - 그래프용 응답
  - 포함: 월별 원가 추이, 거래처 Top N 비용 비중, 증빙유형 분포
- `GET /dashboard/project/{project_id}/export.csv`
- `GET /dashboard/project/{project_id}/pnl-statement.csv`
