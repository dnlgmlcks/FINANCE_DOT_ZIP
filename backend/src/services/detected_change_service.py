"""
AI 연동용 detected_changes 생성 모듈

역할:
- signal_service.py에서 생성된 signals를
  AI 파트가 사용하기 쉬운 detected_changes 구조로 변환
- Tavily 검색 키워드 생성에 바로 사용할 수 있도록
  metric_key, signal_code, search_keywords, query_hint 포함
"""


SIGNAL_TO_CHANGE_RULES = {
    # Negative signals
    "매출 급감": {
        "metric_key": "revenue",
        "metric_label": "매출액",
        "change_type": "sharp_decrease",
        "direction": "decrease",
        "search_keywords": ["매출 감소", "수요 둔화", "실적 부진"],
    },
    "매출액 급감": {
        "metric_key": "revenue",
        "metric_label": "매출액",
        "change_type": "sharp_decrease",
        "direction": "decrease",
        "search_keywords": ["매출 감소", "수요 둔화", "실적 부진"],
    },
    "영업이익 급감": {
        "metric_key": "operating_income",
        "metric_label": "영업이익",
        "change_type": "sharp_decrease",
        "direction": "decrease",
        "search_keywords": ["영업이익 감소", "수익성 악화", "비용 증가", "실적 악화"],
    },
    "영업이익 감소": {
        "metric_key": "operating_income",
        "metric_label": "영업이익",
        "change_type": "decrease",
        "direction": "decrease",
        "search_keywords": ["영업이익 감소", "수익성 악화", "실적 둔화"],
    },
    "영업적자 발생": {
        "metric_key": "operating_income",
        "metric_label": "영업이익",
        "change_type": "turn_to_loss",
        "direction": "decrease",
        "search_keywords": ["영업적자", "적자 전환", "수익성 악화", "실적 악화"],
    },
    "영업이익 적자 전환": {
        "metric_key": "operating_income",
        "metric_label": "영업이익",
        "change_type": "turn_to_loss",
        "direction": "decrease",
        "search_keywords": ["영업이익 적자 전환", "영업손실", "수익성 악화"],
    },
    "순손실 발생": {
        "metric_key": "net_income",
        "metric_label": "당기순이익",
        "change_type": "turn_to_loss",
        "direction": "decrease",
        "search_keywords": ["당기순손실", "순손실", "적자 전환", "손실 발생"],
    },
    "당기순이익 적자": {
        "metric_key": "net_income",
        "metric_label": "당기순이익",
        "change_type": "turn_to_loss",
        "direction": "decrease",
        "search_keywords": ["당기순손실", "순이익 감소", "적자 전환"],
    },
    "부채비율 과다": {
        "metric_key": "debt_ratio",
        "metric_label": "부채비율",
        "change_type": "high_level",
        "direction": "increase",
        "search_keywords": ["부채비율 상승", "차입금 증가", "재무 부담", "유동성 우려"],
    },
    "부채비율 200% 초과": {
        "metric_key": "debt_ratio",
        "metric_label": "부채비율",
        "change_type": "high_level",
        "direction": "increase",
        "search_keywords": ["부채비율 상승", "차입금 증가", "재무 부담", "유동성 우려"],
    },
    "부채비율 급증": {
        "metric_key": "debt_ratio",
        "metric_label": "부채비율",
        "change_type": "increase",
        "direction": "increase",
        "search_keywords": ["부채비율 상승", "재무구조 악화", "차입 부담"],
    },
    "유동성 위험": {
        "metric_key": "current_ratio",
        "metric_label": "유동비율",
        "change_type": "low_level",
        "direction": "decrease",
        "search_keywords": ["유동비율 하락", "유동성 악화", "단기 지급능력"],
    },
    "유동비율 100% 미만": {
        "metric_key": "current_ratio",
        "metric_label": "유동비율",
        "change_type": "low_level",
        "direction": "decrease",
        "search_keywords": ["유동비율 하락", "유동성 악화", "단기 지급능력"],
    },
    "이자상환 위험": {
        "metric_key": "interest_coverage_ratio",
        "metric_label": "이자보상배율",
        "change_type": "low_level",
        "direction": "decrease",
        "search_keywords": ["이자보상배율 하락", "금융비용 부담", "이자비용 증가"],
    },
    "이자보상배율 1 미만": {
        "metric_key": "interest_coverage_ratio",
        "metric_label": "이자보상배율",
        "change_type": "low_level",
        "direction": "decrease",
        "search_keywords": ["이자보상배율 하락", "금융비용 부담", "이자비용 증가"],
    },
    "매출채권 회전율 악화": {
        "metric_key": "receivables_turnover",
        "metric_label": "매출채권회전율",
        "change_type": "decrease",
        "direction": "decrease",
        "search_keywords": ["매출채권 회수 지연", "대손충당금", "채권 회수"],
    },
    "매출채권 회수 지연": {
        "metric_key": "receivables_turnover",
        "metric_label": "매출채권회전율",
        "change_type": "decrease",
        "direction": "decrease",
        "search_keywords": ["매출채권 회수 지연", "대손충당금", "채권 회수"],
    },
    "재고자산 회전율 악화": {
        "metric_key": "inventory_turnover",
        "metric_label": "재고자산회전율",
        "change_type": "decrease",
        "direction": "decrease",
        "search_keywords": ["재고 증가", "재고 부담", "재고자산 평가손실"],
    },
    "재고자산 회전율 하락": {
        "metric_key": "inventory_turnover",
        "metric_label": "재고자산회전율",
        "change_type": "decrease",
        "direction": "decrease",
        "search_keywords": ["재고 증가", "재고 부담", "재고자산 평가손실"],
    },
    "기술 업종 수익성 급락": {
        "metric_key": "operating_income",
        "metric_label": "영업이익",
        "change_type": "industry_profitability_drop",
        "direction": "decrease",
        "search_keywords": ["반도체 업황", "IT 수요 둔화", "수익성 악화", "영업이익 감소"],
    },

    # Positive signals
    "매출 퀀텀 점프": {
        "metric_key": "revenue",
        "metric_label": "매출액",
        "change_type": "sharp_increase",
        "direction": "increase",
        "search_keywords": ["매출 성장", "수요 증가", "신사업 성장", "실적 개선"],
    },
    "어닝 서프라이즈": {
        "metric_key": "operating_income",
        "metric_label": "영업이익",
        "change_type": "sharp_increase",
        "direction": "increase",
        "search_keywords": ["어닝 서프라이즈", "영업이익 증가", "실적 개선"],
    },
    "순이익 고성장": {
        "metric_key": "net_income",
        "metric_label": "당기순이익",
        "change_type": "sharp_increase",
        "direction": "increase",
        "search_keywords": ["순이익 증가", "실적 개선", "수익성 개선"],
    },
    "자기자본비율 개선": {
        "metric_key": "equity_ratio",
        "metric_label": "자기자본비율",
        "change_type": "improve",
        "direction": "increase",
        "search_keywords": ["재무구조 개선", "자기자본비율 상승", "부채 감소"],
    },
    "재무구조 개선": {
        "metric_key": "borrowings_dependency",
        "metric_label": "차입금의존도",
        "change_type": "improve",
        "direction": "decrease",
        "search_keywords": ["차입금 감소", "재무구조 개선", "부채 부담 완화"],
    },
    "차입금의존도 감소": {
        "metric_key": "borrowings_dependency",
        "metric_label": "차입금의존도",
        "change_type": "improve",
        "direction": "decrease",
        "search_keywords": ["차입금 감소", "재무구조 개선", "부채 부담 완화"],
    },
    "현금 창출력 강화": {
        "metric_key": "operating_cash_flow",
        "metric_label": "영업활동현금흐름",
        "change_type": "improve",
        "direction": "increase",
        "search_keywords": ["영업현금흐름 개선", "현금 창출력", "현금흐름 개선"],
    },
    "Capa 확대": {
        "metric_key": "total_assets",
        "metric_label": "자산 규모",
        "change_type": "capacity_expansion",
        "direction": "increase",
        "search_keywords": ["설비 투자", "CAPEX", "생산능력 확대", "투자 확대"],
    },
    "자산 가동률 상승": {
        "metric_key": "asset_turnover",
        "metric_label": "자산회전율",
        "change_type": "improve",
        "direction": "increase",
        "search_keywords": ["자산 효율성 개선", "자산회전율 상승", "운영 효율화"],
    },
}


SEVERITY_MAP = {
    "HIGH": "high",
    "MEDIUM": "medium",
    "LOW": "low",
    "INFO": "info",
}


def get_year_item_map(finance_summary):
    return {
        item.get("year"): item
        for item in finance_summary
        if item.get("year") is not None
    }


def get_base_year(year, finance_summary):
    if year is None:
        return None

    years = sorted([
        item.get("year")
        for item in finance_summary
        if item.get("year") is not None
    ])

    previous_years = [
        target_year
        for target_year in years
        if target_year < year
    ]

    if previous_years:
        return previous_years[-1]

    return None


def get_metric_value(item, metric_key):
    if not item:
        return None

    if metric_key == "asset_turnover":
        revenue = item.get("revenue")
        total_assets = item.get("total_assets")

        if revenue is None or total_assets in (None, 0):
            return None

        return round(revenue / total_assets, 4)

    return item.get(metric_key)


def get_metric_yoy(item, metric_key):
    if not item:
        return None

    yoy_key_map = {
        "revenue": "revenue_yoy",
        "operating_income": "operating_income_yoy",
        "net_income": "net_income_yoy",
        "debt_ratio": "debt_ratio_change",
        "equity_ratio": "equity_ratio_change",
        "receivables_turnover": "receivables_turnover_yoy",
        "inventory_turnover": "inventory_turnover_yoy",
        "borrowings_dependency": "borrowings_dependency_change",
        "net_margin": "net_margin_change",
    }

    yoy_key = yoy_key_map.get(metric_key)

    if not yoy_key:
        return None

    return item.get(yoy_key)


def build_detected_change(
    signal,
    finance_summary,
    company_name="",
    stock_code="",
    industry_group="unknown",
):
    rule = SIGNAL_TO_CHANGE_RULES.get(signal.get("signal"))

    if not rule:
        return None

    year = signal.get("year")
    base_year = get_base_year(year, finance_summary)

    year_item_map = get_year_item_map(finance_summary)
    current_item = year_item_map.get(year)

    metric_key = signal.get("metric_key") or rule["metric_key"]
    current_value = get_metric_value(current_item, metric_key)
    yoy_change_rate = get_metric_yoy(current_item, metric_key)

    source_signal = signal.get("signal", "")
    signal_type = signal.get("type", "unknown")
    signal_code = signal.get("signal_code")

    query_hint = f"{company_name} {source_signal} 원인".strip()

    return {
        "metric_key": metric_key,
        "metric_label": rule["metric_label"],
        "year": year,
        "base_year": base_year,

        "change_type": rule["change_type"],
        "direction": rule["direction"],

        "severity": SEVERITY_MAP.get(
            signal.get("severity"),
            "medium"
        ),

        "signal_type": signal_type,
        "signal_code": signal_code,

        "company_name": company_name,
        "stock_code": stock_code,
        "industry_group": industry_group,

        "current_value": current_value,
        "yoy_change_rate": yoy_change_rate,

        "description": signal.get("description", ""),
        "source_signal": source_signal,

        "query_hint": query_hint,
        "search_keywords": rule["search_keywords"],
    }


def build_detected_changes(
    finance_summary,
    signals,
    company_name="",
    stock_code="",
    industry_group="unknown",
):
    detected_changes = []

    if not signals:
        return detected_changes

    for signal in signals:
        change = build_detected_change(
            signal,
            finance_summary,
            company_name=company_name,
            stock_code=stock_code,
            industry_group=industry_group,
        )

        if change:
            detected_changes.append(change)

    return detected_changes