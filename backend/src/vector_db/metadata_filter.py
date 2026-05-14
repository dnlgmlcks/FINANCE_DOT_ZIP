"""
Vector DB metadata filtering 생성 모듈

역할:
- detected_changes 결과를 기반으로 Vector DB 검색 filter 생성
- stock_code, year, signal_type, signal_code, industry_group, data_type 기준 검색 가능
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
    data_type=None,
    date=None,
):
    filter_dict = {
        "data_type": data_type,
        "stock_code": stock_code,
        "company_name": company_name,
        "year": year,
        "signal_type": signal_type,
        "signal_code": signal_code,
        "industry_group": industry_group,
        "date": date,
    }

    return remove_empty_filter_values(filter_dict)


def build_filter_from_detected_change(
    detected_change,
    data_type=None,
):
    if not detected_change:
        return {}

    return build_metadata_filter(
        stock_code=detected_change.get("stock_code"),
        company_name=detected_change.get("company_name"),
        year=detected_change.get("year"),
        signal_type=detected_change.get("signal_type"),
        signal_code=detected_change.get("signal_code"),
        industry_group=detected_change.get("industry_group"),
        data_type=data_type,
    )


def build_relaxed_filter_from_detected_change(
    detected_change,
    data_type=None,
):
    if not detected_change:
        return {}

    return build_metadata_filter(
        stock_code=detected_change.get("stock_code"),
        industry_group=detected_change.get("industry_group"),
        data_type=data_type,
    )


def build_company_filter(stock_code, data_type=None):
    return build_metadata_filter(
        stock_code=stock_code,
        data_type=data_type,
    )


def build_industry_filter(industry_group, data_type=None):
    return build_metadata_filter(
        industry_group=industry_group,
        data_type=data_type,
    )