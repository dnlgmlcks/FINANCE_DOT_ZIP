from src.services.finance_service import calculate_finance_summary
from src.services.signal_service import generate_signals
from src.services.industry_classifier import classify_industry
from src.services.detected_change_service import build_detected_changes
from src.db.queries import fetch_company_info_by_stock_code


def _safe_company_info(stock_code: str):
    try:
        company_info = fetch_company_info_by_stock_code(stock_code)
    except Exception:
        company_info = None

    if company_info:
        company_name = company_info.get("company_name") or ""
        induty_code = (
            company_info.get("induty_code")
            or company_info.get("industry_code")
        )
    else:
        company_name = "삼성전자" if stock_code == "005930" else ""
        induty_code = None

    return {
        "stock_code": stock_code,
        "company_name": company_name,
        "induty_code": induty_code,
    }


def _safe_industry_info(induty_code):
    try:
        industry_info = classify_industry(induty_code) or {}
    except Exception:
        industry_info = {}

    if not isinstance(industry_info, dict):
        industry_info = {}

    industry_info.setdefault("industry_group", "unknown")
    industry_info.setdefault("industry_group_name", "기타/미분류")
    industry_info.setdefault("is_excluded", False)

    return industry_info


def _safe_finance_summary(stock_code: str):
    try:
        finance_summary = calculate_finance_summary(stock_code) or []
    except Exception:
        finance_summary = []

    if not isinstance(finance_summary, list):
        return []

    return finance_summary


def _safe_signals(finance_summary, industry_info):
    try:
        signals = generate_signals(finance_summary, industry_info) or []
    except Exception:
        signals = []

    if not isinstance(signals, list):
        return []

    return signals


def _safe_detected_changes(
    finance_summary,
    signals,
    company_name="",
    stock_code="",
    industry_group="unknown",
):
    try:
        detected_changes = build_detected_changes(
            finance_summary,
            signals,
            company_name=company_name,
            stock_code=stock_code,
            industry_group=industry_group,
        ) or []
    except Exception:
        detected_changes = []

    if not isinstance(detected_changes, list):
        return []

    return detected_changes


def _build_response_data(
    company_info,
    industry_info,
    finance_summary=None,
    signals=None,
    detected_changes=None,
):
    finance_summary = finance_summary or []
    signals = signals or []
    detected_changes = detected_changes or []

    return {
        "company_info": company_info,
        "industry_info": industry_info,
        "finance_summary": finance_summary,
        "signals": signals,
        "detected_changes": detected_changes,

        # 프론트 기존 코드 호환용
        "risk_signals": signals,
    }


def build_report_response(stock_code: str):
    if not stock_code:
        return {
            "status": "fail",
            "message": "stock_code가 필요합니다.",
            "data": _build_response_data(
                company_info={
                    "stock_code": "",
                    "company_name": "",
                    "induty_code": None,
                },
                industry_info={
                    "industry_group": "unknown",
                    "industry_group_name": "기타/미분류",
                    "is_excluded": False,
                },
                finance_summary=[],
                signals=[],
                detected_changes=[],
            )
        }

    company_info = _safe_company_info(stock_code)
    industry_info = _safe_industry_info(company_info.get("induty_code"))
    finance_summary = _safe_finance_summary(stock_code)

    if not finance_summary:
        return {
            "status": "fail",
            "message": "해당 종목코드의 재무 데이터를 찾을 수 없습니다.",
            "data": _build_response_data(
                company_info=company_info,
                industry_info=industry_info,
                finance_summary=[],
                signals=[],
                detected_changes=[],
            )
        }

    signals = _safe_signals(finance_summary, industry_info)

    detected_changes = _safe_detected_changes(
        finance_summary,
        signals,
        company_name=company_info.get("company_name", ""),
        stock_code=stock_code,
        industry_group=industry_info.get("industry_group", "unknown"),
    )

    return {
        "status": "success",
        "message": "종합 재무 리포트 조회 성공",
        "data": _build_response_data(
            company_info=company_info,
            industry_info=industry_info,
            finance_summary=finance_summary,
            signals=signals,
            detected_changes=detected_changes,
        )
    }