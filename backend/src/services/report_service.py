from src.services.finance_service import calculate_finance_summary
from src.services.signal_service import generate_signals
from src.services.industry_classifier import classify_industry
from src.services.detected_change_service import build_detected_changes
from src.db.queries import fetch_company_info_by_stock_code


def build_report_response(stock_code: str):
    company_info = fetch_company_info_by_stock_code(stock_code)

    if company_info:
        company_name = company_info.get("company_name") or ""
        induty_code = (
            company_info.get("induty_code")
            or company_info.get("industry_code")
        )
    else:
        company_name = "삼성전자" if stock_code == "005930" else ""
        induty_code = None

    industry_info = classify_industry(induty_code)

    finance_summary = calculate_finance_summary(stock_code)

    if not finance_summary:
        return {
            "status": "fail",
            "message": "해당 종목코드의 재무 데이터를 찾을 수 없습니다.",
            "data": {
                "company_info": {
                    "stock_code": stock_code,
                    "company_name": company_name,
                    "induty_code": induty_code,
                },
                "industry_info": industry_info,
                "finance_summary": [],
                "signals": [],
                "risk_signals": [],
                "detected_changes": [],
            }
        }

    signals = generate_signals(finance_summary, industry_info)
    detected_changes = build_detected_changes(finance_summary, signals)

    return {
        "status": "success",
        "message": "종합 재무 리포트 조회 성공",
        "data": {
            "company_info": {
                "stock_code": stock_code,
                "company_name": company_name,
                "induty_code": induty_code,
            },
            "industry_info": industry_info,
            "finance_summary": finance_summary,
            "signals": signals,
            "detected_changes": detected_changes,

            # 프론트 기존 코드 호환용
            "risk_signals": signals,
        }
    }