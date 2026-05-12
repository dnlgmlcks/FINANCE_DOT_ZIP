"""
Vector DB metadata schema 정의 파일

역할:
- 뉴스/공시 chunk를 Vector DB에 저장할 때 사용할 metadata 기준 정의
- detected_changes 기반 filtering에 사용할 key를 통일
- Pinecone, Chroma 등 Vector DB 교체 시에도 공통 기준으로 사용
"""


VECTOR_METADATA_FIELDS = {
    "stock_code": str,
    "company_name": str,
    "year": int,

    "signal_type": str,
    "signal_code": str,

    "industry_group": str,

    "source": str,
    "source_url": str,
    "date": str,
}


REQUIRED_METADATA_FIELDS = [
    "stock_code",
    "company_name",
    "source",
]


FILTERABLE_METADATA_FIELDS = [
    "stock_code",
    "company_name",
    "year",
    "signal_type",
    "signal_code",
    "industry_group",
    "date",
]


def build_base_metadata(
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
        "stock_code": stock_code,
        "company_name": company_name,
        "year": year,
        "signal_type": signal_type,
        "signal_code": signal_code,
        "industry_group": industry_group,
        "source": source,
        "source_url": source_url,
        "date": date,
    }


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