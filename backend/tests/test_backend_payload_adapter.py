"""
test_backend_payload_adapter.py

backend_payload_adapter.py 단독 테스트 파일입니다.

테스트 목적:
1. 백엔드 종합 리포트 API 응답 구조를 ai_input으로 변환할 수 있는지 확인합니다.
2. analysis_year / base_year가 정상 결정되는지 확인합니다.
3. finance_summary에서 financial_metrics가 생성되는지 확인합니다.
4. detected_changes에 base_year, base_value, signal_type이 보강되는지 확인합니다.

실행:
python -m tests.test_backend_payload_adapter
또는
pytest tests/test_backend_payload_adapter.py
"""

import json

from src.ai.backend_payload_adapter import build_ai_input_from_backend_response


def build_sample_backend_payload() -> dict:
    """
    실제 API 응답 구조를 축약한 테스트용 payload를 생성합니다.
    """

    return {
        "status": "success",
        "message": "종합 재무 리포트 조회 성공",
        "data": {
            "company_info": {
                "stock_code": "005930",
                "company_name": "삼성전자",
                "induty_code": "26",
            },
            "industry_info": {
                "industry_group": "tech_equipment",
                "industry_group_name": "기술 및 장치 산업",
                "is_excluded": False,
                "reason": "전자/IT/통신/소프트웨어 중심 업종으로 분류되었습니다.",
            },
            "finance_summary": [
                {
                    "year": 2022,
                    "revenue": 302231360000000,
                    "operating_income": 43376630000000,
                    "net_income": 55654077000000,
                    "debt_ratio": 26.41,
                    "equity_ratio": 79.11,
                    "current_ratio": 278.86,
                    "operating_cash_flow": 71728568000000,
                    "revenue_yoy": 8.09,
                    "operating_income_yoy": -15.99,
                    "net_income_yoy": 39.46,
                    "debt_ratio_change": -13.51,
                    "equity_ratio_change": 7.64,
                },
                {
                    "year": 2023,
                    "revenue": 258935494000000,
                    "operating_income": 6566976000000,
                    "net_income": 15487100000000,
                    "debt_ratio": 25.36,
                    "equity_ratio": 79.77,
                    "current_ratio": 258.77,
                    "operating_cash_flow": 46547889000000,
                    "revenue_yoy": -14.33,
                    "operating_income_yoy": -84.86,
                    "net_income_yoy": -72.17,
                    "debt_ratio_change": -1.05,
                    "equity_ratio_change": 0.66,
                },
            ],
            "signals": [
                {
                    "year": 2023,
                    "type": "negative",
                    "severity": "HIGH",
                    "signal": "영업이익 급감",
                    "description": "전년 대비 영업이익이 -84.86% 감소했습니다.",
                },
                {
                    "year": 2023,
                    "type": "positive",
                    "severity": "LOW",
                    "signal": "현금 창출력 강화",
                    "description": "영업활동현금흐름이 순이익보다 커 현금 창출력이 양호합니다.",
                },
            ],
            "detected_changes": [
                {
                    "metric_key": "operating_income",
                    "metric_label": "영업이익",
                    "year": 2023,
                    "change_type": "sharp_decrease",
                    "direction": "decrease",
                    "severity": "high",
                    "current_value": 6566976000000,
                    "yoy_change_rate": -84.86,
                    "description": "전년 대비 영업이익이 -84.86% 감소했습니다.",
                    "search_keywords": [
                        "영업이익 감소",
                        "수익성 악화",
                        "비용 증가",
                        "실적 악화",
                    ],
                    "source_signal": "영업이익 급감",
                },
                {
                    "metric_key": "operating_cash_flow",
                    "metric_label": "영업활동현금흐름",
                    "year": 2023,
                    "change_type": "improve",
                    "direction": "increase",
                    "severity": "low",
                    "current_value": 46547889000000,
                    "yoy_change_rate": None,
                    "description": "영업활동현금흐름이 순이익보다 커 현금 창출력이 양호합니다.",
                    "search_keywords": [
                        "영업현금흐름 개선",
                        "현금 창출력",
                        "현금흐름 개선",
                    ],
                    "source_signal": "현금 창출력 강화",
                },
            ],
        },
    }


def test_build_ai_input_from_backend_response() -> None:
    """
    백엔드 payload가 AI 입력 형식으로 정상 변환되는지 확인합니다.
    """

    payload = build_sample_backend_payload()
    ai_input = build_ai_input_from_backend_response(payload)

    assert ai_input["company_info"]["stock_code"] == "005930"
    assert ai_input["company_info"]["company_name"] == "삼성전자"

    assert ai_input["industry_info"]["industry_group"] == "tech_equipment"
    assert ai_input["industry_info"]["industry_group_name"] == "기술 및 장치 산업"

    assert ai_input["analysis_year"] == 2023
    assert ai_input["base_year"] == 2022

    assert "financial_metrics" in ai_input
    assert "operating_income" in ai_input["financial_metrics"]

    operating_income = ai_input["financial_metrics"]["operating_income"]

    assert operating_income["current_year"] == 2023
    assert operating_income["base_year"] == 2022
    assert operating_income["current_value"] == 6566976000000
    assert operating_income["base_value"] == 43376630000000
    assert operating_income["yoy_change_rate"] == -84.86

    detected_changes = ai_input["detected_changes"]

    assert len(detected_changes) == 2

    operating_income_change = detected_changes[0]

    assert operating_income_change["base_year"] == 2022
    assert operating_income_change["base_value"] == 43376630000000
    assert operating_income_change["signal_type"] == "negative"

    operating_cash_flow_change = detected_changes[1]

    assert operating_cash_flow_change["base_year"] == 2022
    assert operating_cash_flow_change["base_value"] == 71728568000000
    assert operating_cash_flow_change["signal_type"] == "positive"

    assert ai_input["source"] == "backend_api"


if __name__ == "__main__":
    test_build_ai_input_from_backend_response()

    payload = build_sample_backend_payload()
    ai_input = build_ai_input_from_backend_response(payload)

    print("[Backend Payload Adapter Test Passed]")
    print("company:", ai_input["company_info"]["company_name"])
    print("stock_code:", ai_input["company_info"]["stock_code"])
    print("industry_group:", ai_input["industry_info"]["industry_group"])
    print("analysis_year:", ai_input["analysis_year"])
    print("base_year:", ai_input["base_year"])
    print("financial_metric_count:", len(ai_input["financial_metrics"]))
    print("detected_change_count:", len(ai_input["detected_changes"]))

    print("\n[Detected Changes]")
    print(json.dumps(ai_input["detected_changes"], ensure_ascii=False, indent=2))
