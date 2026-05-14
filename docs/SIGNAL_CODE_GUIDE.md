# SIGNAL_CODE_GUIDE

## 개요

본 문서는 Finance_DOT_ZIP 프로젝트에서 사용하는 `signals` 구조와 `signal_code` 목록을 정리한 문서입니다.

`signals`는 정량 재무 데이터 기반으로 감지된 Warning / Positive Signal입니다.

현재 Signal은 다음 흐름으로 사용됩니다.

```text
finance_summary
    ↓
signal_service.py
    ↓
signals
    ↓
detected_change_service.py
    ↓
detected_changes
    ↓
AI / RAG 검색 query 생성
```

---

# signals 기본 구조

```json
{
  "year": 2023,
  "type": "negative",
  "severity": "HIGH",
  "signal": "매출액 50% 이상 감소",
  "signal_code": "REVENUE_DROP_50",
  "metric_key": "revenue",
  "description": "전년 대비 매출액이 -50.0% 감소했습니다."
}
```

---

# 필드 설명

| 필드 | 설명 |
|---|---|
| year | Signal이 발생한 연도 |
| type | positive / negative / excluded |
| severity | CRITICAL / HIGH / MEDIUM / LOW / INFO |
| signal | 사용자에게 보여줄 한글 Signal명 |
| signal_code | AI/프론트/검색 연동용 고정 코드 |
| metric_key | Signal 판단에 사용된 재무 지표 |
| description | Signal 설명 문장 |

---

# Negative Signal Codes

| signal_code | signal | severity | metric_key | 설명 |
|---|---|---|---|---|
| REVENUE_DROP_50 | 매출액 50% 이상 감소 | HIGH | revenue | 전년 대비 매출액이 50% 이상 감소 |
| OPERATING_LOSS_3Y | 영업손실 3개년 지속 | HIGH | operating_income | 최근 3개년 연속 영업손실 발생 |
| INTEREST_COVERAGE_3Y_LOW | 이자보상배율 3개년 연속 1 미만 | HIGH | interest_coverage_ratio | 최근 3개년 연속 이자보상배율 1 미만 |
| CASH_FLOW_NEGATIVE_3Y | 영업활동현금흐름 3개년 적자 | HIGH | operating_cash_flow | 최근 3개년 연속 영업활동현금흐름 음수 |
| CASH_LESS_THAN_SHORT_BORROWINGS | 현금성자산 단기차입금 미달 | MEDIUM | cash | 현금성자산이 단기차입금보다 적음 |
| DEBT_RATIO_OVER_400 | 부채비율 400% 초과 | HIGH | debt_ratio | 부채비율이 400% 초과 |
| CAPITAL_IMPAIRMENT_PARTIAL | 부분자본잠식 | HIGH | total_equity | 자본총계가 자본금보다 작음 |
| CAPITAL_IMPAIRMENT_FULL | 완전자본잠식 | CRITICAL | total_equity | 자본총계가 0보다 작음 |

---

# Positive Signal Codes

| signal_code | signal | severity | metric_key | 설명 |
|---|---|---|---|---|
| REVENUE_JUMP | 매출 퀀텀 점프 | HIGH | revenue | 전년 대비 매출액 30% 이상 증가 |
| EARNINGS_SURPRISE | 어닝 서프라이즈 | HIGH | operating_income | 전년 대비 영업이익 50% 이상 증가 |
| OPERATING_INCOME_TURN_TO_PROFIT | 영업이익 흑자 전환 | HIGH | operating_income | 전년도 적자에서 당해 연도 흑자 전환 |
| ASSET_EFFICIENCY_UP | 자산 가동률 상승 | MEDIUM | asset_turnover | 재고자산회전율 또는 매출채권회전율 개선 |
| CAPACITY_EXPANSION | Capa 확대 | MEDIUM | total_assets | 자산 규모 30% 이상 증가 |
| DEBT_RATIO_DOWN | 재무 구조 개선 | LOW | debt_ratio | 부채비율 전년 대비 50%p 이상 감소 |
| CASH_FLOW_STRONG | 현금 창출력 강화 | LOW | operating_cash_flow | 영업활동현금흐름 전년 대비 크게 개선 |

---

# Industry Specific Signal Codes

| signal_code | signal | type | severity | metric_key | 설명 |
|---|---|---|---|---|---|
| TECH_LOSS_WIDENING_3Y | 기술 업종 적자 심화 | negative | HIGH | operating_income | 기술 업종에서 3개년 영업손실 확대 |
| TECH_CAPA_EXPANSION_CASH_RISK | 기술 업종 공격적 투자 부담 | negative | HIGH | operating_cash_flow | 현금흐름 음수 상태에서 자산 규모 증가 |
| MANUFACTURING_MARGIN_DROP_INTEREST_RISK | 제조업 수익성 급락 및 이자부담 | negative | HIGH | operating_margin | 영업이익률 급락 + 이자보상배율 1 미만 |
| MANUFACTURING_INVENTORY_LIQUIDITY_RISK | 제조업 재고 부담 및 유동성 위험 | negative | HIGH | inventory_turnover | 재고 회전 악화 + 현금성자산 부족 |
| DISTRIBUTION_LOW_MARGIN_REVENUE_DROP | 유통 서비스 저마진 및 매출 감소 | negative | MEDIUM | operating_margin | 저마진 + 매출 감소 |
| DISTRIBUTION_COLLECTION_LIQUIDITY_RISK | 유통 서비스 현금 회수 지연 | negative | HIGH | receivables_turnover | 매출채권 회전 악화 + 현금성자산 부족 |
| CONSTRUCTION_CASH_FLOW_SHORT_BORROWING_RISK | 수주형 업종 현금흐름 및 단기차입 위험 | negative | HIGH | operating_cash_flow | 영업현금흐름 음수 + 단기차입금 증가 |
| CONSTRUCTION_CASH_FLOW_RISK | 수주형 업종 현금흐름 악화 | negative | HIGH | operating_cash_flow | 순이익 흑자이나 영업현금흐름 음수 |
| FACILITY_SERVICE_INTEREST_BURDEN | 장치형 서비스 금융비용 부담 | negative | HIGH | interest_expense | 매출 대비 이자비용 부담 + 영업손실 |

---

# Excluded Signal

| signal_code | signal | type | severity | 설명 |
|---|---|---|---|---|
| INDUSTRY_EXCLUDED | 분석 제외 업종 | excluded | INFO | 금융업 등 일반 재무 Trigger 분석 제외 업종 |

---

# 사용 기준

## 프론트엔드

프론트에서는 `signal`을 사용자 표시용 문구로 사용하고,  
`signal_code`는 아이콘, 색상, 필터링, 정렬 기준으로 사용할 수 있습니다.

예시:

```json
{
  "signal": "어닝 서프라이즈",
  "signal_code": "EARNINGS_SURPRISE",
  "type": "positive",
  "severity": "HIGH"
}
```

---

## AI / RAG

AI 파트에서는 `signal_code`를 기준으로 검색 query 또는 프롬프트 분기를 처리하는 것을 권장합니다.

이유:
- `signal` 문구는 변경될 수 있음
- `signal_code`는 고정 식별자 역할
- detected_changes와 Vector DB metadata 연결에 사용 가능

---

# 주의 사항

- 현재 Signal은 정량 재무 데이터 기반으로 생성됩니다.
- 뉴스 / 공시 텍스트는 현재 Trigger 판단보다는 원인 분석 및 근거 Retrieval에 사용됩니다.
- 일부 종목은 company_info 매핑 누락 시 `industry_group=unknown`으로 처리될 수 있습니다.