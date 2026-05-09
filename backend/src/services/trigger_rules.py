def get_common_trigger_rules():
    return {
        "negative": {
            "debt_ratio_high": {
                "threshold": 200,
                "severity": "HIGH",
                "signal": "부채비율 과다",
                "description": "부채비율이 200%를 초과했습니다."
            },

            "operating_margin_negative": {
                "threshold": 0,
                "severity": "HIGH",
                "signal": "영업적자 발생",
                "description": "영업이익률이 음수입니다."
            },

            "net_income_negative": {
                "threshold": 0,
                "severity": "MEDIUM",
                "signal": "순손실 발생",
                "description": "당기순이익이 적자입니다."
            },

            "current_ratio_low": {
                "threshold": 100,
                "severity": "MEDIUM",
                "signal": "유동성 위험",
                "description": "유동비율이 100% 미만입니다."
            },

            "interest_coverage_low": {
                "threshold": 1,
                "severity": "HIGH",
                "signal": "이자상환 위험",
                "description": "이자보상배율이 1 미만입니다."
            },

            "revenue_drop": {
                "threshold": -20,
                "severity": "MEDIUM",
                "signal": "매출 급감",
                "description_template": "전년 대비 매출이 {value}% 감소했습니다."
            },

            "operating_income_drop_high": {
                "threshold": -50,
                "severity": "HIGH",
                "signal": "영업이익 급감",
                "description_template": "전년 대비 영업이익이 {value}% 감소했습니다."
            },

            "operating_income_drop_medium": {
                "threshold": -20,
                "severity": "MEDIUM",
                "signal": "영업이익 감소",
                "description_template": "전년 대비 영업이익이 {value}% 감소했습니다."
            },

            "receivables_turnover_drop": {
                "threshold": -20,
                "severity": "MEDIUM",
                "signal": "매출채권 회전율 악화",
                "description_template": "매출채권회전율이 전년 대비 {value}% 감소했습니다."
            },

            "inventory_turnover_drop": {
                "threshold": -20,
                "severity": "MEDIUM",
                "signal": "재고자산 회전율 악화",
                "description_template": "재고자산회전율이 전년 대비 {value}% 감소했습니다."
            }
        },

        "positive": {

            "revenue_jump": {
                "threshold": 30,
                "severity": "HIGH",
                "signal": "매출 퀀텀 점프",
                "description_template": "전년 대비 매출이 {value}% 급증했습니다."
            },

            "earnings_surprise": {
                "threshold": 50,
                "severity": "HIGH",
                "signal": "어닝 서프라이즈",
                "description_template": "전년 대비 영업이익이 {value}% 증가했습니다."
            },

            "net_income_growth": {
                "threshold": 50,
                "severity": "MEDIUM",
                "signal": "순이익 고성장",
                "description_template": "전년 대비 순이익이 {value}% 증가했습니다."
            },

            "equity_ratio_improve": {
                "threshold": 5,
                "severity": "LOW",
                "signal": "자기자본비율 개선",
                "description_template": "자기자본비율이 전년 대비 {value}%p 상승했습니다."
            },

            "borrowings_dependency_down": {
                "threshold": -3,
                "severity": "LOW",
                "signal": "재무구조 개선",
                "description_template": "차입금의존도가 전년 대비 {value}%p 감소했습니다."
            },

            "cash_flow_strong": {
                "severity": "LOW",
                "signal": "현금 창출력 강화",
                "description": "영업활동현금흐름이 순이익보다 커 현금 창출력이 양호합니다."
            },

            "asset_efficiency_up": {
                "threshold": 10,
                "severity": "MEDIUM",
                "signal": "자산 가동률 상승",
                "description_template": "총자산 대비 매출 효율이 전년 대비 개선되었습니다."
            },

            "capacity_expansion": {
                "threshold": 20,
                "severity": "MEDIUM",
                "signal": "Capa 확대",
                "description_template": "유형자산 및 자산 규모가 크게 증가했습니다."
            }
        }
    }


def get_industry_trigger_rules(industry_group):
    return {
        "industry_group": industry_group
    }