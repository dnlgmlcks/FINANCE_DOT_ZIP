from services.finance_service import calculate_finance_summary
from services.signal_service import generate_warning_signals


def build_report_response(stock_code: str):
    finance_summary = calculate_finance_summary(stock_code)
    risk_signals = generate_warning_signals(finance_summary)

    return {
        "status": "success",
        "data": {
            "company_info": {
                "stock_code": stock_code,
                "company_name": "삼성전자" if stock_code == "005930" else ""
            },
            "finance_summary": finance_summary,
            "risk_signals": risk_signals
        }
    }