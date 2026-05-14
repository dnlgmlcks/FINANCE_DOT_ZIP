"""
test_report_chat_api_fast.py

이미 생성된 AI 리포트 결과를 챗봇 API에 전달하는 빠른 구조 테스트 파일입니다.

테스트 대상:
1. GET  /api/v1/report/comprehensive/{stock_code}/ai
2. POST /api/v1/report/comprehensive/{stock_code}/chat

목적:
- AI 리포트 생성 체인은 1회만 실행합니다.
- 챗봇 API는 ai_report_result를 받아서 답변만 생성합니다.
- 챗봇 API 내부에서 create_ai_report()가 다시 실행되지 않는지 확인합니다.

실행:
cd backend
python -m tests.test_report_chat_api_fast
"""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_STOCK_CODE = "005930"
DEFAULT_QUESTION = "삼성전자는 2023년에 영업이익이 왜 감소했어?"


def fetch_ai_report(
    stock_code: str = DEFAULT_STOCK_CODE,
    base_url: str = DEFAULT_BASE_URL,
    use_mock_disclosures: bool = True,
    include_searched_news: bool = False,
) -> dict:
    """
    AI 리포트 생성 API를 1회 호출합니다.
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


def post_report_chat_fast(
    ai_report_result: dict,
    stock_code: str = DEFAULT_STOCK_CODE,
    question: str = DEFAULT_QUESTION,
    base_url: str = DEFAULT_BASE_URL,
    use_mock_disclosures: bool = True,
) -> dict:
    """
    이미 생성된 ai_report_result를 챗봇 API에 전달합니다.
    """

    url = f"{base_url.rstrip('/')}/api/v1/report/comprehensive/{stock_code}/chat"

    payload = {
        "question": question,
        "ai_report_result": ai_report_result,
        "use_mock_disclosures": use_mock_disclosures,
        "allow_generate_report": False,
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
        with urlopen(request, timeout=120) as response:
            response_body = response.read().decode("utf-8")
            return json.loads(response_body)

    except HTTPError as error:
        error_body = error.read().decode("utf-8", errors="ignore")
        raise RuntimeError(
            f"챗봇 API 호출 실패: HTTP {error.code} / url={url} / body={error_body}"
        ) from error

    except URLError as error:
        raise RuntimeError(
            "챗봇 API에 연결할 수 없습니다. Django 서버가 실행 중인지 확인하세요. "
            f"url={url}"
        ) from error


def assert_chat_response(response: dict) -> None:
    """
    챗봇 API 응답 구조를 검증합니다.
    """

    assert isinstance(response, dict)
    assert response.get("status") == "success"

    data = response.get("data")

    assert isinstance(data, dict)
    assert data.get("answer")
    assert data.get("question")
    assert isinstance(data.get("used_sources"), list)
    assert isinstance(data.get("metadata"), dict)

    metadata = data["metadata"]

    assert metadata.get("received_ai_report_result") is True
    assert metadata.get("generated_ai_report_inside_chat") is False
    assert metadata.get("chat_context", {}).get("finance_summary_count", 0) > 0


def test_report_chat_api_fast() -> None:
    """
    AI 리포트를 1회 생성한 뒤, 챗봇 API가 그 결과를 재사용하는지 확인합니다.
    """

    base_url = os.getenv("BACKEND_BASE_URL", DEFAULT_BASE_URL)
    stock_code = os.getenv("TEST_STOCK_CODE", DEFAULT_STOCK_CODE)
    question = os.getenv("TEST_CHAT_QUESTION", DEFAULT_QUESTION)

    ai_report_response = fetch_ai_report(
        stock_code=stock_code,
        base_url=base_url,
        use_mock_disclosures=True,
        include_searched_news=False,
    )

    assert ai_report_response.get("status") == "success"

    ai_report_result = ai_report_response["data"]

    chat_response = post_report_chat_fast(
        ai_report_result=ai_report_result,
        stock_code=stock_code,
        question=question,
        base_url=base_url,
        use_mock_disclosures=True,
    )

    assert_chat_response(chat_response)


if __name__ == "__main__":
    base_url = os.getenv("BACKEND_BASE_URL", DEFAULT_BASE_URL)
    stock_code = os.getenv("TEST_STOCK_CODE", DEFAULT_STOCK_CODE)
    question = os.getenv("TEST_CHAT_QUESTION", DEFAULT_QUESTION)

    ai_report_response = fetch_ai_report(
        stock_code=stock_code,
        base_url=base_url,
        use_mock_disclosures=True,
        include_searched_news=False,
    )

    assert ai_report_response.get("status") == "success"

    ai_report_result = ai_report_response["data"]

    chat_response = post_report_chat_fast(
        ai_report_result=ai_report_result,
        stock_code=stock_code,
        question=question,
        base_url=base_url,
        use_mock_disclosures=True,
    )

    assert_chat_response(chat_response)

    data = chat_response["data"]

    print("[Fast Report Chat API Test Passed]")
    print("company:", data.get("company_info", {}).get("company_name"))
    print("stock_code:", data.get("company_info", {}).get("stock_code"))
    print("analysis_year:", data.get("analysis_year"))
    print("question:", data.get("question"))
    print("answer:", data.get("answer"))
    print("used_source_count:", len(data.get("used_sources", [])))
    print("received_ai_report_result:", data.get("metadata", {}).get("received_ai_report_result"))
    print("generated_ai_report_inside_chat:", data.get("metadata", {}).get("generated_ai_report_inside_chat"))
    print("finance_summary_count:", data.get("metadata", {}).get("chat_context", {}).get("finance_summary_count"))

    print("\n[Full Response Data]")
    print(json.dumps(data, ensure_ascii=False, indent=2))
