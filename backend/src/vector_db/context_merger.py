"""
[보류] 검색 결과 context formatting 유틸

주의:
- 실제 LLM prompt context 구성은 AI/Agent 파트 담당
- 현재 파일은 추후 연동 필요 시 참고용으로 유지
"""

def merge_documents_as_context(documents):
    if not documents:
        return "관련 근거를 찾을 수 없습니다."

    context_parts = []

    for idx, doc in enumerate(documents, start=1):
        metadata = doc.metadata

        section = f"""
[근거 {idx}]
회사명: {metadata.get("company_name")}
Signal: {metadata.get("signal_code")}
출처: {metadata.get("source")}

내용:
{doc.page_content}
""".strip()

        context_parts.append(section)

    return "\n\n".join(context_parts)