from src.services.trigger_rules import (
    get_common_trigger_rules,
    get_industry_trigger_rules,
)


def make_signal(
    year,
    signal_type,
    severity,
    signal,
    description,
    signal_code=None,
    metric_key=None,
):
    return {
        "year": year,
        "type": signal_type,
        "severity": severity,
        "signal": signal,
        "signal_code": signal_code,
        "metric_key": metric_key,
        "description": description,
    }


def add_common_negative_signals(signals, item, previous_item, rules):
    year = item["year"]
    negative_rules = rules["negative"]

    debt_ratio = item.get("debt_ratio")
    if debt_ratio is not None and debt_ratio > negative_rules["debt_ratio_high"]["threshold"]:
        rule = negative_rules["debt_ratio_high"]
        signals.append(make_signal(
            year,
            "negative",
            rule["severity"],
            rule["signal"],
            rule["description"],
            signal_code="DEBT_RATIO_HIGH",
            metric_key="debt_ratio",
        ))

    operating_margin = item.get("operating_margin")
    if operating_margin is not None and operating_margin < negative_rules["operating_margin_negative"]["threshold"]:
        rule = negative_rules["operating_margin_negative"]
        signals.append(make_signal(
            year,
            "negative",
            rule["severity"],
            rule["signal"],
            rule["description"],
            signal_code="OPERATING_MARGIN_NEGATIVE",
            metric_key="operating_margin",
        ))

    net_income = item.get("net_income")
    if net_income is not None and net_income < negative_rules["net_income_negative"]["threshold"]:
        rule = negative_rules["net_income_negative"]
        signals.append(make_signal(
            year,
            "negative",
            rule["severity"],
            rule["signal"],
            rule["description"],
            signal_code="NET_INCOME_NEGATIVE",
            metric_key="net_income",
        ))

    current_ratio = item.get("current_ratio")
    if current_ratio is not None and current_ratio < negative_rules["current_ratio_low"]["threshold"]:
        rule = negative_rules["current_ratio_low"]
        signals.append(make_signal(
            year,
            "negative",
            rule["severity"],
            rule["signal"],
            rule["description"],
            signal_code="CURRENT_RATIO_LOW",
            metric_key="current_ratio",
        ))

    interest_coverage_ratio = item.get("interest_coverage_ratio")
    if (
        interest_coverage_ratio is not None
        and interest_coverage_ratio < negative_rules["interest_coverage_low"]["threshold"]
    ):
        rule = negative_rules["interest_coverage_low"]
        signals.append(make_signal(
            year,
            "negative",
            rule["severity"],
            rule["signal"],
            rule["description"],
            signal_code="INTEREST_COVERAGE_LOW",
            metric_key="interest_coverage_ratio",
        ))

    revenue_yoy = item.get("revenue_yoy")
    if revenue_yoy is not None and revenue_yoy <= negative_rules["revenue_drop"]["threshold"]:
        rule = negative_rules["revenue_drop"]
        signals.append(make_signal(
            year,
            "negative",
            rule["severity"],
            rule["signal"],
            rule["description_template"].format(value=revenue_yoy),
            signal_code="REVENUE_DROP",
            metric_key="revenue",
        ))

    operating_income_yoy = item.get("operating_income_yoy")
    if operating_income_yoy is not None:
        if operating_income_yoy <= negative_rules["operating_income_drop_high"]["threshold"]:
            rule = negative_rules["operating_income_drop_high"]
            signals.append(make_signal(
                year,
                "negative",
                rule["severity"],
                rule["signal"],
                rule["description_template"].format(value=operating_income_yoy),
                signal_code="OPERATING_INCOME_DROP_HIGH",
                metric_key="operating_income",
            ))
        elif operating_income_yoy <= negative_rules["operating_income_drop_medium"]["threshold"]:
            rule = negative_rules["operating_income_drop_medium"]
            signals.append(make_signal(
                year,
                "negative",
                rule["severity"],
                rule["signal"],
                rule["description_template"].format(value=operating_income_yoy),
                signal_code="OPERATING_INCOME_DROP_MEDIUM",
                metric_key="operating_income",
            ))

    debt_ratio_change = item.get("debt_ratio_change")
    if debt_ratio_change is not None and debt_ratio_change >= 30:
        signals.append(make_signal(
            year,
            "negative",
            "MEDIUM",
            "부채비율 급증",
            f"전년 대비 부채비율이 {debt_ratio_change}%p 증가했습니다.",
            signal_code="DEBT_RATIO_INCREASE",
            metric_key="debt_ratio",
        ))

    receivables_turnover_yoy = item.get("receivables_turnover_yoy")
    if (
        receivables_turnover_yoy is not None
        and receivables_turnover_yoy <= negative_rules["receivables_turnover_drop"]["threshold"]
    ):
        rule = negative_rules["receivables_turnover_drop"]
        signals.append(make_signal(
            year,
            "negative",
            rule["severity"],
            rule["signal"],
            rule["description_template"].format(value=receivables_turnover_yoy),
            signal_code="RECEIVABLES_TURNOVER_DROP",
            metric_key="receivables_turnover",
        ))

    inventory_turnover_yoy = item.get("inventory_turnover_yoy")
    if (
        inventory_turnover_yoy is not None
        and inventory_turnover_yoy <= negative_rules["inventory_turnover_drop"]["threshold"]
    ):
        rule = negative_rules["inventory_turnover_drop"]
        signals.append(make_signal(
            year,
            "negative",
            rule["severity"],
            rule["signal"],
            rule["description_template"].format(value=inventory_turnover_yoy),
            signal_code="INVENTORY_TURNOVER_DROP",
            metric_key="inventory_turnover",
        ))

    if previous_item:
        previous_operating_income = previous_item.get("operating_income")
        current_operating_income = item.get("operating_income")

        if (
            previous_operating_income is not None
            and current_operating_income is not None
            and previous_operating_income > 0
            and current_operating_income < 0
        ):
            signals.append(make_signal(
                year,
                "negative",
                "HIGH",
                "영업이익 적자 전환",
                "전년도 흑자였던 영업이익이 당해 연도 적자로 전환되었습니다.",
                signal_code="OPERATING_INCOME_TURN_TO_LOSS",
                metric_key="operating_income",
            ))


def add_common_positive_signals(signals, item, previous_item, rules):
    year = item["year"]
    positive_rules = rules["positive"]

    revenue_yoy = item.get("revenue_yoy")
    if revenue_yoy is not None and revenue_yoy >= positive_rules["revenue_jump"]["threshold"]:
        rule = positive_rules["revenue_jump"]
        signals.append(make_signal(
            year,
            "positive",
            rule["severity"],
            rule["signal"],
            rule["description_template"].format(value=revenue_yoy),
            signal_code="REVENUE_JUMP",
            metric_key="revenue",
        ))

    net_income_yoy = item.get("net_income_yoy")
    if net_income_yoy is not None and net_income_yoy >= positive_rules["net_income_growth"]["threshold"]:
        rule = positive_rules["net_income_growth"]
        signals.append(make_signal(
            year,
            "positive",
            rule["severity"],
            rule["signal"],
            rule["description_template"].format(value=net_income_yoy),
            signal_code="NET_INCOME_GROWTH",
            metric_key="net_income",
        ))

    operating_income_yoy = item.get("operating_income_yoy")
    if (
        operating_income_yoy is not None
        and operating_income_yoy >= positive_rules["earnings_surprise"]["threshold"]
    ):
        rule = positive_rules["earnings_surprise"]
        signals.append(make_signal(
            year,
            "positive",
            rule["severity"],
            rule["signal"],
            rule["description_template"].format(value=operating_income_yoy),
            signal_code="EARNINGS_SURPRISE",
            metric_key="operating_income",
        ))

    total_assets = item.get("total_assets")
    revenue = item.get("revenue")

    if (
        total_assets is not None
        and revenue is not None
        and total_assets > 0
    ):
        asset_turnover = revenue / total_assets

        if asset_turnover >= 0.7:
            rule = positive_rules["asset_efficiency_up"]
            signals.append(make_signal(
                year,
                "positive",
                rule["severity"],
                rule["signal"],
                rule["description_template"],
                signal_code="ASSET_EFFICIENCY_UP",
                metric_key="asset_turnover",
            ))

    if previous_item:
        previous_assets = previous_item.get("total_assets")
        current_assets = item.get("total_assets")

        if (
            previous_assets is not None
            and current_assets is not None
            and previous_assets > 0
        ):
            asset_growth = (
                (current_assets - previous_assets)
                / previous_assets
            ) * 100

            if asset_growth >= positive_rules["capacity_expansion"]["threshold"]:
                rule = positive_rules["capacity_expansion"]
                signals.append(make_signal(
                    year,
                    "positive",
                    rule["severity"],
                    rule["signal"],
                    rule["description_template"],
                    signal_code="CAPACITY_EXPANSION",
                    metric_key="total_assets",
                ))

    equity_ratio_change = item.get("equity_ratio_change")
    if equity_ratio_change is not None and equity_ratio_change >= positive_rules["equity_ratio_improve"]["threshold"]:
        rule = positive_rules["equity_ratio_improve"]
        signals.append(make_signal(
            year,
            "positive",
            rule["severity"],
            rule["signal"],
            rule["description_template"].format(value=equity_ratio_change),
            signal_code="EQUITY_RATIO_IMPROVE",
            metric_key="equity_ratio",
        ))

    borrowings_dependency_change = item.get("borrowings_dependency_change")
    if (
        borrowings_dependency_change is not None
        and borrowings_dependency_change <= positive_rules["borrowings_dependency_down"]["threshold"]
    ):
        rule = positive_rules["borrowings_dependency_down"]
        signals.append(make_signal(
            year,
            "positive",
            rule["severity"],
            rule["signal"],
            rule["description_template"].format(value=borrowings_dependency_change),
            signal_code="BORROWINGS_DEPENDENCY_DOWN",
            metric_key="borrowings_dependency",
        ))

    operating_cash_flow = item.get("operating_cash_flow")
    net_income = item.get("net_income")
    if (
        operating_cash_flow is not None
        and net_income is not None
        and operating_cash_flow > 0
        and operating_cash_flow > net_income
    ):
        rule = positive_rules["cash_flow_strong"]
        signals.append(make_signal(
            year,
            "positive",
            rule["severity"],
            rule["signal"],
            rule["description"],
            signal_code="CASH_FLOW_STRONG",
            metric_key="operating_cash_flow",
        ))

    if previous_item:
        previous_operating_income = previous_item.get("operating_income")
        current_operating_income = item.get("operating_income")

        if (
            previous_operating_income is not None
            and current_operating_income is not None
            and previous_operating_income < 0
            and current_operating_income > 0
        ):
            signals.append(make_signal(
                year,
                "positive",
                "HIGH",
                "영업이익 흑자 전환",
                "전년도 적자였던 영업이익이 당해 연도 흑자로 전환되었습니다.",
                signal_code="OPERATING_INCOME_TURN_TO_PROFIT",
                metric_key="operating_income",
            ))


def add_industry_specific_signals(signals, item, industry_group, industry_rule):
    year = item["year"]

    if industry_group == "tech_equipment":
        operating_income_yoy = item.get("operating_income_yoy")

        if (
            operating_income_yoy is not None
            and operating_income_yoy <= -50
        ):
            signals.append(make_signal(
                year,
                "negative",
                "HIGH",
                "기술 업종 수익성 급락",
                "영업이익이 전년 대비 크게 감소하여 기술 업종 특성상 수익성 변동 위험이 있습니다.",
                signal_code="TECH_PROFITABILITY_DROP",
                metric_key="operating_income",
            ))

    if industry_group == "heavy_manufacturing":
        inventory_turnover_yoy = item.get("inventory_turnover_yoy")
        borrowings_dependency_change = item.get("borrowings_dependency_change")

        if inventory_turnover_yoy is not None and inventory_turnover_yoy <= -20:
            signals.append(make_signal(
                year,
                "negative",
                "MEDIUM",
                "제조업 재고 부담 증가",
                f"재고자산회전율이 전년 대비 {inventory_turnover_yoy}% 하락하여 재고 부담 가능성이 있습니다.",
                signal_code="MANUFACTURING_INVENTORY_BURDEN",
                metric_key="inventory_turnover",
            ))

        if borrowings_dependency_change is not None and borrowings_dependency_change >= 5:
            signals.append(make_signal(
                year,
                "negative",
                "MEDIUM",
                "제조업 차입 부담 증가",
                f"차입금의존도가 전년 대비 {borrowings_dependency_change}%p 증가했습니다.",
                signal_code="MANUFACTURING_BORROWINGS_BURDEN",
                metric_key="borrowings_dependency",
            ))

    if industry_group == "distribution_service":
        receivables_turnover_yoy = item.get("receivables_turnover_yoy")
        inventory_turnover_yoy = item.get("inventory_turnover_yoy")

        if receivables_turnover_yoy is not None and receivables_turnover_yoy <= -20:
            signals.append(make_signal(
                year,
                "negative",
                "MEDIUM",
                "유통/서비스 채권 회수 둔화",
                f"매출채권회전율이 전년 대비 {receivables_turnover_yoy}% 하락했습니다.",
                signal_code="DISTRIBUTION_RECEIVABLES_COLLECTION_SLOWDOWN",
                metric_key="receivables_turnover",
            ))

        if inventory_turnover_yoy is not None and inventory_turnover_yoy <= -20:
            signals.append(make_signal(
                year,
                "negative",
                "MEDIUM",
                "유통 재고 회전 둔화",
                f"재고자산회전율이 전년 대비 {inventory_turnover_yoy}% 하락했습니다.",
                signal_code="DISTRIBUTION_INVENTORY_TURNOVER_DROP",
                metric_key="inventory_turnover",
            ))

    if industry_group == "construction_order":
        operating_cash_flow = item.get("operating_cash_flow")
        net_income = item.get("net_income")

        if (
            operating_cash_flow is not None
            and net_income is not None
            and net_income > 0
            and operating_cash_flow < 0
        ):
            signals.append(make_signal(
                year,
                "negative",
                "HIGH",
                "수주형 업종 현금흐름 악화",
                "순이익은 흑자이나 영업활동현금흐름이 음수로 수주형 업종의 현금 회수 위험이 있습니다.",
                signal_code="CONSTRUCTION_CASH_FLOW_RISK",
                metric_key="operating_cash_flow",
            ))

    if industry_group == "facility_service":
        interest_coverage_ratio = item.get("interest_coverage_ratio")

        if interest_coverage_ratio is not None and interest_coverage_ratio < 2:
            signals.append(make_signal(
                year,
                "negative",
                "MEDIUM",
                "장치형 서비스 이자 부담 주의",
                "이자보상배율이 2 미만으로 장치형 서비스업의 금융비용 부담을 점검해야 합니다.",
                signal_code="FACILITY_SERVICE_INTEREST_BURDEN",
                metric_key="interest_coverage_ratio",
            ))


def remove_duplicate_signals(signals):
    result = []
    seen = set()

    for signal in signals:
        key = (
            signal.get("year"),
            signal.get("type"),
            signal.get("signal_code"),
            signal.get("signal"),
        )

        if key in seen:
            continue

        seen.add(key)
        result.append(signal)

    return result


def generate_signals(finance_summary, industry_info=None):
    signals = []

    common_rules = get_common_trigger_rules()

    industry_group = "unknown"
    if industry_info:
        industry_group = industry_info.get("industry_group") or "unknown"

    industry_rule = get_industry_trigger_rules(industry_group)

    if industry_info and industry_info.get("is_excluded"):
        return [
            {
                "year": None,
                "type": "excluded",
                "severity": "INFO",
                "signal": "분석 제외 업종",
                "signal_code": "INDUSTRY_EXCLUDED",
                "metric_key": None,
                "description": industry_info.get(
                    "reason",
                    "해당 업종은 일반 재무 Trigger 분석 대상에서 제외됩니다."
                )
            }
        ]

    previous_item = None

    for item in finance_summary:
        add_common_negative_signals(signals, item, previous_item, common_rules)
        add_common_positive_signals(signals, item, previous_item, common_rules)
        add_industry_specific_signals(signals, item, industry_group, industry_rule)

        previous_item = item

    return remove_duplicate_signals(signals)


# 기존 코드 호환용
def generate_warning_signals(finance_summary):
    return generate_signals(finance_summary)