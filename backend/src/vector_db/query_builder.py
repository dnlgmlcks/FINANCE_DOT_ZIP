"""
AI 파트 연동용 검색 query 생성 유틸

주의:
- 실제 Tavily Search / Vector DB Search 실행은 AI/Agent 파트에서 담당
- 본 모듈은 detected_changes를 기반으로 검색용 query 문자열만 생성
"""


SIGNAL_QUERY_TEMPLATE = {
    "REV_DOWN": "매출 감소 원인",
    "REV_UP": "매출 증가 원인",

    "OPM_DOWN": "영업이익 감소 원인",
    "OPM_UP": "영업이익 증가 원인",

    "DEBT_UP": "부채 증가 원인",
    "DEBT_DOWN": "부채 감소 원인",

    "CASH_DOWN": "현금 감소 원인",
    "CASH_UP": "현금 증가 원인",
}


def build_query_from_change(detected_change):
    company_name = detected_change.get("company_name", "")
    signal_code = detected_change.get("signal_code", "")

    reason_text = SIGNAL_QUERY_TEMPLATE.get(
        signal_code,
        "재무 변동 원인",
    )

    return f"{company_name} {reason_text}"


def build_queries_from_changes(detected_changes):
    queries = []

    for detected_change in detected_changes:
        query = build_query_from_change(detected_change)

        queries.append({
            "query": query,
            "signal_code": detected_change.get("signal_code"),
        })

    return queries