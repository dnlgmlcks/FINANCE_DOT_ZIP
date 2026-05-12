"""
AI 파트 연동용 retrieval payload 생성 모듈

주의:
- 실제 Vector DB 검색 실행은 AI/Agent 파트에서 담당
- 본 모듈은 detected_changes 기반 query/filter payload 생성만 담당
- LangChain Retriever, Pinecone similarity_search, LLM context 생성은 직접 수행하지 않음
"""

from src.vector_db.metadata_filter import (
    build_filter_from_detected_change,
    build_relaxed_filter_from_detected_change,
)


def build_retrieval_query(detected_change):
    if not detected_change:
        return ""

    query_hint = detected_change.get("query_hint")
    if query_hint:
        return query_hint

    company_name = detected_change.get("company_name", "")
    source_signal = detected_change.get("source_signal", "")
    metric_label = detected_change.get("metric_label", "")

    return f"{company_name} {metric_label} {source_signal} 원인".strip()


def build_retrieval_payload(detected_change, top_k=5):
    query = build_retrieval_query(detected_change)
    metadata_filter = build_filter_from_detected_change(detected_change)

    return {
        "query": query,
        "filter": metadata_filter,
        "top_k": top_k,
    }


def build_relaxed_retrieval_payload(detected_change, top_k=5):
    query = build_retrieval_query(detected_change)
    metadata_filter = build_relaxed_filter_from_detected_change(detected_change)

    return {
        "query": query,
        "filter": metadata_filter,
        "top_k": top_k,
    }


def build_retrieval_payloads_from_detected_changes(
    detected_changes,
    top_k=5,
):
    payloads = []

    if not detected_changes:
        return payloads

    for detected_change in detected_changes:
        payloads.append(
            build_retrieval_payload(
                detected_change,
                top_k=top_k,
            )
        )

    return payloads