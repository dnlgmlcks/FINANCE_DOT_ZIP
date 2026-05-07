"""
OpenDART 원본 JSON을 분석용 데이터로 가공하는 모듈
"""

import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

STANDARD_ACCOUNT_CANDIDATES: Dict[str, List[str]] = {
    # BS 기본 계정
    "유동자산": ["유동자산"],
    "비유동자산": ["비유동자산", "비유동자산"],
    "자산총계": ["자산총계"],
    "유동부채": ["유동부채"],
    "비유동부채": ["비유동부채"],
    "부채총계": ["부채총계"],
    "자본총계": ["자본총계"],

    # IS 기본 계정
    "매출액": ["매출액", "매출", "수익(매출액)"],
    "영업이익": ["영업이익"],
    "법인세차감전순이익": ["법인세차감전순이익", "법인세비용차감전순이익(손실)"],
    "당기순이익": ["당기순이익", "당기순손실"],

    # 추가 확인 계정
    "현금및현금성자산": [
        "현금및현금성자산",
        "현금및현금성자산및단기금융상품",
        "현금및현금성자산과단기금융상품",
        "CashAndCashEquivalents"
    ],
    "재고자산": ["재고자산", "Inventories", "Inventory"],
    "매출채권": ["매출채권", "Receivables", "TradeReceivables"],
    "매출채권및기타채권": [
        "매출채권및기타채권",
        "매출채권 및 기타채권",
        "TradeAndOtherReceivables"
    ],
    "미수금": ["미수금", "OtherReceivables"],
    "매출채권/미수금": [
        "매출채권",
        "미수금",
        "매출채권및미수금",
        "매출채권/미수금",
        "매출채권 및 미수금"
    ],
    "유형자산": ["유형자산", "PropertyPlantAndEquipment"],
    "건설중인자산": ["건설중인자산", "ConstructionInProgress"],
    "단기차입금": ["단기차입금", "ShortTermBorrowings"],
    "매입채무": ["매입채무", "TradePayables"],
    "사채": ["사채", "Debentures", "Bonds"],
    "장기차입금": ["장기차입금", "LongTermBorrowings"],
    "차입금": ["차입금", "Borrowings"],
    "매출원가": ["매출원가", "제품매출원가", "상품매출원가", "CostOfSales", "CostOfGoodsSold"],
    "원재료비": ["원재료비", "재료비", "원재료비및소모품비", "RawMaterials"],
    "급여": ["급여", "인건비", "임금", "Salaries"],
    "퇴직급여": ["퇴직급여", "RetirementBenefits"],
    "복리후생비": ["복리후생비", "복리후생비용", "EmployeeBenefits"],
    "이자비용": ["이자비용", "이자비용및수수료", "차입금이자비용", "InterestExpense"],
    "금융비용": ["금융비용", "FinanceCosts"],
    "영업활동현금흐름": [
        "영업활동현금흐름",
        "영업활동으로 인한 현금흐름",
        "영업에서 창출된 현금흐름",
        "CashFlowsFromUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivities"
    ]
}

BASIC_ACCOUNTS = [
    "유동자산",
    "비유동자산",
    "자산총계",
    "유동부채",
    "비유동부채",
    "부채총계",
    "자본총계",
    "매출액",
    "영업이익",
    "법인세차감전순이익",
    "당기순이익"
]

ADDITIONAL_ACCOUNTS = [
    "현금및현금성자산",
    "재고자산",
    "매출채권",
    "유형자산",
    "단기차입금",
    "장기차입금",
    "사채",
    "이자비용",
    "금융비용",
    "영업활동현금흐름"
]

ALL_STANDARD_ACCOUNTS = BASIC_ACCOUNTS + ADDITIONAL_ACCOUNTS

# 현재 확정된 Warning/Positive Signal 계산 기준에서 실제로 필요한 계정입니다.
# 유동자산, 비유동자산, 매출원가 등 이전 탐색 단계의 계정은 이번 1차
# Signal 계산 기준에서는 필수로 보지 않습니다.
CURRENT_SIGNAL_REQUIRED_ACCOUNTS = [
    "매출액",
    "영업이익",
    "당기순이익",
    "자산총계",
    "부채총계",
    "자본총계",
    "유동부채",
    "현금및현금성자산",
    "재고자산",
    "매출채권",
    "유형자산",
    "영업활동현금흐름",
    "단기차입금",
    "장기차입금",
    "사채",
    "이자비용",
    "금융비용"
]

# 이번 기준에서는 필수 목록에서 제외하지만, 사람이 후속 검토할 수 있도록
# summary에는 별도로 남기는 계정입니다.
NOT_REQUIRED_FOR_CURRENT_SIGNAL_ACCOUNTS = [
    "건설중인자산",
    "원재료비",
    "급여",
    "퇴직급여",
    "복리후생비"
]


def normalize_account_name(name: str) -> str:
    """계정명 정규화: 공백과 괄호 등 제거, 소문자 변환"""
    normalized = re.sub(r"[\s\(\)\[\]\{\}\.·/\\,]+", "", name)
    return normalized.lower()


def parse_amount(amount_str: Optional[str]) -> Optional[int]:
    """숫자 문자열에서 쉼표 제거 후 정수 변환"""
    if amount_str is None:
        return None
    value = amount_str.strip()
    if value == "" or value == "-":
        return None
    value = value.replace(",", "")
    if value.isdigit():
        return int(value)
    try:
        return int(float(value))
    except ValueError:
        return None


def build_account_inventory(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """연도별, sj_div별 account_nm 목록 생성"""
    rows: List[Dict[str, Any]] = []
    seen = set()
    for year, items in raw_data.get("data", {}).items():
        for item in items:
            row = (str(year), item.get("sj_div", ""), item.get("account_nm", ""))
            if row not in seen:
                seen.add(row)
                rows.append({
                    "year": str(year),
                    "sj_div": item.get("sj_div", ""),
                    "account_nm": item.get("account_nm", "")
                })
    return rows


def find_standard_account(account_nm: str) -> Tuple[Optional[str], Optional[str]]:
    """원본 계정명을 표준 계정명으로 매핑"""
    normalized = normalize_account_name(account_nm)
    best_match: Tuple[int, Optional[str], Optional[str]] = (0, None, None)
    for standard, candidates in STANDARD_ACCOUNT_CANDIDATES.items():
        for candidate in candidates:
            candidate_norm = normalize_account_name(candidate)
            if not candidate_norm:
                continue
            if normalized == candidate_norm:
                return standard, candidate
            if candidate_norm in normalized or normalized in candidate_norm:
                score = len(candidate_norm)
                if score > best_match[0]:
                    best_match = (score, standard, candidate)
    if best_match[1] is not None:
        return best_match[1], best_match[2]
    return None, None


def build_account_availability(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """기본/추가 계정 추출 가능 여부 확인 표 생성"""
    availability: Dict[str, Dict[str, Any]] = {
        account: {
            "standard_account": account,
            "category": "basic" if account in BASIC_ACCOUNTS else "additional",
            "found": False,
            "matched_names": set(),
            "years_found": set(),
            "sj_divs": set(),
            "status": "not_found"
        }
        for account in ALL_STANDARD_ACCOUNTS
    }

    for year, items in raw_data.get("data", {}).items():
        for item in items:
            account_nm = item.get("account_nm", "")
            standard, matched_candidate = find_standard_account(account_nm)
            if standard:
                record = availability[standard]
                record["found"] = True
                record["matched_names"].add(account_nm)
                record["years_found"].add(str(year))
                record["sj_divs"].add(item.get("sj_div", ""))

    rows: List[Dict[str, Any]] = []
    for standard, record in availability.items():
        found = record["found"]
        category = record["category"]
        if found:
            status = "found"
        elif category == "basic":
            status = "not_found"
        else:
            status = "needs_note_or_text"

        rows.append({
            "standard_account": standard,
            "category": category,
            "found": str(found).lower(),
            "years_found": ", ".join(sorted(record["years_found"])),
            "sj_divs": ", ".join(sorted(record["sj_divs"])),
            "matched_names": ", ".join(sorted(record["matched_names"])),
            "status": status
        })
    return rows


def build_standard_financials(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """표준 계정만 추출하여 숫자값으로 변환"""
    rows: List[Dict[str, Any]] = []
    for year, items in raw_data.get("data", {}).items():
        for item in items:
            account_nm = item.get("account_nm", "")
            standard, matched_candidate = find_standard_account(account_nm)
            if not standard:
                continue
            row = {
                "year": str(year),
                "sj_div": item.get("sj_div", ""),
                "account_nm": account_nm,
                "standard_account": standard,
                "matched_candidate": matched_candidate or "",
                "thstrm_amount": parse_amount(item.get("thstrm_amount")),
                "frmtrm_amount": parse_amount(item.get("frmtrm_amount")),
                "bfefrmtrm_amount": parse_amount(item.get("bfefrmtrm_amount")),
                "currency": item.get("currency", ""),
                "rcept_no": item.get("rcept_no", ""),
                "reprt_code": item.get("reprt_code", ""),
                "corp_code": item.get("corp_code", ""),
                "stock_code": item.get("stock_code", "")
            }
            rows.append(row)
    return rows


def get_string_fields(item: Dict[str, Any]) -> Dict[str, str]:
    """DART 응답 행에서 문자열 필드만 모아 계정 검색 대상으로 사용합니다."""
    return {
        str(key): value.strip()
        for key, value in item.items()
        if isinstance(value, str) and value.strip()
    }


def find_standard_account_in_item(
    item: Dict[str, Any]
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    전체 재무제표 API 행을 기존 표준 계정 후보에 매핑합니다.

    매칭 우선순위는 1) account_nm 정확 일치, 2) account_id 후보 발견,
    3) 기타 문자열 필드에서 후보 발견입니다. 유동자산/비유동자산처럼
    부분 문자열이 서로 포함되는 계정은 오매칭 위험이 크므로 account_nm에는
    부분 문자열 매칭을 적용하지 않습니다.
    """
    string_fields = get_string_fields(item)
    account_nm = string_fields.get("account_nm", "")
    account_id = string_fields.get("account_id", "")
    normalized_account_nm = normalize_account_name(account_nm)
    normalized_account_id = normalize_account_name(account_id)
    account_id_leaf = account_id.split("_")[-1]
    normalized_account_id_leaf = normalize_account_name(account_id_leaf)

    for standard, candidates in STANDARD_ACCOUNT_CANDIDATES.items():
        for candidate in candidates:
            normalized_candidate = normalize_account_name(candidate)
            if normalized_candidate and normalized_account_nm == normalized_candidate:
                return standard, candidate, "account_nm", "exact"

    for standard, candidates in STANDARD_ACCOUNT_CANDIDATES.items():
        for candidate in candidates:
            normalized_candidate = normalize_account_name(candidate)
            if not normalized_candidate:
                continue
            if normalized_candidate in {normalized_account_id, normalized_account_id_leaf}:
                return standard, candidate, "account_id", "exact"

    return None, None, None, None


def build_single_all_account_inventory(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """전체 재무제표 API의 계정 목록을 연도와 재무제표 구분별로 정리합니다."""
    rows: List[Dict[str, Any]] = []
    seen = set()

    for year, items in raw_data.get("data", {}).items():
        for item in items:
            row_key = (
                str(year),
                item.get("fs_div", ""),
                item.get("sj_div", ""),
                item.get("account_id", ""),
                item.get("account_nm", ""),
                item.get("account_detail", "")
            )
            if row_key in seen:
                continue

            seen.add(row_key)
            rows.append({
                "year": str(year),
                "fs_div": item.get("fs_div", ""),
                "fs_nm": item.get("fs_nm", ""),
                "sj_div": item.get("sj_div", ""),
                "sj_nm": item.get("sj_nm", ""),
                "account_id": item.get("account_id", ""),
                "account_nm": item.get("account_nm", ""),
                "account_detail": item.get("account_detail", "")
            })

    return rows


def build_single_all_account_availability(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """전체 재무제표 API 기준 표준 계정 후보의 발견 여부를 정리합니다."""
    availability: Dict[str, Dict[str, Any]] = {
        account: {
            "standard_account": account,
            "category": "basic" if account in BASIC_ACCOUNTS else "additional",
            "found": False,
            "years_found": set(),
            "sj_divs": set(),
            "matched_names": set(),
            "matched_account_ids": set(),
            "matched_fields": set(),
            "status": "not_found_in_single_all"
        }
        for account in CURRENT_SIGNAL_REQUIRED_ACCOUNTS
    }

    for year, items in raw_data.get("data", {}).items():
        for item in items:
            standard, matched_candidate, matched_field, match_type = find_standard_account_in_item(item)
            if not standard:
                continue
            if standard not in availability:
                continue

            record = availability[standard]
            record["found"] = True
            record["years_found"].add(str(year))
            record["sj_divs"].add(item.get("sj_div", ""))
            record["matched_names"].add(item.get("account_nm", ""))
            record["matched_account_ids"].add(item.get("account_id", ""))
            if matched_field:
                record["matched_fields"].add(matched_field)

            if matched_field == "account_nm" and match_type == "exact":
                record["status"] = "found_in_single_all"
            elif matched_field == "account_id" and record["status"] != "found_in_single_all":
                record["status"] = "found_in_account_id"
            elif record["status"] not in {"found_in_single_all", "found_in_account_id"}:
                record["status"] = "found_with_different_name"

    rows: List[Dict[str, Any]] = []
    for standard, record in availability.items():
        if record["found"]:
            recommended_action = "기존 standard_account 매핑 후보로 사용할 수 있습니다."
        elif standard in {"원재료비", "급여", "퇴직급여", "복리후생비"}:
            record["status"] = "needs_xbrl_or_note"
            recommended_action = "전체 재무제표 본문보다 주석, 원가명세 또는 XBRL 상세 태그 확인이 필요합니다."
        else:
            recommended_action = "DART 원문 계정명 또는 account_id 후보를 사람이 재검토해야 합니다."

        rows.append({
            "standard_account": standard,
            "category": record["category"],
            "found": str(record["found"]).lower(),
            "years_found": ", ".join(sorted(record["years_found"])),
            "sj_divs": ", ".join(sorted(filter(None, record["sj_divs"]))),
            "matched_names": ", ".join(sorted(filter(None, record["matched_names"]))),
            "matched_account_ids": ", ".join(sorted(filter(None, record["matched_account_ids"]))),
            "status": record["status"],
            "recommended_action": recommended_action
        })

    return rows


def build_single_all_standard_financials(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """전체 재무제표 API에서 표준 계정 후보로 매핑 가능한 행만 추출합니다."""
    rows: List[Dict[str, Any]] = []

    for year, items in raw_data.get("data", {}).items():
        for item in items:
            standard, matched_candidate, matched_field, match_type = find_standard_account_in_item(item)
            if not standard:
                continue
            if standard not in CURRENT_SIGNAL_REQUIRED_ACCOUNTS:
                continue

            rows.append({
                "year": str(year),
                "fs_div": item.get("fs_div", ""),
                "fs_nm": item.get("fs_nm", ""),
                "sj_div": item.get("sj_div", ""),
                "sj_nm": item.get("sj_nm", ""),
                "account_id": item.get("account_id", ""),
                "account_nm": item.get("account_nm", ""),
                "account_detail": item.get("account_detail", ""),
                "standard_account": standard,
                "matched_candidate": matched_candidate or "",
                "matched_field": matched_field or "",
                "match_type": match_type or "",
                "thstrm_amount": parse_amount(item.get("thstrm_amount")),
                "frmtrm_amount": parse_amount(item.get("frmtrm_amount")),
                "bfefrmtrm_amount": parse_amount(item.get("bfefrmtrm_amount")),
                "currency": item.get("currency", ""),
                "rcept_no": item.get("rcept_no", ""),
                "reprt_code": item.get("reprt_code", ""),
                "corp_code": item.get("corp_code", ""),
                "stock_code": item.get("stock_code", "")
            })

    return rows


def write_csv(rows: List[Dict[str, Any]], output_path: Path, fieldnames: List[str]) -> None:
    """CSV 파일로 저장"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(data: Any, output_path: Path) -> None:
    """JSON 파일로 저장"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def process_financial_data(
    input_path: Path,
    output_dir: Path
) -> Dict[str, Any]:
    """원본 JSON을 읽고 가공 결과를 저장"""
    raw_data = json.loads(input_path.read_text(encoding="utf-8"))

    inventory_rows = build_account_inventory(raw_data)
    availability_rows = build_account_availability(raw_data)
    standard_rows = build_standard_financials(raw_data)

    inventory_path = output_dir / "account_name_inventory_2019_2023.csv"
    availability_path = output_dir / "account_availability_2019_2023.csv"
    standard_csv_path = output_dir / "standard_financials_2019_2023.csv"
    standard_json_path = output_dir / "standard_financials_2019_2023.json"

    write_csv(
        inventory_rows,
        inventory_path,
        ["year", "sj_div", "account_nm"]
    )
    write_csv(
        availability_rows,
        availability_path,
        ["standard_account", "category", "found", "years_found", "sj_divs", "matched_names", "status"]
    )
    write_csv(
        standard_rows,
        standard_csv_path,
        [
            "year",
            "sj_div",
            "account_nm",
            "standard_account",
            "matched_candidate",
            "thstrm_amount",
            "frmtrm_amount",
            "bfefrmtrm_amount",
            "currency",
            "rcept_no",
            "reprt_code",
            "corp_code",
            "stock_code"
        ]
    )
    write_json(standard_rows, standard_json_path)

    return {
        "inventory_path": str(inventory_path),
        "availability_path": str(availability_path),
        "standard_csv_path": str(standard_csv_path),
        "standard_json_path": str(standard_json_path)
    }
