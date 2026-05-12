"""
test_ai_report_with_backend_api.py

실제 백엔드 종합 리포트 API 응답을 사용해
AI 리포트 생성 파이프라인을 테스트하는 통합 테스트 파일입니다.

테스트 흐름:
1. GET /api/v1/report/comprehensive/{stock_code} 호출
2. backend_payload_adapter.py로 API 응답을 ai_input으로 변환
3. create_ai_report(ai_input) 실행
4. 최종 AI 리포트 JSON 구조 확인

주의:
- Django/FastAPI 백엔드 서버가 먼저 실행되어 있어야 합니다.
- OPENAI_API_KEY, TAVILY_API_KEY가 .env에 설정되어 있어야 합니다.
- Tavily와 OpenAI를 호출하므로 실제 API 비용/사용량이 발생할 수 있습니다.

실행:
cd backend
python -m tests.test_ai_report_with_backend_api

또는:
cd backend
pytest tests/test_ai_report_with_backend_api.py
"""

import json
import os
from urllib.error import URLError, HTTPError
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

    assert ai_input["company_info"]["stock_code"] == stock_code
    assert ai_input["analysis_year"] is not None
    assert ai_input["base_year"] is not None
    assert len(ai_input.get("finance_summary", [])) > 0
    assert len(ai_input.get("detected_changes", [])) > 0

    result = create_ai_report(
        ai_input=ai_input,
        vector_store=None,
        max_results_per_query=5,
        max_total_news_results=20,
        max_evidence_news=5,
        include_searched_news=False,
    )

    assert isinstance(result, dict)

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
        "metadata",
    ]

    for key in required_top_level_keys:
        assert key in result, f"missing top-level key: {key}"

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

    assert metadata["detected_change_count"] > 0
    assert metadata["query_group_count"] > 0
    assert metadata["searched_news_count"] >= 0
    assert metadata["evidence_news_count"] >= 0

    # 아직 disclosure_retriever.py 미연결 상태이므로 0이 정상입니다.
    assert metadata["evidence_disclosure_count"] == 0
    assert metadata["disclosure_enabled"] is False


if __name__ == "__main__":
    base_url = os.getenv("BACKEND_BASE_URL", DEFAULT_BASE_URL)
    stock_code = os.getenv("TEST_STOCK_CODE", DEFAULT_STOCK_CODE)

    backend_payload = fetch_backend_report(
        stock_code=stock_code,
        base_url=base_url,
    )

    ai_input = build_ai_input_from_backend_response(backend_payload)

    print("[Backend API → AI Input]")
    print("company:", ai_input.get("company_info", {}).get("company_name"))
    print("stock_code:", ai_input.get("company_info", {}).get("stock_code"))
    print("industry_group:", ai_input.get("industry_info", {}).get("industry_group"))
    print("analysis_year:", ai_input.get("analysis_year"))
    print("base_year:", ai_input.get("base_year"))
    print("finance_summary_count:", len(ai_input.get("finance_summary", [])))
    print("financial_metric_count:", len(ai_input.get("financial_metrics", {})))
    print("detected_change_count:", len(ai_input.get("detected_changes", [])))

    result = create_ai_report(
        ai_input=ai_input,
        vector_store=None,
        max_results_per_query=5,
        max_total_news_results=20,
        max_evidence_news=5,
        include_searched_news=False,
    )

    print("\n[Actual API Based AI Report Test Passed]")
    print("company:", result.get("company_info", {}).get("company_name"))
    print("analysis_year:", result.get("analysis_year"))
    print("base_year:", result.get("base_year"))
    print("searched_news_count:", result.get("metadata", {}).get("searched_news_count"))
    print("evidence_news_count:", result.get("metadata", {}).get("evidence_news_count"))
    print("evidence_disclosure_count:", result.get("metadata", {}).get("evidence_disclosure_count"))

    print("\n[Final Report]")
    print(json.dumps(result.get("report", {}), ensure_ascii=False, indent=2))
