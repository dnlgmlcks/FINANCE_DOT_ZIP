"""
test_report_chat_api.py

Django DRF 챗봇 API 연결 테스트 파일입니다.

테스트 대상:
POST /api/v1/report/comprehensive/{stock_code}/chat

테스트 흐름:
1. Django 서버가 실행 중인지 확인합니다.
2. 챗봇 API에 question을 POST로 전달합니다.
3. 응답 status가 success인지 확인합니다.
4. data.answer, data.used_sources, data.metadata가 정상 반환되는지 확인합니다.

주의:
- 백엔드 서버가 먼저 실행되어 있어야 합니다.
- OPENAI_API_KEY, TAVILY_API_KEY가 .env에 설정되어 있어야 합니다.
- use_mock_disclosures=true로 보내면 Vector DB 없이도 공시 Mock 근거를 포함해 테스트할 수 있습니다.
- OpenAI/Tavily 호출이 포함되므로 실제 API 비용/사용량이 발생할 수 있습니다.

실행:
cd backend
python -m tests.test_report_chat_api

또는:
cd backend
pytest tests/test_report_chat_api.py
"""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_STOCK_CODE = "005930"
DEFAULT_QUESTION = "삼성전자는 2023년에 영업이익이 왜 감소했어?"


def post_report_chat(
    stock_code: str = DEFAULT_STOCK_CODE,
    question: str = DEFAULT_QUESTION,
    base_url: str = DEFAULT_BASE_URL,
    use_mock_disclosures: bool = True,
) -> dict:
    """
    챗봇 API에 POST 요청을 보내고 JSON 응답을 반환합니다.
    """

    url = f"{base_url.rstrip('/')}/api/v1/report/comprehensive/{stock_code}/chat"

    payload = {
        "question": question,
        "use_mock_disclosures": use_mock_disclosures,
    }

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    request = Request(
        url=url,
        data=body,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=300) as response:
            response_body = response.read().decode("utf-8")
            return json.loads(response_body)

    except HTTPError as error:
        error_body = error.read().decode("utf-8", errors="ignore")
        raise RuntimeError(
            f"챗봇 API 호출 실패: HTTP {error.code} / url={url} / body={error_body}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            "챗봇 API에 연결할 수 없습니다. "
            "Django 서버가 실행 중인지 확인하세요. "
            f"url={url}"
        ) from error


def assert_report_chat_api_response(response: dict) -> None:
    """
    챗봇 API 응답 구조를 검증합니다.
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
        "question",
        "answer",
        "used_sources",
        "limitations",
        "metadata",
    ]

    for key in required_keys:
        assert key in data, f"missing response data key: {key}"

    assert data["company_info"].get("stock_code")
    assert data["company_info"].get("company_name")
    assert data["industry_info"].get("industry_group")
    assert data["analysis_year"] is not None
    assert data["base_year"] is not None
    assert data["question"]
    assert data["answer"]
    assert isinstance(data["used_sources"], list)
    assert data["limitations"]
    assert isinstance(data["metadata"], dict)

    assert data["metadata"].get("source") in {"llm", "fallback", "rule_based"}
    assert "chat_context" in data["metadata"]
    assert "ai_report" in data["metadata"]


def test_report_chat_api() -> None:
    """
    실제 Django 챗봇 API가 정상 응답하는지 확인합니다.
    """

    base_url = os.getenv("BACKEND_BASE_URL", DEFAULT_BASE_URL)
    stock_code = os.getenv("TEST_STOCK_CODE", DEFAULT_STOCK_CODE)
    question = os.getenv("TEST_CHAT_QUESTION", DEFAULT_QUESTION)

    response = post_report_chat(
        stock_code=stock_code,
        question=question,
        base_url=base_url,
        use_mock_disclosures=True,
    )

    assert_report_chat_api_response(response)


if __name__ == "__main__":
    base_url = os.getenv("BACKEND_BASE_URL", DEFAULT_BASE_URL)
    stock_code = os.getenv("TEST_STOCK_CODE", DEFAULT_STOCK_CODE)
    question = os.getenv("TEST_CHAT_QUESTION", DEFAULT_QUESTION)

    response = post_report_chat(
        stock_code=stock_code,
        question=question,
        base_url=base_url,
        use_mock_disclosures=True,
    )

    assert_report_chat_api_response(response)

    data = response["data"]

    print("[Report Chat API Test Passed]")
    print("company:", data.get("company_info", {}).get("company_name"))
    print("stock_code:", data.get("company_info", {}).get("stock_code"))
    print("industry_group:", data.get("industry_info", {}).get("industry_group"))
    print("analysis_year:", data.get("analysis_year"))
    print("question:", data.get("question"))
    print("answer:", data.get("answer"))
    print("used_source_count:", len(data.get("used_sources", [])))
    print("use_mock_disclosures:", data.get("metadata", {}).get("use_mock_disclosures"))

    print("\n[Full Response Data]")
    print(json.dumps(data, ensure_ascii=False, indent=2))
