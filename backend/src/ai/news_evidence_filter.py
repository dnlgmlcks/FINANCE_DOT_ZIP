"""
news_evidence_filter.py

Tavily로 수집한 뉴스 후보(searched_news) 중에서
재무 지표 변화와 관련 있는 기사만 선별하는 News Evidence Filter Chain 모듈입니다.

역할:
1. news_search_service.py가 수집한 후보 뉴스 리스트를 입력받습니다.
2. rule-based 1차 필터링으로 후보 뉴스에 rule_score를 부여합니다.
3. 공통 LLM 객체를 사용해 뉴스가 재무 변화의 근거로 적절한지 판단합니다.
4. LLM 결과를 그대로 믿지 않고, 코드 레벨에서 다시 검증합니다.
5. 최종적으로 report_writer_chain.py에서 사용할 evidence_news JSON을 반환합니다.

주의:
- news_search_service.py는 후보 뉴스 수집용입니다.
- 이 파일은 후보 뉴스 중 리포트 근거로 쓸 수 있는 뉴스만 선별합니다.
- 현재 disclosure_retriever.py가 아직 연결되지 않았으므로 evidence_disclosures는 빈 리스트로 반환합니다.
- Vector DB에 적재할 원천 뉴스 후보는 searched_news를 그대로 사용하면 됩니다.
"""

import json
from typing import Any, Dict, List, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


# ---------------------------------------------------------------------
# 1. 공통 유틸 함수
# ---------------------------------------------------------------------

def extract_json_from_llm_output(output: str) -> Dict[str, Any]:
    """
    LLM 응답 문자열에서 JSON을 파싱합니다.
    LLM이 코드블록 형태로 JSON을 반환하는 경우도 처리합니다.
    """

    cleaned = output.strip()
    fence = "`" * 3

    if cleaned.startswith(f"{fence}json"):
        cleaned = cleaned.replace(f"{fence}json", "", 1).strip()

    if cleaned.startswith(fence):
        cleaned = cleaned.replace(fence, "", 1).strip()

    if cleaned.endswith(fence):
        cleaned = cleaned[:-3].strip()

    return json.loads(cleaned)


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


def safe_text(value: Any) -> str:
    """
    None 또는 비문자열 값을 안전하게 문자열로 변환합니다.
    """

    if value is None:
        return ""

    return str(value)


def shorten_text(text: str, max_length: int = 1200) -> str:
    """
    LLM 입력이 너무 길어지지 않도록 텍스트를 자릅니다.
    """

    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[:max_length] + "...(truncated)"


def normalize_score(value: Any, default: float = 0.0) -> float:
    """
    relevance_score를 안전하게 float으로 변환합니다.
    """

    try:
        score = float(value)
    except (TypeError, ValueError):
        return default

    if score < 0:
        return 0.0

    if score > 1:
        return 1.0

    return round(score, 3)


# ---------------------------------------------------------------------
# 2. 지표별 관련 키워드 정의
# ---------------------------------------------------------------------

METRIC_KEYWORDS = {
    "revenue": [
        "매출",
        "매출액",
        "수요",
        "판매",
        "실적",
        "출하",
        "시장",
    ],
    "operating_income": [
        "영업이익",
        "영업익",
        "영업손실",
        "수익성",
        "비용",
        "원가",
        "감산",
        "반도체",
        "업황",
        "실적",
        "어닝쇼크",
    ],
    "net_income": [
        "당기순이익",
        "순이익",
        "순손실",
        "적자",
        "흑자",
        "손실",
        "수익성",
    ],
    "debt_ratio": [
        "부채",
        "부채비율",
        "차입금",
        "재무구조",
        "재무 부담",
        "자본",
        "재무건전성",
    ],
    "current_ratio": [
        "유동비율",
        "유동성",
        "단기차입금",
        "단기 지급",
        "현금흐름",
        "현금",
        "운전자본",
    ],
}


def contains_any_keyword(text: str, keywords: List[str]) -> bool:
    """
    텍스트에 키워드 중 하나라도 포함되어 있는지 확인합니다.
    """

    if not text:
        return False

    return any(keyword in text for keyword in keywords)


def is_metric_related(metric_key: str, text: str) -> bool:
    """
    기사 본문이 특정 재무 지표와 직접 관련 있는지 확인합니다.
    """

    keywords = METRIC_KEYWORDS.get(metric_key)

    if not keywords:
        return True

    return contains_any_keyword(text, keywords)


def has_company_name(company_name: str, text: str) -> bool:
    """
    기사 본문 또는 제목에 분석 대상 기업명이 포함되는지 확인합니다.
    """

    if not company_name:
        return True

    return company_name in text


# ---------------------------------------------------------------------
# 3. rule-based 1차 후보 정리
# ---------------------------------------------------------------------

def calculate_rule_score(
    ai_input: Dict[str, Any],
    news_item: Dict[str, Any],
) -> float:
    """
    뉴스 후보가 기업명/지표/연도/검색어와 얼마나 관련 있는지 간단히 점수화합니다.
    """

    score = 0.0

    company_name = get_company_name(ai_input)
    title = safe_text(news_item.get("title"))
    content = safe_text(news_item.get("content"))
    raw_content = safe_text(news_item.get("raw_content"))
    query = safe_text(news_item.get("query"))

    combined_text = f"{title} {content} {raw_content}"

    metric_key = safe_text(news_item.get("metric_key"))
    metric_label = safe_text(news_item.get("metric_label"))
    year = safe_text(news_item.get("year"))

    if company_name and company_name in combined_text:
        score += 2.0

    if metric_label and metric_label in combined_text:
        score += 1.5

    if metric_key and is_metric_related(metric_key, combined_text):
        score += 1.5

    if year and year in combined_text:
        score += 0.8

    query_terms = [
        term.strip()
        for term in query.split()
        if len(term.strip()) >= 2
    ]

    matched_terms = 0

    for term in query_terms:
        if term in combined_text:
            matched_terms += 1

    score += min(matched_terms * 0.25, 1.2)

    tavily_score = news_item.get("score")

    if isinstance(tavily_score, (int, float)):
        score += min(tavily_score, 1.0)

    return round(score, 3)


def prepare_news_candidates(
    ai_input: Dict[str, Any],
    searched_news: List[Dict[str, Any]],
    max_candidates: int = 15,
) -> List[Dict[str, Any]]:
    """
    searched_news 후보를 LLM에 넘기기 좋은 형태로 정리합니다.
    """

    candidates = []

    for idx, item in enumerate(searched_news, start=1):
        title = safe_text(item.get("title"))
        url = safe_text(item.get("url"))
        content = safe_text(item.get("content"))
        raw_content = safe_text(item.get("raw_content"))

        if not url or not (title or content or raw_content):
            continue

        rule_score = calculate_rule_score(
            ai_input=ai_input,
            news_item=item,
        )

        candidates.append(
            {
                "candidate_id": idx,
                "metric_key": item.get("metric_key"),
                "metric_label": item.get("metric_label"),
                "year": item.get("year"),
                "base_year": item.get("base_year"),
                "change_type": item.get("change_type"),
                "direction": item.get("direction"),
                "severity": item.get("severity"),
                "yoy_change_rate": item.get("yoy_change_rate"),
                "query": item.get("query"),
                "title": title,
                "url": url,
                "content": shorten_text(content, max_length=700),
                "raw_content": shorten_text(raw_content, max_length=1200),
                "published_date": item.get("published_date", ""),
                "tavily_score": item.get("score"),
                "rule_score": rule_score,
                "source": item.get("source", "tavily"),
            }
        )

    candidates = sorted(
        candidates,
        key=lambda item: item.get("rule_score", 0),
        reverse=True,
    )

    return candidates[:max_candidates]


def build_candidate_map(candidates: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """
    candidate_id 기준으로 후보 뉴스 맵을 생성합니다.
    """

    candidate_map = {}

    for candidate in candidates:
        candidate_id = candidate.get("candidate_id")

        if candidate_id is None:
            continue

        candidate_map[int(candidate_id)] = candidate

    return candidate_map


# ---------------------------------------------------------------------
# 4. evidence 후처리 검증
# ---------------------------------------------------------------------

def validate_evidence_item(
    ai_input: Dict[str, Any],
    evidence_item: Dict[str, Any],
    candidate: Dict[str, Any],
) -> bool:
    """
    LLM이 선별한 evidence가 실제 후보 뉴스와 지표에 맞는지 코드 레벨에서 검증합니다.
    """

    company_name = get_company_name(ai_input)
    metric_key = safe_text(candidate.get("metric_key"))

    title = safe_text(candidate.get("title"))
    content = safe_text(candidate.get("content"))
    raw_content = safe_text(candidate.get("raw_content"))
    evidence_summary = safe_text(evidence_item.get("evidence_summary"))
    reason = safe_text(evidence_item.get("reason"))

    combined_text = f"{title} {content} {raw_content} {evidence_summary} {reason}"

    if not has_company_name(company_name, combined_text):
        return False

    if not is_metric_related(metric_key, combined_text):
        return False

    return True


def clean_llm_evidence_news(
    ai_input: Dict[str, Any],
    evidence_news: List[Dict[str, Any]],
    candidate_map: Dict[int, Dict[str, Any]],
    max_evidence: int = 5,
) -> List[Dict[str, Any]]:
    """
    LLM이 반환한 evidence_news를 실제 후보 뉴스 기준으로 검증하고 정제합니다.
    """

    cleaned_evidence_news = []
    seen_keys = set()

    for item in evidence_news:
        candidate_id = item.get("candidate_id")

        if candidate_id is None:
            continue

        try:
            candidate_id = int(candidate_id)
        except (TypeError, ValueError):
            continue

        candidate = candidate_map.get(candidate_id)

        if not candidate:
            continue

        if not validate_evidence_item(
            ai_input=ai_input,
            evidence_item=item,
            candidate=candidate,
        ):
            continue

        dedup_key = (
            candidate.get("url"),
            candidate.get("metric_key"),
        )

        if dedup_key in seen_keys:
            continue

        seen_keys.add(dedup_key)

        relevance_score = normalize_score(
            item.get("relevance_score"),
            default=0.0,
        )

        if relevance_score == 0.0:
            relevance_score = min(
                round(candidate.get("rule_score", 0.0) / 6.0, 3),
                1.0,
            )

        cleaned_evidence_news.append(
            {
                "metric_key": candidate.get("metric_key"),
                "metric_label": candidate.get("metric_label"),
                "year": candidate.get("year"),
                "base_year": candidate.get("base_year"),
                "change_type": candidate.get("change_type"),
                "direction": candidate.get("direction"),
                "severity": candidate.get("severity"),
                "yoy_change_rate": candidate.get("yoy_change_rate"),
                "title": candidate.get("title", ""),
                "url": candidate.get("url", ""),
                "content": candidate.get("content", ""),
                "published_date": candidate.get("published_date", ""),
                "evidence_summary": item.get("evidence_summary", ""),
                "relevance_score": relevance_score,
                "reason": item.get("reason", ""),
                "source": "llm",
            }
        )

        if len(cleaned_evidence_news) >= max_evidence:
            break

    return cleaned_evidence_news


# ---------------------------------------------------------------------
# 5. fallback Evidence Filter
# ---------------------------------------------------------------------

def build_fallback_evidence_news(
    ai_input: Dict[str, Any],
    searched_news: List[Dict[str, Any]],
    max_evidence: int = 5,
) -> List[Dict[str, Any]]:
    """
    LLM 필터링 실패 시 사용할 fallback 근거 뉴스 선별 로직입니다.
    """

    candidates = prepare_news_candidates(
        ai_input=ai_input,
        searched_news=searched_news,
        max_candidates=20,
    )

    evidence_news = []
    seen_keys = set()

    for candidate in candidates:
        title = safe_text(candidate.get("title"))
        content = safe_text(candidate.get("content"))
        raw_content = safe_text(candidate.get("raw_content"))

        combined_text = f"{title} {content} {raw_content}"

        if candidate.get("rule_score", 0) < 3.0:
            continue

        if not has_company_name(get_company_name(ai_input), combined_text):
            continue

        if not is_metric_related(
            safe_text(candidate.get("metric_key")),
            combined_text,
        ):
            continue

        dedup_key = (
            candidate.get("url"),
            candidate.get("metric_key"),
        )

        if dedup_key in seen_keys:
            continue

        seen_keys.add(dedup_key)

        relevance_score = min(
            round(candidate.get("rule_score", 0.0) / 6.0, 3),
            1.0,
        )

        evidence_news.append(
            {
                "metric_key": candidate.get("metric_key"),
                "metric_label": candidate.get("metric_label"),
                "year": candidate.get("year"),
                "base_year": candidate.get("base_year"),
                "change_type": candidate.get("change_type"),
                "direction": candidate.get("direction"),
                "severity": candidate.get("severity"),
                "yoy_change_rate": candidate.get("yoy_change_rate"),
                "title": candidate.get("title"),
                "url": candidate.get("url"),
                "content": candidate.get("content"),
                "published_date": candidate.get("published_date"),
                "evidence_summary": "rule-based 기준으로 기업명과 재무 지표 관련성이 확인된 후보 뉴스입니다.",
                "relevance_score": relevance_score,
                "reason": "LLM 필터링 실패 또는 미사용으로 rule-based 점수를 기준으로 선별했습니다.",
                "source": "fallback_rule",
            }
        )

        if len(evidence_news) >= max_evidence:
            break

    return evidence_news


# ---------------------------------------------------------------------
# 6. News Evidence Filter Chain
# ---------------------------------------------------------------------

NEWS_EVIDENCE_FILTER_SYSTEM_PROMPT = """
당신은 재무 분석 리포트를 위한 뉴스 근거 선별 전문가입니다.

목표:
- Tavily로 수집된 후보 뉴스 중에서 기업의 재무 지표 변화와 관련 있는 기사만 선별합니다.
- 단순히 검색어가 일부 포함되었다는 이유만으로 관련 있다고 판단하지 않습니다.
- 기사 본문이 실제로 해당 기업, 해당 연도 또는 인접 시점, 해당 재무 지표 변화와 관련이 있는지 판단합니다.

중요 규칙:
1. 반드시 news_candidates에 존재하는 candidate_id만 선택하세요.
2. 새 기사 제목, 새 URL, 새 내용을 만들어내지 마세요.
3. candidate_id 없이 evidence를 만들지 마세요.
4. 기사 본문 핵심 내용이 분석 대상 기업과 무관하면 제외하세요.
5. 기업명이 추천기사, 사이드바, 광고, 관련기사 목록에만 등장하면 제외하세요.
6. 재무 지표와 직접 관련이 없는 기사는 제외하세요.
7. 동일한 기사를 여러 지표에 무리하게 연결하지 마세요.
8. 부채비율, 유동비율은 본문에 부채, 차입금, 유동성, 현금흐름 등 직접 관련 키워드가 있을 때만 선택하세요.
9. 메모리 반도체 업황 악화 기사는 매출액, 영업이익, 순이익 관련 근거로는 사용할 수 있지만, 부채비율/유동비율 근거로는 사용하지 마세요.
10. 투자 판단, 매수, 매도, 보유 추천으로 이어지는 내용은 제외하세요.
11. relevance_score는 0.0~1.0 사이 숫자로 작성하세요.
12. 관련성이 낮으면 evidence_news에 포함하지 마세요.
13. 근거가 부족하면 빈 리스트를 반환해도 됩니다.

반드시 JSON만 반환하세요.
마크다운, 설명 문장, 코드블록은 출력하지 마세요.

반환 JSON 형식:
{{
  "evidence_news": [
    {{
      "candidate_id": 1,
      "evidence_summary": "이 뉴스가 재무 변화와 관련 있는 배경 요약",
      "relevance_score": 0.82,
      "reason": "선별 이유"
    }}
  ]
}}
"""


def build_news_evidence_filter_chain(llm):
    """
    공통 LLM 객체에 News Evidence Filter 전용 prompt를 연결한 Chain을 생성합니다.
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", NEWS_EVIDENCE_FILTER_SYSTEM_PROMPT),
            (
                "human",
                """
다음 정보를 바탕으로 리포트 근거로 사용할 수 있는 evidence_news JSON을 생성하세요.

분석 대상 기업:
{company_name}

AI 입력 데이터:
{ai_input_json}

재무 문맥:
{financial_context_json}

뉴스 후보:
{news_candidates_json}
""",
            ),
        ]
    )

    return prompt | llm | StrOutputParser()


def filter_news_evidence_with_llm(
    llm,
    ai_input: Dict[str, Any],
    financial_context: Dict[str, Any],
    searched_news: List[Dict[str, Any]],
    max_candidates: int = 15,
    max_evidence: int = 5,
) -> List[Dict[str, Any]]:
    """
    LLM Chain을 사용해 evidence_news를 선별합니다.
    """

    news_candidates = prepare_news_candidates(
        ai_input=ai_input,
        searched_news=searched_news,
        max_candidates=max_candidates,
    )

    if not news_candidates:
        return []

    candidate_map = build_candidate_map(news_candidates)

    chain = build_news_evidence_filter_chain(llm)

    raw_output = chain.invoke(
        {
            "company_name": get_company_name(ai_input),
            "ai_input_json": json.dumps(
                ai_input,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            "financial_context_json": json.dumps(
                financial_context,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            "news_candidates_json": json.dumps(
                news_candidates,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
        }
    )

    parsed = extract_json_from_llm_output(raw_output)

    evidence_news = parsed.get("evidence_news", [])

    if not isinstance(evidence_news, list):
        raise ValueError("LLM 출력의 evidence_news가 list가 아닙니다.")

    return clean_llm_evidence_news(
        ai_input=ai_input,
        evidence_news=evidence_news,
        candidate_map=candidate_map,
        max_evidence=max_evidence,
    )


# ---------------------------------------------------------------------
# 7. 대표 실행 함수
# ---------------------------------------------------------------------

def filter_evidence(
    llm,
    ai_input: Dict[str, Any],
    financial_context: Dict[str, Any],
    searched_news: List[Dict[str, Any]],
    disclosure_context: Optional[Dict[str, Any]] = None,
    max_candidates: int = 15,
    max_evidence: int = 5,
) -> Dict[str, Any]:
    """
    뉴스 후보와 공시 후보를 통합해 최종 evidence를 반환합니다.

    현재는 disclosure_retriever.py가 연결되지 않았으므로
    evidence_disclosures는 빈 리스트로 반환합니다.
    """

    if not searched_news:
        return {
            "evidence_news": [],
            "evidence_disclosures": [],
            "metadata": {
                "searched_news_count": 0,
                "evidence_news_count": 0,
                "evidence_disclosure_count": 0,
                "source": "empty",
            },
        }

    try:
        evidence_news = filter_news_evidence_with_llm(
            llm=llm,
            ai_input=ai_input,
            financial_context=financial_context,
            searched_news=searched_news,
            max_candidates=max_candidates,
            max_evidence=max_evidence,
        )

        source = "llm"

    except Exception as error:
        print(f"[WARN] LLM 기반 뉴스 근거 선별 실패. fallback evidence를 사용합니다: {error}")

        evidence_news = build_fallback_evidence_news(
            ai_input=ai_input,
            searched_news=searched_news,
            max_evidence=max_evidence,
        )

        source = "fallback"

    return {
        "evidence_news": evidence_news,
        "evidence_disclosures": [],
        "metadata": {
            "searched_news_count": len(searched_news),
            "evidence_news_count": len(evidence_news),
            "evidence_disclosure_count": 0,
            "source": source,
        },
    }


def filter_news_evidence(
    llm,
    ai_input: Dict[str, Any],
    financial_context: Dict[str, Any],
    searched_news: List[Dict[str, Any]],
    disclosure_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    filter_evidence()의 alias 함수입니다.
    """

    return filter_evidence(
        llm=llm,
        ai_input=ai_input,
        financial_context=financial_context,
        searched_news=searched_news,
        disclosure_context=disclosure_context,
    )


# ---------------------------------------------------------------------
# 8. 단독 실행 테스트
# ---------------------------------------------------------------------

if __name__ == "__main__":
    try:
        from src.ai.llm_client import get_llm
        from src.ai.sample_report_data import get_sample_ai_input
        from src.ai.financial_context_builder import build_financial_context
        from src.ai.news_query_builder import build_news_queries
        from src.ai.news_search_service import search_news_by_query_groups
    except ModuleNotFoundError:
        from llm_client import get_llm
        from sample_report_data import get_sample_ai_input
        from financial_context_builder import build_financial_context
        from news_query_builder import build_news_queries
        from news_search_service import search_news_by_query_groups

    llm = get_llm()

    sample_ai_input = get_sample_ai_input(case="warning")

    sample_ai_input["company_info"]["company_name"] = "삼성전자"
    sample_ai_input["company_info"]["stock_code"] = "005930"
    sample_ai_input["analysis_year"] = 2023
    sample_ai_input["base_year"] = 2022

    for change in sample_ai_input.get("detected_changes", []):
        change["year"] = 2023
        change["base_year"] = 2022

    financial_context = build_financial_context(
        llm=llm,
        ai_input=sample_ai_input,
    )

    query_groups = build_news_queries(
        ai_input=sample_ai_input,
        llm=llm,
    )

    searched_news = search_news_by_query_groups(
        query_groups=query_groups,
        max_results_per_query=5,
        max_total_results=20,
    )

    evidence = filter_evidence(
        llm=llm,
        ai_input=sample_ai_input,
        financial_context=financial_context,
        searched_news=searched_news,
    )

    print("[News Evidence Filter Test]")
    print("searched_news_count:", len(searched_news))
    print("evidence_news_count:", len(evidence.get("evidence_news", [])))

    print("\n[Evidence]")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))