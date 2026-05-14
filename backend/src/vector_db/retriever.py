"""
Vector DB 검색 테스트 / 인터페이스 모듈

역할:
- Vector DB에 적재된 뉴스/공시 데이터 검색 테스트
- metadata filter 적용 여부 검증
- 작지님 AI/RAG 파트가 사용할 수 있는 최소 검색 인터페이스 제공

주의:
- LangChain Hybrid Chain, Prompt, 최종 Report 생성은 AI/Agent 파트 담당
- 본 모듈은 Vector DB 검색 가능 여부와 metadata filtering 검증까지만 담당
"""

from src.vector_db.metadata_filter import build_metadata_filter
from src.vector_db.vector_store import (
    similarity_search,
    similarity_search_with_score,
)


def format_document_result(doc, score=None):
    metadata = doc.metadata or {}

    result = {
        "content": doc.page_content,
        "metadata": metadata,
    }

    if score is not None:
        result["score"] = score

    return result


def search_similar_documents(
    query,
    stock_code=None,
    company_name=None,
    year=None,
    signal_type=None,
    signal_code=None,
    industry_group=None,
    data_type=None,
    date=None,
    top_k=5,
    with_score=False,
):
    """
    metadata filter 기반 Vector DB 검색 함수.

    예시:
    search_similar_documents(
        query="삼성전자 영업이익 감소 원인",
        stock_code="005930",
        data_type="disclosure",
        top_k=5,
    )
    """
    metadata_filter = build_metadata_filter(
        stock_code=stock_code,
        company_name=company_name,
        year=year,
        signal_type=signal_type,
        signal_code=signal_code,
        industry_group=industry_group,
        data_type=data_type,
        date=date,
    )

    if with_score:
        results = similarity_search_with_score(
            query=query,
            metadata_filter=metadata_filter,
            k=top_k,
        )

        return [
            format_document_result(doc, score)
            for doc, score in results
        ]

    docs = similarity_search(
        query=query,
        metadata_filter=metadata_filter,
        k=top_k,
    )

    return [
        format_document_result(doc)
        for doc in docs
    ]


def search_by_detected_change(
    detected_change,
    top_k=5,
    data_type=None,
    with_score=False,
):
    """
    detected_changes 한 건을 받아 Vector DB 검색.

    detected_change 예시:
    {
        "query_hint": "삼성전자 영업이익 급감 원인",
        "stock_code": "005930",
        "year": 2023,
        "signal_type": "negative",
        "signal_code": "OPERATING_INCOME_DROP_HIGH",
        "industry_group": "tech_equipment"
    }
    """
    if not detected_change:
        return []

    query = (
        detected_change.get("query_hint")
        or " ".join(detected_change.get("search_keywords", []))
        or detected_change.get("source_signal")
        or ""
    )

    return search_similar_documents(
        query=query,
        stock_code=detected_change.get("stock_code"),
        year=detected_change.get("year"),
        signal_type=detected_change.get("signal_type"),
        signal_code=detected_change.get("signal_code"),
        industry_group=detected_change.get("industry_group"),
        data_type=data_type,
        top_k=top_k,
        with_score=with_score,
    )


def print_search_results(results):
    if not results:
        print("검색 결과가 없습니다.")
        return

    for index, item in enumerate(results, start=1):
        metadata = item.get("metadata", {})
        content = item.get("content", "")
        score = item.get("score")

        print("=" * 80)
        print(f"[검색 결과 {index}]")

        if score is not None:
            print(f"score: {score}")

        print("data_type:", metadata.get("data_type"))
        print("stock_code:", metadata.get("stock_code"))
        print("company_name:", metadata.get("company_name"))
        print("year:", metadata.get("year"))
        print("signal_type:", metadata.get("signal_type"))
        print("signal_code:", metadata.get("signal_code"))
        print("industry_group:", metadata.get("industry_group"))
        print("source:", metadata.get("source"))
        print("source_url:", metadata.get("source_url"))
        print("-" * 80)
        print(content[:500])


if __name__ == "__main__":
    results = search_similar_documents(
        query="합병 결정 공시",
        stock_code="091700",
        data_type="disclosure",
        top_k=5,
        with_score=True,
    )

    print_search_results(results)