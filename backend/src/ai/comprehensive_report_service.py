"""
comprehensive_report_service.py

AI 재무 분석 리포트 파이프라인을 하나로 연결하는 상위 서비스 모듈입니다.

현재 연결된 흐름:
1. Backend/Data 파트 또는 sample_report_data.py에서 ai_input을 받습니다.
2. llm_client.py에서 공통 LLM 객체를 가져옵니다.
3. financial_context_builder.py로 재무 문맥을 생성합니다.
4. industry_analysis_rules.py로 업종별 분석 가이드를 생성합니다.
5. news_query_builder.py로 뉴스 검색 query_groups를 생성합니다.
6. news_search_service.py로 Tavily 뉴스 후보를 수집합니다.
7. news_evidence_filter.py로 리포트 근거로 사용할 뉴스만 선별합니다.
8. report_writer_chain.py로 최종 리포트 JSON을 생성합니다.
9. 백엔드/프론트 연동용 최종 AI 리포트 JSON을 반환합니다.

주의:
- disclosure_retriever.py는 아직 구현되지 않았으므로 기본적으로 공시 RAG 검색은 수행하지 않습니다.
- 나중에 disclosure_retriever.py가 구현되면 vector_store를 전달하거나 retrieve_disclosure_context()를 연결하면 됩니다.
- 이 모듈은 화면 출력용이 아니라, 백엔드/프론트에 전달할 최종 구조화 JSON을 만드는 역할입니다.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import time

from src.ai.financial_context_builder import build_financial_context
from src.ai.industry_analysis_rules import build_industry_analysis_instruction
from src.ai.llm_client import get_llm
from src.ai.news_evidence_filter import filter_evidence
from src.ai.news_query_builder import build_news_queries
from src.ai.news_search_service import search_news_by_query_groups
from src.ai.report_writer_chain import generate_report


# ---------------------------------------------------------------------
# 1. 공통 유틸 함수
# ---------------------------------------------------------------------

def get_model_name(llm: Any) -> str:
    """
    ChatOpenAI 객체에서 모델명을 추출합니다.
    """

    return (
        getattr(llm, "model_name", None)
        or getattr(llm, "model", None)
        or "unknown"
    )


def get_company_info(ai_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    ai_input에서 기업 정보를 추출합니다.
    """

    company_info = ai_input.get("company_info", {}) or {}

    return {
        "stock_code": company_info.get("stock_code", ""),
        "company_name": company_info.get("company_name", ""),
        "induty_code": company_info.get("induty_code", ""),
    }


def get_industry_info(ai_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    ai_input에서 업종 정보를 추출합니다.
    """

    return ai_input.get("industry_info", {}) or {}


def get_detected_changes(ai_input: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    ai_input에서 AI 리포트 생성용 detected_changes를 추출합니다.
    """

    return ai_input.get("detected_changes", []) or []


def get_all_detected_changes(ai_input: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    ai_input에서 원본 전체 detected_changes를 추출합니다.

    backend_payload_adapter.py v2에서는:
    - detected_changes: AI 뉴스 검색/리포트 생성용 핵심 변동
    - all_detected_changes: API에서 받은 전체 변동
    """

    return ai_input.get("all_detected_changes", []) or get_detected_changes(ai_input)


def build_empty_disclosure_result() -> Dict[str, Any]:
    """
    disclosure_retriever.py가 아직 연결되지 않은 경우 사용할 빈 공시 근거 결과입니다.
    """

    return {
        "evidence_disclosures": [],
        "disclosure_context": None,
        "metadata": {
            "enabled": False,
            "reason": "disclosure_retriever.py is not implemented or vector_store is not provided.",
            "evidence_disclosure_count": 0,
        },
    }


def log_step_time(step_name: str, start_time: float, extra: str = "") -> None:
    elapsed = time.perf_counter() - start_time
    suffix = f" | {extra}" if extra else ""
    print(f"[AI_PIPELINE_TIME] {step_name}: {elapsed:.2f}s{suffix}")


# ---------------------------------------------------------------------
# 2. 최종 JSON 조립
# ---------------------------------------------------------------------

def build_final_report_json(
    ai_input: Dict[str, Any],
    financial_context: Dict[str, Any],
    query_groups: List[Dict[str, Any]],
    searched_news: List[Dict[str, Any]],
    evidence: Dict[str, Any],
    report: Dict[str, Any],
    disclosure_result: Optional[Dict[str, Any]] = None,
    model_name: str = "unknown",
    include_searched_news: bool = True,
    industry_analysis_instruction: Optional[str] = None,
) -> Dict[str, Any]:
    """
    각 Chain의 결과를 백엔드/프론트에서 사용하기 좋은 최종 JSON으로 조립합니다.
    """

    disclosure_result = disclosure_result or build_empty_disclosure_result()

    evidence_news = evidence.get("evidence_news", []) or []
    evidence_disclosures = evidence.get("evidence_disclosures", []) or []

    searched_news_for_output = searched_news if include_searched_news else []
    industry_info = get_industry_info(ai_input)

    return {
        "company_info": get_company_info(ai_input),
        "industry_info": industry_info,
        "analysis_year": ai_input.get("analysis_year"),
        "base_year": ai_input.get("base_year"),

        # Data/PM 파트가 넘겨준 전체 신호 및 AI 검색용 핵심 변동
        "signals": ai_input.get("signals", []) or [],
        "detected_changes": get_detected_changes(ai_input),
        "all_detected_changes": get_all_detected_changes(ai_input),

        # AI 파트 중간 산출물
        "financial_context": financial_context,
        "query_groups": query_groups,
        "industry_analysis_instruction": industry_analysis_instruction or "",

        # 뉴스 후보 수집 결과
        "searched_news": searched_news_for_output,

        # 리포트 근거
        "evidence_news": evidence_news,
        "evidence_disclosures": evidence_disclosures,

        # 최종 리포트 본문
        "report": report,

        # 공시 RAG 관련 정보
        "disclosure_result": disclosure_result,

        # 전체 파이프라인 메타데이터
        "metadata": {
            "model": model_name,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "analysis_year": ai_input.get("analysis_year"),
            "base_year": ai_input.get("base_year"),
            "industry_group": industry_info.get("industry_group"),
            "industry_group_name": industry_info.get("industry_group_name"),
            "industry_instruction_applied": bool(industry_analysis_instruction),
            "detected_change_count": len(get_detected_changes(ai_input)),
            "all_detected_change_count": len(get_all_detected_changes(ai_input)),
            "query_group_count": len(query_groups),
            "searched_news_count": len(searched_news),
            "searched_news_included": include_searched_news,
            "evidence_news_count": len(evidence_news),
            "evidence_disclosure_count": len(evidence_disclosures),
            "financial_context_source": financial_context.get("source"),
            "evidence_source": (evidence.get("metadata", {}) or {}).get("source"),
            "report_source": report.get("source"),
            "disclosure_enabled": bool(
                (disclosure_result.get("metadata", {}) or {}).get("enabled")
            ),
            "adapter_metadata": ai_input.get("adapter_metadata", {}),
        },
    }


# ---------------------------------------------------------------------
# 3. 공시 RAG 연결 자리
# ---------------------------------------------------------------------

def try_retrieve_disclosure_context(
    ai_input: Dict[str, Any],
    vector_store: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    disclosure_retriever.py가 구현된 뒤 연결할 자리입니다.

    현재는 vector_store가 전달되어도 disclosure_retriever.py가 안정적으로 구현되었다는 보장이 없으므로,
    기본적으로 빈 공시 결과를 반환합니다.

    나중에 disclosure_retriever.py 구현 후 아래처럼 교체하면 됩니다.

    from src.ai.disclosure_retriever import retrieve_disclosure_context

    disclosure_context = retrieve_disclosure_context(
        ai_input=ai_input,
        vector_store=vector_store,
    )

    return {
        "evidence_disclosures": disclosure_context.get("evidence_disclosures", []),
        "disclosure_context": disclosure_context,
        "metadata": {
            "enabled": True,
            "evidence_disclosure_count": len(disclosure_context.get("evidence_disclosures", [])),
        },
    }
    """

    return build_empty_disclosure_result()


# ---------------------------------------------------------------------
# 4. 대표 실행 함수
# ---------------------------------------------------------------------

def create_ai_report(
    ai_input: Dict[str, Any],
    vector_store: Optional[Any] = None,
    max_results_per_query: int = 5,
    max_total_news_results: int = 30,
    max_evidence_news: int = 5,
    include_searched_news: bool = True,
) -> Dict[str, Any]:
    """
    전체 AI 리포트 파이프라인을 실행합니다.

    Args:
        ai_input: Backend/Data 파트에서 전달한 AI 입력 데이터
        vector_store: 공시/사업보고서 Vector DB 또는 retriever 객체. 현재는 optional.
        max_results_per_query: Tavily query 하나당 최대 검색 결과 수
        max_total_news_results: 전체 뉴스 후보 최대 개수
        max_evidence_news: 최종 리포트 근거 뉴스 최대 개수
        include_searched_news: 최종 JSON에 searched_news 전체를 포함할지 여부

    Returns:
        최종 AI 리포트 JSON
    """

    pipeline_start = time.perf_counter()

    step_start = time.perf_counter()
    llm = get_llm()
    model_name = get_model_name(llm)
    log_step_time("get_llm", step_start, f"model={model_name}")

    industry_info = get_industry_info(ai_input)
    industry_analysis_instruction = build_industry_analysis_instruction(industry_info)

    # 1. 재무 문맥 생성
    step_start = time.perf_counter()
    financial_context = build_financial_context(
        llm=llm,
        ai_input=ai_input,
    )
    log_step_time("financial_context_builder", step_start)

    # financial_context_builder.py가 industry_info를 포함하지 않는 경우에 대비해 보강합니다.
    financial_context["industry_info"] = industry_info
    financial_context["industry_analysis_instruction"] = industry_analysis_instruction

    # 2. 공시 RAG 검색
    # 현재는 disclosure_retriever.py 미구현 상태이므로 빈 결과가 반환됩니다.
    step_start = time.perf_counter()
    disclosure_result = try_retrieve_disclosure_context(
        ai_input=ai_input,
        vector_store=vector_store,
    )
    log_step_time(
        "disclosure_retriever",
        step_start,
        f"enabled={(disclosure_result.get('metadata', {}) or {}).get('enabled')}"
    )

    # 3. 뉴스 검색 query 생성
    step_start = time.perf_counter()
    query_groups = build_news_queries(
        ai_input=ai_input,
        llm=llm,
    )

    query_groups = query_groups[:2]
    log_step_time("news_query_builder", step_start, f"query_group_count={len(query_groups)}")

    # 4. Tavily 뉴스 후보 수집
    step_start = time.perf_counter()
    searched_news = search_news_by_query_groups(
        query_groups=query_groups,
        max_results_per_query=max_results_per_query,
        max_total_results=max_total_news_results,
    )
    log_step_time("news_search_service", step_start, f"searched_news_count={len(searched_news)}")

    # 5. 뉴스 근거 선별
    step_start = time.perf_counter()
    evidence = filter_evidence(
        llm=llm,
        ai_input=ai_input,
        financial_context=financial_context,
        searched_news=searched_news,
        disclosure_context=disclosure_result.get("disclosure_context"),
        max_evidence=max_evidence_news,
    )
    log_step_time(
        "news_evidence_filter",
        step_start,
        f"evidence_news_count={len(evidence.get('evidence_news', []))}"
    )

    # disclosure_retriever.py가 붙기 전까지는 빈 리스트 유지
    evidence["evidence_disclosures"] = disclosure_result.get("evidence_disclosures", [])

    # 6. 최종 리포트 생성
    step_start = time.perf_counter()
    report = generate_report(
        llm=llm,
        financial_context=financial_context,
        evidence_news=evidence.get("evidence_news", []),
        evidence_disclosures=evidence.get("evidence_disclosures", []),
        industry_info=industry_info,
        industry_analysis_instruction=industry_analysis_instruction,
    )
    log_step_time("report_writer_chain", step_start)

    # 7. 최종 JSON 조립
    step_start = time.perf_counter()
    final_json = build_final_report_json(
        ai_input=ai_input,
        financial_context=financial_context,
        query_groups=query_groups,
        searched_news=searched_news,
        evidence=evidence,
        report=report,
        disclosure_result=disclosure_result,
        model_name=model_name,
        include_searched_news=include_searched_news,
        industry_analysis_instruction=industry_analysis_instruction,
    )
    log_step_time("build_final_report_json", step_start)

    log_step_time("TOTAL_create_ai_report", pipeline_start)

    return final_json


def run_ai_report_pipeline(
    ai_input: Dict[str, Any],
    vector_store: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    create_ai_report()의 alias 함수입니다.
    """

    return create_ai_report(
        ai_input=ai_input,
        vector_store=vector_store,
    )


# ---------------------------------------------------------------------
# 5. 단독 실행 테스트
# ---------------------------------------------------------------------

if __name__ == "__main__":
    try:
        from src.ai.sample_report_data import get_sample_ai_input
    except ModuleNotFoundError:
        from sample_report_data import get_sample_ai_input

    sample_ai_input = get_sample_ai_input(case="warning")

    # 테스트용으로 실제 뉴스 검색이 가능한 기업명을 사용합니다.
    # 현재 재무 수치는 Mock 데이터이므로 최종 발표용 샘플로 쓰기 전에는 실제 재무 데이터와 맞춰야 합니다.
    sample_ai_input["company_info"]["company_name"] = "삼성전자"
    sample_ai_input["company_info"]["stock_code"] = "005930"
    sample_ai_input["industry_info"] = {
        "industry_group": "tech_equipment",
        "industry_group_name": "기술 및 장치 산업",
    }
    sample_ai_input["analysis_year"] = 2023
    sample_ai_input["base_year"] = 2022

    for change in sample_ai_input.get("detected_changes", []):
        change["year"] = 2023
        change["base_year"] = 2022

    result = create_ai_report(
        ai_input=sample_ai_input,
        vector_store=None,
        max_results_per_query=3,
        max_total_news_results=10,
        max_evidence_news=3,
        include_searched_news=False,
    )

    print("[Comprehensive Report Service Test]")
    print("company:", result.get("company_info", {}).get("company_name"))
    print("industry_group:", result.get("industry_info", {}).get("industry_group"))
    print("analysis_year:", result.get("analysis_year"))
    print("detected_change_count:", result.get("metadata", {}).get("detected_change_count"))
    print("searched_news_count:", result.get("metadata", {}).get("searched_news_count"))
    print("searched_news_included:", result.get("metadata", {}).get("searched_news_included"))
    print("evidence_news_count:", result.get("metadata", {}).get("evidence_news_count"))
    print("evidence_disclosure_count:", result.get("metadata", {}).get("evidence_disclosure_count"))
    print("industry_instruction_applied:", result.get("metadata", {}).get("industry_instruction_applied"))

    print("\n[Final AI Report JSON]")
    print(json.dumps(result, ensure_ascii=False, indent=2))
