"""
OpenDART 단일회사 전체 재무제표 API 수집 및 계정 매핑 점검 스크립트.

이번 스크립트는 계산 로직, DB 저장 로직, Warning Signal 로직을 건드리지 않고
fnlttSinglAcntAll.json 응답에서 기존 전처리 규격에 맞는 계정 후보를 찾는 데만
사용합니다.
"""

import csv
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

from dotenv import load_dotenv


# backend/src 기준으로 실행해도, 프로젝트 루트에서 실행해도 import가 되도록
# src 경로를 명시적으로 추가합니다.
BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE_DIR))

# 기존 설정 모듈은 backend/.env를 우선 찾기 때문에, 프로젝트 루트 .env와
# 프로젝트 내부 data 경로를 먼저 환경변수로 주입합니다. API 키 값은 출력하지 않습니다.
load_dotenv(PROJECT_ROOT / ".env")
os.environ.setdefault("DATA_RAW_PATH", str(PROJECT_ROOT / "data" / "raw"))
os.environ.setdefault("DATA_INTERIM_PATH", str(PROJECT_ROOT / "data" / "interim"))
os.environ.setdefault("DATA_PROCESSED_PATH", str(PROJECT_ROOT / "data" / "processed"))

from services.financial_processor import (
    ALL_STANDARD_ACCOUNTS,
    CURRENT_SIGNAL_REQUIRED_ACCOUNTS,
    NOT_REQUIRED_FOR_CURRENT_SIGNAL_ACCOUNTS,
    STANDARD_ACCOUNT_CANDIDATES,
    build_single_all_account_availability,
    build_single_all_account_inventory,
    build_single_all_standard_financials,
    find_standard_account_in_item,
    get_string_fields,
    write_csv,
    write_json,
)


STOCK_CODE = "005930"
COMPANY_NAME = "삼성전자"
YEARS = [2019, 2020, 2021, 2022, 2023]
REPORT_CODE = os.getenv("TARGET_REPORT_CODE", "11011")
FS_DIV = "CFS"

RAW_MAIN_PATH = PROJECT_ROOT / "data" / "raw" / "samsung_electronics_2023_2019.json"
RAW_SINGLE_ALL_PATH = PROJECT_ROOT / "data" / "raw" / "samsung_single_all_accounts_2019_2023.json"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


SEARCH_TERMS = [
    *CURRENT_SIGNAL_REQUIRED_ACCOUNTS,
    "영업활동으로 인한 현금흐름",
    "영업에서 창출된 현금흐름",
    "CashAndCashEquivalents",
    "Inventories",
    "TradeReceivables",
    "CurrentTradeReceivables",
    "PropertyPlantAndEquipment",
    "CashFlowsFromUsedInOperatingActivities",
    "CashFlowsFromUsedInOperations",
    "ShorttermBorrowings",
    "LongTermBorrowings",
    "Bonds",
    "InterestExpense",
    "FinanceCosts",
]


SIGNAL_REQUIREMENTS = [
    ("부채 과다", ["부채총계", "자본총계"]),
    ("실적 급락", ["매출액", "영업이익"]),
    ("수익성 악화", ["영업이익"]),
    ("수익성 악화2", ["당기순이익"]),
    ("영업현금흐름 적자 지속", ["영업활동현금흐름"]),
    ("매출채권 회수 지연", ["매출액", "매출채권"]),
    ("재고 적체", ["매출액", "재고자산"]),
    ("단기 상환 압박", ["현금및현금성자산", "유동부채"]),
    ("이자 부담 능력", ["영업이익", "이자비용"]),
    ("비용 레버리지 위험", ["매출액", "영업이익"]),
    ("매출 퀀텀 점프", ["매출액"]),
    ("어닝 서프라이즈", ["매출액", "영업이익"]),
    ("흑자 전환", ["영업이익"]),
    ("자산 가동률 상승", ["매출액", "재고자산", "매출채권"]),
    ("Capa 확대", ["유형자산"]),
    ("M&A 및 신사업 진출", []),
    ("재무 구조 개선", ["부채총계", "자본총계"]),
    ("현금 창출력 강화", ["영업활동현금흐름"]),
    ("이자 부담 해소", ["단기차입금", "장기차입금", "사채", "자산총계"]),
]


def load_json(path: Path) -> Dict[str, Any]:
    """JSON 파일을 읽습니다. 파일이 없으면 빈 규격을 반환합니다."""
    if not path.exists():
        return {"meta": {}, "data": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(data: Dict[str, Any], path: Path) -> None:
    """수집 원본 JSON을 UTF-8로 저장합니다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def collect_single_all_accounts() -> Dict[str, Any]:
    """corpCode 매핑을 재사용하여 삼성전자 전체 재무제표 API를 연도별로 호출합니다."""
    # 이 함수는 원본을 새로 수집해야 할 때만 사용합니다. 평소 산출물 재생성은
    # load_single_all_accounts()로 기존 raw 파일을 읽어 API 키 접근을 피합니다.
    from core.config import DART_API_KEY, ensure_data_dirs
    from data.dart_api import DartAPIClient

    ensure_data_dirs()

    client = DartAPIClient(DART_API_KEY)
    corp_code = client.get_corp_code_by_stock_code(STOCK_CODE)
    if not corp_code:
        raise RuntimeError(f"corp_code를 찾지 못했습니다: {STOCK_CODE}")

    result = {
        "meta": {
            "stock_code": STOCK_CODE,
            "corp_code": corp_code,
            "company_name": COMPANY_NAME,
            "report_code": REPORT_CODE,
            "fs_div": FS_DIV,
            "api": "fnlttSinglAcntAll.json",
            "collected_at": datetime.now().isoformat(),
            "years": YEARS,
        },
        "data": {},
    }

    for year in YEARS:
        response = client.fetch_single_company_all_accounts(
            corp_code=corp_code,
            bsns_year=year,
            reprt_code=REPORT_CODE,
            fs_div=FS_DIV,
        )
        result["data"][str(year)] = response.get("list", []) if response else []
        if year != YEARS[-1]:
            time.sleep(1)

    save_json(result, RAW_SINGLE_ALL_PATH)
    return result


def load_single_all_accounts() -> Dict[str, Any]:
    """이미 수집된 전체 재무제표 API 원본 파일을 읽습니다."""
    if not RAW_SINGLE_ALL_PATH.exists():
        raise FileNotFoundError(f"전체 재무제표 API 원본 파일이 없습니다: {RAW_SINGLE_ALL_PATH}")
    return load_json(RAW_SINGLE_ALL_PATH)


def field_distribution(items: Iterable[Dict[str, Any]], field_name: str) -> str:
    """분포 값을 CSV 한 칸에 들어갈 수 있는 문자열로 정리합니다."""
    counter = Counter(item.get(field_name, "") for item in items)
    return "; ".join(f"{key or '(blank)'}:{value}" for key, value in sorted(counter.items()))


def account_names(items: Iterable[Dict[str, Any]]) -> Set[str]:
    """연도별 계정명 집합을 만듭니다."""
    return {item.get("account_nm", "") for item in items if item.get("account_nm")}


def account_ids(items: Iterable[Dict[str, Any]]) -> Set[str]:
    """연도별 account_id 집합을 만듭니다."""
    return {item.get("account_id", "") for item in items if item.get("account_id")}


def build_comparison_rows(main_data: Dict[str, Any], all_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """기존 주요계정 API 결과와 전체 재무제표 API 결과를 연도별로 비교합니다."""
    rows: List[Dict[str, str]] = []

    for year in YEARS:
        year_key = str(year)
        main_items = main_data.get("data", {}).get(year_key, [])
        all_items = all_data.get("data", {}).get(year_key, [])

        main_names = account_names(main_items)
        all_names = account_names(all_items)
        all_ids = account_ids(all_items)

        rows.append({
            "year": year_key,
            "main_account_count": str(len(main_items)),
            "single_all_account_count": str(len(all_items)),
            "main_account_names": " | ".join(sorted(main_names)),
            "single_all_account_names": " | ".join(sorted(all_names)),
            "single_all_account_ids": " | ".join(sorted(all_ids)),
            "new_account_names_in_single_all": " | ".join(sorted(all_names - main_names)),
            "sj_div_distribution": field_distribution(all_items, "sj_div"),
            "sj_nm_distribution": field_distribution(all_items, "sj_nm"),
            "fs_div_distribution": field_distribution(all_items, "fs_div"),
            "fs_nm_distribution": field_distribution(all_items, "fs_nm"),
        })

    return rows


def search_terms_in_all_fields(all_data: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    """요청받은 후보 계정을 account_nm뿐 아니라 모든 문자열 필드에서 검색합니다."""
    found: Dict[str, List[Dict[str, str]]] = {term: [] for term in SEARCH_TERMS}

    for year, items in all_data.get("data", {}).items():
        for item in items:
            string_fields = get_string_fields(item)
            for term in SEARCH_TERMS:
                normalized_term = term.lower()
                for field_name, field_value in string_fields.items():
                    if normalized_term in field_value.lower():
                        found[term].append({
                            "year": str(year),
                            "field": field_name,
                            "account_nm": item.get("account_nm", ""),
                            "account_id": item.get("account_id", ""),
                            "sj_div": item.get("sj_div", ""),
                        })
                        break

    return found


def collect_account_matches(all_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """전체 재무제표 API 행을 표준 계정별로 모아 Signal availability에 사용합니다."""
    matches: Dict[str, Dict[str, Any]] = {
        account: {
            "matched_account_nm": set(),
            "matched_account_id": set(),
            "years_found": set(),
            "sj_divs": set(),
            "fs_divs": set(),
        }
        for account in CURRENT_SIGNAL_REQUIRED_ACCOUNTS
    }

    for year, items in all_data.get("data", {}).items():
        for item in items:
            standard, _candidate, _field, _match_type = find_standard_account_in_item(item)
            if standard not in matches:
                continue
            matches[standard]["matched_account_nm"].add(item.get("account_nm", ""))
            matches[standard]["matched_account_id"].add(item.get("account_id", ""))
            matches[standard]["years_found"].add(str(year))
            matches[standard]["sj_divs"].add(item.get("sj_div", ""))
            matches[standard]["fs_divs"].add(item.get("fs_div", ""))

    return matches


def has_match(matches: Dict[str, Dict[str, Any]], account: str) -> bool:
    """표준 계정이 하나 이상의 연도에서 발견되었는지 확인합니다."""
    return bool(matches.get(account, {}).get("years_found"))


def format_set(values: Set[str]) -> str:
    """CSV 셀에 넣기 좋게 빈 값을 제외하고 정렬합니다."""
    return ", ".join(sorted(value for value in values if value))


def build_signal_account_availability(all_data: Dict[str, Any]) -> List[Dict[str, str]]:
    """확정된 Signal별 필요 계정의 발견 여부와 계산 가능성을 정리합니다."""
    matches = collect_account_matches(all_data)
    rows: List[Dict[str, str]] = []

    def add_row(
        signal_name: str,
        required_account: str,
        status: str,
        recommended_action: str,
        source_account: str = ""
    ) -> None:
        match_key = source_account or required_account
        match = matches.get(match_key, {
            "matched_account_nm": set(),
            "matched_account_id": set(),
            "years_found": set(),
            "sj_divs": set(),
            "fs_divs": set(),
        })
        found = status in {"found_in_single_all", "proxy_candidate", "calculated_from_components"}
        rows.append({
            "signal_name": signal_name,
            "required_account": required_account,
            "found": str(found).lower(),
            "matched_account_nm": format_set(match["matched_account_nm"]),
            "matched_account_id": format_set(match["matched_account_id"]),
            "years_found": format_set(match["years_found"]),
            "sj_divs": format_set(match["sj_divs"]),
            "fs_divs": format_set(match["fs_divs"]),
            "status": status,
            "recommended_action": recommended_action,
        })

    for signal_name, accounts in SIGNAL_REQUIREMENTS:
        if signal_name == "M&A 및 신사업 진출":
            add_row(
                signal_name,
                "주요사항보고서/원문 키워드",
                "needs_manual_review",
                "재무제표 계정이 아니라 주요사항보고서 또는 사업보고서 원문 키워드 기반으로 확인해야 합니다."
            )
            continue

        for account in accounts:
            if account == "이자비용" and not has_match(matches, "이자비용") and has_match(matches, "금융비용"):
                add_row(
                    signal_name,
                    "이자비용",
                    "proxy_candidate",
                    "이자비용 직접 계정은 없고 금융비용만 확인됩니다. 실제 계산 사용 여부는 사람이 결정해야 합니다.",
                    source_account="금융비용"
                )
            elif signal_name == "이자 부담 해소" and account in {"단기차입금", "장기차입금", "사채"}:
                status = "found_in_single_all" if has_match(matches, account) else "not_found_in_single_all"
                add_row(
                    signal_name,
                    account,
                    status,
                    "단기차입금, 장기차입금, 사채를 합산해 차입금의존도 계산 구성요소로 사용합니다."
                )
            elif has_match(matches, account):
                add_row(
                    signal_name,
                    account,
                    "found_in_single_all",
                    "전체 재무제표 API에서 직접 확인된 계정입니다."
                )
            else:
                status = "needs_xbrl_or_note" if account == "이자비용" else "not_found_in_single_all"
                add_row(
                    signal_name,
                    account,
                    status,
                    "전체 재무제표 API 본문에서 직접 찾지 못했습니다. 필요 시 XBRL, 주석, 원문 확인이 필요합니다."
                )

        if signal_name == "이자 부담 해소":
            components_found = all(has_match(matches, account) for account in ["단기차입금", "장기차입금", "사채"])
            if components_found and has_match(matches, "자산총계"):
                add_row(
                    signal_name,
                    "차입금의존도",
                    "calculated_from_components",
                    "차입금 단일 계정은 없어도 단기차입금, 장기차입금, 사채, 자산총계 조합으로 계산 가능합니다.",
                    source_account="자산총계"
                )

    return rows


def summarize_signal_readiness(signal_rows: List[Dict[str, str]]) -> Dict[str, str]:
    """Signal별 계산 가능 여부를 간단한 상태값으로 요약합니다."""
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for row in signal_rows:
        grouped.setdefault(row["signal_name"], []).append(row)

    readiness: Dict[str, str] = {}
    for signal_name, rows in grouped.items():
        statuses = {row["status"] for row in rows}
        if "needs_manual_review" in statuses:
            readiness[signal_name] = "원문/주요사항보고서 확인 필요"
        elif "proxy_candidate" in statuses:
            readiness[signal_name] = "proxy 확인 후 가능"
        elif "calculated_from_components" in statuses:
            readiness[signal_name] = "조합 계산 가능"
        elif statuses <= {"found_in_single_all"}:
            readiness[signal_name] = "가능"
        elif "not_found_in_single_all" in statuses or "needs_xbrl_or_note" in statuses:
            readiness[signal_name] = "확인 필요"
        else:
            readiness[signal_name] = "확인 필요"

    return readiness


def unique_found_accounts(availability_rows: List[Dict[str, str]]) -> List[str]:
    """availability 결과에서 발견된 standard_account 목록을 반환합니다."""
    return [
        row["standard_account"]
        for row in availability_rows
        if row["found"] == "true"
    ]


def write_summary(
    main_data: Dict[str, Any],
    all_data: Dict[str, Any],
    comparison_rows: List[Dict[str, str]],
    availability_rows: List[Dict[str, str]],
    search_result: Dict[str, List[Dict[str, str]]],
    signal_rows: List[Dict[str, str]],
) -> None:
    """전체 API 수집 및 계정 매핑 결과를 Markdown으로 정리합니다."""
    main_total = sum(len(items) for items in main_data.get("data", {}).values())
    all_total = sum(len(items) for items in all_data.get("data", {}).values())
    found_terms = [term for term, rows in search_result.items() if rows]
    not_found_terms = [term for term, rows in search_result.items() if not rows]
    mapped_accounts = unique_found_accounts(availability_rows)
    unavailable_accounts = [
        row["standard_account"]
        for row in availability_rows
        if row["found"] != "true"
    ]
    xbrl_needed = [
        row["standard_account"]
        for row in availability_rows
        if row["status"] == "needs_xbrl_or_note"
    ]
    proxy_accounts = sorted({
        row["required_account"]
        for row in signal_rows
        if row["status"] == "proxy_candidate"
    })
    component_accounts = sorted({
        row["required_account"]
        for row in signal_rows
        if row["status"] == "calculated_from_components"
    })
    signal_readiness = summarize_signal_readiness(signal_rows)
    manual_or_xbrl_needed = sorted(set(xbrl_needed) | {
        row["required_account"]
        for row in signal_rows
        if row["status"] in {"needs_xbrl_or_note", "needs_manual_review"}
    })

    found_required_accounts = [
        row["standard_account"]
        for row in availability_rows
        if row["found"] == "true"
    ]
    missing_required_accounts = [
        row["standard_account"]
        for row in availability_rows
        if row["found"] != "true"
    ]

    summary_lines = [
        "# 단일회사 전체 재무제표 API 점검 요약",
        "",
        "## 이번 Signal 계산 기준에서 필요한 계정 목록",
        *[f"- {account}" for account in CURRENT_SIGNAL_REQUIRED_ACCOUNTS],
        "",
        "## API 반환 계정 수",
        f"- 기존 주요계정 API 총 계정 수: {main_total}",
        f"- 전체 재무제표 API 총 계정 수: {all_total}",
        "",
        "## 연도별 계정 수",
    ]
    for row in comparison_rows:
        summary_lines.append(
            f"- {row['year']}: 주요계정 {row['main_account_count']}개, "
            f"전체 재무제표 {row['single_all_account_count']}개"
        )

    summary_lines.extend([
        "",
        "## 전체 재무제표 API에서 찾은 계정",
        *[f"- {account}" for account in found_required_accounts],
        "",
        "## proxy_candidate로만 사용할 수 있는 계정",
        *[f"- {account}" for account in proxy_accounts],
        "",
        "## 조합 계산 가능한 항목",
        *[f"- {account}" for account in component_accounts],
        "",
        "## standard_account로 매핑 가능한 계정",
        *[f"- {account}" for account in mapped_accounts],
        "",
        "## Signal별 계산 가능 여부",
        *[f"- {signal}: {status}" for signal, status in signal_readiness.items()],
        "",
        "## 이번 기준에서 필수에서 제외한 계정",
        *[f"- {account}" for account in NOT_REQUIRED_FOR_CURRENT_SIGNAL_ACCOUNTS],
        "",
        "## 여전히 못 찾은 계정",
        *[f"- {account}" for account in missing_required_accounts],
        "",
        "## XBRL/주석/원문 파싱이 필요한 계정",
        *[f"- {account}" for account in manual_or_xbrl_needed],
        "",
        "## 계산/Signal 로직 담당자 참고 사항",
        "- 이자비용 직접 계정은 찾지 못했고, 금융비용만 proxy_candidate로 확인됩니다.",
        "- 차입금이라는 단일 계정은 없어도 단기차입금, 장기차입금, 사채와 자산총계 조합으로 차입금의존도 계산이 가능합니다.",
        "- 매출채권및기타채권은 없지만 매출채권이 있으므로 매출채권회전율 계산에는 매출채권을 사용할 수 있습니다.",
        "- Capa 확대는 유형자산 증가율만 사용하며 건설중인자산은 이번 기준에서 필수 계정이 아닙니다.",
        "- M&A 및 신사업 진출은 재무제표 계정이 아니라 주요사항보고서 또는 사업보고서 원문 키워드 기반입니다.",
        "- DB 저장, 재무비율, Warning Signal 계산 로직은 아직 연결하지 않았습니다.",
        "",
    ])

    summary_path = PROCESSED_DIR / "single_all_api_summary_2019_2023.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")


def main() -> int:
    """기존 전체 API 원본을 기준으로 비교와 전처리 산출물을 생성합니다."""
    main_data = load_json(RAW_MAIN_PATH)
    all_data = load_single_all_accounts()

    inventory_rows = build_single_all_account_inventory(all_data)
    availability_rows = build_single_all_account_availability(all_data)
    standard_rows = build_single_all_standard_financials(all_data)
    comparison_rows = build_comparison_rows(main_data, all_data)
    search_result = search_terms_in_all_fields(all_data)
    signal_rows = build_signal_account_availability(all_data)

    write_csv(
        inventory_rows,
        PROCESSED_DIR / "single_all_account_inventory_2019_2023.csv",
        ["year", "fs_div", "fs_nm", "sj_div", "sj_nm", "account_id", "account_nm", "account_detail"],
    )
    write_csv(
        availability_rows,
        PROCESSED_DIR / "single_all_account_availability_2019_2023.csv",
        [
            "standard_account",
            "category",
            "found",
            "years_found",
            "sj_divs",
            "matched_names",
            "matched_account_ids",
            "status",
            "recommended_action",
        ],
    )
    write_csv(
        standard_rows,
        PROCESSED_DIR / "single_all_standard_financials_2019_2023.csv",
        [
            "year",
            "fs_div",
            "fs_nm",
            "sj_div",
            "sj_nm",
            "account_id",
            "account_nm",
            "account_detail",
            "standard_account",
            "matched_candidate",
            "matched_field",
            "match_type",
            "thstrm_amount",
            "frmtrm_amount",
            "bfefrmtrm_amount",
            "currency",
            "rcept_no",
            "reprt_code",
            "corp_code",
            "stock_code",
        ],
    )
    write_json(standard_rows, PROCESSED_DIR / "single_all_standard_financials_2019_2023.json")
    write_csv(
        signal_rows,
        PROCESSED_DIR / "signal_account_availability_2019_2023.csv",
        [
            "signal_name",
            "required_account",
            "found",
            "matched_account_nm",
            "matched_account_id",
            "years_found",
            "sj_divs",
            "fs_divs",
            "status",
            "recommended_action",
        ],
    )
    write_csv(
        comparison_rows,
        PROCESSED_DIR / "single_main_vs_all_comparison_2019_2023.csv",
        [
            "year",
            "main_account_count",
            "single_all_account_count",
            "main_account_names",
            "single_all_account_names",
            "single_all_account_ids",
            "new_account_names_in_single_all",
            "sj_div_distribution",
            "sj_nm_distribution",
            "fs_div_distribution",
            "fs_nm_distribution",
        ],
    )
    write_summary(main_data, all_data, comparison_rows, availability_rows, search_result, signal_rows)

    print("전체 재무제표 API 기준 Signal 계정 availability 산출물 생성 완료")
    print(f"raw: {RAW_SINGLE_ALL_PATH}")
    print(f"processed: {PROCESSED_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
