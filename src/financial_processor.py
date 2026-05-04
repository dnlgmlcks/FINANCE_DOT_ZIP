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
    "매출액": ["매출액", "매출"],
    "영업이익": ["영업이익"],
    "법인세차감전순이익": ["법인세차감전순이익"],
    "당기순이익": ["당기순이익", "당기순손실"],

    # 추가 확인 계정
    "현금및현금성자산": [
        "현금및현금성자산",
        "현금및현금성자산및단기금융상품",
        "현금및현금성자산과단기금융상품"
    ],
    "재고자산": ["재고자산"],
    "매출채권/미수금": [
        "매출채권",
        "미수금",
        "매출채권및미수금",
        "매출채권/미수금",
        "매출채권 및 미수금"
    ],
    "유형자산": ["유형자산"],
    "단기차입금": ["단기차입금"],
    "매입채무": ["매입채무"],
    "사채": ["사채"],
    "장기차입금": ["장기차입금"],
    "매출원가": ["매출원가", "제품매출원가", "상품매출원가"],
    "원재료비": ["원재료비", "재료비", "원재료비및소모품비"],
    "급여": ["급여", "인건비", "임금"],
    "퇴직급여": ["퇴직급여"],
    "복리후생비": ["복리후생비", "복리후생비용"],
    "이자비용": ["이자비용", "이자비용및수수료", "차입금이자비용"]
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
    "매출채권/미수금",
    "유형자산",
    "단기차입금",
    "매입채무",
    "사채",
    "장기차입금",
    "매출원가",
    "원재료비",
    "급여",
    "퇴직급여",
    "복리후생비",
    "이자비용"
]

ALL_STANDARD_ACCOUNTS = BASIC_ACCOUNTS + ADDITIONAL_ACCOUNTS


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
