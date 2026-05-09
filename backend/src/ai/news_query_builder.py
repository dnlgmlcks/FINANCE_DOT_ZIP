"""
news_query_builder.py

detected_changes를 기반으로 Tavily 뉴스 검색용 쿼리를 생성하는
News Query Generator Chain 모듈입니다.

이번 AI 파이프라인은 하나의 공통 LLM 객체를 사용하되,
각 하위 Chain마다 서로 다른 system prompt를 적용해 역할을 분리하는 구조입니다.

이 파일의 역할:
1. sample_report_data.py 또는 Backend/Data 파트에서 전달한 ai_input을 입력으로 받습니다.
2. ai_input["detected_changes"]에 포함된 재무 지표 변화 정보를 분석합니다.
3. 공통 LLM 객체가 전달되면 News Query Generator prompt를 적용해 검색 쿼리를 생성합니다.
4. LLM 호출 실패 또는 llm 미전달 시 기존 rule-based 방식으로 fallback 쿼리를 생성합니다.
5. 이후 news_search_service.py에서 Tavily API에 전달할 query group 또는 flat query list를 반환합니다.

주의:
- 이 모듈은 재무 계산을 수행하지 않습니다.
- yoy_change_rate와 detected_changes는 Data/PM 파트에서 이미 계산되어 전달된다고 가정합니다.
- 이 파일 안에서 ChatOpenAI(...)를 새로 생성하지 않습니다.
- 공통 LLM 객체는 llm_client.py의 get_llm()으로 생성한 뒤 인자로 주입합니다.
"""

import json
from typing import Any, Dict, List, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


# ---------------------------------------------------------------------
# 1. 공통 유틸 함수
# ---------------------------------------------------------------------

def remove_duplicates(items: List[str]) -> List[str]:
    """
    리스트 내 중복 문자열을 제거합니다.
    순서는 유지합니다.

    Args:
        items: 문자열 리스트

    Returns:
        중복이 제거된 문자열 리스트
    """

    return list(dict.fromkeys(items))


def format_year(year: Any) -> str:
    """
    검색 쿼리에 사용할 연도 문자열을 생성합니다.
    year가 없을 경우 '최근'으로 대체합니다.

    Args:
        year: 분석 기준 연도

    Returns:
        검색 쿼리에 사용할 연도 문자열
    """

    if year is None:
        return "최근"

    return str(year)


def get_company_name(ai_input: Dict[str, Any]) -> str:
    """
    AI 입력 데이터에서 기업명을 추출합니다.

    Args:
        ai_input: AI 리포트 생성 입력 데이터

    Returns:
        기업명 문자열
    """

    company_info = ai_input.get("company_info", {}) or {}

    return (
        company_info.get("company_name")
        or ai_input.get("company_name")
        or "기업"
    )


def get_analysis_year(ai_input: Dict[str, Any]) -> Any:
    """
    AI 입력 데이터에서 분석 연도를 추출합니다.

    Args:
        ai_input: AI 리포트 생성 입력 데이터

    Returns:
        분석 연도
    """

    return ai_input.get("analysis_year")


def extract_json_from_llm_output(output: str) -> Dict[str, Any]:
    """
    LLM 응답 문자열에서 JSON을 파싱합니다.

    LLM이 ```json ... ``` 형태로 반환하는 경우도 처리합니다.

    Args:
        output: LLM 응답 문자열

    Returns:
        파싱된 dict
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
# 2. rule-based fallback 쿼리 생성 로직
# ---------------------------------------------------------------------

def build_default_news_queries(company_name: str) -> List[str]:
    """
    detected_changes가 없을 때 사용할 기본 뉴스 검색 쿼리를 생성합니다.

    Args:
        company_name: 기업명

    Returns:
        기본 뉴스 검색 쿼리 리스트
    """

    return [
        f"{company_name} 최근 실적 발표",
        f"{company_name} 최근 실적 전망",
        f"{company_name} 최근 사업 전략",
        f"{company_name} 최근 산업 동향",
    ]


def build_metric_template_queries(
    company_name: str,
    change: Dict[str, Any],
) -> List[str]:
    """
    개별 detected_change의 metric_key, change_type, direction을 기준으로
    기본 검색 쿼리 템플릿을 생성합니다.

    Args:
        company_name: 기업명
        change: detected_changes 내부의 개별 변화 정보

    Returns:
        검색 쿼리 리스트
    """

    metric_key = change.get("metric_key")
    metric_label = change.get("metric_label", "재무 지표")
    year = format_year(change.get("year"))
    direction = change.get("direction")
    change_type = change.get("change_type")

    if metric_key == "revenue":
        if direction == "decrease":
            return [
                f"{company_name} {year} 매출 감소 원인",
                f"{company_name} {year} 수요 둔화 매출 감소",
                f"{company_name} {year} 실적 부진 매출 감소",
            ]

        if direction == "increase":
            return [
                f"{company_name} {year} 매출 증가 배경",
                f"{company_name} {year} 신사업 성장 매출 증가",
                f"{company_name} {year} 수요 증가 실적 개선",
            ]

    if metric_key == "operating_income":
        if direction == "decrease":
            return [
                f"{company_name} {year} 영업이익 감소 원인",
                f"{company_name} {year} 영업이익 급감 배경",
                f"{company_name} {year} 비용 증가 영업이익 감소",
                f"{company_name} {year} 수익성 악화 실적 부진",
            ]

        if direction == "increase":
            return [
                f"{company_name} {year} 영업이익 증가 배경",
                f"{company_name} {year} 수익성 개선 원인",
                f"{company_name} {year} 비용 절감 영업이익 증가",
            ]

    if metric_key == "net_income":
        if change_type == "turn_to_loss":
            return [
                f"{company_name} {year} 적자 전환 원인",
                f"{company_name} {year} 당기순손실 배경",
                f"{company_name} {year} 순이익 감소 적자 전환",
                f"{company_name} {year} 수익성 악화 손실 발생",
            ]

        if direction == "decrease":
            return [
                f"{company_name} {year} 당기순이익 감소 원인",
                f"{company_name} {year} 순이익 감소 배경",
                f"{company_name} {year} 일회성 비용 순이익 감소",
            ]

        if direction == "increase":
            return [
                f"{company_name} {year} 당기순이익 증가 배경",
                f"{company_name} {year} 순이익 개선 원인",
                f"{company_name} {year} 실적 개선 순이익 증가",
            ]

    if metric_key == "debt_ratio":
        if direction == "increase":
            return [
                f"{company_name} {year} 부채비율 상승 원인",
                f"{company_name} {year} 차입금 증가 재무 부담",
                f"{company_name} {year} 재무구조 악화",
                f"{company_name} {year} 투자 확대 부채 증가",
            ]

        if direction == "decrease":
            return [
                f"{company_name} {year} 부채비율 감소 배경",
                f"{company_name} {year} 재무구조 개선",
                f"{company_name} {year} 차입금 상환 부채 감소",
            ]

    if metric_key == "operating_margin":
        if direction == "decrease":
            return [
                f"{company_name} {year} 영업이익률 하락 원인",
                f"{company_name} {year} 원가 상승 수익성 악화",
                f"{company_name} {year} 비용 증가 영업이익률 감소",
            ]

        if direction == "increase":
            return [
                f"{company_name} {year} 영업이익률 개선 원인",
                f"{company_name} {year} 수익성 개선 배경",
                f"{company_name} {year} 원가 절감 영업이익률 상승",
            ]

    if metric_key == "current_ratio":
        if direction == "decrease":
            return [
                f"{company_name} {year} 유동비율 하락 원인",
                f"{company_name} {year} 유동성 악화",
                f"{company_name} {year} 단기 지급능력 우려",
                f"{company_name} {year} 단기차입금 증가",
            ]

        if direction == "increase":
            return [
                f"{company_name} {year} 유동비율 개선 배경",
                f"{company_name} {year} 유동성 개선",
                f"{company_name} {year} 현금흐름 개선",
            ]

    return [
        f"{company_name} {year} {metric_label} 변동 원인",
        f"{company_name} {year} {metric_label} 변화 배경",
        f"{company_name} {year} 실적 변동 관련 이슈",
    ]


def build_keyword_queries(
    company_name: str,
    change: Dict[str, Any],
) -> List[str]:
    """
    detected_change의 search_keywords를 활용해 추가 검색 쿼리를 생성합니다.

    Args:
        company_name: 기업명
        change: detected_changes 내부의 개별 변화 정보

    Returns:
        search_keywords 기반 검색 쿼리 리스트
    """

    year = format_year(change.get("year"))
    keywords = change.get("search_keywords", []) or []

    return [
        f"{company_name} {year} {keyword}"
        for keyword in keywords
    ]


def build_news_queries_for_change(
    company_name: str,
    change: Dict[str, Any],
    max_queries_per_change: int = 5,
) -> List[str]:
    """
    detected_change 하나를 기반으로 fallback 뉴스 검색 쿼리를 생성합니다.

    Args:
        company_name: 기업명
        change: detected_changes 내부의 개별 변화 정보
        max_queries_per_change: 변화 항목 하나당 생성할 최대 쿼리 수

    Returns:
        해당 변화 항목에 대응하는 뉴스 검색 쿼리 리스트
    """

    template_queries = build_metric_template_queries(
        company_name=company_name,
        change=change,
    )
    keyword_queries = build_keyword_queries(
        company_name=company_name,
        change=change,
    )

    queries = template_queries + keyword_queries
    queries = remove_duplicates(queries)

    return queries[:max_queries_per_change]


def build_fallback_news_query_groups(
    ai_input: Dict[str, Any],
    max_queries_per_change: int = 5,
    include_default_when_empty: bool = True,
) -> List[Dict[str, Any]]:
    """
    LLM을 사용하지 않거나 LLM 쿼리 생성에 실패했을 때 사용할
    rule-based query group을 생성합니다.

    Args:
        ai_input: AI 리포트 생성 입력 데이터
        max_queries_per_change: 변화 항목 하나당 생성할 최대 쿼리 수
        include_default_when_empty: detected_changes가 없을 때 기본 검색 쿼리를 생성할지 여부

    Returns:
        detected_change별 query group 리스트
    """

    company_name = get_company_name(ai_input)
    detected_changes = ai_input.get("detected_changes", []) or []

    if not detected_changes:
        if not include_default_when_empty:
            return []

        analysis_year = get_analysis_year(ai_input)

        return [
            {
                "metric_key": "general",
                "metric_label": "일반 기업 뉴스",
                "year": analysis_year,
                "base_year": ai_input.get("base_year"),
                "change_type": "general",
                "direction": None,
                "severity": "low",
                "yoy_change_rate": None,
                "description": "유의미한 재무 변동이 탐지되지 않아 일반 기업 뉴스 검색어를 생성했습니다.",
                "queries": build_default_news_queries(company_name),
                "source": "fallback",
            }
        ]

    query_groups = []

    sorted_changes = sorted(
        detected_changes,
        key=lambda change: 0 if str(change.get("severity", "")).lower() == "high" else 1,
    )

    for change in sorted_changes:
        queries = build_news_queries_for_change(
            company_name=company_name,
            change=change,
            max_queries_per_change=max_queries_per_change,
        )

        query_groups.append(
            {
                "metric_key": change.get("metric_key"),
                "metric_label": change.get("metric_label"),
                "year": change.get("year"),
                "base_year": change.get("base_year"),
                "change_type": change.get("change_type"),
                "direction": change.get("direction"),
                "severity": change.get("severity"),
                "yoy_change_rate": change.get("yoy_change_rate"),
                "description": change.get("description"),
                "queries": queries,
                "source": "fallback",
            }
        )

    return query_groups


# ---------------------------------------------------------------------
# 3. News Query Generator Chain
# ---------------------------------------------------------------------

NEWS_QUERY_GENERATOR_SYSTEM_PROMPT = """
당신은 재무 분석 리포트 생성을 위한 뉴스 검색 쿼리 생성 전문가입니다.

목표:
- 기업의 재무 지표 변화(detected_changes)를 바탕으로 Tavily 뉴스 검색에 적합한 한국어 검색어를 생성합니다.
- 검색어는 너무 넓지 않아야 하며, 기업명, 연도, 재무 지표명, 변화 방향 또는 변화 배경을 포함해야 합니다.
- 검색 결과가 실제 재무 변화의 배경을 찾는 데 도움이 되도록 작성합니다.

규칙:
1. 반드시 JSON만 반환하세요.
2. 설명 문장, 마크다운, 코드블록을 출력하지 마세요.
3. 각 detected_change마다 query group 하나를 생성하세요.
4. 각 query group에는 queries를 3~5개 생성하세요.
5. 검색어에는 가능한 한 기업명과 연도를 포함하세요.
6. 재무 지표와 관련 없는 일반 뉴스 검색어는 피하세요.
7. 인과관계를 단정하지 말고, "원인", "배경", "관련 이슈", "실적 부진", "수익성 악화"처럼 탐색형 표현을 사용하세요.
8. 투자 추천, 매수, 매도, 보유 판단과 관련된 검색어는 생성하지 마세요.
9. 너무 일반적인 검색어는 피하세요.
   - 나쁜 예: "삼성전자 뉴스"
   - 좋은 예: "삼성전자 2025 영업이익 감소 원인"

반환 JSON 형식:
{{
  "query_groups": [
    {{
      "metric_key": "operating_income",
      "metric_label": "영업이익",
      "year": 2025,
      "base_year": 2024,
      "change_type": "sharp_decrease",
      "direction": "decrease",
      "severity": "high",
      "yoy_change_rate": -86.67,
      "description": "영업이익이 전년 대비 86.67% 감소했습니다.",
      "queries": [
        "삼성전자 2025 영업이익 감소 원인",
        "삼성전자 2025 수익성 악화 배경",
        "삼성전자 2025 비용 증가 영업이익 감소"
      ]
    }}
  ]
}}
"""


def build_news_query_generator_chain(llm):
    """
    공통 LLM 객체에 News Query Generator 전용 prompt를 연결한 Chain을 생성합니다.

    Args:
        llm: llm_client.py에서 생성한 공통 LLM 객체

    Returns:
        LangChain Runnable chain
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", NEWS_QUERY_GENERATOR_SYSTEM_PROMPT),
            (
                "human",
                """
다음 AI 입력 데이터를 바탕으로 Tavily 뉴스 검색용 query_groups JSON을 생성하세요.

AI 입력 데이터:
{ai_input_json}
""",
            ),
        ]
    )

    return prompt | llm | StrOutputParser()


def build_llm_news_query_groups(
    llm,
    ai_input: Dict[str, Any],
    max_queries_per_change: int = 5,
) -> List[Dict[str, Any]]:
    """
    LLM Chain을 사용해 detected_changes 기반 뉴스 검색 query_groups를 생성합니다.

    Args:
        llm: llm_client.py에서 생성한 공통 LLM 객체
        ai_input: AI 리포트 생성 입력 데이터
        max_queries_per_change: 변화 항목 하나당 생성할 최대 쿼리 수

    Returns:
        query group 리스트
    """

    chain = build_news_query_generator_chain(llm)

    ai_input_json = json.dumps(ai_input, ensure_ascii=False, indent=2)

    raw_output = chain.invoke(
        {
            "ai_input_json": ai_input_json,
        }
    )

    parsed = extract_json_from_llm_output(raw_output)
    query_groups = parsed.get("query_groups", [])

    if not isinstance(query_groups, list) or not query_groups:
        raise ValueError("LLM이 유효한 query_groups를 반환하지 않았습니다.")

    cleaned_query_groups = []

    for group in query_groups:
        queries = group.get("queries", []) or []
        queries = remove_duplicates(queries)[:max_queries_per_change]

        if not queries:
            continue

        cleaned_query_groups.append(
            {
                "metric_key": group.get("metric_key"),
                "metric_label": group.get("metric_label"),
                "year": group.get("year"),
                "base_year": group.get("base_year"),
                "change_type": group.get("change_type"),
                "direction": group.get("direction"),
                "severity": group.get("severity"),
                "yoy_change_rate": group.get("yoy_change_rate"),
                "description": group.get("description"),
                "queries": queries,
                "source": "llm",
            }
        )

    if not cleaned_query_groups:
        raise ValueError("정제 후 남은 query group이 없습니다.")

    return cleaned_query_groups


# ---------------------------------------------------------------------
# 4. 대표 실행 함수
# ---------------------------------------------------------------------

def build_news_queries(
    ai_input: Dict[str, Any],
    llm: Optional[Any] = None,
    max_queries_per_change: int = 5,
) -> List[Dict[str, Any]]:
    """
    detected_changes 기반 뉴스 검색 query group을 생성합니다.

    llm이 전달되면 News Query Generator Chain을 사용하고,
    llm이 없거나 LLM 호출에 실패하면 rule-based fallback 쿼리를 사용합니다.

    Args:
        ai_input: AI 리포트 생성 입력 데이터
        llm: llm_client.py에서 생성한 공통 LLM 객체. 없으면 fallback 방식 사용.
        max_queries_per_change: 변화 항목 하나당 생성할 최대 쿼리 수

    Returns:
        query group 리스트
    """

    if llm is None:
        return build_fallback_news_query_groups(
            ai_input=ai_input,
            max_queries_per_change=max_queries_per_change,
        )

    try:
        return build_llm_news_query_groups(
            llm=llm,
            ai_input=ai_input,
            max_queries_per_change=max_queries_per_change,
        )

    except Exception as error:
        print(f"[WARN] LLM 기반 뉴스 쿼리 생성 실패. fallback 쿼리를 사용합니다: {error}")

        return build_fallback_news_query_groups(
            ai_input=ai_input,
            max_queries_per_change=max_queries_per_change,
        )


def flatten_news_query_groups(query_groups: List[Dict[str, Any]]) -> List[str]:
    """
    query group 형태의 결과를 Tavily에 바로 넣기 쉬운 flat query list로 변환합니다.

    Args:
        query_groups: build_news_queries()의 반환값

    Returns:
        중복이 제거된 flat query list
    """

    flat_queries = []

    for group in query_groups:
        flat_queries.extend(group.get("queries", []))

    return remove_duplicates(flat_queries)


def build_flat_news_queries(
    ai_input: Dict[str, Any],
    llm: Optional[Any] = None,
    max_queries_per_change: int = 5,
) -> List[str]:
    """
    detected_changes 기반 뉴스 검색 쿼리를 flat list로 생성합니다.

    Args:
        ai_input: AI 리포트 생성 입력 데이터
        llm: 공통 LLM 객체. 없으면 fallback 방식 사용.
        max_queries_per_change: 변화 항목 하나당 생성할 최대 쿼리 수

    Returns:
        중복 제거된 Tavily 검색용 query list
    """

    query_groups = build_news_queries(
        ai_input=ai_input,
        llm=llm,
        max_queries_per_change=max_queries_per_change,
    )

    return flatten_news_query_groups(query_groups)


# ---------------------------------------------------------------------
# 5. 기존 warning_trigger.py 기반 코드 호환용 함수
# ---------------------------------------------------------------------

def build_news_queries_for_signal(
    company_name: str,
    signal: Dict[str, Any],
) -> List[str]:
    """
    기존 warning_trigger.py의 Warning Signal 하나를 기반으로
    Tavily 뉴스 검색 쿼리를 생성합니다.

    이 함수는 기존 테스트 코드와의 호환성을 위해 유지합니다.
    신규 AI 파이프라인에서는 build_news_queries() 사용을 권장합니다.
    """

    code = signal.get("code")
    year = format_year(signal.get("year"))
    signal_name = signal.get("signal", "재무 변동")
    metric = signal.get("metric", "재무 지표")

    if code == "HIGH_DEBT_RATIO":
        return [
            f"{company_name} {year} 부채비율 증가 원인",
            f"{company_name} {year} 차입금 증가 설비투자",
            f"{company_name} {year} 재무구조 악화",
        ]

    if code == "NET_LOSS":
        return [
            f"{company_name} {year} 적자 전환 원인",
            f"{company_name} {year} 당기순손실 배경",
            f"{company_name} {year} 수익성 악화",
        ]

    if code == "LOW_CURRENT_RATIO":
        return [
            f"{company_name} {year} 유동성 위험",
            f"{company_name} {year} 단기차입금 증가",
            f"{company_name} {year} 유동비율 하락",
        ]

    if code == "OPERATING_MARGIN_DROP":
        return [
            f"{company_name} {year} 영업이익률 하락 원인",
            f"{company_name} {year} 수익성 악화 비용 증가",
            f"{company_name} {year} 영업이익률 감소 배경",
        ]

    if code == "REVENUE_DROP":
        return [
            f"{company_name} {year} 매출 감소 원인",
            f"{company_name} {year} 수요 둔화 매출 감소",
            f"{company_name} {year} 실적 부진 매출",
        ]

    if code == "OPERATING_INCOME_DROP":
        return [
            f"{company_name} {year} 영업이익 감소 원인",
            f"{company_name} {year} 영업이익 급감 배경",
            f"{company_name} {year} 비용 증가 영업이익 감소",
        ]

    if code == "COST_LEVERAGE_RISK":
        return [
            f"{company_name} {year} 매출 감소 영업이익 감소 비용 구조",
            f"{company_name} {year} 고정비 부담 수익성 악화",
            f"{company_name} {year} 원가 부담 영업이익 감소",
        ]

    return [
        f"{company_name} {year} {signal_name} 원인",
        f"{company_name} {year} {metric} 변동 배경",
    ]


def generate_news_queries(
    company_name: str,
    warning_result: Dict[str, Any],
    max_queries: int = 8,
) -> List[str]:
    """
    기존 Warning Trigger 결과 전체를 기반으로 Tavily 검색 쿼리를 생성합니다.

    기존 테스트 코드와의 호환성을 위해 유지하는 함수입니다.
    신규 AI 파이프라인에서는 build_news_queries() 또는 build_flat_news_queries() 사용을 권장합니다.
    """

    signals = warning_result.get("signals", [])

    if not signals:
        return build_default_news_queries(company_name)[:max_queries]

    news_queries = []

    sorted_signals = sorted(
        signals,
        key=lambda signal: 0 if str(signal.get("severity", "")).upper() == "HIGH" else 1,
    )

    for signal in sorted_signals:
        queries = build_news_queries_for_signal(
            company_name=company_name,
            signal=signal,
        )
        news_queries.extend(queries)

    news_queries = remove_duplicates(news_queries)

    return news_queries[:max_queries]


# ---------------------------------------------------------------------
# 6. 단독 실행 테스트
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

    query_groups = build_news_queries(
        ai_input=sample_ai_input,
        llm=llm,
    )
    flat_queries = flatten_news_query_groups(query_groups)

    print("[Query Groups]")
    print(json.dumps(query_groups, ensure_ascii=False, indent=2))

    print("\n[Flat Queries]")
    for query in flat_queries:
        print("-", query)