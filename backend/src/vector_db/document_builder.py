"""
Vector DB document 생성 모듈

역할:
- 뉴스 JSON / 공시 CSV row를 Vector DB 저장용 Document로 변환
- metadata schema 적용
- 뉴스와 공시를 data_type으로 구분
"""

from langchain_core.documents import Document

from src.vector_db.metadata_schema import (
    build_news_metadata,
    build_disclosure_metadata,
)


def _safe_str(value):
    if value is None:
        return ""
    return str(value).strip()


def build_news_document(
    title,
    content,
    stock_code,
    company_name,
    source="news",
    source_url="",
    date="",
    year=None,
    signal_type="unknown",
    signal_code="unknown",
    industry_group="unknown",
):
    title = _safe_str(title)
    content = _safe_str(content)

    text = f"""
[뉴스 제목]
{title}

[뉴스 본문]
{content}
""".strip()

    metadata = build_news_metadata(
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


def build_disclosure_document(
    title,
    content,
    stock_code,
    company_name,
    source="disclosure",
    source_url="",
    date="",
    year=None,
    signal_type="unknown",
    signal_code="unknown",
    industry_group="unknown",
):
    title = _safe_str(title)
    content = _safe_str(content)

    text = f"""
[공시 제목]
{title}

[공시 내용]
{content}
""".strip()

    metadata = build_disclosure_metadata(
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

    if not news_list:
        return documents

    for news in news_list:
        document = build_news_document(
            title=news.get("title", ""),
            content=(
                news.get("content")
                or news.get("text")
                or news.get("body")
                or ""
            ),
            stock_code=news.get("stock_code", ""),
            company_name=(
                news.get("company_name")
                or news.get("company")
                or ""
            ),
            source=news.get("source", "news"),
            source_url=(
                news.get("source_url")
                or news.get("url")
                or ""
            ),
            date=(
                news.get("date")
                or news.get("published_date")
                or ""
            ),
            year=news.get("year"),
            signal_type=news.get("signal_type", "unknown"),
            signal_code=news.get("signal_code", "unknown"),
            industry_group=news.get("industry_group", "unknown"),
        )

        documents.append(document)

    return documents


def _normalize_stock_code(value):
    if value is None:
        return ""

    value = str(value).strip()

    if not value:
        return ""

    # pandas/csv에서 40.0처럼 들어오는 경우 방어
    if value.endswith(".0"):
        value = value[:-2]

    # 숫자 종목코드는 6자리로 보정
    if value.isdigit():
        return value.zfill(6)

    return value


def build_document_from_disclosure_row(row):
    """
    공시 CSV row를 Document로 변환한다.

    현재 공시 CSV 컬럼:
    - stock_code
    - corp_code
    - company_name
    - event_category
    - event_code
    - event_name
    - rcept_date
    - report_url
    - source_api
    - summary
    - details_json
    """
    stock_code = _normalize_stock_code(
        row.get("stock_code")
        or row.get("corp_code")
        or row.get("ticker")
        or row.get("종목코드")
        or ""
    )

    company_name = (
        row.get("company_name")
        or row.get("corp_name")
        or row.get("기업명")
        or row.get("회사명")
        or ""
    )

    event_category = row.get("event_category") or ""
    event_code = row.get("event_code") or ""
    event_name = row.get("event_name") or ""

    title = (
        event_name
        or row.get("title")
        or row.get("report_nm")
        or row.get("event_title")
        or row.get("공시제목")
        or row.get("보고서명")
        or "주요 공시"
    )

    summary = row.get("summary") or ""
    details_json = row.get("details_json") or ""

    content = (
        row.get("content")
        or row.get("text")
        or row.get("event_content")
        or row.get("description")
        or row.get("공시내용")
        or row.get("내용")
        or f"""
이벤트 분류: {event_category}
이벤트 코드: {event_code}
이벤트명: {event_name}

요약:
{summary}

상세 JSON:
{details_json}
""".strip()
    )

    date = (
        row.get("date")
        or row.get("rcept_date")
        or row.get("rcept_dt")
        or row.get("공시일자")
        or row.get("접수일자")
        or ""
    )

    year = row.get("year")
    if year is None and date:
        year = str(date)[:4]

    try:
        year = int(year) if year not in (None, "") else None
    except ValueError:
        year = None

    source_url = (
        row.get("source_url")
        or row.get("report_url")
        or row.get("url")
        or row.get("공시링크")
        or ""
    )

    source_api = row.get("source_api") or "disclosure"

    return build_disclosure_document(
        title=title,
        content=content,
        stock_code=stock_code,
        company_name=company_name,
        source=source_api,
        source_url=source_url,
        date=date,
        year=year,
        signal_type=row.get("signal_type", "unknown"),
        signal_code=row.get("signal_code", "unknown"),
        industry_group=row.get("industry_group", "unknown"),
    )


def build_documents_from_disclosure_rows(rows):
    documents = []

    if not rows:
        return documents

    for row in rows:
        document = build_document_from_disclosure_row(row)
        documents.append(document)

    return documents