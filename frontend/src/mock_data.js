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

// MSW mock handler에서 /api/searchCompany 응답으로 사용하는 EXPECTED_AI_OUTPUT 형식 mock
export const EXPECTED_AI_OUTPUT_MOCK = {
  company_info: {
    stock_code: '000000',
    company_name: '테스트기업',
  },
  analysis_year: 2025,
  base_year: 2024,

  summary: {
    one_line_summary: '영업이익 급감 및 당기순손실 전환 등 복합 재무 위험 신호 감지',
    overall_risk_level: 'high',
    key_findings: [
      '매출액 20% 감소 (1,000억 → 800억)',
      '영업이익 86.67% 급감 (150억 → 20억)',
      '당기순이익 흑자에서 적자 전환 (+80억 → -50억)',
      '부채비율 53.46% 급상승 (150.2% → 230.5%)',
      '유동비율 100% 미만으로 하락 (130.5% → 82.3%)',
    ],
  },

  finance_summary: [
    {
      year: 2024,
      revenue: 100_000_000_000,
      operating_income: 15_000_000_000,
      net_income: 8_000_000_000,
      debt_ratio: 150.2,
      operating_margin: 15.0,
      current_ratio: 130.5,
    },
    {
      year: 2025,
      revenue: 80_000_000_000,
      operating_income: 2_000_000_000,
      net_income: -5_000_000_000,
      debt_ratio: 230.5,
      operating_margin: 2.5,
      current_ratio: 82.3,
    },
  ],

  financial_metrics: {
    revenue: { label: '매출액', current_year: 2025, base_year: 2024, current_value: 80_000_000_000, base_value: 100_000_000_000, yoy_change_rate: -20.0, unit: 'KRW' },
    operating_income: { label: '영업이익', current_year: 2025, base_year: 2024, current_value: 2_000_000_000, base_value: 15_000_000_000, yoy_change_rate: -86.67, unit: 'KRW' },
    net_income: { label: '당기순이익', current_year: 2025, base_year: 2024, current_value: -5_000_000_000, base_value: 8_000_000_000, yoy_change_rate: -162.5, unit: 'KRW' },
    debt_ratio: { label: '부채비율', current_year: 2025, base_year: 2024, current_value: 230.5, base_value: 150.2, yoy_change_rate: 53.46, unit: '%' },
    operating_margin: { label: '영업이익률', current_year: 2025, base_year: 2024, current_value: 2.5, base_value: 15.0, yoy_change_rate: -83.33, unit: '%' },
    current_ratio: { label: '유동비율', current_year: 2025, base_year: 2024, current_value: 82.3, base_value: 130.5, yoy_change_rate: -36.93, unit: '%' },
  },

  detected_changes: [
    { metric_key: 'revenue', metric_label: '매출액', year: 2025, base_year: 2024, change_type: 'decrease', direction: 'decrease', severity: 'medium', current_value: 80_000_000_000, base_value: 100_000_000_000, yoy_change_rate: -20.0, description: '매출액이 전년 대비 20.0% 감소했습니다.', search_keywords: ['매출 감소', '수요 둔화', '실적 부진'] },
    { metric_key: 'operating_income', metric_label: '영업이익', year: 2025, base_year: 2024, change_type: 'sharp_decrease', direction: 'decrease', severity: 'high', current_value: 2_000_000_000, base_value: 15_000_000_000, yoy_change_rate: -86.67, description: '영업이익이 전년 대비 86.67% 급감했습니다.', search_keywords: ['영업이익 감소', '수익성 악화', '비용 증가'] },
    { metric_key: 'net_income', metric_label: '당기순이익', year: 2025, base_year: 2024, change_type: 'turn_to_loss', direction: 'decrease', severity: 'high', current_value: -5_000_000_000, base_value: 8_000_000_000, yoy_change_rate: -162.5, description: '당기순이익이 흑자에서 적자로 전환되었습니다.', search_keywords: ['당기순손실', '적자 전환', '손실 발생'] },
    { metric_key: 'debt_ratio', metric_label: '부채비율', year: 2025, base_year: 2024, change_type: 'increase', direction: 'increase', severity: 'high', current_value: 230.5, base_value: 150.2, yoy_change_rate: 53.46, description: '부채비율이 전년 대비 크게 상승했습니다.', search_keywords: ['부채비율 상승', '차입금 증가', '재무 부담'] },
    { metric_key: 'current_ratio', metric_label: '유동비율', year: 2025, base_year: 2024, change_type: 'decrease', direction: 'decrease', severity: 'medium', current_value: 82.3, base_value: 130.5, yoy_change_rate: -36.93, description: '유동비율이 100% 미만으로 하락했습니다.', search_keywords: ['유동비율 하락', '유동성 악화', '단기 지급능력'] },
  ],

  evidence_news: [
    { metric_key: 'revenue', metric_label: '매출액', title: '테스트기업, 2025년 매출 20% 감소…수요 위축 장기화 우려', url: '#', content: '테스트기업이 2025년 연간 매출이 전년 대비 약 20% 감소했다고 공시했다. 주요 시장 수요 위축과 경쟁 심화가 복합적으로 작용한 결과로 분석된다.', published_date: '2025-03-15', evidence_summary: '매출 감소의 주요 원인은 시장 수요 위축과 경쟁 심화로 파악됨.', relevance_score: 0.92 },
    { metric_key: 'operating_income', metric_label: '영업이익', title: '테스트기업 영업이익 급감, 원가 상승·단가 하락 이중고', url: '#', content: '테스트기업의 2025년 영업이익이 전년 대비 86% 이상 감소한 것으로 나타났다. 원재료 비용 상승과 제품 단가 하락이 수익성을 크게 악화시켰다.', published_date: '2025-03-20', evidence_summary: '원가 상승과 판가 하락으로 영업이익률이 2.5%로 급락함.', relevance_score: 0.88 },
    { metric_key: 'net_income', metric_label: '당기순이익', title: '테스트기업 적자 전환 충격, 재무 건전성 우려 고조', url: '#', content: '테스트기업이 2025년 당기순손실 50억 원을 기록하며 흑자에서 적자로 전환됐다. 투자자들은 재무 건전성 악화에 우려를 표하고 있다.', published_date: '2025-03-22', evidence_summary: '영업외 비용 증가와 이자 부담이 순손실 전환을 가속함.', relevance_score: 0.85 },
    { metric_key: 'debt_ratio', metric_label: '부채비율', title: '테스트기업 차입금 급증, 부채비율 230% 돌파', url: '#', content: '테스트기업의 부채비율이 2025년 230.5%로 급상승했다. 신규 설비 투자 재원을 차입금으로 조달한 것이 주요 원인으로 지목된다.', published_date: '2025-04-01', evidence_summary: '설비 투자를 위한 차입금 증가로 재무 레버리지가 확대됨.', relevance_score: 0.81 },
    { metric_key: 'current_ratio', metric_label: '유동비율', title: '테스트기업 유동비율 82%…단기 유동성 경고등', url: '#', content: '테스트기업의 유동비율이 82.3%로 100% 미만으로 떨어졌다. 단기 지급 능력에 대한 우려가 커지고 있어 현금 흐름 관리가 시급한 상황이다.', published_date: '2025-04-05', evidence_summary: '유동부채 증가와 유동자산 감소가 동시에 발생하며 유동성 악화.', relevance_score: 0.79 },
  ],

  report: {
    executive_summary: '테스트기업은 2025년 매출 20% 감소, 영업이익 86.67% 급감, 당기순이익 적자 전환이라는 복합 재무 위험 신호를 보이고 있습니다. 부채비율이 230.5%로 급상승하고 유동비율이 82.3%로 하락하면서 단기 유동성 위험도 증가했습니다. 이는 시장 수요 위축, 원가 상승, 경쟁 심화가 동시에 작용한 결과로 분석됩니다.',
    financial_change_summary: '주요 재무 지표가 전반적으로 악화되었습니다. 매출액 -20.0%(1,000억→800억), 영업이익 -86.67%(150억→20억), 당기순이익 흑자→적자 전환(+80억→-50억), 부채비율 +53.46%(150.2%→230.5%), 유동비율 -36.93%(130.5%→82.3%)로 단기 지급 능력까지 위협받는 상황입니다.',
    related_news_summary: '매출 감소 관련 뉴스는 주로 시장 수요 위축과 경쟁 심화를 원인으로 지목했습니다. 영업이익 급감은 원가 상승과 제품 단가 하락이 동시에 작용한 것으로 보도되었으며, 부채비율 상승과 유동성 악화에 대한 투자자 우려 기사도 다수 확인되었습니다.',
    possible_causes: '① 주력 시장 수요 위축으로 인한 매출 급감\n② 원재료 비용 상승과 제품 단가 하락으로 인한 수익성 악화\n③ 신규 설비 투자 재원 조달을 위한 차입금 증가로 부채비율 상승\n④ 영업이익 급감에 따른 내부 현금 창출 능력 저하로 유동성 위기 심화',
    interview_point: '· 2026년 매출 회복을 위한 구체적인 시장 전략과 목표 수치는?\n· 부채비율 230.5%에 대한 재무 건전성 개선 로드맵은?\n· 유동비율 100% 미만 상황에서의 단기 유동성 확보 방안은?\n· 원가 절감 및 수익성 개선을 위한 구조적 대응 방안은?',
    limitations: '본 분석은 공개된 재무 데이터와 뉴스 기사를 기반으로 AI가 생성한 보고서입니다. 비공개 내부 정보, 산업 전문가 의견, 실사 결과는 반영되지 않았습니다. 투자 의사결정에 단독으로 활용하지 마십시오.',
  },

  metadata: {
    source_count: 5,
    model: 'claude-3-5-sonnet-20241022',
    generated_at: '2025-05-14T10:00:00+09:00',
  },
};

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