"""
news_search_service.py

news_query_builder.py에서 생성한 query_groups를 기반으로
Tavily API를 호출하여 뉴스 검색 결과를 수집하고 정제하는 서비스 모듈입니다.

역할:
1. query_groups를 입력받습니다.
2. 각 query를 Tavily API로 검색합니다.
3. title, url, content, raw_content, published_date 형태로 결과를 정제합니다.
4. 중복 URL을 제거합니다.
5. 빈 결과와 API 에러를 안전하게 처리합니다.

주의:
- 이 파일은 LLM Chain이 아닙니다.
- Tavily API 호출과 검색 결과 정제만 담당합니다.
- 이 단계에서는 최종 근거 뉴스를 선별하지 않습니다.
- 관련성 판단, 기업명/연도/지표 기준 필터링은 이후 news_evidence_filter.py에서 수행합니다.
- 이 파일의 목적은 다른 팀원이 전처리 및 Vector DB 적재에 사용할 후보 뉴스 리스트를 수집하는 것입니다.
"""

import json
import os
from typing import Any, Dict, List, Optional, Set

from dotenv import load_dotenv
from tavily import TavilyClient


load_dotenv()


# 국내 뉴스 후보 수집에 사용할 도메인 목록
# 너무 강하게 제한하면 결과가 0개가 될 수 있으므로,
# 주요 경제/산업/IT 언론 위주로 구성합니다.
KOREAN_NEWS_DOMAINS = [
    "yna.co.kr",
    "newsis.com",
    "hankyung.com",
    "mk.co.kr",
    "sedaily.com",
    "edaily.co.kr",
    "etnews.com",
    "zdnet.co.kr",
    "biz.chosun.com",
    "thelec.kr",
    "fnnews.com",
    "mt.co.kr",
    "asiae.co.kr",
    "heraldcorp.com",
    "chosun.com",
    "joongang.co.kr",
    "donga.com",
    "ddaily.co.kr",
    "bloter.net",
    "it.chosun.com",
]


# ---------------------------------------------------------------------
# 1. Tavily Client
# ---------------------------------------------------------------------

def get_tavily_client() -> TavilyClient:
    """
    TAVILY_API_KEY를 사용해 TavilyClient를 생성합니다.

    Returns:
        TavilyClient: Tavily API 클라이언트

    Raises:
        ValueError: TAVILY_API_KEY가 설정되어 있지 않은 경우
    """

    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise ValueError(
            "TAVILY_API_KEY가 설정되어 있지 않습니다. "
            ".env 파일 또는 환경 변수에 TAVILY_API_KEY를 추가해주세요."
        )

    return TavilyClient(api_key=api_key)


# ---------------------------------------------------------------------
# 2. 검색 결과 정제 유틸
# ---------------------------------------------------------------------

def normalize_news_item(
    item: Dict[str, Any],
    query: str,
    query_group: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Tavily 검색 결과 하나를 서비스에서 사용할 뉴스 dict 형태로 정제합니다.

    Args:
        item: Tavily results 내부의 개별 검색 결과
        query: 검색에 사용한 query
        query_group: 해당 query가 속한 query group

    Returns:
        정제된 뉴스 dict
    """

    return {
        # 어떤 재무 변화 때문에 검색된 뉴스인지 추적하기 위한 정보
        "metric_key": query_group.get("metric_key"),
        "metric_label": query_group.get("metric_label"),
        "year": query_group.get("year"),
        "base_year": query_group.get("base_year"),
        "change_type": query_group.get("change_type"),
        "direction": query_group.get("direction"),
        "severity": query_group.get("severity"),
        "yoy_change_rate": query_group.get("yoy_change_rate"),

        # 실제 검색 query
        "query": query,

        # Tavily 검색 결과 원문 정보
        "title": item.get("title", ""),
        "url": item.get("url", ""),
        "content": item.get("content", ""),
        "raw_content": item.get("raw_content", ""),
        "published_date": item.get("published_date", ""),
        "score": item.get("score"),

        # 출처 구분
        "source": "tavily",
    }


def is_valid_news_item(news_item: Dict[str, Any]) -> bool:
    """
    뉴스 검색 결과가 최소 사용 가능한 형태인지 확인합니다.

    news_search_service.py는 뉴스 후보 수집이 목적이므로
    관련성 판단을 강하게 하지 않습니다.

    관련성 판단은 이후 news_evidence_filter.py에서 수행합니다.

    조건:
    1. URL이 있어야 함
    2. title 또는 content 또는 raw_content 중 하나는 있어야 함
    """

    has_url = bool(news_item.get("url"))

    has_text = bool(
        news_item.get("title")
        or news_item.get("content")
        or news_item.get("raw_content")
    )

    return has_url and has_text


def remove_duplicate_news(news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    URL 기준으로 중복 뉴스를 제거합니다.

    Args:
        news_items: 정제된 뉴스 리스트

    Returns:
        중복 제거된 뉴스 리스트
    """

    seen_urls: Set[str] = set()
    unique_items = []

    for item in news_items:
        url = item.get("url", "")

        if not url:
            continue

        if url in seen_urls:
            continue

        seen_urls.add(url)
        unique_items.append(item)

    return unique_items


# ---------------------------------------------------------------------
# 3. Tavily 검색 실행
# ---------------------------------------------------------------------

def search_news_once(
    client: TavilyClient,
    query: str,
    query_group: Dict[str, Any],
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    query 하나에 대해 Tavily 검색을 수행합니다.

    Args:
        client: TavilyClient
        query: 검색어
        query_group: 해당 query가 속한 query group
        max_results: query당 최대 검색 결과 수

    Returns:
        정제된 뉴스 후보 결과 리스트
    """

    try:
        # topic="news"가 글로벌 영어 뉴스로 튀는 경우가 있어
        # 국내 결과 우선 수집을 위해 topic="general" + country="south korea" 조합을 사용합니다.
        response = client.search(
            query=f"{query} 국내 뉴스 한국어 기사",
            topic="general",
            country="south korea",
            search_depth="basic",
            max_results=max_results,
            include_domains=KOREAN_NEWS_DOMAINS,
            include_answer=False,
            include_raw_content=True,
            include_images=False,
        )

        results = response.get("results", []) or []

        normalized_results = []

        for item in results:
            news_item = normalize_news_item(
                item=item,
                query=query,
                query_group=query_group,
            )

            if is_valid_news_item(news_item):
                normalized_results.append(news_item)

        return normalized_results

    except Exception as error:
        print(f"[WARN] Tavily 검색 실패: query={query}, error={error}")
        return []


def search_news_by_query_groups(
    query_groups: List[Dict[str, Any]],
    max_results_per_query: int = 5,
    max_total_results: int = 30,
    client: Optional[TavilyClient] = None,
) -> List[Dict[str, Any]]:
    """
    query_groups 전체에 대해 Tavily 검색을 수행합니다.

    Args:
        query_groups: news_query_builder.py에서 생성한 query group 리스트
        max_results_per_query: query 하나당 최대 검색 결과 수
        max_total_results: 최종 반환할 최대 뉴스 개수
        client: 외부에서 주입할 TavilyClient. 없으면 내부에서 생성.

    Returns:
        정제 및 중복 제거된 뉴스 후보 리스트
    """

    if client is None:
        client = get_tavily_client()

    searched_news = []

    for query_group in query_groups:
        queries = query_group.get("queries", []) or []

        for query in queries:
            news_results = search_news_once(
                client=client,
                query=query,
                query_group=query_group,
                max_results=max_results_per_query,
            )

            searched_news.extend(news_results)

    searched_news = remove_duplicate_news(searched_news)

    return searched_news[:max_total_results]


def search_news_by_queries(
    query_groups: List[Dict[str, Any]],
    max_results_per_query: int = 5,
    max_total_results: int = 30,
    client: Optional[TavilyClient] = None,
) -> List[Dict[str, Any]]:
    """
    search_news_by_query_groups()의 alias 함수입니다.

    다른 모듈에서 함수명을 직관적으로 사용할 수 있도록 제공합니다.

    Args:
        query_groups: news_query_builder.py에서 생성한 query group 리스트
        max_results_per_query: query 하나당 최대 검색 결과 수
        max_total_results: 최종 반환할 최대 뉴스 개수
        client: 외부에서 주입할 TavilyClient. 없으면 내부에서 생성.

    Returns:
        정제 및 중복 제거된 뉴스 후보 리스트
    """

    return search_news_by_query_groups(
        query_groups=query_groups,
        max_results_per_query=max_results_per_query,
        max_total_results=max_total_results,
        client=client,
    )


# ---------------------------------------------------------------------
# 4. 단독 실행 테스트
# ---------------------------------------------------------------------

if __name__ == "__main__":
    try:
        from src.ai.llm_client import get_llm
        from src.ai.sample_report_data import get_sample_ai_input
        from src.ai.news_query_builder import build_news_queries
    except ModuleNotFoundError:
        from llm_client import get_llm
        from sample_report_data import get_sample_ai_input
        from news_query_builder import build_news_queries

    llm = get_llm()
    sample_ai_input = get_sample_ai_input(case="warning")

    # Tavily 검색 테스트는 실제 뉴스가 존재하는 기업명으로 수행합니다.
    # 테스트기업은 Mock 이름이라 검색 결과가 부정확하게 나올 수 있습니다.
    sample_ai_input["company_info"]["company_name"] = "삼성전자"
    sample_ai_input["company_info"]["stock_code"] = "005930"
    sample_ai_input["analysis_year"] = 2023
    sample_ai_input["base_year"] = 2022

    for change in sample_ai_input.get("detected_changes", []):
        change["year"] = 2023
        change["base_year"] = 2022

    query_groups = build_news_queries(
        ai_input=sample_ai_input,
        llm=llm,
    )

    searched_news = search_news_by_query_groups(
        query_groups=query_groups,
        max_results_per_query=5,
        max_total_results=30,
    )

    print("[News Search Service Test]")
    print("query_group_count:", len(query_groups))
    print("searched_news_count:", len(searched_news))

    print("\n[Searched News]")
    print(json.dumps(searched_news, ensure_ascii=False, indent=2))