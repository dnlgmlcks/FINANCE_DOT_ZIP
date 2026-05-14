# Final Report Format

## Overview

AI 기반 최종 재무 분석 리포트 응답 구조 정의

---

# Report Structure

```json
{
  "executive_summary": "",
  "financial_change_summary": "",
  "news_evidence_summary": "",
  "disclosure_evidence_summary": "",
  "possible_causes": "",
  "interview_point": "",
  "limitations": "",
  "source": "llm",
  "metadata": {
    "news_evidence_count": 0,
    "disclosure_evidence_count": 0,
    "generated_at": "",
    "model": "",
    "industry_group": "",
    "industry_group_name": "",
    "industry_instruction_applied": false
  }
}
```

---

# Field Description

## AI Analysis Fields

| Field | Description |
|---|---|
| executive_summary | 종합 요약 |
| financial_change_summary | 재무 변동 요약 |
| news_evidence_summary | 뉴스 근거 요약 |
| disclosure_evidence_summary | 공시 근거 요약 |
| possible_causes | 변동 원인 분석 |
| interview_point | 인터뷰 포인트 |
| limitations | 한계 및 주의사항 |
| source | 응답 출처 (llm / cache 등) |

## Metadata Fields

| Field | Description |
|---|---|
| news_evidence_count | 활용된 뉴스 근거 수 |
| disclosure_evidence_count | 활용된 공시 근거 수 |
| generated_at | 생성 시각 |
| model | 사용 모델명 |
| industry_group | 산업 그룹 코드 |
| industry_group_name | 산업 그룹명 |
| industry_instruction_applied | 산업별 프롬프트 적용 여부 |

---

# AI Analysis Flow

```text
detected_changes
    ↓
query_hint 생성
    ↓
뉴스/공시 검색
    ↓
관련 evidence filtering
    ↓
AI 요약 생성
```

---

# Example Output

> 삼성전자 (005930) 기준 테스트 결과

```json
{
  "executive_summary": "삼성전자는 2023년 재무 성과에서 매출, 영업이익, 당기순이익이 모두 감소하였으며, 특히 영업이익은 84.86% 감소하여 심각한 실적 악화를 겪고 있습니다. 총자산과 자본총계는 증가하였으나, 유동자산과 유동부채는 감소하였습니다.",
  "financial_change_summary": "2023년 삼성전자의 매출은 258.94조 원으로 전년 대비 14.33% 감소하였고, 영업이익은 6.57조 원으로 84.86% 감소하였습니다. 당기순이익은 15.49조 원으로 72.17% 감소하였습니다.",
  "news_evidence_summary": "여러 뉴스 기사에서 삼성전자의 영업이익 급감 원인으로 반도체 업황 악화와 스마트폰 판매 둔화가 언급되었습니다.",
  "disclosure_evidence_summary": "공시 근거는 없습니다.",
  "possible_causes": "영업이익의 급감은 반도체 업황의 부진, 스마트폰 판매 둔화, 재고 관리 문제 등과 관련이 있을 수 있습니다.",
  "interview_point": "영업이익 급감의 원인으로 반도체 업황 악화와 관련된 사항을 강조할 필요가 있습니다.",
  "limitations": "뉴스 근거가 부족한 부분이 있으며, 공시 근거가 전혀 없는 점은 주의해야 합니다.",
  "source": "llm",
  "metadata": {
    "news_evidence_count": 5,
    "disclosure_evidence_count": 0,
    "generated_at": "2026-05-13T16:59:43",
    "model": "gpt-4o-mini",
    "industry_group": "tech_equipment",
    "industry_group_name": "기술 및 장치 산업",
    "industry_instruction_applied": true
  }
}
```