def get_common_trigger_rules():
    return {
        "negative": {
            "revenue_drop_50": {
                "threshold": -50,
                "severity": "HIGH",
                "signal": "매출액 50% 이상 감소",
                "description_template": "전년 대비 매출액이 {value}% 감소했습니다.",
            },
            "operating_loss_3y": {
                "severity": "HIGH",
                "signal": "영업손실 3개년 지속",
                "description": "최근 3개년 연속 영업손실이 발생했습니다.",
            },
            "interest_coverage_3y_low": {
                "threshold": 1,
                "severity": "HIGH",
                "signal": "이자보상배율 3개년 연속 1 미만",
                "description": "최근 3개년 연속 이자보상배율이 1 미만입니다.",
            },
            "cash_flow_negative_3y": {
                "severity": "HIGH",
                "signal": "영업활동현금흐름 3개년 적자",
                "description": "최근 3개년 연속 영업활동현금흐름이 음수입니다.",
            },
            "cash_less_than_short_borrowings": {
                "severity": "MEDIUM",
                "signal": "현금성자산 단기차입금 미달",
                "description": "현금성자산이 단기차입금보다 적습니다.",
            },
            "debt_ratio_over_400": {
                "threshold": 400,
                "severity": "HIGH",
                "signal": "부채비율 400% 초과",
                "description": "부채비율이 400%를 초과했습니다.",
            },
            "partial_capital_impairment": {
                "severity": "HIGH",
                "signal": "부분자본잠식",
                "description": "자본총계가 자본금보다 작아 부분자본잠식 상태입니다.",
            },
            "full_capital_impairment": {
                "severity": "CRITICAL",
                "signal": "완전자본잠식",
                "description": "자본총계가 0보다 작아 완전자본잠식 상태입니다.",
            },
        },
        "positive": {
            "revenue_jump": {
                "threshold": 30,
                "severity": "HIGH",
                "signal": "매출 퀀텀 점프",
                "description_template": "전년 대비 매출액이 {value}% 증가했습니다.",
            },
            "earnings_surprise": {
                "threshold": 50,
                "severity": "HIGH",
                "signal": "어닝 서프라이즈",
                "description_template": "전년 대비 영업이익이 {value}% 증가했습니다.",
            },
            "turnaround": {
                "severity": "HIGH",
                "signal": "영업이익 흑자 전환",
                "description": "최근 적자 흐름 이후 당기 영업이익이 흑자로 전환되었습니다.",
            },
            "asset_efficiency_up": {
                "threshold": 20,
                "severity": "MEDIUM",
                "signal": "자산 가동률 상승",
                "description_template": "재고자산회전율 또는 매출채권회전율이 전년 대비 20% 이상 개선되었습니다.",
            },
            "capacity_expansion": {
                "threshold": 30,
                "severity": "MEDIUM",
                "signal": "Capa 확대",
                "description_template": "유형자산 또는 자산 규모가 전년 대비 30% 이상 증가했습니다.",
            },
            "debt_ratio_down": {
                "threshold": -50,
                "severity": "LOW",
                "signal": "재무 구조 개선",
                "description_template": "부채비율이 전년 대비 {value}%p 감소했습니다.",
            },
            "cash_flow_strong": {
                "threshold": 50,
                "severity": "LOW",
                "signal": "현금 창출력 강화",
                "description_template": "영업활동현금흐름이 전년 대비 크게 개선되었습니다.",
            },
        },
    }


def get_industry_trigger_rules(industry_group):
    return {
        "industry_group": industry_group
    }