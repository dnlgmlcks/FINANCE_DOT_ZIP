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


def safe_number(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def get_recent_items(finance_summary, current_index, count):
    start = max(0, current_index - count + 1)
    return finance_summary[start: current_index + 1]


def all_values_present(items, key):
    return all(item.get(key) is not None for item in items)


def is_operating_loss_3y(items):
    if len(items) < 3 or not all_values_present(items, "operating_income"):
        return False

    return all(safe_number(item.get("operating_income")) < 0 for item in items)


def is_interest_coverage_low_3y(items, threshold=1):
    if len(items) < 3 or not all_values_present(items, "interest_coverage_ratio"):
        return False

    return all(
        safe_number(item.get("interest_coverage_ratio")) < threshold
        for item in items
    )


def is_cash_flow_negative_3y(items):
    if len(items) < 3 or not all_values_present(items, "operating_cash_flow"):
        return False

    return all(
        safe_number(item.get("operating_cash_flow")) < 0
        for item in items
    )


def is_operating_loss_widening_3y(items):
    if len(items) < 3 or not all_values_present(items, "operating_income"):
        return False

    values = [safe_number(item.get("operating_income")) for item in items]

    return (
        values[0] < 0
        and values[1] < 0
        and values[2] < 0
        and abs(values[0]) < abs(values[1]) < abs(values[2])
    )


def add_common_negative_signals(signals, item, recent_3_items, rules):
    year = item.get("year")
    negative_rules = rules["negative"]

    revenue_yoy = safe_number(item.get("revenue_yoy"))
    if (
        revenue_yoy is not None
        and revenue_yoy <= negative_rules["revenue_drop_50"]["threshold"]
    ):
        rule = negative_rules["revenue_drop_50"]
        signals.append(make_signal(
            year,
            "negative",
            rule["severity"],
            rule["signal"],
            rule["description_template"].format(value=revenue_yoy),
            signal_code="REVENUE_DROP_50",
            metric_key="revenue",
        ))

    if is_operating_loss_3y(recent_3_items):
        rule = negative_rules["operating_loss_3y"]
        signals.append(make_signal(
            year,
            "negative",
            rule["severity"],
            rule["signal"],
            rule["description"],
            signal_code="OPERATING_LOSS_3Y",
            metric_key="operating_income",
        ))

    if is_interest_coverage_low_3y(
        recent_3_items,
        negative_rules["interest_coverage_3y_low"]["threshold"],
    ):
        rule = negative_rules["interest_coverage_3y_low"]
        signals.append(make_signal(
            year,
            "negative",
            rule["severity"],
            rule["signal"],
            rule["description"],
            signal_code="INTEREST_COVERAGE_3Y_LOW",
            metric_key="interest_coverage_ratio",
        ))

    if is_cash_flow_negative_3y(recent_3_items):
        rule = negative_rules["cash_flow_negative_3y"]
        signals.append(make_signal(
            year,
            "negative",
            rule["severity"],
            rule["signal"],
            rule["description"],
            signal_code="CASH_FLOW_NEGATIVE_3Y",
            metric_key="operating_cash_flow",
        ))

    cash = safe_number(item.get("cash"))
    short_term_borrowings = safe_number(item.get("short_term_borrowings"))
    if (
        cash is not None
        and short_term_borrowings is not None
        and short_term_borrowings > 0
        and cash < short_term_borrowings
    ):
        rule = negative_rules["cash_less_than_short_borrowings"]
        signals.append(make_signal(
            year,
            "negative",
            rule["severity"],
            rule["signal"],
            rule["description"],
            signal_code="CASH_LESS_THAN_SHORT_BORROWINGS",
            metric_key="cash",
        ))

    debt_ratio = safe_number(item.get("debt_ratio"))
    if (
        debt_ratio is not None
        and debt_ratio > negative_rules["debt_ratio_over_400"]["threshold"]
    ):
        rule = negative_rules["debt_ratio_over_400"]
        signals.append(make_signal(
            year,
            "negative",
            rule["severity"],
            rule["signal"],
            rule["description"],
            signal_code="DEBT_RATIO_OVER_400",
            metric_key="debt_ratio",
        ))

    total_equity = safe_number(item.get("total_equity"))
    capital_stock = safe_number(
        item.get("capital_stock")
        or item.get("capital")
        or item.get("common_stock")
    )

    if total_equity is not None and total_equity < 0:
        rule = negative_rules["full_capital_impairment"]
        signals.append(make_signal(
            year,
            "negative",
            rule["severity"],
            rule["signal"],
            rule["description"],
            signal_code="CAPITAL_IMPAIRMENT_FULL",
            metric_key="total_equity",
        ))

    elif (
        total_equity is not None
        and capital_stock is not None
        and total_equity < capital_stock
    ):
        rule = negative_rules["partial_capital_impairment"]
        signals.append(make_signal(
            year,
            "negative",
            rule["severity"],
            rule["signal"],
            rule["description"],
            signal_code="CAPITAL_IMPAIRMENT_PARTIAL",
            metric_key="total_equity",
        ))


def add_common_positive_signals(signals, item, previous_item, recent_3_items, rules):
    year = item.get("year")
    positive_rules = rules["positive"]

    revenue_yoy = safe_number(item.get("revenue_yoy"))
    if (
        revenue_yoy is not None
        and revenue_yoy >= positive_rules["revenue_jump"]["threshold"]
    ):
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

    operating_income_yoy = safe_number(item.get("operating_income_yoy"))
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

    if previous_item:
        previous_operating_income = safe_number(previous_item.get("operating_income"))
        current_operating_income = safe_number(item.get("operating_income"))

        if (
            previous_operating_income is not None
            and current_operating_income is not None
            and previous_operating_income < 0
            and current_operating_income > 0
        ):
            rule = positive_rules["turnaround"]
            signals.append(make_signal(
                year,
                "positive",
                rule["severity"],
                rule["signal"],
                rule["description"],
                signal_code="OPERATING_INCOME_TURN_TO_PROFIT",
                metric_key="operating_income",
            ))

    receivables_turnover_yoy = safe_number(item.get("receivables_turnover_yoy"))
    inventory_turnover_yoy = safe_number(item.get("inventory_turnover_yoy"))

    if (
        receivables_turnover_yoy is not None
        and receivables_turnover_yoy >= positive_rules["asset_efficiency_up"]["threshold"]
    ) or (
        inventory_turnover_yoy is not None
        and inventory_turnover_yoy >= positive_rules["asset_efficiency_up"]["threshold"]
    ):
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
        previous_assets = safe_number(previous_item.get("total_assets"))
        current_assets = safe_number(item.get("total_assets"))

        if (
            previous_assets is not None
            and current_assets is not None
            and previous_assets > 0
        ):
            asset_growth = ((current_assets - previous_assets) / previous_assets) * 100

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

    debt_ratio_change = safe_number(item.get("debt_ratio_change"))
    if (
        debt_ratio_change is not None
        and debt_ratio_change <= positive_rules["debt_ratio_down"]["threshold"]
    ):
        rule = positive_rules["debt_ratio_down"]
        signals.append(make_signal(
            year,
            "positive",
            rule["severity"],
            rule["signal"],
            rule["description_template"].format(value=debt_ratio_change),
            signal_code="DEBT_RATIO_DOWN",
            metric_key="debt_ratio",
        ))

    operating_cash_flow = safe_number(item.get("operating_cash_flow"))
    previous_operating_cash_flow = None

    if previous_item:
        previous_operating_cash_flow = safe_number(previous_item.get("operating_cash_flow"))

    if (
        operating_cash_flow is not None
        and previous_operating_cash_flow is not None
        and previous_operating_cash_flow > 0
    ):
        cash_flow_yoy = (
            (operating_cash_flow - previous_operating_cash_flow)
            / previous_operating_cash_flow
        ) * 100

        if cash_flow_yoy >= positive_rules["cash_flow_strong"]["threshold"]:
            rule = positive_rules["cash_flow_strong"]
            signals.append(make_signal(
                year,
                "positive",
                rule["severity"],
                rule["signal"],
                rule["description_template"],
                signal_code="CASH_FLOW_STRONG",
                metric_key="operating_cash_flow",
            ))


def add_industry_specific_signals(signals, item, previous_item, recent_3_items, industry_group):
    year = item.get("year")

    if industry_group == "tech_equipment":
        if is_operating_loss_widening_3y(recent_3_items):
            signals.append(make_signal(
                year,
                "negative",
                "HIGH",
                "기술 업종 적자 심화",
                "최근 3개년 영업손실 규모가 지속적으로 확대되고 있습니다.",
                signal_code="TECH_LOSS_WIDENING_3Y",
                metric_key="operating_income",
            ))

        operating_cash_flow = safe_number(item.get("operating_cash_flow"))
        total_assets = safe_number(item.get("total_assets"))
        previous_assets = safe_number(previous_item.get("total_assets")) if previous_item else None

        if (
            operating_cash_flow is not None
            and operating_cash_flow < 0
            and total_assets is not None
            and previous_assets is not None
            and previous_assets > 0
        ):
            asset_growth = ((total_assets - previous_assets) / previous_assets) * 100

            if asset_growth >= 30:
                signals.append(make_signal(
                    year,
                    "negative",
                    "HIGH",
                    "기술 업종 공격적 투자 부담",
                    "영업현금흐름이 음수인 상황에서 자산 규모가 크게 증가했습니다.",
                    signal_code="TECH_CAPA_EXPANSION_CASH_RISK",
                    metric_key="operating_cash_flow",
                ))

    if industry_group == "heavy_manufacturing":
        operating_margin = safe_number(item.get("operating_margin"))
        previous_operating_margin = safe_number(previous_item.get("operating_margin")) if previous_item else None
        interest_coverage_ratio = safe_number(item.get("interest_coverage_ratio"))

        if (
            operating_margin is not None
            and previous_operating_margin is not None
            and previous_operating_margin > 0
            and interest_coverage_ratio is not None
        ):
            margin_drop_rate = (
                (operating_margin - previous_operating_margin)
                / previous_operating_margin
            ) * 100

            if margin_drop_rate <= -50 and interest_coverage_ratio < 1:
                signals.append(make_signal(
                    year,
                    "negative",
                    "HIGH",
                    "제조업 수익성 급락 및 이자부담",
                    "영업이익률이 전년 대비 50% 이상 급락하고 이자보상배율이 1 미만입니다.",
                    signal_code="MANUFACTURING_MARGIN_DROP_INTEREST_RISK",
                    metric_key="operating_margin",
                ))

        cash = safe_number(item.get("cash"))
        short_term_borrowings = safe_number(item.get("short_term_borrowings"))
        inventory_yoy = safe_number(item.get("inventory_turnover_yoy"))

        if (
            cash is not None
            and short_term_borrowings is not None
            and inventory_yoy is not None
            and cash < short_term_borrowings
            and inventory_yoy <= -30
        ):
            signals.append(make_signal(
                year,
                "negative",
                "HIGH",
                "제조업 재고 부담 및 유동성 위험",
                "현금성자산이 단기차입금보다 적고 재고 회전 효율이 크게 악화되었습니다.",
                signal_code="MANUFACTURING_INVENTORY_LIQUIDITY_RISK",
                metric_key="inventory_turnover",
            ))

    if industry_group == "distribution_service":
        operating_margin = safe_number(item.get("operating_margin"))
        revenue_yoy = safe_number(item.get("revenue_yoy"))

        if (
            operating_margin is not None
            and revenue_yoy is not None
            and operating_margin < 2
            and revenue_yoy < 0
        ):
            signals.append(make_signal(
                year,
                "negative",
                "MEDIUM",
                "유통 서비스 저마진 및 매출 감소",
                "영업이익률이 2% 미만이고 매출액이 전년 대비 감소했습니다.",
                signal_code="DISTRIBUTION_LOW_MARGIN_REVENUE_DROP",
                metric_key="operating_margin",
            ))

        receivables_turnover_yoy = safe_number(item.get("receivables_turnover_yoy"))
        cash = safe_number(item.get("cash"))
        short_term_borrowings = safe_number(item.get("short_term_borrowings"))

        if (
            receivables_turnover_yoy is not None
            and cash is not None
            and short_term_borrowings is not None
            and receivables_turnover_yoy <= -20
            and cash < short_term_borrowings
        ):
            signals.append(make_signal(
                year,
                "negative",
                "HIGH",
                "유통 서비스 현금 회수 지연",
                "매출채권 회전 효율이 악화되고 현금성자산이 단기차입금보다 적습니다.",
                signal_code="DISTRIBUTION_COLLECTION_LIQUIDITY_RISK",
                metric_key="receivables_turnover",
            ))

    if industry_group == "construction_order":
        operating_cash_flow = safe_number(item.get("operating_cash_flow"))
        short_term_borrowings_change = safe_number(item.get("short_term_borrowings_change"))

        if (
            operating_cash_flow is not None
            and operating_cash_flow < 0
            and short_term_borrowings_change is not None
            and short_term_borrowings_change >= 50
        ):
            signals.append(make_signal(
                year,
                "negative",
                "HIGH",
                "수주형 업종 현금흐름 및 단기차입 위험",
                "영업활동현금흐름이 음수이고 단기차입금이 전년 대비 크게 증가했습니다.",
                signal_code="CONSTRUCTION_CASH_FLOW_SHORT_BORROWING_RISK",
                metric_key="operating_cash_flow",
            ))

        operating_cash_flow = safe_number(item.get("operating_cash_flow"))
        net_income = safe_number(item.get("net_income"))

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
                "순이익은 흑자이나 영업활동현금흐름이 음수입니다.",
                signal_code="CONSTRUCTION_CASH_FLOW_RISK",
                metric_key="operating_cash_flow",
            ))

    if industry_group == "facility_service":
        interest_expense = safe_number(item.get("interest_expense"))
        revenue = safe_number(item.get("revenue"))
        operating_income = safe_number(item.get("operating_income"))

        if (
            interest_expense is not None
            and revenue is not None
            and revenue > 0
            and operating_income is not None
        ):
            interest_to_revenue = (interest_expense / revenue) * 100

            if interest_to_revenue > 10 and operating_income < 0:
                signals.append(make_signal(
                    year,
                    "negative",
                    "HIGH",
                    "장치형 서비스 금융비용 부담",
                    "매출액 대비 이자비용 비중이 높고 영업손실이 발생했습니다.",
                    signal_code="FACILITY_SERVICE_INTEREST_BURDEN",
                    metric_key="interest_expense",
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

    if not finance_summary:
        return signals

    finance_summary = sorted(
        finance_summary,
        key=lambda item: item.get("year") or 0
    )

    common_rules = get_common_trigger_rules()

    industry_group = "unknown"
    if industry_info:
        industry_group = industry_info.get("industry_group") or "unknown"

    get_industry_trigger_rules(industry_group)

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
                ),
            }
        ]

    previous_item = None

    for index, item in enumerate(finance_summary):
        recent_3_items = get_recent_items(finance_summary, index, 3)

        add_common_negative_signals(
            signals,
            item,
            recent_3_items,
            common_rules,
        )

        add_common_positive_signals(
            signals,
            item,
            previous_item,
            recent_3_items,
            common_rules,
        )

        add_industry_specific_signals(
            signals,
            item,
            previous_item,
            recent_3_items,
            industry_group,
        )

        previous_item = item

    return remove_duplicate_signals(signals)


def generate_warning_signals(finance_summary):
    return generate_signals(finance_summary)