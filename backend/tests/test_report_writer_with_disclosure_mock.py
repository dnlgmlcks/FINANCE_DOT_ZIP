"""
test_report_writer_with_disclosure_mock.py

실제 백엔드 API 응답 + Tavily 뉴스 근거 + 공시 Mock 근거를 사용해
report_writer_chain.py가 공시 정성 근거를 반영한 리포트를 생성하는지 확인하는 테스트 파일입니다.

테스트 흐름:
1. GET /api/v1/report/comprehensive/{stock_code} 호출
2. backend_payload_adapter.py로 ai_input 변환
3. financial_context 생성
4. news_query_builder → news_search_service → news_evidence_filter 실행
5. sample_disclosure_data.py에서 evidence_disclosures Mock 로드
6. report_writer_chain.py의 generate_report() 실행
7. 최종 report에 공시 근거 count와 산업별 분석 가이드가 반영됐는지 확인

주의:
- 백엔드 서버가 먼저 실행되어 있어야 합니다.
- OPENAI_API_KEY, TAVILY_API_KEY가 .env에 설정되어 있어야 합니다.
- disclosure_retriever.py는 아직 미구현 상태이므로 sample_disclosure_data.py의 Mock 데이터를 사용합니다.
- Tavily와 OpenAI를 호출하므로 실제 API 비용/사용량이 발생할 수 있습니다.

실행:
cd backend
python -m tests.test_report_writer_with_disclosure_mock

또는:
cd backend
pytest tests/test_report_writer_with_disclosure_mock.py
"""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from src.ai.backend_payload_adapter import build_ai_input_from_backend_response
from src.ai.financial_context_builder import build_financial_context
from src.ai.industry_analysis_rules import build_industry_analysis_instruction
from src.ai.llm_client import get_llm
from src.ai.news_evidence_filter import filter_evidence
from src.ai.news_query_builder import build_news_queries
from src.ai.news_search_service import search_news_by_query_groups
from src.ai.report_writer_chain import generate_report
from src.ai.sample_disclosure_data import get_sample_evidence_disclosures


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


def build_pipeline_inputs_from_backend_api(
    stock_code: str = DEFAULT_STOCK_CODE,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    """
    실제 API 응답에서 report_writer_chain 테스트에 필요한 중간 산출물을 생성합니다.
    """

    backend_payload = fetch_backend_report(
        stock_code=stock_code,
        base_url=base_url,
    )

    ai_input = build_ai_input_from_backend_response(backend_payload)

    llm = get_llm()

    financial_context = build_financial_context(
        llm=llm,
        ai_input=ai_input,
    )

    industry_info = ai_input.get("industry_info", {}) or {}
    industry_analysis_instruction = build_industry_analysis_instruction(industry_info)

    # financial_context_builder.py가 industry_info를 포함하지 않는 경우에 대비해 보강합니다.
    financial_context["industry_info"] = industry_info
    financial_context["industry_analysis_instruction"] = industry_analysis_instruction

    query_groups = build_news_queries(
        ai_input=ai_input,
        llm=llm,
    )

    searched_news = search_news_by_query_groups(
        query_groups=query_groups,
        max_results_per_query=5,
        max_total_results=20,
    )

    evidence = filter_evidence(
        llm=llm,
        ai_input=ai_input,
        financial_context=financial_context,
        searched_news=searched_news,
        max_evidence=5,
    )

    evidence_disclosures = get_sample_evidence_disclosures(
        stock_code=stock_code,
        year=ai_input.get("analysis_year"),
        max_items=3,
    )

    return {
        "llm": llm,
        "ai_input": ai_input,
        "financial_context": financial_context,
        "industry_info": industry_info,
        "industry_analysis_instruction": industry_analysis_instruction,
        "query_groups": query_groups,
        "searched_news": searched_news,
        "evidence_news": evidence.get("evidence_news", []),
        "evidence_disclosures": evidence_disclosures,
    }


def test_report_writer_with_disclosure_mock() -> None:
    """
    공시 Mock 근거를 포함해 report_writer_chain.py가 정상 리포트를 생성하는지 확인합니다.
    """

    base_url = os.getenv("BACKEND_BASE_URL", DEFAULT_BASE_URL)
    stock_code = os.getenv("TEST_STOCK_CODE", DEFAULT_STOCK_CODE)

    pipeline_inputs = build_pipeline_inputs_from_backend_api(
        stock_code=stock_code,
        base_url=base_url,
    )

    llm = pipeline_inputs["llm"]
    ai_input = pipeline_inputs["ai_input"]
    financial_context = pipeline_inputs["financial_context"]
    industry_info = pipeline_inputs["industry_info"]
    industry_analysis_instruction = pipeline_inputs["industry_analysis_instruction"]
    evidence_news = pipeline_inputs["evidence_news"]
    evidence_disclosures = pipeline_inputs["evidence_disclosures"]

    assert ai_input["company_info"]["stock_code"] == stock_code
    assert ai_input["industry_info"].get("industry_group")
    assert ai_input["analysis_year"] is not None
    assert len(evidence_news) >= 0
    assert len(evidence_disclosures) == 3

    report = generate_report(
        llm=llm,
        financial_context=financial_context,
        evidence_news=evidence_news,
        evidence_disclosures=evidence_disclosures,
        industry_info=industry_info,
        industry_analysis_instruction=industry_analysis_instruction,
    )

    assert isinstance(report, dict)

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

    metadata = report["metadata"]

    assert metadata["news_evidence_count"] == len(evidence_news)
    assert metadata["disclosure_evidence_count"] == len(evidence_disclosures)
    assert metadata["industry_group"] == industry_info.get("industry_group")
    assert metadata["industry_group_name"] == industry_info.get("industry_group_name")
    assert metadata["industry_instruction_applied"] is True

    # 공시 Mock을 넣었으므로 "공시 근거 없음"만 나오는 상태는 아니어야 합니다.
    assert "공시 근거는 없습니다" not in report["disclosure_evidence_summary"]


if __name__ == "__main__":
    base_url = os.getenv("BACKEND_BASE_URL", DEFAULT_BASE_URL)
    stock_code = os.getenv("TEST_STOCK_CODE", DEFAULT_STOCK_CODE)

    pipeline_inputs = build_pipeline_inputs_from_backend_api(
        stock_code=stock_code,
        base_url=base_url,
    )

    llm = pipeline_inputs["llm"]
    ai_input = pipeline_inputs["ai_input"]
    financial_context = pipeline_inputs["financial_context"]
    industry_info = pipeline_inputs["industry_info"]
    industry_analysis_instruction = pipeline_inputs["industry_analysis_instruction"]
    evidence_news = pipeline_inputs["evidence_news"]
    evidence_disclosures = pipeline_inputs["evidence_disclosures"]

    report = generate_report(
        llm=llm,
        financial_context=financial_context,
        evidence_news=evidence_news,
        evidence_disclosures=evidence_disclosures,
        industry_info=industry_info,
        industry_analysis_instruction=industry_analysis_instruction,
    )

    print("[Report Writer With Disclosure Mock Test Passed]")
    print("company:", ai_input.get("company_info", {}).get("company_name"))
    print("stock_code:", ai_input.get("company_info", {}).get("stock_code"))
    print("industry_group:", industry_info.get("industry_group"))
    print("analysis_year:", ai_input.get("analysis_year"))
    print("evidence_news_count:", len(evidence_news))
    print("evidence_disclosure_count:", len(evidence_disclosures))
    print("report_disclosure_evidence_count:", report.get("metadata", {}).get("disclosure_evidence_count"))
    print("industry_instruction_applied:", report.get("metadata", {}).get("industry_instruction_applied"))

    print("\n[Disclosure Evidence Summary]")
    print(report.get("disclosure_evidence_summary"))

    print("\n[Final Report]")
    print(json.dumps(report, ensure_ascii=False, indent=2))
