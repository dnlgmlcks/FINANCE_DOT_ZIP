"""
test_comprehensive_report_service.py

AI 재무 분석 리포트 전체 파이프라인 E2E 테스트 파일입니다.

테스트 흐름:
1. sample_report_data.py의 Mock ai_input을 불러옵니다.
2. 테스트용으로 기업명을 삼성전자로 변경합니다.
3. create_ai_report()를 실행합니다.
4. 최종 결과 JSON에 필수 key가 존재하는지 확인합니다.
5. metadata의 count 값이 정상적으로 들어오는지 확인합니다.

주의:
- 현재 재무 수치는 Mock 데이터입니다.
- disclosure_retriever.py는 아직 구현되지 않았으므로 evidence_disclosures는 빈 리스트가 정상입니다.
- Tavily API를 호출하므로 .env에 TAVILY_API_KEY가 있어야 합니다.
- OpenAI API를 호출하므로 .env에 OPENAI_API_KEY가 있어야 합니다.
"""

import json

from src.ai.comprehensive_report_service import create_ai_report
from src.ai.sample_report_data import get_sample_ai_input


def build_test_ai_input() -> dict:
    """
    E2E 테스트용 ai_input을 생성합니다.

    sample_report_data.py의 Mock 데이터를 사용하되,
    Tavily 검색이 가능하도록 기업명만 실제 기업인 삼성전자로 변경합니다.
    """

    ai_input = get_sample_ai_input(case="warning")

    ai_input["company_info"]["company_name"] = "삼성전자"
    ai_input["company_info"]["stock_code"] = "005930"
    ai_input["analysis_year"] = 2023
    ai_input["base_year"] = 2022

    for change in ai_input.get("detected_changes", []):
        change["year"] = 2023
        change["base_year"] = 2022

    return ai_input


def test_create_ai_report_e2e() -> None:
    """
    전체 AI 리포트 파이프라인이 최종 JSON을 정상 반환하는지 확인합니다.
    """

    ai_input = build_test_ai_input()

    result = create_ai_report(
        ai_input=ai_input,
        vector_store=None,
        max_results_per_query=5,
        max_total_news_results=20,
        max_evidence_news=5,
        include_searched_news=False,
    )

    assert isinstance(result, dict)

    # 최상위 필수 key 확인
    required_top_level_keys = [
        "company_info",
        "analysis_year",
        "base_year",
        "detected_changes",
        "financial_context",
        "query_groups",
        "searched_news",
        "evidence_news",
        "evidence_disclosures",
        "report",
        "disclosure_result",
        "metadata",
    ]

    for key in required_top_level_keys:
        assert key in result, f"missing top-level key: {key}"

    # report 필수 key 확인
    required_report_keys = [
        "executive_summary",
        "financial_change_summary",
        "news_evidence_summary",
        "disclosure_evidence_summary",
        "possible_causes",
        "interview_point",
        "limitations",
        "metadata",
    ]

    report = result["report"]

    for key in required_report_keys:
        assert key in report, f"missing report key: {key}"

    # metadata 확인
    metadata = result["metadata"]

    assert metadata["detected_change_count"] > 0
    assert metadata["query_group_count"] > 0
    assert metadata["searched_news_count"] >= 0
    assert metadata["evidence_news_count"] >= 0
    assert metadata["evidence_disclosure_count"] == 0
    assert metadata["disclosure_enabled"] is False

    # searched_news는 include_searched_news=False로 숨겼으므로 빈 리스트가 정상
    assert result["searched_news"] == []
    assert metadata["searched_news_included"] is False

    # disclosure_retriever.py 미구현 상태에서는 빈 리스트가 정상
    assert result["evidence_disclosures"] == []


if __name__ == "__main__":
    test_create_ai_report_e2e()

    ai_input = build_test_ai_input()

    result = create_ai_report(
        ai_input=ai_input,
        vector_store=None,
        max_results_per_query=5,
        max_total_news_results=20,
        max_evidence_news=5,
        include_searched_news=False,
    )

    print("[E2E Test Passed]")
    print("company:", result.get("company_info", {}).get("company_name"))
    print("analysis_year:", result.get("analysis_year"))
    print("searched_news_count:", result.get("metadata", {}).get("searched_news_count"))
    print("evidence_news_count:", result.get("metadata", {}).get("evidence_news_count"))
    print("evidence_disclosure_count:", result.get("metadata", {}).get("evidence_disclosure_count"))

    print("\n[Final Report]")
    print(json.dumps(result.get("report", {}), ensure_ascii=False, indent=2))
