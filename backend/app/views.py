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


def to_bool(value, default=False):
    """
    request.data에서 넘어온 값을 bool로 변환합니다.
    """

    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y", "on"}

    return bool(value)


def inject_mock_disclosures_for_chat(ai_report_result, stock_code):
    """
    disclosure_retriever.py가 아직 구현되지 않은 상태에서
    챗봇 테스트/발표용으로 sample_disclosure_data.py의 Mock 공시 근거를 주입합니다.

    실제 Vector DB 연결 후에는 이 함수 사용을 중단하고,
    disclosure_retriever.py 결과를 evidence_disclosures로 연결하면 됩니다.
    """

    try:
        from src.ai.sample_disclosure_data import get_sample_evidence_disclosures
    except Exception:
        return ai_report_result

    evidence_disclosures = get_sample_evidence_disclosures(
        stock_code=stock_code,
        year=ai_report_result.get("analysis_year"),
        max_items=3,
    )

    ai_report_result["evidence_disclosures"] = evidence_disclosures

    disclosure_summary = " ".join(
        item.get("evidence_summary", "")
        for item in evidence_disclosures
        if item.get("evidence_summary")
    ).strip()

    report = ai_report_result.get("report", {}) or {}

    if disclosure_summary:
        report["disclosure_evidence_summary"] = disclosure_summary

    report_metadata = report.get("metadata", {}) or {}
    report_metadata["disclosure_evidence_count"] = len(evidence_disclosures)
    report["metadata"] = report_metadata
    ai_report_result["report"] = report

    metadata = ai_report_result.get("metadata", {}) or {}
    metadata["evidence_disclosure_count"] = len(evidence_disclosures)
    metadata["mock_disclosure_injected"] = True
    ai_report_result["metadata"] = metadata

    disclosure_result = ai_report_result.get("disclosure_result", {}) or {}
    disclosure_result["evidence_disclosures"] = evidence_disclosures
    disclosure_result["metadata"] = {
        **(disclosure_result.get("metadata", {}) or {}),
        "enabled": False,
        "source": "mock_disclosure",
        "evidence_disclosure_count": len(evidence_disclosures),
        "reason": "disclosure_retriever.py is not implemented. Mock disclosures are injected for chat API.",
    }
    ai_report_result["disclosure_result"] = disclosure_result

    return ai_report_result


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


@api_view(["POST"])
def report_chat(request, stock_code):
    """
    종합 재무 리포트 기반 Q&A 챗봇 API입니다.

    Endpoint:
    POST /api/v1/report/comprehensive/{stock_code}/chat

    Request body:
    {
        "question": "삼성전자는 2023년에 영업이익이 왜 감소했어?",
        "use_mock_disclosures": true
    }

    Response data:
    {
        "company_info": {...},
        "industry_info": {...},
        "analysis_year": 2023,
        "base_year": 2022,
        "question": "...",
        "answer": "...",
        "used_sources": [...],
        "limitations": "...",
        "metadata": {...}
    }
    """

    print("\n===== [1] report_chat 호출됨 =====")
    print("[2] stock_code:", stock_code)

    if not stock_code:
        return fail_response(
            message="stock_code가 필요합니다.",
            data=None
        )

    question = str(request.data.get("question", "")).strip()

    if not question:
        return fail_response(
            message="question이 필요합니다.",
            data=None
        )

    use_mock_disclosures = to_bool(
        request.data.get("use_mock_disclosures"),
        default=False,
    )

    try:
        from src.services.report_service import build_report_response
        from src.ai.backend_payload_adapter import build_ai_input_from_backend_response
        from src.ai.comprehensive_report_service import create_ai_report
        from src.ai.chat_context_builder import build_chat_context
        from src.ai.llm_client import get_llm
        from src.ai.report_chat_chain import answer_report_question

        print("[3] build_report_response 실행")
        report_response = build_report_response(stock_code)

        if report_response.get("status") == "fail":
            return fail_response(
                message=report_response.get("message", "리포트 조회 실패"),
                data=report_response.get("data")
            )

        print("[4] backend_payload_adapter 실행")
        ai_input = build_ai_input_from_backend_response(report_response)

        print("[5] create_ai_report 실행")
        ai_report_result = create_ai_report(
            ai_input=ai_input,
            vector_store=None,
            max_results_per_query=5,
            max_total_news_results=20,
            max_evidence_news=5,
            include_searched_news=False,
        )

        if use_mock_disclosures:
            print("[6] 공시 Mock 근거 주입")
            ai_report_result = inject_mock_disclosures_for_chat(
                ai_report_result=ai_report_result,
                stock_code=stock_code,
            )

        print("[7] chat_context_builder 실행")
        chat_context = build_chat_context(ai_report_result)

        print("[8] report_chat_chain 실행")
        llm = get_llm()
        chat_answer = answer_report_question(
            llm=llm,
            question=question,
            chat_context=chat_context,
        )

    except Exception as e:
        print("[ERROR] report_chat 내부 오류 발생")
        print(type(e).__name__, str(e))

        return fail_response(
            message=f"챗봇 답변 생성 중 오류 발생: {str(e)}",
            data=None
        )

    company_info = ai_report_result.get("company_info", {}) or {}
    industry_info = ai_report_result.get("industry_info", {}) or {}

    response_data = {
        "company_info": company_info,
        "industry_info": industry_info,
        "analysis_year": ai_report_result.get("analysis_year"),
        "base_year": ai_report_result.get("base_year"),
        "question": question,
        "answer": chat_answer.get("answer", ""),
        "used_sources": chat_answer.get("used_sources", []),
        "limitations": chat_answer.get("limitations", ""),
        "metadata": {
            **(chat_answer.get("metadata", {}) or {}),
            "chat_context": chat_context.get("metadata", {}),
            "ai_report": ai_report_result.get("metadata", {}),
            "use_mock_disclosures": use_mock_disclosures,
        },
    }

    return success_response(
        data=response_data,
        message="리포트 챗봇 답변 생성 성공"
    )
