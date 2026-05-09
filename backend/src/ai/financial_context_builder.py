"""
financial_context_builder.py

재무 데이터와 detected_changes를 LLM 입력용 재무 문맥으로 정리하는
Financial Context Builder Chain 모듈입니다.

이번 AI 파이프라인은 하나의 공통 LLM 객체를 사용하되,
각 하위 Chain마다 서로 다른 system prompt를 적용해 역할을 분리하는 구조입니다.

이 파일의 역할:
1. Backend/Data 파트 또는 sample_report_data.py에서 전달한 ai_input을 입력으로 받습니다.
2. financial_metrics와 detected_changes를 바탕으로 LLM 입력용 재무 문맥을 생성합니다.
3. 계산은 하지 않고, 이미 계산된 수치와 변동 감지 결과를 보기 좋게 구조화합니다.
4. 이후 News Query Generator Chain, Evidence Filter Chain, Report Writer Chain에서 사용할 수 있는 context dict를 반환합니다.

주의:
- 이 파일 안에서 ChatOpenAI(...)를 새로 생성하지 않습니다.
- 공통 LLM 객체는 llm_client.py의 get_llm()으로 생성하고, 이 파일에는 인자로 주입합니다.
- LLM 출력 JSON 파싱 실패에 대비해 fallback context 생성 함수를 함께 제공합니다.
"""

import json
from typing import Any, Dict, List

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


# ---------------------------------------------------------------------
# 1. 공통 유틸 함수
# ---------------------------------------------------------------------

def get_company_name(ai_input: Dict[str, Any]) -> str:
    """
    AI 입력 데이터에서 기업명을 추출합니다.
    """

    company_info = ai_input.get("company_info", {}) or {}

    return (
        company_info.get("company_name")
        or ai_input.get("company_name")
        or "기업"
    )


def get_stock_code(ai_input: Dict[str, Any]) -> str:
    """
    AI 입력 데이터에서 종목코드를 추출합니다.
    """

    company_info = ai_input.get("company_info", {}) or {}

    return company_info.get("stock_code", "")


def format_value(value: Any, unit: str = "") -> str:
    """
    재무 수치를 사람이 읽기 좋은 문자열로 변환합니다.

    Args:
        value: 재무 수치
        unit: 단위

    Returns:
        포맷팅된 문자열
    """

    if value is None:
        return "N/A"

    if isinstance(value, (int, float)):
        if unit == "KRW":
            return f"{value:,.0f}원"

        if unit == "%":
            return f"{value:,.2f}%"

        return f"{value:,.2f}"

    return str(value)


def extract_json_from_llm_output(output: str) -> Dict[str, Any]:
    """
    LLM 응답 문자열에서 JSON을 파싱합니다.

    LLM이 ```json ... ``` 형태로 반환하는 경우도 처리합니다.
    """

    cleaned = output.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.replace("```json", "", 1).strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```", "", 1).strip()

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()

    return json.loads(cleaned)


# ---------------------------------------------------------------------
# 2. fallback 재무 문맥 생성
# ---------------------------------------------------------------------

def build_metric_summary_lines(financial_metrics: Dict[str, Any]) -> List[str]:
    """
    financial_metrics를 사람이 읽기 좋은 요약 문장 리스트로 변환합니다.
    """

    lines = []

    for metric_key, metric in financial_metrics.items():
        label = metric.get("label", metric_key)
        current_year = metric.get("current_year")
        base_year = metric.get("base_year")
        current_value = format_value(
            metric.get("current_value"),
            metric.get("unit", ""),
        )
        base_value = format_value(
            metric.get("base_value"),
            metric.get("unit", ""),
        )
        yoy_change_rate = metric.get("yoy_change_rate")
        unit = metric.get("unit", "")

        if yoy_change_rate is None:
            change_text = "전년 대비 증감률 정보가 없습니다."
        else:
            change_text = f"전년 대비 {yoy_change_rate:.2f}% 변동했습니다."

        lines.append(
            f"- {label}: {current_year}년 {current_value}, "
            f"{base_year}년 {base_value}, {change_text} "
            f"(metric_key: {metric_key}, unit: {unit})"
        )

    return lines


def build_detected_change_summary_lines(detected_changes: List[Dict[str, Any]]) -> List[str]:
    """
    detected_changes를 사람이 읽기 좋은 요약 문장 리스트로 변환합니다.
    """

    if not detected_changes:
        return ["- 유의미한 재무 변동이 탐지되지 않았습니다."]

    lines = []

    for change in detected_changes:
        metric_label = change.get("metric_label", "재무 지표")
        year = change.get("year")
        base_year = change.get("base_year")
        direction = change.get("direction")
        severity = change.get("severity")
        yoy_change_rate = change.get("yoy_change_rate")
        description = change.get("description", "")

        if yoy_change_rate is None:
            yoy_text = "증감률 정보 없음"
        else:
            yoy_text = f"전년 대비 {yoy_change_rate:.2f}%"

        lines.append(
            f"- {metric_label}: {base_year}년 대비 {year}년에 {yoy_text} 변동. "
            f"방향: {direction}, 심각도: {severity}. {description}"
        )

    return lines


def build_fallback_financial_context(ai_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    LLM 호출 실패 시 사용할 rule-based 재무 문맥을 생성합니다.
    """

    company_name = get_company_name(ai_input)
    stock_code = get_stock_code(ai_input)
    analysis_year = ai_input.get("analysis_year")
    base_year = ai_input.get("base_year")
    financial_metrics = ai_input.get("financial_metrics", {}) or {}
    detected_changes = ai_input.get("detected_changes", []) or []

    metric_lines = build_metric_summary_lines(financial_metrics)
    change_lines = build_detected_change_summary_lines(detected_changes)

    financial_context = "\n".join(
        [
            f"분석 기업: {company_name}",
            f"종목 코드: {stock_code}",
            f"분석 연도: {analysis_year}",
            f"비교 기준 연도: {base_year}",
            "",
            "[주요 재무 지표]",
            *metric_lines,
            "",
            "[탐지된 주요 재무 변동]",
            *change_lines,
            "",
            "[주의사항]",
            "- 위 수치는 이미 계산된 입력값을 기반으로 정리한 것입니다.",
            "- LLM은 재무 수치를 새로 계산하지 않고, 제공된 값만 해석해야 합니다.",
            "- 뉴스와 재무 지표의 관계는 인과관계가 아니라 가능한 배경 요인으로만 해석해야 합니다.",
        ]
    )

    detected_change_summary = "\n".join(change_lines)

    return {
        "company_info": {
            "company_name": company_name,
            "stock_code": stock_code,
        },
        "analysis_year": analysis_year,
        "base_year": base_year,
        "financial_context": financial_context,
        "metric_summary": "\n".join(metric_lines),
        "detected_change_summary": detected_change_summary,
        "raw_financial_metrics": financial_metrics,
        "raw_detected_changes": detected_changes,
        "source": "fallback",
    }


# ---------------------------------------------------------------------
# 3. Financial Context Builder Chain
# ---------------------------------------------------------------------

FINANCIAL_CONTEXT_BUILDER_SYSTEM_PROMPT = """
당신은 재무 분석 리포트를 위한 재무 문맥 정리 전문가입니다.

목표:
- 입력으로 제공된 기업 정보, 재무 지표, detected_changes를 바탕으로
  이후 리포트 작성 Chain이 사용할 수 있는 재무 문맥을 정리합니다.
- 계산을 새로 수행하지 말고, 입력에 이미 포함된 current_value, base_value, yoy_change_rate만 사용합니다.
- 재무 수치의 변화가 무엇인지 명확하게 정리하되, 원인은 단정하지 않습니다.

규칙:
1. 반드시 JSON만 반환하세요.
2. 설명 문장, 마크다운, 코드블록을 출력하지 마세요.
3. 재무 수치를 새로 계산하지 마세요.
4. 입력 데이터에 없는 수치를 만들지 마세요.
5. detected_changes가 있으면 어떤 지표가 얼마나 변했는지 요약하세요.
6. detected_changes가 없으면 안정적인 흐름으로 정리하되, 과장하지 마세요.
7. 투자 추천, 매수, 매도, 보유 판단은 절대 작성하지 마세요.
8. 원인 표현은 단정하지 말고, 이후 뉴스 근거와 함께 검토해야 한다는 식으로 표현하세요.

반환해야 하는 JSON 필드:
- company_info
- analysis_year
- base_year
- financial_context
- metric_summary
- detected_change_summary
- source

source 값은 "llm"으로 작성하세요.
"""


def build_financial_context_chain(llm):
    """
    공통 LLM 객체에 Financial Context Builder 전용 prompt를 연결한 Chain을 생성합니다.

    Args:
        llm: llm_client.py에서 생성한 공통 LLM 객체

    Returns:
        LangChain Runnable chain
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", FINANCIAL_CONTEXT_BUILDER_SYSTEM_PROMPT),
            (
                "human",
                """
다음 AI 입력 데이터를 바탕으로 재무 분석 리포트 작성에 사용할 financial_context JSON을 생성하세요.

AI 입력 데이터:
{ai_input_json}
""",
            ),
        ]
    )

    return prompt | llm | StrOutputParser()


def build_financial_context(
    llm,
    ai_input: Dict[str, Any],
) -> Dict[str, Any]:
    """
    LLM Chain을 사용해 재무 문맥을 생성합니다.

    Args:
        llm: llm_client.py에서 생성한 공통 LLM 객체
        ai_input: AI 리포트 생성 입력 데이터

    Returns:
        재무 문맥 dict
    """

    chain = build_financial_context_chain(llm)

    try:
        ai_input_json = json.dumps(ai_input, ensure_ascii=False, indent=2)

        raw_output = chain.invoke(
            {
                "ai_input_json": ai_input_json,
            }
        )

        parsed = extract_json_from_llm_output(raw_output)

        required_keys = [
            "company_info",
            "analysis_year",
            "base_year",
            "financial_context",
            "metric_summary",
            "detected_change_summary",
        ]

        for key in required_keys:
            if key not in parsed:
                raise ValueError(f"LLM 출력에 필수 key가 없습니다: {key}")

        parsed["raw_financial_metrics"] = ai_input.get("financial_metrics", {}) or {}
        parsed["raw_detected_changes"] = ai_input.get("detected_changes", []) or {}
        parsed["source"] = "llm"

        return parsed

    except Exception as error:
        print(f"[WARN] LLM 기반 재무 문맥 생성 실패. fallback context를 사용합니다: {error}")

        return build_fallback_financial_context(ai_input)


# ---------------------------------------------------------------------
# 4. 단독 실행 테스트
# ---------------------------------------------------------------------

if __name__ == "__main__":
    try:
        from src.ai.llm_client import get_llm
        from src.ai.sample_report_data import get_sample_ai_input
    except ModuleNotFoundError:
        from llm_client import get_llm
        from sample_report_data import get_sample_ai_input

    llm = get_llm()
    sample_ai_input = get_sample_ai_input(case="warning")

    financial_context = build_financial_context(
        llm=llm,
        ai_input=sample_ai_input,
    )

    print("[Financial Context]")
    print(json.dumps(financial_context, ensure_ascii=False, indent=2))