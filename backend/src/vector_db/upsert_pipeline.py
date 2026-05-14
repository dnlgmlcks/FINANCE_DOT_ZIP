"""
Vector DB 적재 파이프라인
"""

import csv
import json
from pathlib import Path

from src.vector_db.document_builder import (
    build_documents_from_news_list,
    build_documents_from_disclosure_rows,
)

from src.vector_db.news_preprocessor import (
    preprocess_news_list,
)

from src.vector_db.vector_store import upsert_documents


def get_project_root():
    current = Path(__file__).resolve()

    for parent in current.parents:
        if (parent / "data" / "export" / "disclosure").exists():
            return parent

    raise RuntimeError(
        "프로젝트 루트 또는 data/export/disclosure 폴더를 찾을 수 없습니다."
    )


def load_json_file(file_path):
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        if "articles" in data:
            return data["articles"]

        if "news" in data:
            return data["news"]

        if "data" in data:
            return data["data"]

    return []


def load_csv_file(file_path):
    path = Path(file_path)

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)
        return list(reader)


def upsert_news_json(
    json_path,
    detected_change=None,
    index_name="finance-dot-news",
):
    """
    뉴스 JSON 파일 적재
    """

    news_list = load_json_file(json_path)

    return upsert_news_articles(
        news_list=news_list,
        detected_change=detected_change,
        index_name=index_name,
    )


def upsert_news_articles(
    news_list,
    detected_change=None,
    index_name="finance-dot-news",
):
    """
    실시간 뉴스 기사 리스트 적재

    사용 예시:
    - Tavily 검색 결과
    - 뉴스 API 응답
    - 전처리 완료된 뉴스 article list
    """

    preprocessed_news_list = preprocess_news_list(
        news_list,
        detected_change=detected_change,
    )

    documents = build_documents_from_news_list(
        preprocessed_news_list
    )

    result = upsert_documents(
        documents=documents,
        index_name=index_name,
    )

    return {
        **result,
        "data_type": "news",
        "input_count": len(news_list),
    }


def upsert_disclosure_csv(
    csv_path,
    index_name="finance-dot-news",
):
    rows = load_csv_file(csv_path)

    documents = build_documents_from_disclosure_rows(
        rows
    )

    result = upsert_documents(
        documents=documents,
        index_name=index_name,
    )

    return {
        **result,
        "data_type": "disclosure",
        "source_file": str(csv_path),
    }


def upsert_disclosure_folder(
    folder_path=None,
    index_name="finance-dot-news",
):
    if folder_path is None:
        project_root = get_project_root()

        folder = (
            project_root
            / "data"
            / "export"
            / "disclosure"
        )

    else:
        folder = Path(folder_path).resolve()

    print("[DEBUG] disclosure folder:", folder)
    print("[DEBUG] folder exists:", folder.exists())

    csv_files = list(folder.rglob("*.csv"))

    print("[DEBUG] csv file count:", len(csv_files))

    for csv_file in csv_files[:5]:
        print("[DEBUG] csv sample:", csv_file)

    results = []

    for csv_file in csv_files:
        result = upsert_disclosure_csv(
            csv_path=csv_file,
            index_name=index_name,
        )

        results.append(result)

    total_count = sum(
        item.get("count", 0)
        for item in results
    )

    return {
        "status": "success",
        "message": "공시 CSV 폴더 적재 완료",
        "total_files": len(csv_files),
        "total_count": total_count,
        "results": results,
    }


if __name__ == "__main__":

    # =========================
    # 공시 데이터 적재 테스트
    # =========================

    disclosure_result = upsert_disclosure_folder(
        index_name="finance-dot-news",
    )

    print(disclosure_result)

    # =========================
    # 뉴스 데이터 적재 테스트
    # =========================
    # 실제 뉴스 JSON 파일이 있을 경우 사용
    #
    # news_result = upsert_news_json(
    #     json_path="../../data/news/news_sample.json",
    #     detected_change={
    #         "stock_code": "005930",
    #         "company_name": "삼성전자",
    #         "signal_type": "negative",
    #         "signal_code": "OPERATING_INCOME_DROP_HIGH",
    #         "industry_group": "tech_equipment",
    #         "year": 2023,
    #     },
    #     index_name="finance-dot-news",
    # )
    #
    # print(news_result)