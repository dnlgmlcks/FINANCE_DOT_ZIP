import sys
from pathlib import Path

from rest_framework.decorators import api_view
from rest_framework.response import Response


# =========================
# src 경로 강제 등록
# =========================
CURRENT_FILE = Path(__file__).resolve()

PROJECT_ROOT = None

for parent in CURRENT_FILE.parents:
    if (parent / "src").exists():
        PROJECT_ROOT = parent
        break

if PROJECT_ROOT is None:
    raise RuntimeError("src 폴더를 찾을 수 없습니다. 프로젝트 구조를 확인해주세요.")

SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


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
        return fail_response(message="keyword가 필요합니다.", data=[])

    result = [
        company for company in TEMP_COMPANY_DATA
        if keyword in company["CORP_NAME"] or keyword in company["TICKER"]
    ]

    if not result:
        return fail_response(message="검색 결과가 없습니다.", data=[])

    matched = result[0]
    stock_code = matched["TICKER"]

    try:
        from src.services.report_service import build_report_response
        report_result = build_report_response(stock_code)
    except Exception as e:
        return fail_response(message=f"리포트 생성 오류: {str(e)}")

    if report_result.get("status") == "fail":
        return fail_response(message=report_result.get("message", "리포트 조회 실패"))

    report_data = report_result.get("data", {})

    news_data = {
        "detected_changes": report_data.get("detected_changes", []) or [],
        "evidence_news": [],
        "signals": report_data.get("signals", []) or [],
        "company_info": report_data.get("company_info", {}),
    }

    return success_response(
        data={
            "reportData": report_data,
            "newsData": news_data,
            "disclosureData": {"company_info": report_data.get("company_info", {})},
        },
        message="기업 검색 성공"
    )


@api_view(["GET"])
def comprehensive_report(request, stock_code):
    print("\n===== [1] comprehensive_report 호출됨 =====")
    print("[2] stock_code:", stock_code)

    if not stock_code:
        print("[ERROR] stock_code 없음")
        return fail_response(
            message="stock_code가 필요합니다.",
            data=None
        )

    try:
        print("[3] build_report_response import 직전")
        from src.services.report_service import build_report_response

        print("[4] build_report_response 실행 직전")
        result = build_report_response(stock_code)

        print("[5] build_report_response 실행 완료")
        print("[6] result:", result)

    except Exception as e:
        print("[ERROR] build_report_response 내부 오류 발생")
        print(type(e).__name__, str(e))

        return fail_response(
            message=f"리포트 생성 중 오류 발생: {str(e)}",
            data=None
        )

    if result.get("status") == "fail":
        print("[7] result status = fail")
        print("[8] message:", result.get("message"))

        return fail_response(
            message=result.get("message", "리포트 조회 실패"),
            data=result.get("data")
        )

    print("[9] 최종 응답 반환")

    return success_response(
        data=result.get("data"),
        message="종합 재무 리포트 조회 성공"
    )