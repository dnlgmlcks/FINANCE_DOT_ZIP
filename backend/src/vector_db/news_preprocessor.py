"""
뉴스 데이터 전처리 모듈

역할:
- Tavily / 뉴스 JSON 결과의 title, content 텍스트 정제
- 이메일, 불필요한 괄호, 과도한 공백 제거
- 금융/산업 용어 정규화
- Vector DB 적재 전 뉴스 article 구조 통일

주의:
- 실제 Tavily Search 실행은 AI/Agent 파트 담당
- 본 모듈은 전달받은 뉴스 데이터를 Vector DB 적재 가능한 형태로 정제하는 역할만 담당
"""

import re


FINANCE_TERMS = {
    "semiconductor": {
        "반도체": ["메모리", "D램", "DRAM", "낸드", "NAND", "파운드리"],
        "업황 둔화": ["수요 둔화", "수요 부진", "경기 둔화"],
        "가격 하락": ["가격 약세", "단가 하락", "ASP 하락"],
    },
    "finance": {
        "영업이익 감소": ["영업익 감소", "영업이익 급감", "수익성 악화"],
        "매출 감소": ["매출액 감소", "외형 축소"],
        "재무 부담": ["차입 부담", "부채 부담", "유동성 우려"],
    },
}


def normalize_finance_terms(text: str) -> str:
    if not text:
        return ""

    normalized_text = str(text)

    for category_dict in FINANCE_TERMS.values():
        for standard_term, synonyms in category_dict.items():
            for synonym in synonyms:
                normalized_text = normalized_text.replace(
                    synonym,
                    standard_term,
                )

    return normalized_text


def clean_news_text(text: str) -> str:
    if not text:
        return ""

    cleaned = str(text)

    # 이메일 제거
    cleaned = re.sub(
        r"[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        "",
        cleaned,
    )

    # 기자명/불필요한 괄호 표현 일부 제거
    cleaned = re.sub(r"\(.*?\)|\[.*?\]", "", cleaned)

    # 과도한 특수문자 정리
    cleaned = re.sub(r"[^\w\s\.\,\%\-\+\/가-힣]", " ", cleaned)

    # 공백 정리
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    cleaned = normalize_finance_terms(cleaned)

    return cleaned


def preprocess_news_article(news: dict, detected_change: dict | None = None) -> dict:
    detected_change = detected_change or {}

    title = (
        news.get("title")
        or news.get("headline")
        or ""
    )

    content = (
        news.get("content")
        or news.get("text")
        or news.get("body")
        or news.get("raw_content")
        or ""
    )

    cleaned_title = clean_news_text(title)
    cleaned_content = clean_news_text(content)

    return {
        "title": cleaned_title,
        "content": cleaned_content,

        "stock_code": (
            news.get("stock_code")
            or detected_change.get("stock_code")
            or ""
        ),
        "company_name": (
            news.get("company_name")
            or news.get("company")
            or detected_change.get("company_name")
            or ""
        ),
        "signal_type": (
            news.get("signal_type")
            or detected_change.get("signal_type")
            or "unknown"
        ),
        "signal_code": (
            news.get("signal_code")
            or detected_change.get("signal_code")
            or "unknown"
        ),
        "industry_group": (
            news.get("industry_group")
            or detected_change.get("industry_group")
            or "unknown"
        ),
        "year": (
            news.get("year")
            or detected_change.get("year")
        ),

        "source": (
            news.get("source")
            or "news"
        ),
        "source_url": (
            news.get("source_url")
            or news.get("url")
            or ""
        ),
        "date": (
            news.get("date")
            or news.get("published_date")
            or news.get("published_at")
            or ""
        ),
    }


def preprocess_news_list(news_list, detected_change: dict | None = None) -> list:
    if not news_list:
        return []

    return [
        preprocess_news_article(
            news,
            detected_change=detected_change,
        )
        for news in news_list
    ]