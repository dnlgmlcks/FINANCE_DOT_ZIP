"""
sample_disclosure_data.py

공시/사업보고서 정성 근거 Mock 데이터를 제공하는 모듈입니다.

목적:
1. disclosure_retriever.py가 아직 구현되지 않은 상태에서 report_writer_chain.py를 테스트합니다.
2. 최종 리포트 생성 시 evidence_disclosures가 들어왔을 때 문장이 잘 작성되는지 확인합니다.
3. 나중에 Vector DB 검색 결과가 반환해야 할 evidence_disclosures 형식을 미리 고정합니다.

주의:
- 이 파일의 데이터는 테스트용 Mock 데이터입니다.
- 실제 서비스에서는 disclosure_retriever.py가 Vector DB에서 검색한 결과를
  동일한 evidence_disclosures 형식으로 반환하면 됩니다.
- chunk_text는 공시 원문 일부처럼 보이도록 작성한 예시이며, 실제 공시 문구가 아닙니다.
"""

from copy import deepcopy
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------
# 1. 공시 근거 Mock 데이터
# ---------------------------------------------------------------------

SAMPLE_EVIDENCE_DISCLOSURES = [
    {
        "stock_code": "005930",
        "company_name": "삼성전자",
        "year": 2023,
        "base_year": 2022,
        "source_type": "disclosure",
        "report_type": "사업보고서",
        "source": "2023_삼성전자_사업보고서_mock",
        "page": 12,
        "section": "사업의 내용",
        "metric_key": "operating_income",
        "metric_label": "영업이익",
        "chunk_id": "005930_2023_business_report_operating_income_001",
        "chunk_text": (
            "2023년 반도체 부문은 메모리 제품 수요 둔화와 가격 하락의 영향을 받았으며, "
            "주요 제품의 판매 단가 하락과 재고 부담 증가로 수익성이 약화되었습니다. "
            "회사는 시장 상황에 대응하기 위해 제품 믹스 개선과 고부가가치 제품 중심의 판매 전략을 추진하고 있습니다."
        ),
        "evidence_summary": (
            "공시 Mock 문서에서는 메모리 수요 둔화, 가격 하락, 재고 부담 증가가 "
            "수익성 약화와 관련된 배경으로 제시됩니다."
        ),
        "relevance_score": 0.92,
        "retrieval_reason": "영업이익 급감 및 기술 업종 수익성 둔화와 관련된 사업 내용입니다.",
        "metadata": {
            "industry_group": "tech_equipment",
            "industry_group_name": "기술 및 장치 산업",
            "signal_type": "negative",
            "severity": "high",
            "direction": "decrease",
            "source_signal": "영업이익 급감",
        },
    },
    {
        "stock_code": "005930",
        "company_name": "삼성전자",
        "year": 2023,
        "base_year": 2022,
        "source_type": "disclosure",
        "report_type": "사업보고서",
        "source": "2023_삼성전자_사업보고서_mock",
        "page": 18,
        "section": "위험요인",
        "metric_key": "operating_income",
        "metric_label": "영업이익",
        "chunk_id": "005930_2023_business_report_risk_001",
        "chunk_text": (
            "글로벌 경기 둔화, IT 수요 감소, 반도체 가격 변동성은 회사의 매출과 수익성에 "
            "부정적인 영향을 미칠 수 있습니다. 특히 메모리 반도체 시장은 수급 상황에 따라 "
            "가격 변동 폭이 커질 수 있으며, 이는 영업성과의 변동성을 확대할 수 있습니다."
        ),
        "evidence_summary": (
            "공시 Mock 문서에서는 글로벌 경기 둔화, IT 수요 감소, 반도체 가격 변동성이 "
            "수익성 변동 위험과 관련된 요인으로 언급됩니다."
        ),
        "relevance_score": 0.89,
        "retrieval_reason": "기술 업종 수익성 급락 신호와 연결되는 위험요인입니다.",
        "metadata": {
            "industry_group": "tech_equipment",
            "industry_group_name": "기술 및 장치 산업",
            "signal_type": "negative",
            "severity": "high",
            "direction": "decrease",
            "source_signal": "기술 업종 수익성 급락",
        },
    },
    {
        "stock_code": "005930",
        "company_name": "삼성전자",
        "year": 2023,
        "base_year": 2022,
        "source_type": "disclosure",
        "report_type": "사업보고서",
        "source": "2023_삼성전자_사업보고서_mock",
        "page": 24,
        "section": "현금흐름 및 투자활동",
        "metric_key": "operating_cash_flow",
        "metric_label": "영업활동현금흐름",
        "chunk_id": "005930_2023_business_report_cashflow_001",
        "chunk_text": (
            "회사는 업황 둔화에도 불구하고 영업활동에서 현금흐름을 창출하고 있으며, "
            "중장기 경쟁력 확보를 위해 연구개발과 생산 역량 강화를 위한 투자를 지속하고 있습니다. "
            "다만 시장 회복 시점과 수요 개선 여부에 따라 투자 부담과 현금흐름의 변동성이 발생할 수 있습니다."
        ),
        "evidence_summary": (
            "공시 Mock 문서에서는 업황 둔화에도 영업활동현금흐름이 유지되고 있으나, "
            "투자 지속에 따른 현금흐름 변동성은 추가 확인이 필요하다고 볼 수 있습니다."
        ),
        "relevance_score": 0.84,
        "retrieval_reason": "기술 및 장치 산업 가이드의 현금흐름 대조 기준과 관련된 내용입니다.",
        "metadata": {
            "industry_group": "tech_equipment",
            "industry_group_name": "기술 및 장치 산업",
            "signal_type": "positive",
            "severity": "low",
            "direction": "increase",
            "source_signal": "현금 창출력 강화",
        },
    },
]


# ---------------------------------------------------------------------
# 2. 대표 함수
# ---------------------------------------------------------------------

def get_sample_evidence_disclosures(
    stock_code: Optional[str] = None,
    year: Optional[int] = None,
    metric_key: Optional[str] = None,
    max_items: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    조건에 맞는 공시 Mock evidence_disclosures를 반환합니다.

    Args:
        stock_code: 종목코드 필터. 예: "005930"
        year: 분석 연도 필터. 예: 2023
        metric_key: 재무 지표 필터. 예: "operating_income"
        max_items: 최대 반환 개수

    Returns:
        evidence_disclosures 형식의 list[dict]
    """

    results = deepcopy(SAMPLE_EVIDENCE_DISCLOSURES)

    if stock_code:
        results = [
            item
            for item in results
            if item.get("stock_code") == stock_code
        ]

    if year is not None:
        results = [
            item
            for item in results
            if item.get("year") == year
        ]

    if metric_key:
        results = [
            item
            for item in results
            if item.get("metric_key") == metric_key
        ]

    if max_items is not None:
        results = results[:max_items]

    return results


def get_sample_disclosure_context(
    stock_code: Optional[str] = None,
    year: Optional[int] = None,
    metric_key: Optional[str] = None,
    max_items: Optional[int] = None,
) -> Dict[str, Any]:
    """
    disclosure_retriever.py가 나중에 반환할 수 있는 context 형태의 Mock 결과를 반환합니다.

    Returns:
        {
            "evidence_disclosures": [...],
            "metadata": {...}
        }
    """

    evidence_disclosures = get_sample_evidence_disclosures(
        stock_code=stock_code,
        year=year,
        metric_key=metric_key,
        max_items=max_items,
    )

    return {
        "evidence_disclosures": evidence_disclosures,
        "metadata": {
            "source": "mock_disclosure",
            "stock_code": stock_code,
            "year": year,
            "metric_key": metric_key,
            "evidence_disclosure_count": len(evidence_disclosures),
        },
    }


# ---------------------------------------------------------------------
# 3. 단독 실행 테스트
# ---------------------------------------------------------------------

if __name__ == "__main__":
    import json

    disclosures = get_sample_evidence_disclosures(
        stock_code="005930",
        year=2023,
    )

    print("[Sample Disclosure Data Test]")
    print("evidence_disclosure_count:", len(disclosures))
    print(json.dumps(disclosures, ensure_ascii=False, indent=2))
