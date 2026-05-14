"""
검색 결과 context formatting 유틸

주의:
- 실제 LLM Prompt 구성 및 Report 생성은 AI/Agent 파트 담당
- 본 모듈은 Vector DB 검색 결과를 사람이 읽기 쉬운 문자열로 정리하는 역할만 담당
"""


def _get_metadata_from_result(item):
    if hasattr(item, "metadata"):
        return item.metadata or {}

    if isinstance(item, dict):
        return item.get("metadata", {}) or {}

    return {}


def _get_content_from_result(item):
    if hasattr(item, "page_content"):
        return item.page_content or ""

    if isinstance(item, dict):
        return item.get("content", "") or item.get("page_content", "") or ""

    return ""


def merge_documents_as_context(documents, max_content_length=800):
    """
    Document 또는 retriever.py 결과 dict 리스트를 context 문자열로 변환한다.
    """
    if not documents:
        return "관련 근거를 찾을 수 없습니다."

    context_parts = []

    for idx, item in enumerate(documents, start=1):
        metadata = _get_metadata_from_result(item)
        content = _get_content_from_result(item)

        if max_content_length and len(content) > max_content_length:
            content = content[:max_content_length] + "..."

        section = f"""
[근거 {idx}]
데이터 유형: {metadata.get("data_type")}
회사명: {metadata.get("company_name")}
종목코드: {metadata.get("stock_code")}
연도: {metadata.get("year")}
Signal: {metadata.get("signal_code")}
출처: {metadata.get("source")}
URL: {metadata.get("source_url")}

내용:
{content}
""".strip()

        context_parts.append(section)

    return "\n\n".join(context_parts)