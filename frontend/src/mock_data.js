/*
backend/sample_report_data.py에 기록된 샘플 입력/출력 데이터 정의 양식대로 
*/



export const SAMPLE_NORMAL_AI_INPUT = {
    "company_info": {
        "stock_code": "005930",
        "company_name": "삼성전자",
    },
    "analysis_year": 2025,
    "base_year": 2024,

    //기존 warning_trigger.py, 테스트 코드와의 호환성을 위해 유지
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

    // AI 파트에서 사용하기 좋은 정규화된 지표 구조
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

    // 안정적인 케이스이므로 주요 변동 없음
    "detected_changes": [],
}


 export const SAMPLE_WARNING_AI_INPUT = {
    "company_info": {
        "stock_code": "000000",
        "company_name": "테스트기업",
    },
    "analysis_year": 2025,
    "base_year": 2024,

    // 기존 warning_trigger.py, 테스트 코드와의 호환성을 위해 유지
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

    // AI 파트에서 사용할 정규화된 지표 구조
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

    // Data/PM 파트에서 AI 파트로 넘겨준다고 가정하는 변동 감지 결과
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

export const MOCK = {
  title: '삼성전자 주식회사',
  sections: [
    {
      id: 'I',
      title: '공시의 의미 및 요약',
      items: [
        '삼성전자는 2024년 3분기 분기보고서를 통해 영업이익이 전년 동기 대비 감소하였음을 공시하였습니다.',
        '반도체 부문(DS)에서의 실적 악화가 주요 원인으로 분석되며, 메모리 가격 하락과 수요 둔화가 복합적으로 작용하였습니다.',
        '스마트폰(MX) 부문은 갤럭시 S24 시리즈의 견조한 판매로 선방하였으나, 전체 영업이익을 상쇄하기에는 역부족이었습니다.',
      ],
    },
    {
      id: 'II',
      title: '사업의 내용 발췌',
      items: [
        '반도체 사업부는 HBM3E 개발 및 양산에 집중하며 AI 메모리 시장 공략을 강화하고 있습니다.',
        '파운드리 사업은 2nm 공정 개발을 진행 중이며, 주요 고객사 확보를 위한 협상이 지속되고 있습니다.',
        '가전·TV(VD/DA) 부문은 AI 탑재 제품군 확대로 프리미엄 시장 내 경쟁력을 유지하고 있습니다.',
      ],
    },
  ],
};