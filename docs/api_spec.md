# API Specification

## 종합 재무 리포트 조회 API

### Endpoint

```httpGET /api/v1/report/comprehensive/{stock_code}```

### Description

특정 기업의 종합 재무 리포트를 조회한다.

재무 데이터, Warning Signal, detected_changes, 산업 분류 정보 등을 함께 반환한다.

### Request Parameter

| Parameter | Type | Description |
|---|---|---|
| stock_code | string | 종목코드 |

### Response Structure

```json
{
  "status": "success",
  "message": "종합 재무 리포트 조회 성공",
  "data": {
    "company_info": {},
    "industry_info": {},
    "finance_summary": [],
    "signals": [],
    "detected_changes": [],
    "risk_signals": []
  }
}
```

### detected_changes Structure

| Field | Description |
|---|---|
| signal_code | Signal 코드 |
| metric_key | 지표 키 |
| query_hint | AI 검색용 Query |
| search_keywords | 뉴스 검색 키워드 |
| industry_group | 산업 그룹 |

### Example

```httpGET /api/v1/report/comprehensive/005930```