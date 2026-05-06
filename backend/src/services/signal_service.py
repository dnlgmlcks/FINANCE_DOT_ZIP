def generate_warning_signals(finance_summary):
    signals = []

    previous_item = None

    for item in finance_summary:
        year = item["year"]

        if item.get("debt_ratio") is not None and item["debt_ratio"] > 200:
            signals.append({
                "year": year,
                "type": "negative",
                "severity": "HIGH",
                "signal": "부채비율 200% 초과",
                "description": "부채비율이 200%를 초과하여 재무 안정성 위험이 있습니다."
            })

        if item.get("operating_margin") is not None and item["operating_margin"] < 0:
            signals.append({
                "year": year,
                "type": "negative",
                "severity": "HIGH",
                "signal": "영업이익률 적자",
                "description": "영업이익률이 음수로 전환되어 영업 손실 가능성이 있습니다."
            })

        if item.get("net_income") is not None and item["net_income"] < 0:
            signals.append({
                "year": year,
                "type": "negative",
                "severity": "HIGH",
                "signal": "당기순이익 적자",
                "description": "당기순이익이 음수로 적자 상태입니다."
            })

        if item.get("current_ratio") is not None and item["current_ratio"] < 100:
            signals.append({
                "year": year,
                "type": "negative",
                "severity": "MEDIUM",
                "signal": "유동비율 100% 미만",
                "description": "유동비율이 100% 미만으로 단기 상환 능력에 주의가 필요합니다."
            })

        if item.get("interest_coverage_ratio") is not None and item["interest_coverage_ratio"] < 1:
            signals.append({
                "year": year,
                "type": "negative",
                "severity": "HIGH",
                "signal": "이자보상배율 1 미만",
                "description": "영업이익으로 이자비용을 감당하기 어려운 상태입니다."
            })

        revenue_yoy = item.get("revenue_yoy")
        if revenue_yoy is not None and revenue_yoy <= -20:
            signals.append({
                "year": year,
                "type": "negative",
                "severity": "MEDIUM",
                "signal": "매출액 20% 이상 감소",
                "description": f"전년 대비 매출액이 {revenue_yoy}% 감소했습니다."
            })

        operating_income_yoy = item.get("operating_income_yoy")

        if operating_income_yoy is not None and operating_income_yoy <= -50:
            severity = "HIGH"
        elif operating_income_yoy is not None and operating_income_yoy <= -20:
            severity = "MEDIUM"
        else:
            severity = None

        if severity:
            signals.append({
                "year": year,
                "type": "negative",
                "severity": severity,
                "signal": "영업이익 급감",
                "description": f"전년 대비 영업이익이 {operating_income_yoy}% 감소했습니다."
            })

        debt_ratio_change = item.get("debt_ratio_change")
        if debt_ratio_change is not None and debt_ratio_change >= 30:
            signals.append({
                "year": year,
                "type": "negative",
                "severity": "MEDIUM",
                "signal": "부채비율 급증",
                "description": f"전년 대비 부채비율이 {debt_ratio_change}%p 증가했습니다."
            })

        receivables_turnover_yoy = item.get("receivables_turnover_yoy")
        if receivables_turnover_yoy is not None and receivables_turnover_yoy <= -30:
            signals.append({
                "year": year,
                "type": "negative",
                "severity": "MEDIUM",
                "signal": "매출채권 회수 지연",
                "description": f"매출채권회전율이 전년 대비 {receivables_turnover_yoy}% 하락했습니다."
            })

        inventory_turnover_yoy = item.get("inventory_turnover_yoy")
        if inventory_turnover_yoy is not None and inventory_turnover_yoy <= -30:
            signals.append({
                "year": year,
                "type": "negative",
                "severity": "MEDIUM",
                "signal": "재고자산 회전율 하락",
                "description": f"재고자산회전율이 전년 대비 {inventory_turnover_yoy}% 하락했습니다."
            })

        borrowings_dependency_change = item.get("borrowings_dependency_change")
        if borrowings_dependency_change is not None and borrowings_dependency_change <= -10:
            signals.append({
                "year": year,
                "type": "positive",
                "severity": "LOW",
                "signal": "차입금의존도 감소",
                "description": f"차입금의존도가 전년 대비 {borrowings_dependency_change}%p 감소했습니다."
            })

        if item.get("revenue_yoy") is not None and item["revenue_yoy"] >= 30:
            signals.append({
                "year": year,
                "type": "positive",
                "severity": "MEDIUM",
                "signal": "매출 퀀텀 점프",
                "description": f"전년 대비 매출액이 {item['revenue_yoy']}% 증가했습니다."
            })

        if previous_item:
            previous_operating_income = previous_item.get("operating_income")
            current_operating_income = item.get("operating_income")

            if (
                previous_operating_income is not None
                and current_operating_income is not None
                and previous_operating_income > 0
                and current_operating_income < 0
            ):
                signals.append({
                    "year": year,
                    "type": "negative",
                    "severity": "HIGH",
                    "signal": "영업이익 적자 전환",
                    "description": "전년도 흑자였던 영업이익이 당해 연도 적자로 전환되었습니다."
                })

            if (
                previous_operating_income is not None
                and current_operating_income is not None
                and previous_operating_income < 0
                and current_operating_income > 0
            ):
                signals.append({
                    "year": year,
                    "type": "positive",
                    "severity": "HIGH",
                    "signal": "영업이익 흑자 전환",
                    "description": "전년도 적자였던 영업이익이 당해 연도 흑자로 전환되었습니다."
                })

        previous_item = item

    return signals