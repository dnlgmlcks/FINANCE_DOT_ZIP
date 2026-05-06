"""
sample_report_data.py

AI 리포트 파이프라인 개발을 위한 샘플 입력/출력 데이터 정의 파일입니다.

이 파일은 DB, Backend API, Data 파트가 완성되기 전에도
AI 파트의 기능을 독립적으로 테스트할 수 있도록 Mock 데이터를 제공합니다.

주요 목적:
1. Backend/Data 파트가 AI 파트에 넘겨줄 입력 JSON 구조 정의
2. 재무 지표, yoy_change_rate, detected_changes 예시 제공
3. Tavily 뉴스 검색, Evidence Filter, Report Writer Chain 테스트용 데이터 제공
4. 백엔드/UI 연동을 위한 최종 출력 JSON 초안 정의

주의:
- 실제 서비스에서는 이 파일의 Mock 데이터 대신 Backend/Data 파트에서 전달받은 데이터를 사용합니다.
- AI 파트는 재무 계산을 직접 수행하지 않고, 이미 계산된 yoy_change_rate와 detected_changes를 입력받는 것을 원칙으로 합니다.
"""

from copy import deepcopy


# ---------------------------------------------------------------------
# 1. AI 입력용 Mock 데이터
# ---------------------------------------------------------------------

SAMPLE_NORMAL_AI_INPUT = {
    "company_info": {
        "stock_code": "005930",
        "company_name": "삼성전자",
    },
    "analysis_year": 2025,
    "base_year": 2024,

    # 기존 warning_trigger.py, 테스트 코드와의 호환성을 위해 유지
    "finance_summary": [
        {
            "year": 2025,
            "revenue": 300_000_000_000_000,
            "operating_income": 50_000_000_000_000,
            "net_income": 40_000_000_000_000,
            "debt_ratio": 35.2,
            "operating_margin": 16.7,
            "current_ratio": 180.5,
        },
        {
            "year": 2024,
            "revenue": 280_000_000_000_000,
            "operating_income": 45_000_000_000_000,
            "net_income": 35_000_000_000_000,
            "debt_ratio": 37.1,
            "operating_margin": 16.1,
            "current_ratio": 190.2,
        },
    ],

    # AI 파트에서 사용하기 좋은 정규화된 지표 구조
    "financial_metrics": {
        "revenue": {
            "label": "매출액",
            "current_year": 2025,
            "base_year": 2024,
            "current_value": 300_000_000_000_000,
            "base_value": 280_000_000_000_000,
            "yoy_change_rate": 7.14,
            "unit": "KRW",
        },
        "operating_income": {
            "label": "영업이익",
            "current_year": 2025,
            "base_year": 2024,
            "current_value": 50_000_000_000_000,
            "base_value": 45_000_000_000_000,
            "yoy_change_rate": 11.11,
            "unit": "KRW",
        },
        "net_income": {
            "label": "당기순이익",
            "current_year": 2025,
            "base_year": 2024,
            "current_value": 40_000_000_000_000,
            "base_value": 35_000_000_000_000,
            "yoy_change_rate": 14.29,
            "unit": "KRW",
        },
        "debt_ratio": {
            "label": "부채비율",
            "current_year": 2025,
            "base_year": 2024,
            "current_value": 35.2,
            "base_value": 37.1,
            "yoy_change_rate": -5.12,
            "unit": "%",
        },
        "operating_margin": {
            "label": "영업이익률",
            "current_year": 2025,
            "base_year": 2024,
            "current_value": 16.7,
            "base_value": 16.1,
            "yoy_change_rate": 3.73,
            "unit": "%",
        },
        "current_ratio": {
            "label": "유동비율",
            "current_year": 2025,
            "base_year": 2024,
            "current_value": 180.5,
            "base_value": 190.2,
            "yoy_change_rate": -5.10,
            "unit": "%",
        },
    },

    # 안정적인 케이스이므로 주요 변동 없음
    "detected_changes": [],
}


SAMPLE_WARNING_AI_INPUT = {
    "company_info": {
        "stock_code": "000000",
        "company_name": "테스트기업",
    },
    "analysis_year": 2025,
    "base_year": 2024,

    # 기존 warning_trigger.py, 테스트 코드와의 호환성을 위해 유지
    "finance_summary": [
        {
            "year": 2025,
            "revenue": 80_000_000_000,
            "operating_income": 2_000_000_000,
            "net_income": -5_000_000_000,
            "debt_ratio": 230.5,
            "operating_margin": 2.5,
            "current_ratio": 82.3,
        },
        {
            "year": 2024,
            "revenue": 100_000_000_000,
            "operating_income": 15_000_000_000,
            "net_income": 8_000_000_000,
            "debt_ratio": 150.2,
            "operating_margin": 15.0,
            "current_ratio": 130.5,
        },
    ],

    # AI 파트에서 사용할 정규화된 지표 구조
    "financial_metrics": {
        "revenue": {
            "label": "매출액",
            "current_year": 2025,
            "base_year": 2024,
            "current_value": 80_000_000_000,
            "base_value": 100_000_000_000,
            "yoy_change_rate": -20.0,
            "unit": "KRW",
        },
        "operating_income": {
            "label": "영업이익",
            "current_year": 2025,
            "base_year": 2024,
            "current_value": 2_000_000_000,
            "base_value": 15_000_000_000,
            "yoy_change_rate": -86.67,
            "unit": "KRW",
        },
        "net_income": {
            "label": "당기순이익",
            "current_year": 2025,
            "base_year": 2024,
            "current_value": -5_000_000_000,
            "base_value": 8_000_000_000,
            "yoy_change_rate": -162.5,
            "unit": "KRW",
        },
        "debt_ratio": {
            "label": "부채비율",
            "current_year": 2025,
            "base_year": 2024,
            "current_value": 230.5,
            "base_value": 150.2,
            "yoy_change_rate": 53.46,
            "unit": "%",
        },
        "operating_margin": {
            "label": "영업이익률",
            "current_year": 2025,
            "base_year": 2024,
            "current_value": 2.5,
            "base_value": 15.0,
            "yoy_change_rate": -83.33,
            "unit": "%",
        },
        "current_ratio": {
            "label": "유동비율",
            "current_year": 2025,
            "base_year": 2024,
            "current_value": 82.3,
            "base_value": 130.5,
            "yoy_change_rate": -36.93,
            "unit": "%",
        },
    },

    # Data/PM 파트에서 AI 파트로 넘겨준다고 가정하는 변동 감지 결과
    "detected_changes": [
        {
            "metric_key": "revenue",
            "metric_label": "매출액",
            "year": 2025,
            "base_year": 2024,
            "change_type": "decrease",
            "direction": "decrease",
            "severity": "medium",
            "current_value": 80_000_000_000,
            "base_value": 100_000_000_000,
            "yoy_change_rate": -20.0,
            "description": "매출액이 전년 대비 20.0% 감소했습니다.",
            "search_keywords": [
                "매출 감소",
                "수요 둔화",
                "실적 부진",
            ],
        },
        {
            "metric_key": "operating_income",
            "metric_label": "영업이익",
            "year": 2025,
            "base_year": 2024,
            "change_type": "sharp_decrease",
            "direction": "decrease",
            "severity": "high",
            "current_value": 2_000_000_000,
            "base_value": 15_000_000_000,
            "yoy_change_rate": -86.67,
            "description": "영업이익이 전년 대비 86.67% 감소했습니다.",
            "search_keywords": [
                "영업이익 감소",
                "수익성 악화",
                "비용 증가",
                "실적 악화",
            ],
        },
        {
            "metric_key": "net_income",
            "metric_label": "당기순이익",
            "year": 2025,
            "base_year": 2024,
            "change_type": "turn_to_loss",
            "direction": "decrease",
            "severity": "high",
            "current_value": -5_000_000_000,
            "base_value": 8_000_000_000,
            "yoy_change_rate": -162.5,
            "description": "당기순이익이 흑자에서 적자로 전환되었습니다.",
            "search_keywords": [
                "당기순손실",
                "적자 전환",
                "순이익 감소",
                "손실 발생",
            ],
        },
        {
            "metric_key": "debt_ratio",
            "metric_label": "부채비율",
            "year": 2025,
            "base_year": 2024,
            "change_type": "increase",
            "direction": "increase",
            "severity": "high",
            "current_value": 230.5,
            "base_value": 150.2,
            "yoy_change_rate": 53.46,
            "description": "부채비율이 전년 대비 크게 상승했습니다.",
            "search_keywords": [
                "부채비율 상승",
                "차입금 증가",
                "재무 부담",
                "유동성 우려",
            ],
        },
        {
            "metric_key": "current_ratio",
            "metric_label": "유동비율",
            "year": 2025,
            "base_year": 2024,
            "change_type": "decrease",
            "direction": "decrease",
            "severity": "medium",
            "current_value": 82.3,
            "base_value": 130.5,
            "yoy_change_rate": -36.93,
            "description": "유동비율이 100% 미만으로 하락했습니다.",
            "search_keywords": [
                "유동비율 하락",
                "유동성 악화",
                "단기 지급능력",
                "현금흐름 부담",
            ],
        },
    ],
}


# ---------------------------------------------------------------------
# 2. 최종 AI 출력 JSON 초안
# ---------------------------------------------------------------------

EXPECTED_AI_OUTPUT = {
    "company_info": {
        "stock_code": "000000",
        "company_name": "테스트기업",
    },
    "analysis_year": 2025,
    "base_year": 2024,

    "summary": {
        "one_line_summary": "",
        "overall_risk_level": "",
        "key_findings": [],
    },

    "detected_changes": [
        {
            "metric_key": "",
            "metric_label": "",
            "change_type": "",
            "direction": "",
            "severity": "",
            "yoy_change_rate": 0.0,
            "description": "",
        }
    ],

    "evidence_news": [
        {
            "metric_key": "",
            "metric_label": "",
            "title": "",
            "url": "",
            "content": "",
            "published_date": "",
            "evidence_summary": "",
            "relevance_score": 0.0,
        }
    ],

    "report": {
        "executive_summary": "",
        "financial_change_summary": "",
        "related_news_summary": "",
        "possible_causes": "",
        "interview_point": "",
        "limitations": "",
    },

    "metadata": {
        "source_count": 0,
        "model": "",
        "generated_at": "",
    },
}


# ---------------------------------------------------------------------
# 3. Getter 함수
# ---------------------------------------------------------------------

def get_sample_normal_report_data() -> dict:
    """
    비교적 안정적인 재무 흐름을 가진 기업 예시 데이터를 반환합니다.

    Returns:
        dict: 정상 재무 흐름을 가진 AI 입력용 Mock 데이터
    """

    return deepcopy(SAMPLE_NORMAL_AI_INPUT)


def get_sample_warning_report_data() -> dict:
    """
    여러 재무 위험 신호가 동시에 발생한 예시 데이터를 반환합니다.

    Returns:
        dict: 위험 신호가 포함된 AI 입력용 Mock 데이터
    """

    return deepcopy(SAMPLE_WARNING_AI_INPUT)


def get_sample_report_data(case: str = "normal") -> dict:
    """
    테스트 케이스에 따라 Mock report_data를 반환합니다.

    기존 테스트 코드와의 호환성을 위해 함수명을 유지합니다.

    Args:
        case: "normal" 또는 "warning"

    Returns:
        dict: company_info, finance_summary, financial_metrics, detected_changes를 포함한 Mock 데이터

    Raises:
        ValueError: 지원하지 않는 case가 입력된 경우
    """

    if case == "normal":
        return get_sample_normal_report_data()

    if case == "warning":
        return get_sample_warning_report_data()

    raise ValueError("case는 'normal' 또는 'warning'만 사용할 수 있습니다.")


def get_sample_ai_input(case: str = "warning") -> dict:
    """
    AI 파이프라인 테스트에 사용할 입력 데이터를 반환합니다.

    news_query_builder, financial_context_builder, report_writer_chain 등
    AI 파트의 주요 모듈은 이 함수의 반환값을 기준으로 테스트할 수 있습니다.

    Args:
        case: "normal" 또는 "warning"

    Returns:
        dict: AI 파이프라인 입력용 Mock 데이터
    """

    return get_sample_report_data(case=case)


def get_expected_ai_output() -> dict:
    """
    백엔드/UI 연동을 위한 최종 AI 출력 JSON 초안을 반환합니다.

    Returns:
        dict: 최종 AI 리포트 출력 형식 초안
    """

    return deepcopy(EXPECTED_AI_OUTPUT)


# ---------------------------------------------------------------------
# 4. 단독 실행 테스트
# ---------------------------------------------------------------------

if __name__ == "__main__":
    sample_data = get_sample_ai_input(case="warning")
    expected_output = get_expected_ai_output()

    print("[Sample AI Input]")
    print(sample_data)

    print("\n[Expected AI Output]")
    print(expected_output)