# Database Schema

## Overview

본 시스템은 MySQL 기반으로 기업 정보, 재무 데이터, Warning Signal 정보를 관리한다.

---

# Tables

## companies

기업 기본 정보 테이블

| Column | Type | Description |
|---|---|---|
| stock_code | VARCHAR | 종목코드 |
| corp_code | VARCHAR | DART 기업코드 |
| company_name | VARCHAR | 기업명 |
| induty_code | VARCHAR | 업종코드 |

---

## financials

연도별 재무 데이터 저장 테이블

| Column | Description |
|---|---|
| revenue | 매출액 |
| operating_income | 영업이익 |
| total_assets | 총자산 |
| total_liabilities | 총부채 |

---

## financial_ratios

재무 비율 저장 테이블

| Column | Description |
|---|---|
| debt_ratio | 부채비율 |
| roe | ROE |
| roa | ROA |

---

## warning_signals

Warning / Positive Signal 저장 테이블

| Column | Description |
|---|---|
| signal_code | Signal 코드 |
| signal_type | positive / negative |
| severity | 위험도 |

---

# Relationship

```text
companies
  └── financials
        └── warning_signals
```

---

# Company Batch Loading

- `companies_for_db.csv` 기반 기업 정보 적재
- 총 3963개 기업 적재 완료