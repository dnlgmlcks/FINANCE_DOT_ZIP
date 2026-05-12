"""
Export compact OpenDART major-event disclosures for vector DB ingestion.

This covers the screenshot-style "주요사항보고서" / event disclosures such as
bankruptcy, business suspension, rehabilitation, transfer/acquisition, merger,
split, and similar qualitative event reports.
"""

from __future__ import annotations

import argparse
import csv
import re
import time
from pathlib import Path
from typing import Any

import requests

from export_disclosure_business_sections import (
    DART_API_BASE,
    DISCLOSURE_EXPORT_ROOT,
    EXPORT_ROOT,
    SOURCE_API,
    chunk_text,
    disclosure_url,
    download_document_zip,
    html_to_text,
    load_api_key,
    read_csv_rows,
    read_zip_text,
    sanitize_error_message,
)


LIST_API = "list.json"

CSV_HEADERS = [
    "title",
    "content",
    "url",
    "published_date",
    "source_type",
    "disclosure_type",
    "event_category",
    "stock_code",
    "company_name",
    "corp_code",
    "rcept_no",
    "report_name",
    "document_id",
    "chunk_id",
    "chunk_index",
    "chunk_count",
]

EVENT_KEYWORDS = [
    ("부도발생", ["부도발생", "부도 발생"]),
    ("영업정지", ["영업정지", "영업 정지"]),
    ("회생절차", ["회생절차", "회생 절차"]),
    ("해산사유", ["해산사유", "해산 사유"]),
    ("영업양수", ["영업양수", "영업 양수"]),
    ("영업양도", ["영업양도", "영업 양도"]),
    ("유형자산양수", ["유형자산 양수", "유형자산양수"]),
    ("유형자산양도", ["유형자산 양도", "유형자산양도"]),
    ("회사합병", ["회사합병", "합병 결정", "합병결정"]),
    ("회사분할", ["회사분할", "분할 결정", "분할결정"]),
    ("회사분할합병", ["분할합병", "분할합병 결정"]),
]


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_HEADERS})


def normalize_date(value: str) -> str:
    value = (value or "").strip()
    if re.fullmatch(r"\d{8}", value):
        return f"{value[:4]}-{value[4:6]}-{value[6:8]}"
    return value


def infer_event_category(report_name: str, text: str = "") -> str:
    haystack = f"{report_name}\n{text[:3000]}"
    for category, keywords in EVENT_KEYWORDS:
        if any(keyword in haystack for keyword in keywords):
            return category
    match = re.search(r"주요사항보고서\(([^)]+)\)", report_name or "")
    if match:
        return match.group(1).strip()
    return "주요사항보고서"


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


def fetch_major_disclosure_list(
    api_key: str,
    corp_code: str,
    bgn_de: str,
    end_de: str,
    page_count: int = 100,
) -> list[dict[str, Any]]:
    response = requests.get(
        f"{DART_API_BASE}/{LIST_API}",
        params={
            "crtfc_key": api_key,
            "corp_code": corp_code,
            "bgn_de": bgn_de,
            "end_de": end_de,
            "last_reprt_at": "Y",
            "pblntf_ty": "B",
            "pblntf_detail_ty": "B001",
            "sort": "date",
            "sort_mth": "desc",
            "page_no": "1",
            "page_count": str(page_count),
        },
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    if data.get("status") == "013":
        return []
    if data.get("status") != "000":
        raise ValueError(f"OpenDART list error: {data.get('status')} {data.get('message')}")
    return data.get("list", []) or []


def build_output_rows(
    disclosure: dict[str, Any],
    document_text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[dict[str, Any]]:
    rcept_no = disclosure.get("rcept_no", "")
    report_name = disclosure.get("report_nm", "")
    company_name = disclosure.get("corp_name", "")
    stock_code = disclosure.get("stock_code", "")
    published_date = normalize_date(disclosure.get("rcept_dt", ""))
    title = f"{company_name} {report_name}".strip()
    document_id = f"dart_{rcept_no}_major"
    event_category = infer_event_category(report_name, document_text)
    chunks = chunk_text(document_text, chunk_size, chunk_overlap)

    rows: list[dict[str, Any]] = []
    for index, chunk in enumerate(chunks):
        rows.append(
            {
                "title": title,
                "content": chunk,
                "url": disclosure_url(rcept_no),
                "published_date": published_date,
                "source_type": "disclosure",
                "disclosure_type": "major_event",
                "event_category": event_category,
                "stock_code": stock_code,
                "company_name": company_name,
                "corp_code": disclosure.get("corp_code", ""),
                "rcept_no": rcept_no,
                "report_name": report_name,
                "document_id": document_id,
                "chunk_id": f"{document_id}_{index:04d}",
                "chunk_index": index,
                "chunk_count": len(chunks),
            }
        )
    return rows


def export_major_disclosures(
    batch_id: str,
    limit: int,
    company_limit: int | None,
    bgn_de: str,
    end_de: str,
    chunk_size: int,
    chunk_overlap: int,
    sleep_interval: float,
    force_refresh: bool,
    output_root: Path = DISCLOSURE_EXPORT_ROOT,
) -> dict[str, int]:
    api_key = load_api_key()
    if not api_key:
        raise RuntimeError("DART_API_KEY is not configured.")

    companies = load_companies(batch_id, company_limit)
    output_rows: list[dict[str, Any]] = []
    seen_rcept_numbers: set[str] = set()
    counters = {
        "companies_checked": 0,
        "disclosures_found": 0,
        "success": 0,
        "failed": 0,
        "chunks": 0,
    }

    print(
        f"[start] major disclosures batch_id={batch_id}, companies={len(companies)}, "
        f"limit={limit}, period={bgn_de}-{end_de}",
        flush=True,
    )

    for company in companies:
        if limit > 0 and counters["success"] >= limit:
            break

        counters["companies_checked"] += 1
        corp_code = company.get("corp_code", "")
        try:
            disclosures = fetch_major_disclosure_list(
                api_key=api_key,
                corp_code=corp_code,
                bgn_de=bgn_de,
                end_de=end_de,
            )
        except Exception as error:
            counters["failed"] += 1
            print(
                f"[list-fail] stock_code={company.get('stock_code', '')} "
                f"error={sanitize_error_message(str(error))}",
                flush=True,
            )
            continue

        counters["disclosures_found"] += len(disclosures)

        for disclosure in disclosures:
            if limit > 0 and counters["success"] >= limit:
                break

            rcept_no = disclosure.get("rcept_no", "")
            if not rcept_no or rcept_no in seen_rcept_numbers:
                continue
            seen_rcept_numbers.add(rcept_no)

            try:
                zip_path = download_document_zip(api_key, rcept_no, force_refresh=force_refresh)
                document_text = read_zip_text(zip_path)
                if not document_text:
                    raise ValueError("empty document text")

                rows = build_output_rows(
                    disclosure=disclosure,
                    document_text=document_text,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
                output_rows.extend(rows)
                counters["success"] += 1
                counters["chunks"] += len(rows)
                print(
                    f"[ok] {counters['success']}/{limit} stock_code={disclosure.get('stock_code', '')} "
                    f"report={disclosure.get('report_nm', '')} chunks={len(rows)}",
                    flush=True,
                )
            except Exception as error:
                counters["failed"] += 1
                print(
                    f"[doc-fail] rcept_no={rcept_no} error={sanitize_error_message(str(error))}",
                    flush=True,
                )

            if sleep_interval > 0:
                time.sleep(sleep_interval)

    output_path = output_root / batch_id / "major_disclosures_ver2.csv"
    write_csv_rows(output_path, output_rows)

    print(f"[done] output={output_path}", flush=True)
    print(f"[done] counters={counters}", flush=True)
    return counters


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export compact OpenDART 주요사항보고서 chunks for vector DB ingestion."
    )
    parser.add_argument("--batch-id", default="kospi_001")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--company-limit", type=int, default=200)
    parser.add_argument("--bgn-de", default="20190101")
    parser.add_argument("--end-de", default="20260512")
    parser.add_argument("--chunk-size", type=int, default=1800)
    parser.add_argument("--chunk-overlap", type=int, default=200)
    parser.add_argument("--sleep-interval", type=float, default=0.5)
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument(
        "--output-root",
        default=str(DISCLOSURE_EXPORT_ROOT),
        help="Directory where disclosure exports are written.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    export_major_disclosures(
        batch_id=args.batch_id,
        limit=args.limit,
        company_limit=args.company_limit,
        bgn_de=args.bgn_de,
        end_de=args.end_de,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        sleep_interval=args.sleep_interval,
        force_refresh=args.force_refresh,
        output_root=Path(args.output_root),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
