"""
test_ai_report_with_backend_api.py

실제 백엔드 종합 리포트 API 응답을 사용해
AI 리포트 생성 파이프라인을 테스트하는 통합 테스트 파일입니다.

테스트 흐름:
1. GET /api/v1/report/comprehensive/{stock_code} 호출
2. backend_payload_adapter.py로 API 응답을 ai_input으로 변환
3. create_ai_report(ai_input) 실행
4. 최종 AI 리포트 JSON 구조 확인
5. industry_info / 산업별 분석 가이드 / detected_changes 필터링 결과 확인

주의:
- 백엔드 서버가 먼저 실행되어 있어야 합니다.
- OPENAI_API_KEY, TAVILY_API_KEY가 .env에 설정되어 있어야 합니다.
- Tavily와 OpenAI를 호출하므로 실제 API 비용/사용량이 발생할 수 있습니다.
- disclosure_retriever.py는 아직 미구현이므로 evidence_disclosure_count == 0이 정상입니다.

실행:
cd backend
python -m tests.test_ai_report_with_backend_api

또는:
cd backend
pytest tests/test_ai_report_with_backend_api.py
"""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from src.ai.backend_payload_adapter import build_ai_input_from_backend_response
from src.ai.comprehensive_report_service import create_ai_report


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_STOCK_CODE = "005930"


def fetch_backend_report(
    stock_code: str = DEFAULT_STOCK_CODE,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    """
    백엔드 종합 리포트 API를 호출해 JSON 응답을 반환합니다.
    """

    url = f"{base_url.rstrip('/')}/api/v1/report/comprehensive/{stock_code}"

    try:
        with urlopen(url, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)

    except HTTPError as error:
        raise RuntimeError(
            f"백엔드 API 호출 실패: HTTP {error.code} / url={url}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            "백엔드 API에 연결할 수 없습니다. "
            "서버가 실행 중인지 확인하세요. "
            f"url={url}"
        ) from error


def assert_ai_input_structure(ai_input: dict, stock_code: str) -> None:
    """
    Adapter 변환 결과인 ai_input 구조를 검증합니다.
    """

    assert isinstance(ai_input, dict)

    assert ai_input["company_info"]["stock_code"] == stock_code
    assert ai_input["company_info"].get("company_name")

    assert "industry_info" in ai_input
    assert ai_input["industry_info"].get("industry_group")
    assert ai_input["industry_info"].get("industry_group_name")

    assert ai_input["analysis_year"] is not None
    assert ai_input["base_year"] is not None
    assert ai_input["analysis_year"] > ai_input["base_year"]

    assert len(ai_input.get("finance_summary", [])) > 0
    assert len(ai_input.get("financial_metrics", {})) > 0

    assert len(ai_input.get("detected_changes", [])) > 0
    assert len(ai_input.get("all_detected_changes", [])) >= len(ai_input.get("detected_changes", []))

    assert "adapter_metadata" in ai_input

    adapter_metadata = ai_input["adapter_metadata"]

    assert adapter_metadata["original_detected_change_count"] >= adapter_metadata["selected_detected_change_count"]
    assert adapter_metadata["selected_detected_change_count"] == len(ai_input["detected_changes"])
    assert adapter_metadata["original_detected_change_count"] == len(ai_input["all_detected_changes"])
    assert adapter_metadata["filter_to_primary_changes"] is True

    for change in ai_input["detected_changes"]:
        assert change.get("year") == ai_input["analysis_year"]
        assert change.get("base_year") == ai_input["base_year"]
        assert change.get("metric_key")
        assert change.get("metric_label")
        assert "base_value" in change
        assert "current_value" in change
        assert "signal_type" in change


def assert_final_report_structure(result: dict) -> None:
    """
    create_ai_report() 최종 결과 JSON 구조를 검증합니다.
    """

    assert isinstance(result, dict)

    required_top_level_keys = [
        "company_info",
        "industry_info",
        "analysis_year",
        "base_year",
        "signals",
        "detected_changes",
        "all_detected_changes",
        "financial_context",
        "query_groups",
        "industry_analysis_instruction",
        "searched_news",
        "evidence_news",
        "evidence_disclosures",
        "report",
        "disclosure_result",
        "metadata",
    ]

    for key in required_top_level_keys:
        assert key in result, f"missing top-level key: {key}"

    assert result["industry_info"].get("industry_group")
    assert result["industry_info"].get("industry_group_name")
    assert result["industry_analysis_instruction"]

    report = result["report"]

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

    for key in required_report_keys:
        assert key in report, f"missing report key: {key}"

    metadata = result["metadata"]

    assert metadata["analysis_year"] == result["analysis_year"]
    assert metadata["base_year"] == result["base_year"]

    assert metadata["industry_group"] == result["industry_info"]["industry_group"]
    assert metadata["industry_group_name"] == result["industry_info"]["industry_group_name"]
    assert metadata["industry_instruction_applied"] is True

    assert metadata["detected_change_count"] == len(result["detected_changes"])
    assert metadata["all_detected_change_count"] == len(result["all_detected_changes"])
    assert metadata["all_detected_change_count"] >= metadata["detected_change_count"]

    assert metadata["query_group_count"] > 0
    assert metadata["searched_news_count"] >= 0
    assert metadata["evidence_news_count"] >= 0

    # include_searched_news=False로 실행하므로 최종 응답 본문에는 빈 리스트가 정상입니다.
    assert result["searched_news"] == []
    assert metadata["searched_news_included"] is False

    # 아직 disclosure_retriever.py 미연결 상태이므로 0/False가 정상입니다.
    assert metadata["evidence_disclosure_count"] == 0
    assert metadata["disclosure_enabled"] is False
    assert result["evidence_disclosures"] == []

    report_metadata = report["metadata"]

    assert report_metadata["industry_group"] == result["industry_info"]["industry_group"]
    assert report_metadata["industry_group_name"] == result["industry_info"]["industry_group_name"]
    assert report_metadata["industry_instruction_applied"] is True
    assert report_metadata["disclosure_evidence_count"] == 0


def test_create_ai_report_with_backend_api() -> None:
    """
    실제 백엔드 API 응답 기반으로 AI 리포트 생성까지 성공하는지 확인합니다.
    """

    base_url = os.getenv("BACKEND_BASE_URL", DEFAULT_BASE_URL)
    stock_code = os.getenv("TEST_STOCK_CODE", DEFAULT_STOCK_CODE)

    backend_payload = fetch_backend_report(
        stock_code=stock_code,
        base_url=base_url,
    )

    ai_input = build_ai_input_from_backend_response(backend_payload)

    assert_ai_input_structure(
        ai_input=ai_input,
        stock_code=stock_code,
    )

    result = create_ai_report(
        ai_input=ai_input,
        vector_store=None,
        max_results_per_query=5,
        max_total_news_results=20,
        max_evidence_news=5,
        include_searched_news=False,
    )

    assert_final_report_structure(result)


if __name__ == "__main__":
    base_url = os.getenv("BACKEND_BASE_URL", DEFAULT_BASE_URL)
    stock_code = os.getenv("TEST_STOCK_CODE", DEFAULT_STOCK_CODE)

    backend_payload = fetch_backend_report(
        stock_code=stock_code,
        base_url=base_url,
    )

    ai_input = build_ai_input_from_backend_response(backend_payload)

    assert_ai_input_structure(
        ai_input=ai_input,
        stock_code=stock_code,
    )

    print("[Backend API → AI Input]")
    print("company:", ai_input.get("company_info", {}).get("company_name"))
    print("stock_code:", ai_input.get("company_info", {}).get("stock_code"))
    print("industry_group:", ai_input.get("industry_info", {}).get("industry_group"))
    print("industry_group_name:", ai_input.get("industry_info", {}).get("industry_group_name"))
    print("analysis_year:", ai_input.get("analysis_year"))
    print("base_year:", ai_input.get("base_year"))
    print("finance_summary_count:", len(ai_input.get("finance_summary", [])))
    print("financial_metric_count:", len(ai_input.get("financial_metrics", {})))
    print("detected_change_count:", len(ai_input.get("detected_changes", [])))
    print("all_detected_change_count:", len(ai_input.get("all_detected_changes", [])))
    print("adapter_metadata:", json.dumps(ai_input.get("adapter_metadata", {}), ensure_ascii=False))

    result = create_ai_report(
        ai_input=ai_input,
        vector_store=None,
        max_results_per_query=5,
        max_total_news_results=20,
        max_evidence_news=5,
        include_searched_news=False,
    )

    assert_final_report_structure(result)

    print("\n[Actual API Based AI Report Test Passed]")
    print("company:", result.get("company_info", {}).get("company_name"))
    print("industry_group:", result.get("industry_info", {}).get("industry_group"))
    print("analysis_year:", result.get("analysis_year"))
    print("base_year:", result.get("base_year"))
    print("detected_change_count:", result.get("metadata", {}).get("detected_change_count"))
    print("all_detected_change_count:", result.get("metadata", {}).get("all_detected_change_count"))
    print("searched_news_count:", result.get("metadata", {}).get("searched_news_count"))
    print("evidence_news_count:", result.get("metadata", {}).get("evidence_news_count"))
    print("evidence_disclosure_count:", result.get("metadata", {}).get("evidence_disclosure_count"))
    print("industry_instruction_applied:", result.get("metadata", {}).get("industry_instruction_applied"))

    print("\n[Final Report]")
    print(json.dumps(result.get("report", {}), ensure_ascii=False, indent=2))
