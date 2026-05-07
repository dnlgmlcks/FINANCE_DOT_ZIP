import sys
from pathlib import Path

from rest_framework.decorators import api_view
from rest_framework.response import Response

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from services.report_service import build_report_response
from db.queries import search_companies


TEMP_COMPANY_DATA = [
    {"CORP_ID": "001", "CORP_NAME": "삼성전자", "TICKER": "005930"},
    {"CORP_ID": "002", "CORP_NAME": "SK하이닉스", "TICKER": "000660"},
    {"CORP_ID": "003", "CORP_NAME": "현대자동차", "TICKER": "005380"},
    {"CORP_ID": "004", "CORP_NAME": "LG화학", "TICKER": "051910"},
    {"CORP_ID": "005", "CORP_NAME": "카카오", "TICKER": "035720"},
]


def success_response(data=None, message="요청 성공"):
    return Response({
        "status": "success",
        "message": message,
        "data": data
    })


def fail_response(message="요청 실패", data=None):
    return Response({
        "status": "fail",
        "message": message,
        "data": data
    })


@api_view(["GET", "POST"])
def test_api(request):
    return success_response(
        data={
            "method": request.method
        },
        message=f"DRF {request.method} 연결 성공"
    )


@api_view(["GET", "POST"])
def init_data(request):
    return success_response(
        data=TEMP_COMPANY_DATA,
        message="초기 기업 데이터 조회 성공"
    )


@api_view(["GET", "POST"])
def search_company(request):
    if request.method == "GET":
        keyword = request.query_params.get("keyword", "").strip()
    else:
        keyword = str(request.data.get("keyword", "")).strip()

    if not keyword:
        return fail_response(
            message="keyword가 필요합니다.",
            data=[]
        )

    result = search_companies(keyword)

    return success_response(
        data={
            "count": len(result),
            "companies": result
        },
        message="기업 검색 성공"
    )


@api_view(["GET"])
def comprehensive_report(request, stock_code):
    if not stock_code:
        return fail_response(
            message="stock_code가 필요합니다.",
            data=None
        )

    result = build_report_response(stock_code)

    if result.get("status") == "fail":
        return fail_response(
            message=result.get("message", "리포트 조회 실패"),
            data=result.get("data")
        )

    return success_response(
        data=result.get("data"),
        message="종합 재무 리포트 조회 성공"
    )