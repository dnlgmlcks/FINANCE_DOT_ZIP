"""
AI 파트 연동용 검색 query 생성 유틸

주의:
- 실제 Tavily Search / Vector DB Search 실행은 AI/Agent 파트에서 담당
- 본 모듈은 detected_changes를 기반으로 검색용 query 문자열만 생성
- LangChain Chain, Prompt, LLM 호출은 수행하지 않음
"""


SIGNAL_QUERY_TEMPLATE = {
    "REVENUE_DROP_50": "매출 급감 원인",
    "OPERATING_LOSS_3Y": "영업손실 3개년 지속 원인",
    "INTEREST_COVERAGE_3Y_LOW": "이자보상배율 3개년 연속 1 미만 원인",
    "CASH_FLOW_NEGATIVE_3Y": "영업활동현금흐름 적자 지속 원인",
    "CASH_LESS_THAN_SHORT_BORROWINGS": "현금성자산 단기차입금 미달 원인",
    "DEBT_RATIO_OVER_400": "부채비율 400% 초과 원인",
    "CAPITAL_IMPAIRMENT_PARTIAL": "부분자본잠식 원인",
    "CAPITAL_IMPAIRMENT_FULL": "완전자본잠식 원인",
    "REVENUE_JUMP": "매출 증가 원인",
    "EARNINGS_SURPRISE": "영업이익 증가 원인",
    "OPERATING_INCOME_TURN_TO_PROFIT": "영업이익 흑자 전환 원인",
    "ASSET_EFFICIENCY_UP": "자산 효율성 개선 원인",
    "CAPACITY_EXPANSION": "설비 투자 확대 원인",
    "DEBT_RATIO_DOWN": "부채비율 감소 원인",
    "CASH_FLOW_STRONG": "영업현금흐름 개선 원인",
    "TECH_LOSS_WIDENING_3Y": "기술 업종 적자 심화 원인",
    "TECH_CAPA_EXPANSION_CASH_RISK": "기술 업종 투자 부담 원인",
    "MANUFACTURING_MARGIN_DROP_INTEREST_RISK": "제조업 수익성 급락 및 이자부담 원인",
    "MANUFACTURING_INVENTORY_LIQUIDITY_RISK": "제조업 재고 부담 및 유동성 위험 원인",
    "DISTRIBUTION_LOW_MARGIN_REVENUE_DROP": "유통 서비스 저마진 및 매출 감소 원인",
    "DISTRIBUTION_COLLECTION_LIQUIDITY_RISK": "유통 서비스 현금 회수 지연 원인",
    "CONSTRUCTION_CASH_FLOW_SHORT_BORROWING_RISK": "수주형 업종 현금흐름 및 단기차입 위험 원인",
    "CONSTRUCTION_CASH_FLOW_RISK": "수주형 업종 현금흐름 악화 원인",
    "FACILITY_SERVICE_INTEREST_BURDEN": "장치형 서비스 금융비용 부담 원인",
}


def _safe_str(value):
    if value is None:
        return ""

    return str(value).strip()


def build_query_from_change(detected_change):
    if not detected_change:
        return ""

    query_hint = _safe_str(detected_change.get("query_hint"))
    if query_hint:
        return query_hint

    company_name = _safe_str(detected_change.get("company_name"))
    signal_code = _safe_str(detected_change.get("signal_code"))
    source_signal = _safe_str(detected_change.get("source_signal"))
    metric_label = _safe_str(detected_change.get("metric_label"))

    reason_text = SIGNAL_QUERY_TEMPLATE.get(signal_code)

    if reason_text:
        return f"{company_name} {reason_text}".strip()

    if source_signal:
        return f"{company_name} {source_signal} 원인".strip()

    search_keywords = detected_change.get("search_keywords") or []
    if search_keywords:
        keyword_text = " ".join([
            _safe_str(keyword)
            for keyword in search_keywords
            if _safe_str(keyword)
        ])

        return f"{company_name} {keyword_text}".strip()

    if metric_label:
        return f"{company_name} {metric_label} 변동 원인".strip()

    return f"{company_name} 재무 변동 원인".strip()


def build_queries_from_changes(detected_changes):
    queries = []

    if not detected_changes:
        return queries

    for detected_change in detected_changes:
        query = build_query_from_change(detected_change)

        queries.append({
            "query": query,
            "stock_code": detected_change.get("stock_code"),
            "company_name": detected_change.get("company_name"),
            "year": detected_change.get("year"),
            "signal_type": detected_change.get("signal_type"),
            "signal_code": detected_change.get("signal_code"),
            "industry_group": detected_change.get("industry_group"),
            "source_signal": detected_change.get("source_signal"),
        })

    return queries