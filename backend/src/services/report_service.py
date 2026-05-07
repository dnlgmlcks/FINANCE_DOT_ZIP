from services.finance_service import calculate_finance_summary
from services.signal_service import generate_warning_signals


def build_report_response(stock_code: str):
    finance_summary = calculate_finance_summary(stock_code)

    if not finance_summary:
        return {
            "status": "fail",
            "message": "해당 종목코드의 재무 데이터를 찾을 수 없습니다.",
            "data": {
                "company_info": {
                    "stock_code": stock_code,
                    "company_name": ""
                },
                "finance_summary": [],
                "risk_signals": []
            }
        }

    risk_signals = generate_warning_signals(finance_summary)

    return {
        "status": "success",
        "message": "종합 재무 리포트 생성 성공",
        "data": {
            "company_info": {
                "stock_code": stock_code,
                "company_name": "삼성전자" if stock_code == "005930" else ""
            },
            "finance_summary": finance_summary,
            "risk_signals": risk_signals
        }
    }