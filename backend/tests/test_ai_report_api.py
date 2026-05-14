"""
test_ai_report_api.py

AI 종합 리포트 1회 생성 API 테스트 파일입니다.

테스트 대상:
GET /api/v1/report/comprehensive/{stock_code}/ai

목적:
- 화면 최초 진입 또는 리포트 생성 버튼 클릭 시 AI 리포트가 1회 생성되는지 확인합니다.
- 생성 결과에 finance_summary, report, evidence_news, evidence_disclosures가 포함되는지 확인합니다.
- 이후 챗봇 API가 이 결과를 재사용할 수 있는지 확인하기 위한 선행 테스트입니다.

실행:
cd backend
python -m tests.test_ai_report_api
"""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_STOCK_CODE = "005930"


def fetch_ai_report(
    stock_code: str = DEFAULT_STOCK_CODE,
    base_url: str = DEFAULT_BASE_URL,
    use_mock_disclosures: bool = True,
    include_searched_news: bool = False,
) -> dict:
    """
    AI 리포트 생성 API를 호출합니다.
    """

    query = urlencode(
        {
            "use_mock_disclosures": str(use_mock_disclosures).lower(),
            "include_searched_news": str(include_searched_news).lower(),
        }
    )

    url = f"{base_url.rstrip('/')}/api/v1/report/comprehensive/{stock_code}/ai?{query}"

    try:
        with urlopen(url, timeout=300) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)

    except HTTPError as error:
        error_body = error.read().decode("utf-8", errors="ignore")
        raise RuntimeError(
            f"AI 리포트 API 호출 실패: HTTP {error.code} / url={url} / body={error_body}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            "AI 리포트 API에 연결할 수 없습니다. Django 서버가 실행 중인지 확인하세요. "
            f"url={url}"
        ) from error


def assert_ai_report_api_response(response: dict) -> None:
    """
    AI 리포트 API 응답 구조를 검증합니다.
    """

    assert isinstance(response, dict)
    assert response.get("status") == "success"

    data = response.get("data")

    assert isinstance(data, dict)

    required_keys = [
        "company_info",
        "industry_info",
        "analysis_year",
        "base_year",
        "finance_summary",
        "signals",
        "detected_changes",
        "report",
        "evidence_news",
        "evidence_disclosures",
        "metadata",
    ]

    for key in required_keys:
        assert key in data, f"missing data key: {key}"

    assert data["company_info"].get("stock_code")
    assert data["company_info"].get("company_name")
    assert data["industry_info"].get("industry_group")
    assert data["analysis_year"] is not None
    assert data["base_year"] is not None
    assert len(data.get("finance_summary", [])) > 0
    assert len(data.get("detected_changes", [])) > 0
    assert isinstance(data.get("report"), dict)
    assert data["report"].get("executive_summary")

    metadata = data.get("metadata", {})

    assert metadata.get("generated_by_endpoint") == "ai_comprehensive_report"
    assert metadata.get("use_mock_disclosures") is True
    assert metadata.get("chat_finance_summary_count") is None or metadata.get("chat_finance_summary_count", 0) >= 0


def test_ai_report_api() -> None:
    """
    실제 AI 리포트 생성 API가 정상 응답하는지 확인합니다.
    """

    base_url = os.getenv("BACKEND_BASE_URL", DEFAULT_BASE_URL)
    stock_code = os.getenv("TEST_STOCK_CODE", DEFAULT_STOCK_CODE)

    response = fetch_ai_report(
        stock_code=stock_code,
        base_url=base_url,
        use_mock_disclosures=True,
        include_searched_news=False,
    )

    assert_ai_report_api_response(response)


if __name__ == "__main__":
    base_url = os.getenv("BACKEND_BASE_URL", DEFAULT_BASE_URL)
    stock_code = os.getenv("TEST_STOCK_CODE", DEFAULT_STOCK_CODE)

    response = fetch_ai_report(
        stock_code=stock_code,
        base_url=base_url,
        use_mock_disclosures=True,
        include_searched_news=False,
    )

    assert_ai_report_api_response(response)

    data = response["data"]

    print("[AI Report API Test Passed]")
    print("company:", data.get("company_info", {}).get("company_name"))
    print("stock_code:", data.get("company_info", {}).get("stock_code"))
    print("industry_group:", data.get("industry_info", {}).get("industry_group"))
    print("analysis_year:", data.get("analysis_year"))
    print("base_year:", data.get("base_year"))
    print("finance_summary_count:", len(data.get("finance_summary", [])))
    print("detected_change_count:", len(data.get("detected_changes", [])))
    print("evidence_news_count:", len(data.get("evidence_news", [])))
    print("evidence_disclosure_count:", len(data.get("evidence_disclosures", [])))
    print("generated_by_endpoint:", data.get("metadata", {}).get("generated_by_endpoint"))

    print("\n[Report]")
    print(json.dumps(data.get("report", {}), ensure_ascii=False, indent=2))
