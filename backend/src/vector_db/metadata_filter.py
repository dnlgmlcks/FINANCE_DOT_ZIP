"""
Vector DB metadata filtering 생성 모듈

역할:
- detected_changes 결과를 기반으로 Vector DB 검색 filter를 생성
- stock_code, year, signal_type, signal_code, industry_group 기준 검색 가능
"""


def remove_empty_filter_values(filter_dict):
    return {
        key: value
        for key, value in filter_dict.items()
        if value not in (None, "", [], {})
    }


def build_metadata_filter(
    stock_code=None,
    company_name=None,
    year=None,
    signal_type=None,
    signal_code=None,
    industry_group=None,
    date=None,
):
    filter_dict = {
        "stock_code": stock_code,
        "company_name": company_name,
        "year": year,
        "signal_type": signal_type,
        "signal_code": signal_code,
        "industry_group": industry_group,
        "date": date,
    }

    return remove_empty_filter_values(filter_dict)


def build_filter_from_detected_change(detected_change):
    if not detected_change:
        return {}

    return build_metadata_filter(
        stock_code=detected_change.get("stock_code"),
        company_name=detected_change.get("company_name"),
        year=detected_change.get("year"),
        signal_type=detected_change.get("signal_type"),
        signal_code=detected_change.get("signal_code"),
        industry_group=detected_change.get("industry_group"),
    )


def build_relaxed_filter_from_detected_change(detected_change):
    """
    검색 결과가 없을 때 사용하는 완화 필터.

    1차 검색:
    stock_code + signal_code + year

    완화 검색:
    stock_code + industry_group
    """
    if not detected_change:
        return {}

    return build_metadata_filter(
        stock_code=detected_change.get("stock_code"),
        industry_group=detected_change.get("industry_group"),
    )


def build_company_filter(stock_code):
    return build_metadata_filter(stock_code=stock_code)


def build_industry_filter(industry_group):
    return build_metadata_filter(industry_group=industry_group)