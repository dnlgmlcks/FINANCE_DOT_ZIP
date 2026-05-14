"""
Vector DB metadata schema 정의 파일

역할:
- 뉴스 / 공시 데이터를 Vector DB에 적재할 때 사용할 metadata 기준 통일
- namespace를 사용하지 않고 metadata filtering 기반으로 검색 가능하게 설계
- detected_changes의 stock_code / signal_code / year / industry_group과 연결
"""


DATA_TYPE_NEWS = "news"
DATA_TYPE_DISCLOSURE = "disclosure"


VECTOR_METADATA_FIELDS = {
    "data_type": str,

    "stock_code": str,
    "company_name": str,
    "company": str,

    "year": int,

    "signal_type": str,
    "signal_code": str,

    "industry_group": str,

    "source": str,
    "source_url": str,
    "date": str,
}


REQUIRED_METADATA_FIELDS = [
    "data_type",
    "stock_code",
    "company_name",
    "source",
]


FILTERABLE_METADATA_FIELDS = [
    "data_type",
    "stock_code",
    "company_name",
    "company",
    "year",
    "signal_type",
    "signal_code",
    "industry_group",
    "date",
]


def build_base_metadata(
    data_type,
    stock_code,
    company_name,
    source,
    source_url="",
    date="",
    year=None,
    signal_type="unknown",
    signal_code="unknown",
    industry_group="unknown",
):
    return {
        "data_type": data_type,

        "stock_code": stock_code or "",
        "company_name": company_name or "",
        "company": company_name or "",

        "year": year,

        "signal_type": signal_type or "unknown",
        "signal_code": signal_code or "unknown",

        "industry_group": industry_group or "unknown",

        "source": source or "",
        "source_url": source_url or "",
        "date": date or "",
    }


def build_news_metadata(
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
    return build_base_metadata(
        data_type=DATA_TYPE_NEWS,
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


def build_disclosure_metadata(
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
    return build_base_metadata(
        data_type=DATA_TYPE_DISCLOSURE,
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


def validate_metadata(metadata):
    missing_fields = [
        field
        for field in REQUIRED_METADATA_FIELDS
        if field not in metadata or metadata.get(field) in (None, "")
    ]

    return {
        "is_valid": len(missing_fields) == 0,
        "missing_fields": missing_fields,
    }