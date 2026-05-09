"""
test_news_query_builder.py

AI 파트의 뉴스 검색 쿼리 생성기가 정상적으로 동작하는지 확인하기 위한 테스트 파일입니다.

테스트 목적:
1. sample_report_data.py에서 AI 입력용 Mock 데이터를 불러옵니다.
2. ai_input["detected_changes"]를 기반으로 query_groups를 생성합니다.
3. 정상 케이스와 위험 케이스에서 검색 쿼리가 의도대로 생성되는지 확인합니다.

실행 방법:
    cd backend
    python -m tests.test_news_query_builder

주의:
    이 파일은 backend 폴더를 기준으로 실행하는 것을 전제로 합니다.
    따라서 import 경로는 `src.ai...` 형식을 사용합니다.
"""

from src.ai.sample_report_data import get_sample_ai_input
from src.ai.news_query_builder import build_news_queries, build_flat_news_queries


def print_news_query_groups(case: str) -> None:
    """
    지정한 테스트 케이스에 대해 뉴스 검색 query_groups를 출력합니다.

    Args:
        case: "normal" 또는 "warning"
    """

    ai_input = get_sample_ai_input(case=case)

    company_name = ai_input["company_info"]["company_name"]
    detected_changes = ai_input.get("detected_changes", [])

    query_groups = build_news_queries(ai_input)
    flat_queries = build_flat_news_queries(ai_input)

    print(f"\n===== {case.upper()} CASE =====")
    print("Company:", company_name)
    print("Detected Change Count:", len(detected_changes))
    print("Query Group Count:", len(query_groups))
    print("Flat Query Count:", len(flat_queries))

    print("\n[Generated Query Groups]")
    for idx, group in enumerate(query_groups, start=1):
        print(f"\n[{idx}] {group.get('metric_label')}")
        print("metric_key:", group.get("metric_key"))
        print("year:", group.get("year"))
        print("severity:", group.get("severity"))

        for query_idx, query in enumerate(group.get("queries", []), start=1):
            print(f"  {query_idx}. {query}")

    print("\n[Flat Queries]")
    for idx, query in enumerate(flat_queries, start=1):
        print(f"{idx}. {query}")


def validate_news_query_groups(case: str) -> None:
    """
    query_groups의 기본 구조를 간단히 검증합니다.

    Args:
        case: "normal" 또는 "warning"
    """

    ai_input = get_sample_ai_input(case=case)
    query_groups = build_news_queries(ai_input)

    assert isinstance(query_groups, list)
    assert len(query_groups) > 0

    for group in query_groups:
        assert "metric_key" in group
        assert "metric_label" in group
        assert "queries" in group
        assert isinstance(group["queries"], list)
        assert len(group["queries"]) > 0

    print(f"[PASS] {case} case query group validation passed.")


if __name__ == "__main__":
    print_news_query_groups("normal")
    print_news_query_groups("warning")

    validate_news_query_groups("normal")
    validate_news_query_groups("warning")