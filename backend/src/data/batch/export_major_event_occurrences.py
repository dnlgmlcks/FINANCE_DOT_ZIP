"""
Export structured OpenDART major-event occurrences for event detection.

This script targets the screenshot use case: determine whether selected
major-event disclosures occurred for each company. It calls OpenDART DS005
"주요사항보고서 주요정보" JSON APIs and writes positive event rows only.
If a company has no row for an event type in the output, that event can be
treated as not observed in the selected period.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
import time
from pathlib import Path
from typing import Any

import requests

from export_disclosure_business_sections import (
    DART_API_BASE,
    EXPORT_ROOT,
    disclosure_url,
    load_api_key,
    read_csv_rows,
    sanitize_error_message,
)


DISCLOSURE_EXPORT_ROOT = EXPORT_ROOT / "disclosure"
DISCLOSURE_DICTIONARY_PATH = (
    Path(__file__).resolve().parents[4]
    / "backend"
    / "src"
    / "vector_db"
    / "참고"
    / "disclosure_dictionary.py"
)
DEFAULT_BATCH_IDS = [
    "konex_001",
    "kosdaq_001",
    "kosdaq_002",
    "kosdaq_003",
    "kosdaq_004",
    "kospi_001",
    "kospi_002",
]


EVENT_APIS = [
    {
        "event_code": "default_occurrence",
        "event_name": "부도발생",
        "endpoint": "dfOcr.json",
        "category": "warning_signal",
    },
    {
        "event_code": "business_suspension",
        "event_name": "영업정지",
        "endpoint": "bsnSp.json",
        "category": "warning_signal",
    },
    {
        "event_code": "rehabilitation_request",
        "event_name": "회생절차 개시신청",
        "endpoint": "ctrcvsBgrq.json",
        "category": "warning_signal",
    },
    {
        "event_code": "dissolution_reason",
        "event_name": "해산사유 발생",
        "endpoint": "dsRsOcr.json",
        "category": "warning_signal",
    },
    {
        "event_code": "business_acquisition",
        "event_name": "영업양수 결정",
        "endpoint": "bsnInhDecsn.json",
        "category": "mna",
    },
    {
        "event_code": "business_transfer",
        "event_name": "영업양도 결정",
        "endpoint": "bsnTrfDecsn.json",
        "category": "mna",
    },
    {
        "event_code": "tangible_asset_acquisition",
        "event_name": "유형자산 양수 결정",
        "endpoint": "tgastInhDecsn.json",
        "category": "mna",
    },
    {
        "event_code": "tangible_asset_transfer",
        "event_name": "유형자산 양도 결정",
        "endpoint": "tgastTrfDecsn.json",
        "category": "mna",
    },
    {
        "event_code": "merger_decision",
        "event_name": "회사합병 결정",
        "endpoint": "cmpMgDecsn.json",
        "category": "mna",
    },
    {
        "event_code": "split_decision",
        "event_name": "회사분할 결정",
        "endpoint": "cmpDvDecsn.json",
        "category": "mna",
    },
    {
        "event_code": "split_merger_decision",
        "event_name": "회사분할합병 결정",
        "endpoint": "cmpDvmgDecsn.json",
        "category": "mna",
    },
]


CSV_HEADERS = [
    "batch_id",
    "stock_code",
    "corp_code",
    "company_name",
    "event_category",
    "event_code",
    "event_name",
    "rcept_date",
    "report_url",
    "source_api",
    "summary",
    "details_json",
]

SUMMARY_EXCLUDED_FIELDS = {
    "rcept_no",
    "corp_cls",
    "corp_code",
    "corp_name",
    "stock_code",
    "reprt_code",
}


def load_disclosure_detail_keys() -> set[str]:
    if not DISCLOSURE_DICTIONARY_PATH.exists():
        raise FileNotFoundError(f"Disclosure dictionary not found: {DISCLOSURE_DICTIONARY_PATH}")

    tree = ast.parse(DISCLOSURE_DICTIONARY_PATH.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "DISCLOSURE_DICTIONARY"
            for target in node.targets
        ):
            continue
        dictionary = ast.literal_eval(node.value)
        return set(dictionary.keys())

    raise ValueError("DISCLOSURE_DICTIONARY is not defined.")


DISCLOSURE_DETAIL_KEYS = load_disclosure_detail_keys()


def single_line_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()


def clean_detail_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        text = single_line_text(value)
        if not text or text == "-":
            return None
        return text
    return value


def filter_details(item: dict[str, Any]) -> dict[str, Any]:
    filtered: dict[str, Any] = {}
    for key, value in item.items():
        if key not in DISCLOSURE_DETAIL_KEYS:
            continue
        cleaned_value = clean_detail_value(value)
        if cleaned_value is None:
            continue
        filtered[key] = cleaned_value
    return filtered


def load_companies(batch_id: str, company_limit: int | None) -> list[dict[str, str]]:
    companies_path = EXPORT_ROOT / batch_id / "companies.csv"
    rows = [
        row
        for row in read_csv_rows(companies_path)
        if row.get("corp_code") and row.get("stock_code")
    ]
    if company_limit and company_limit > 0:
        return rows[:company_limit]
    return rows


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_HEADERS})


def rcept_date_from_no(rcept_no: str) -> str:
    if re.fullmatch(r"\d{14}", rcept_no or ""):
        return f"{rcept_no[:4]}-{rcept_no[4:6]}-{rcept_no[6:8]}"
    return ""


def build_summary(item: dict[str, Any], max_fields: int = 5) -> str:
    parts: list[str] = []
    for key, value in item.items():
        if key in SUMMARY_EXCLUDED_FIELDS:
            continue
        text = single_line_text(value)
        if not text or text == "-":
            continue
        parts.append(f"{key}={text}")
        if len(parts) >= max_fields:
            break
    return " | ".join(parts)


def fetch_event_items(
    api_key: str,
    endpoint: str,
    corp_code: str,
    bgn_de: str,
    end_de: str,
) -> list[dict[str, Any]]:
    response = requests.get(
        f"{DART_API_BASE}/{endpoint}",
        params={
            "crtfc_key": api_key,
            "corp_code": corp_code,
            "bgn_de": bgn_de,
            "end_de": end_de,
        },
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    status = data.get("status")
    if status == "013":
        return []
    if status != "000":
        raise ValueError(f"OpenDART {endpoint} error: {status} {data.get('message')}")
    return data.get("list", []) or []


def build_event_row(
    batch_id: str,
    company: dict[str, str],
    event_api: dict[str, str],
    item: dict[str, Any],
) -> dict[str, Any]:
    rcept_no = str(item.get("rcept_no", "")).strip()
    stock_code = item.get("stock_code") or company.get("stock_code", "")
    corp_code = item.get("corp_code") or company.get("corp_code", "")
    company_name = item.get("corp_name") or company.get("corp_name", "")
    filtered_details = filter_details(item)

    return {
        "batch_id": batch_id,
        "stock_code": stock_code,
        "corp_code": corp_code,
        "company_name": company_name,
        "event_category": event_api["category"],
        "event_code": event_api["event_code"],
        "event_name": event_api["event_name"],
        "rcept_date": rcept_date_from_no(rcept_no),
        "report_url": disclosure_url(rcept_no) if rcept_no else "",
        "source_api": event_api["endpoint"],
        "summary": build_summary(filtered_details),
        "details_json": json.dumps(filtered_details, ensure_ascii=False, sort_keys=True),
    }


def export_major_event_occurrences(
    batch_id: str,
    company_limit: int | None,
    event_limit: int | None,
    bgn_de: str,
    end_de: str,
    sleep_interval: float,
    output_root: Path = DISCLOSURE_EXPORT_ROOT,
) -> dict[str, int]:
    api_key = load_api_key()
    if not api_key:
        raise RuntimeError("DART_API_KEY is not configured.")

    companies = load_companies(batch_id, company_limit)
    output_rows: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, str]] = set()
    counters = {
        "companies_checked": 0,
        "api_calls": 0,
        "events": 0,
        "failed": 0,
    }

    print(
        f"[start] structured events batch_id={batch_id}, companies={len(companies)}, "
        f"period={bgn_de}-{end_de}",
        flush=True,
    )

    for company in companies:
        if event_limit and event_limit > 0 and counters["events"] >= event_limit:
            break

        counters["companies_checked"] += 1
        for event_api in EVENT_APIS:
            if event_limit and event_limit > 0 and counters["events"] >= event_limit:
                break

            try:
                counters["api_calls"] += 1
                items = fetch_event_items(
                    api_key=api_key,
                    endpoint=event_api["endpoint"],
                    corp_code=company.get("corp_code", ""),
                    bgn_de=bgn_de,
                    end_de=end_de,
                )
            except Exception as error:
                counters["failed"] += 1
                print(
                    f"[fail] stock_code={company.get('stock_code', '')} "
                    f"event={event_api['event_name']} error={sanitize_error_message(str(error))}",
                    flush=True,
                )
                continue

            for item in items:
                key = (
                    event_api["event_code"],
                    str(item.get("rcept_no", "")),
                    company.get("stock_code", ""),
                )
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                output_rows.append(
                    build_event_row(
                        batch_id=batch_id,
                        company=company,
                        event_api=event_api,
                        item=item,
                    )
                )
                counters["events"] += 1

            if items:
                print(
                    f"[event] stock_code={company.get('stock_code', '')} "
                    f"event={event_api['event_name']} count={len(items)}",
                    flush=True,
                )

            if sleep_interval > 0:
                time.sleep(sleep_interval)

    output_path = output_root / batch_id / "major_event_occurrences.csv"
    write_csv_rows(output_path, output_rows)

    print(f"[done] output={output_path}", flush=True)
    print(f"[done] counters={counters}", flush=True)
    return counters


def export_batches(
    batch_ids: list[str],
    company_limit: int | None,
    event_limit: int | None,
    bgn_de: str,
    end_de: str,
    sleep_interval: float,
    output_root: Path = DISCLOSURE_EXPORT_ROOT,
) -> dict[str, dict[str, int]]:
    results: dict[str, dict[str, int]] = {}
    for batch_id in batch_ids:
        results[batch_id] = export_major_event_occurrences(
            batch_id=batch_id,
            company_limit=company_limit,
            event_limit=event_limit,
            bgn_de=bgn_de,
            end_de=end_de,
            sleep_interval=sleep_interval,
            output_root=output_root,
        )
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export structured OpenDART DS005 event occurrences."
    )
    parser.add_argument("--batch-id", default="kospi_001")
    parser.add_argument(
        "--all-batches",
        action="store_true",
        help="Export all prepared company batches.",
    )
    parser.add_argument("--company-limit", type=int, default=50)
    parser.add_argument("--event-limit", type=int, default=30)
    parser.add_argument("--bgn-de", default="20190101")
    parser.add_argument("--end-de", default="20260512")
    parser.add_argument("--sleep-interval", type=float, default=0.05)
    parser.add_argument(
        "--output-root",
        default=str(DISCLOSURE_EXPORT_ROOT),
        help="Directory where disclosure exports are written.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_root = Path(args.output_root)
    if args.all_batches:
        results = export_batches(
            batch_ids=DEFAULT_BATCH_IDS,
            company_limit=args.company_limit,
            event_limit=args.event_limit,
            bgn_de=args.bgn_de,
            end_de=args.end_de,
            sleep_interval=args.sleep_interval,
            output_root=output_root,
        )
        print(f"[done] all_batch_counters={results}", flush=True)
    else:
        export_major_event_occurrences(
            batch_id=args.batch_id,
            company_limit=args.company_limit,
            event_limit=args.event_limit,
            bgn_de=args.bgn_de,
            end_de=args.end_de,
            sleep_interval=args.sleep_interval,
            output_root=output_root,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
