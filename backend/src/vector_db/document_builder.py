"""
Vector DB document 생성 모듈

역할:
- 뉴스/공시 원문을 Vector DB 저장용 document 형태로 변환
- metadata schema 적용
- chunk 단위 document 생성
"""

from langchain_core.documents import Document

from src.vector_db.metadata_schema import build_base_metadata


def build_news_document(
    title,
    content,
    stock_code,
    company_name,
    signal_type,
    signal_code,
    source,
    source_url="",
    year=None,
    industry_group="unknown",
    date="",
):
    text = f"""
[제목]
{title}

[본문]
{content}
""".strip()

    metadata = build_base_metadata(
        stock_code=stock_code,
        company_name=company_name,
        source=source,
        source_url=source_url,
        date=date,
        year=year,
        signal_type=signal_type,
        signal_code=signal_code,
        industry_group=industry_group,
    )

    return Document(
        page_content=text,
        metadata=metadata,
    )


def build_documents_from_news_list(news_list):
    documents = []

    for news in news_list:
        document = build_news_document(
            title=news.get("title", ""),
            content=news.get("content", ""),
            stock_code=news.get("stock_code"),
            company_name=news.get("company_name"),
            signal_type=news.get("signal_type"),
            signal_code=news.get("signal_code"),
            source=news.get("source", "news"),
            source_url=news.get("source_url", ""),
            year=news.get("year"),
            industry_group=news.get("industry_group", "unknown"),
            date=news.get("date", ""),
        )

        documents.append(document)

    return documents