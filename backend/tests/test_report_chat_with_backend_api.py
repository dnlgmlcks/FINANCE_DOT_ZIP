"""
test_report_chat_with_backend_api.py

실제 백엔드 API 응답 기반으로 AI 리포트를 생성한 뒤,
그 리포트와 근거 데이터를 사용해 리포트 기반 Q&A 챗봇 답변까지 테스트하는 E2E 파일입니다.

테스트 흐름:
1. GET /api/v1/report/comprehensive/{stock_code} 호출
2. backend_payload_adapter.py로 ai_input 변환
3. create_ai_report(ai_input) 실행
4. sample_disclosure_data.py의 공시 Mock 근거를 최종 결과에 주입
5. chat_context_builder.py로 챗봇 context 생성
6. report_chat_chain.py로 사용자 질문에 대한 답변 생성
7. 답변 JSON 구조와 used_sources를 검증

주의:
- 백엔드 서버가 먼저 실행되어 있어야 합니다.
- OPENAI_API_KEY, TAVILY_API_KEY가 .env에 설정되어 있어야 합니다.
- Tavily와 OpenAI를 호출하므로 실제 API 비용/사용량이 발생할 수 있습니다.
- disclosure_retriever.py는 아직 미구현이므로 공시 근거는 sample_disclosure_data.py의 Mock을 사용합니다.

실행:
cd backend
python -m tests.test_report_chat_with_backend_api

또는:
cd backend
pytest tests/test_report_chat_with_backend_api.py
"""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from src.ai.backend_payload_adapter import build_ai_input_from_backend_response
from src.ai.chat_context_builder import build_chat_context
from src.ai.comprehensive_report_service import create_ai_report
from src.ai.llm_client import get_llm
from src.ai.report_chat_chain import answer_report_question
from src.ai.sample_disclosure_data import get_sample_evidence_disclosures


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_STOCK_CODE = "005930"

DEFAULT_QUESTIONS = [
    "삼성전자는 2023년에 영업이익이 왜 감소했어?",
    "공시 근거에서는 어떤 내용이 언급돼?",
    "뉴스 근거와 공시 근거를 나눠서 설명해줘.",
]


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


def build_ai_report_result_with_mock_disclosures(
    stock_code: str = DEFAULT_STOCK_CODE,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    """
    실제 백엔드 API 기반 AI 리포트를 생성한 뒤,
    공시 Mock evidence_disclosures를 주입한 결과를 반환합니다.
    """

    backend_payload = fetch_backend_report(
        stock_code=stock_code,
        base_url=base_url,
    )

    ai_input = build_ai_input_from_backend_response(backend_payload)

    ai_report_result = create_ai_report(
        ai_input=ai_input,
        vector_store=None,
        max_results_per_query=5,
        max_total_news_results=20,
        max_evidence_news=5,
        include_searched_news=False,
    )

    evidence_disclosures = get_sample_evidence_disclosures(
        stock_code=stock_code,
        year=ai_report_result.get("analysis_year"),
        max_items=3,
    )

    # disclosure_retriever.py가 붙기 전까지는 Mock 공시 근거를 주입해 챗봇 context를 테스트합니다.
    ai_report_result["evidence_disclosures"] = evidence_disclosures

    # report metadata도 테스트 편의를 위해 보강합니다.
    report = ai_report_result.get("report", {}) or {}
    report_metadata = report.get("metadata", {}) or {}
    report_metadata["disclosure_evidence_count"] = len(evidence_disclosures)
    report["metadata"] = report_metadata
    ai_report_result["report"] = report

    metadata = ai_report_result.get("metadata", {}) or {}
    metadata["evidence_disclosure_count"] = len(evidence_disclosures)
    ai_report_result["metadata"] = metadata

    disclosure_result = ai_report_result.get("disclosure_result", {}) or {}
    disclosure_result["evidence_disclosures"] = evidence_disclosures
    disclosure_result["metadata"] = {
        **(disclosure_result.get("metadata", {}) or {}),
        "enabled": False,
        "source": "mock_disclosure",
        "evidence_disclosure_count": len(evidence_disclosures),
        "reason": "disclosure_retriever.py is not implemented. Mock disclosures are injected for chat test.",
    }
    ai_report_result["disclosure_result"] = disclosure_result

    return ai_report_result


def assert_chat_context_structure(chat_context: dict) -> None:
    """
    build_chat_context() 결과 구조를 검증합니다.
    """

    assert isinstance(chat_context, dict)

    required_keys = [
        "company",
        "report",
        "finance_summary",
        "signals",
        "detected_changes",
        "evidence_news",
        "evidence_disclosures",
        "context_text",
        "metadata",
    ]

    for key in required_keys:
        assert key in chat_context, f"missing chat_context key: {key}"

    assert chat_context["company"].get("company_name")
    assert chat_context["company"].get("stock_code")
    assert chat_context["company"].get("analysis_year") is not None

    assert chat_context["report"].get("executive_summary")
    assert chat_context["metadata"]["has_report"] is True

    assert chat_context["metadata"]["news_evidence_count"] >= 0
    assert chat_context["metadata"]["disclosure_evidence_count"] == len(chat_context["evidence_disclosures"])
    assert chat_context["metadata"]["disclosure_evidence_count"] > 0

    assert chat_context["context_text"]
    assert "[기업 정보]" in chat_context["context_text"]
    assert "[최종 AI 리포트]" in chat_context["context_text"]
    assert "[뉴스 근거]" in chat_context["context_text"]
    assert "[공시/사업보고서 근거]" in chat_context["context_text"]


def assert_chat_answer_structure(answer: dict) -> None:
    """
    report_chat_chain.py 답변 JSON 구조를 검증합니다.
    """

    assert isinstance(answer, dict)

    required_keys = [
        "answer",
        "used_sources",
        "limitations",
        "metadata",
    ]

    for key in required_keys:
        assert key in answer, f"missing answer key: {key}"

    assert answer["answer"]
    assert isinstance(answer["used_sources"], list)
    assert answer["limitations"]

    metadata = answer["metadata"]

    assert metadata["source"] in {"llm", "fallback", "rule_based"}
    assert metadata.get("generated_at")


def test_report_chat_with_backend_api() -> None:
    """
    실제 API 기반 AI 리포트와 공시 Mock 근거를 사용해 챗봇 답변까지 생성되는지 확인합니다.
    """

    base_url = os.getenv("BACKEND_BASE_URL", DEFAULT_BASE_URL)
    stock_code = os.getenv("TEST_STOCK_CODE", DEFAULT_STOCK_CODE)

    ai_report_result = build_ai_report_result_with_mock_disclosures(
        stock_code=stock_code,
        base_url=base_url,
    )

    chat_context = build_chat_context(ai_report_result)

    assert_chat_context_structure(chat_context)

    llm = get_llm()

    question = DEFAULT_QUESTIONS[0]

    answer = answer_report_question(
        llm=llm,
        question=question,
        chat_context=chat_context,
    )

    assert_chat_answer_structure(answer)

    assert answer["metadata"].get("question") == question

    # 적어도 리포트, 뉴스, 공시 중 일부 근거를 사용하도록 유도합니다.
    assert answer["metadata"].get("available_source_count", 0) >= 1


if __name__ == "__main__":
    base_url = os.getenv("BACKEND_BASE_URL", DEFAULT_BASE_URL)
    stock_code = os.getenv("TEST_STOCK_CODE", DEFAULT_STOCK_CODE)

    ai_report_result = build_ai_report_result_with_mock_disclosures(
        stock_code=stock_code,
        base_url=base_url,
    )

    chat_context = build_chat_context(ai_report_result)

    assert_chat_context_structure(chat_context)

    llm = get_llm()

    print("[Report Chat With Backend API Test]")
    print("company:", chat_context.get("company", {}).get("company_name"))
    print("stock_code:", chat_context.get("company", {}).get("stock_code"))
    print("analysis_year:", chat_context.get("company", {}).get("analysis_year"))
    print("news_evidence_count:", chat_context.get("metadata", {}).get("news_evidence_count"))
    print("disclosure_evidence_count:", chat_context.get("metadata", {}).get("disclosure_evidence_count"))
    print("detected_change_count:", chat_context.get("metadata", {}).get("detected_change_count"))

    print("\n[Questions & Answers]")

    for question in DEFAULT_QUESTIONS:
        answer = answer_report_question(
            llm=llm,
            question=question,
            chat_context=chat_context,
        )

        assert_chat_answer_structure(answer)

        print("\nQuestion:", question)
        print(json.dumps(answer, ensure_ascii=False, indent=2))
