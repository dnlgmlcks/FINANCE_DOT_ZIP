"""
chat_context_builder.py

AI 리포트 결과 JSON을 리포트 기반 Q&A 챗봇이 사용할 context로 정리하는 모듈입니다.

역할:
1. comprehensive_report_service.py의 create_ai_report() 결과를 입력받습니다.
2. company_info, industry_info, finance_summary, signals, detected_changes, report, evidence_news, evidence_disclosures를 정리합니다.
3. report_chat_chain.py에 전달할 구조화 context와 텍스트 context를 생성합니다.
4. 챗봇이 제공된 근거 안에서만 답변하도록 필요한 정보를 압축합니다.

주의:
- 이 모듈은 LLM을 호출하지 않습니다.
- 새로운 분석이나 계산을 수행하지 않습니다.
- 이미 생성된 리포트와 근거 데이터를 챗봇 답변용으로 정리하는 역할만 합니다.
"""

from typing import Any, Dict, List


# ---------------------------------------------------------------------
# 1. 공통 유틸 함수
# ---------------------------------------------------------------------

def safe_text(value: Any) -> str:
    """
    None 또는 비문자열 값을 안전하게 문자열로 변환합니다.
    """

    if value is None:
        return ""

    return str(value)


def shorten_text(text: Any, max_length: int = 1000) -> str:
    """
    긴 텍스트를 챗봇 context에 넣기 적절한 길이로 자릅니다.
    """

    text = safe_text(text).strip()

    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[:max_length] + "...(truncated)"


def format_number(value: Any) -> str:
    """
    숫자 값을 읽기 쉬운 문자열로 변환합니다.
    """

    if value is None:
        return "N/A"

    if isinstance(value, int):
        return f"{value:,}"

    if isinstance(value, float):
        return f"{value:,.2f}"

    return safe_text(value)


def get_report_section(report: Dict[str, Any], key: str) -> str:
    """
    report에서 특정 section 값을 안전하게 가져옵니다.
    """

    return safe_text(report.get(key, "")).strip()


# ---------------------------------------------------------------------
# 2. 데이터 정리 함수
# ---------------------------------------------------------------------

def prepare_company_context(ai_report_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    회사 및 분석 기준 정보를 정리합니다.
    """

    company_info = ai_report_result.get("company_info", {}) or {}
    industry_info = ai_report_result.get("industry_info", {}) or {}

    return {
        "company_name": company_info.get("company_name", ""),
        "stock_code": company_info.get("stock_code", ""),
        "industry_group": industry_info.get("industry_group", ""),
        "industry_group_name": industry_info.get("industry_group_name", ""),
        "analysis_year": ai_report_result.get("analysis_year"),
        "base_year": ai_report_result.get("base_year"),
    }


def prepare_report_context(ai_report_result: Dict[str, Any]) -> Dict[str, str]:
    """
    최종 AI 리포트 본문을 챗봇 context로 정리합니다.
    """

    report = ai_report_result.get("report", {}) or {}

    return {
        "executive_summary": get_report_section(report, "executive_summary"),
        "financial_change_summary": get_report_section(report, "financial_change_summary"),
        "news_evidence_summary": get_report_section(report, "news_evidence_summary"),
        "disclosure_evidence_summary": get_report_section(report, "disclosure_evidence_summary"),
        "possible_causes": get_report_section(report, "possible_causes"),
        "interview_point": get_report_section(report, "interview_point"),
        "limitations": get_report_section(report, "limitations"),
    }


def prepare_finance_summary_context(
    ai_report_result: Dict[str, Any],
    max_years: int = 5,
) -> List[Dict[str, Any]]:
    """
    연도별 재무지표 요약을 챗봇 context로 정리합니다.
    """

    finance_summary = (
        ai_report_result.get("finance_summary")
        or (ai_report_result.get("financial_context", {}) or {}).get("finance_summary")
        or []
    )

    if not isinstance(finance_summary, list):
        return []

    sorted_summary = sorted(
        finance_summary,
        key=lambda row: row.get("year", 0),
        reverse=True,
    )

    prepared = []

    for row in sorted_summary[:max_years]:
        prepared.append(
            {
                "year": row.get("year"),
                "revenue": row.get("revenue"),
                "operating_income": row.get("operating_income"),
                "net_income": row.get("net_income"),
                "total_assets": row.get("total_assets"),
                "total_liabilities": row.get("total_liabilities"),
                "total_equity": row.get("total_equity"),
                "debt_ratio": row.get("debt_ratio"),
                "current_ratio": row.get("current_ratio"),
                "operating_cash_flow": row.get("operating_cash_flow"),
                "revenue_yoy": row.get("revenue_yoy"),
                "operating_income_yoy": row.get("operating_income_yoy"),
                "net_income_yoy": row.get("net_income_yoy"),
            }
        )

    return prepared


def prepare_signal_context(
    ai_report_result: Dict[str, Any],
    max_items: int = 10,
) -> List[Dict[str, Any]]:
    """
    signals를 챗봇 context로 정리합니다.
    """

    signals = ai_report_result.get("signals", []) or []

    if not isinstance(signals, list):
        return []

    prepared = []

    for item in signals[:max_items]:
        prepared.append(
            {
                "year": item.get("year"),
                "type": item.get("type"),
                "severity": item.get("severity"),
                "signal": item.get("signal"),
                "description": item.get("description"),
            }
        )

    return prepared


def prepare_detected_change_context(
    ai_report_result: Dict[str, Any],
    max_items: int = 10,
) -> List[Dict[str, Any]]:
    """
    AI 리포트 생성에 사용된 핵심 detected_changes를 챗봇 context로 정리합니다.
    """

    detected_changes = ai_report_result.get("detected_changes", []) or []

    if not isinstance(detected_changes, list):
        return []

    prepared = []

    for item in detected_changes[:max_items]:
        prepared.append(
            {
                "metric_key": item.get("metric_key"),
                "metric_label": item.get("metric_label"),
                "year": item.get("year"),
                "base_year": item.get("base_year"),
                "change_type": item.get("change_type"),
                "direction": item.get("direction"),
                "severity": item.get("severity"),
                "signal_type": item.get("signal_type"),
                "current_value": item.get("current_value"),
                "base_value": item.get("base_value"),
                "yoy_change_rate": item.get("yoy_change_rate"),
                "description": item.get("description"),
                "source_signal": item.get("source_signal"),
                "search_keywords": item.get("search_keywords", []),
            }
        )

    return prepared


def prepare_evidence_news_context(
    ai_report_result: Dict[str, Any],
    max_items: int = 5,
) -> List[Dict[str, Any]]:
    """
    리포트 근거로 선별된 뉴스 evidence를 챗봇 context로 정리합니다.
    """

    evidence_news = ai_report_result.get("evidence_news", []) or []

    if not isinstance(evidence_news, list):
        return []

    prepared = []

    for item in evidence_news[:max_items]:
        prepared.append(
            {
                "source_type": "news",
                "metric_key": item.get("metric_key"),
                "metric_label": item.get("metric_label"),
                "year": item.get("year"),
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "published_date": item.get("published_date", ""),
                "content": shorten_text(item.get("content", ""), max_length=700),
                "evidence_summary": shorten_text(item.get("evidence_summary", ""), max_length=500),
                "relevance_score": item.get("relevance_score"),
                "reason": item.get("reason", ""),
            }
        )

    return prepared


def prepare_evidence_disclosure_context(
    ai_report_result: Dict[str, Any],
    max_items: int = 5,
) -> List[Dict[str, Any]]:
    """
    리포트 근거로 선별된 공시 evidence를 챗봇 context로 정리합니다.
    """

    evidence_disclosures = ai_report_result.get("evidence_disclosures", []) or []

    if not isinstance(evidence_disclosures, list):
        return []

    prepared = []

    for item in evidence_disclosures[:max_items]:
        prepared.append(
            {
                "source_type": item.get("source_type", "disclosure"),
                "metric_key": item.get("metric_key"),
                "metric_label": item.get("metric_label"),
                "year": item.get("year"),
                "report_type": item.get("report_type", ""),
                "source": item.get("source", ""),
                "page": item.get("page", ""),
                "section": item.get("section", ""),
                "chunk_text": shorten_text(item.get("chunk_text", ""), max_length=800),
                "evidence_summary": shorten_text(item.get("evidence_summary", ""), max_length=500),
                "relevance_score": item.get("relevance_score"),
            }
        )

    return prepared


# ---------------------------------------------------------------------
# 3. 텍스트 context 생성
# ---------------------------------------------------------------------

def build_finance_summary_text(finance_summary: List[Dict[str, Any]]) -> str:
    """
    finance_summary context를 사람이 읽을 수 있는 텍스트로 변환합니다.
    """

    if not finance_summary:
        return "연도별 재무지표 정보가 제공되지 않았습니다."

    lines = []

    for row in finance_summary:
        year = row.get("year", "N/A")

        lines.append(
            "- "
            f"{year}년: "
            f"매출액={format_number(row.get('revenue'))}, "
            f"영업이익={format_number(row.get('operating_income'))}, "
            f"당기순이익={format_number(row.get('net_income'))}, "
            f"부채비율={format_number(row.get('debt_ratio'))}, "
            f"유동비율={format_number(row.get('current_ratio'))}, "
            f"영업활동현금흐름={format_number(row.get('operating_cash_flow'))}, "
            f"매출액 YoY={format_number(row.get('revenue_yoy'))}, "
            f"영업이익 YoY={format_number(row.get('operating_income_yoy'))}, "
            f"순이익 YoY={format_number(row.get('net_income_yoy'))}"
        )

    return "\n".join(lines)


def build_signal_text(signals: List[Dict[str, Any]]) -> str:
    """
    signal context를 텍스트로 변환합니다.
    """

    if not signals:
        return "signal 정보가 제공되지 않았습니다."

    lines = []

    for item in signals:
        lines.append(
            "- "
            f"{item.get('year')}년 / "
            f"{item.get('type')} / "
            f"{item.get('severity')} / "
            f"{item.get('signal')}: "
            f"{item.get('description')}"
        )

    return "\n".join(lines)


def build_detected_change_text(detected_changes: List[Dict[str, Any]]) -> str:
    """
    detected_changes context를 텍스트로 변환합니다.
    """

    if not detected_changes:
        return "핵심 재무 변동 정보가 제공되지 않았습니다."

    lines = []

    for item in detected_changes:
        lines.append(
            "- "
            f"{item.get('year')}년 {item.get('metric_label')} "
            f"({item.get('metric_key')}): "
            f"{item.get('description')} "
            f"현재값={format_number(item.get('current_value'))}, "
            f"기준값={format_number(item.get('base_value'))}, "
            f"변화율={format_number(item.get('yoy_change_rate'))}, "
            f"severity={item.get('severity')}, "
            f"signal_type={item.get('signal_type')}"
        )

    return "\n".join(lines)


def build_evidence_news_text(evidence_news: List[Dict[str, Any]]) -> str:
    """
    evidence_news context를 텍스트로 변환합니다.
    """

    if not evidence_news:
        return "리포트 근거로 선별된 뉴스가 없습니다."

    lines = []

    for idx, item in enumerate(evidence_news, start=1):
        lines.append(
            f"[뉴스 {idx}] "
            f"{item.get('title')} / "
            f"지표={item.get('metric_label')} / "
            f"요약={item.get('evidence_summary') or item.get('content')} / "
            f"URL={item.get('url')}"
        )

    return "\n".join(lines)


def build_evidence_disclosure_text(evidence_disclosures: List[Dict[str, Any]]) -> str:
    """
    evidence_disclosures context를 텍스트로 변환합니다.
    """

    if not evidence_disclosures:
        return "리포트 근거로 선별된 공시/사업보고서 근거가 없습니다."

    lines = []

    for idx, item in enumerate(evidence_disclosures, start=1):
        lines.append(
            f"[공시 {idx}] "
            f"{item.get('report_type')} / "
            f"{item.get('section')} / "
            f"지표={item.get('metric_label')} / "
            f"요약={item.get('evidence_summary') or item.get('chunk_text')} / "
            f"출처={item.get('source')} / "
            f"page={item.get('page')}"
        )

    return "\n".join(lines)


def build_chat_context_text(chat_context: Dict[str, Any]) -> str:
    """
    구조화된 chat_context를 LLM 프롬프트에 넣을 텍스트 context로 변환합니다.
    """

    company = chat_context.get("company", {}) or {}
    report = chat_context.get("report", {}) or {}

    lines = [
        "[기업 정보]",
        f"기업명: {company.get('company_name')}",
        f"종목코드: {company.get('stock_code')}",
        f"업종: {company.get('industry_group_name')} ({company.get('industry_group')})",
        f"분석 연도: {company.get('analysis_year')}",
        f"비교 기준 연도: {company.get('base_year')}",
        "",
        "[최종 AI 리포트]",
        f"요약: {report.get('executive_summary')}",
        f"주요 재무 변화: {report.get('financial_change_summary')}",
        f"뉴스 근거 요약: {report.get('news_evidence_summary')}",
        f"공시 근거 요약: {report.get('disclosure_evidence_summary')}",
        f"가능한 배경 요인: {report.get('possible_causes')}",
        f"질의응답 포인트: {report.get('interview_point')}",
        f"한계 및 주의사항: {report.get('limitations')}",
        "",
        "[연도별 재무지표]",
        build_finance_summary_text(chat_context.get("finance_summary", [])),
        "",
        "[Signals]",
        build_signal_text(chat_context.get("signals", [])),
        "",
        "[핵심 Detected Changes]",
        build_detected_change_text(chat_context.get("detected_changes", [])),
        "",
        "[뉴스 근거]",
        build_evidence_news_text(chat_context.get("evidence_news", [])),
        "",
        "[공시/사업보고서 근거]",
        build_evidence_disclosure_text(chat_context.get("evidence_disclosures", [])),
    ]

    return "\n".join(lines).strip()


# ---------------------------------------------------------------------
# 4. 대표 함수
# ---------------------------------------------------------------------

def build_chat_context(
    ai_report_result: Dict[str, Any],
    max_news_items: int = 5,
    max_disclosure_items: int = 5,
    max_signal_items: int = 10,
    max_detected_change_items: int = 10,
    max_finance_years: int = 5,
) -> Dict[str, Any]:
    """
    최종 AI 리포트 JSON을 챗봇 답변용 context로 변환합니다.
    """

    company_context = prepare_company_context(ai_report_result)
    report_context = prepare_report_context(ai_report_result)
    finance_summary_context = prepare_finance_summary_context(
        ai_report_result=ai_report_result,
        max_years=max_finance_years,
    )
    signal_context = prepare_signal_context(
        ai_report_result=ai_report_result,
        max_items=max_signal_items,
    )
    detected_change_context = prepare_detected_change_context(
        ai_report_result=ai_report_result,
        max_items=max_detected_change_items,
    )
    evidence_news_context = prepare_evidence_news_context(
        ai_report_result=ai_report_result,
        max_items=max_news_items,
    )
    evidence_disclosure_context = prepare_evidence_disclosure_context(
        ai_report_result=ai_report_result,
        max_items=max_disclosure_items,
    )

    chat_context = {
        "company": company_context,
        "report": report_context,
        "finance_summary": finance_summary_context,
        "signals": signal_context,
        "detected_changes": detected_change_context,
        "evidence_news": evidence_news_context,
        "evidence_disclosures": evidence_disclosure_context,
        "metadata": {
            "source": "chat_context_builder",
            "news_evidence_count": len(evidence_news_context),
            "disclosure_evidence_count": len(evidence_disclosure_context),
            "signal_count": len(signal_context),
            "detected_change_count": len(detected_change_context),
            "finance_summary_count": len(finance_summary_context),
            "has_report": bool(report_context.get("executive_summary")),
        },
    }

    chat_context["context_text"] = build_chat_context_text(chat_context)

    return chat_context


# ---------------------------------------------------------------------
# 5. 단독 실행 테스트
# ---------------------------------------------------------------------

if __name__ == "__main__":
    import json

    sample_ai_report_result = {
        "company_info": {
            "company_name": "삼성전자",
            "stock_code": "005930",
        },
        "industry_info": {
            "industry_group": "tech_equipment",
            "industry_group_name": "기술 및 장치 산업",
        },
        "analysis_year": 2023,
        "base_year": 2022,
        "signals": [
            {
                "year": 2023,
                "type": "negative",
                "severity": "HIGH",
                "signal": "영업이익 급감",
                "description": "전년 대비 영업이익이 -84.86% 감소했습니다.",
            }
        ],
        "detected_changes": [
            {
                "metric_key": "operating_income",
                "metric_label": "영업이익",
                "year": 2023,
                "base_year": 2022,
                "current_value": 6566976000000,
                "base_value": 43376630000000,
                "yoy_change_rate": -84.86,
                "severity": "high",
                "signal_type": "negative",
                "description": "전년 대비 영업이익이 -84.86% 감소했습니다.",
            }
        ],
        "report": {
            "executive_summary": "삼성전자는 2023년 영업이익이 크게 감소했습니다.",
            "financial_change_summary": "영업이익은 전년 대비 84.86% 감소했습니다.",
            "news_evidence_summary": "뉴스에서는 반도체 업황 부진이 관련 배경으로 언급됩니다.",
            "disclosure_evidence_summary": "공시에서는 수요 둔화와 가격 하락이 언급됩니다.",
            "possible_causes": "반도체 업황 부진과 수요 둔화가 가능한 배경입니다.",
            "interview_point": "반도체 부문 회복 전략을 질문할 수 있습니다.",
            "limitations": "추가 공시 확인이 필요합니다.",
        },
        "evidence_news": [
            {
                "metric_label": "영업이익",
                "title": "삼성전자 영업이익 급감",
                "url": "https://example.com/news",
                "evidence_summary": "반도체 업황 부진이 영업이익 감소 배경으로 보도되었습니다.",
            }
        ],
        "evidence_disclosures": [
            {
                "metric_label": "영업이익",
                "report_type": "사업보고서",
                "section": "사업의 내용",
                "source": "2023_삼성전자_사업보고서_mock",
                "page": 12,
                "evidence_summary": "메모리 수요 둔화와 가격 하락이 수익성 약화 배경으로 언급되었습니다.",
            }
        ],
    }

    context = build_chat_context(sample_ai_report_result)

    print("[Chat Context Builder Test]")
    print(json.dumps(context["metadata"], ensure_ascii=False, indent=2))

    print("\n[Context Text]")
    print(context["context_text"])
