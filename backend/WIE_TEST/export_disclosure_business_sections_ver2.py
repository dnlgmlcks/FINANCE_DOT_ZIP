"""
Export a compact OpenDART business-section CSV for vector DB ingestion.

This is a comparison-friendly v2 exporter. It reuses the downloader and parser
from export_disclosure_business_sections.py, but writes a smaller CSV:
disclosure_business_sections_ver2.csv.
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path
from typing import Any

from export_disclosure_business_sections import (
    DISCLOSURE_EXPORT_ROOT,
    EXPORT_ROOT,
    SOURCE_API,
    chunk_text,
    disclosure_url,
    download_document_zip,
    extract_business_section,
    load_api_key,
    read_zip_text,
    report_date_from_rcept_no,
    sanitize_error_message,
    select_report_rows,
)


CSV_HEADERS_V2 = [
    "title",
    "content",
    "url",
    "published_date",
    "source_type",
    "stock_code",
    "company_name",
    "bsns_year",
    "rcept_no",
    "section_title",
    "document_id",
    "chunk_id",
    "chunk_index",
    "chunk_count",
]


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_HEADERS_V2)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_HEADERS_V2})


def build_output_rows(
    report_row: dict[str, str],
    section_title: str,
    section_text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[dict[str, Any]]:
    rcept_no = report_row.get("rcept_no", "")
    stock_code = report_row.get("stock_code", "")
    company_name = report_row.get("corp_name", "")
    bsns_year = report_row.get("bsns_year", "")
    published_date = report_date_from_rcept_no(rcept_no)
    title = f"{company_name} {bsns_year} 사업보고서 II. 사업의 내용".strip()
    document_id = f"dart_{rcept_no}_business"
    chunks = chunk_text(section_text, chunk_size, chunk_overlap)

    rows: list[dict[str, Any]] = []
    for index, chunk in enumerate(chunks):
        rows.append(
            {
                "title": title,
                "content": chunk,
                "url": disclosure_url(rcept_no),
                "published_date": published_date,
                "source_type": "disclosure",
                "stock_code": stock_code,
                "company_name": company_name,
                "bsns_year": bsns_year,
                "rcept_no": rcept_no,
                "section_title": section_title,
                "document_id": document_id,
                "chunk_id": f"{document_id}_{index:04d}",
                "chunk_index": index,
                "chunk_count": len(chunks),
            }
        )
    return rows


def export_disclosure_business_sections_ver2(
    batch_id: str,
    limit: int,
    reprt_code: str,
    chunk_size: int,
    chunk_overlap: int,
    sleep_interval: float,
    force_refresh: bool,
    output_root: Path = DISCLOSURE_EXPORT_ROOT,
) -> dict[str, int]:
    api_key = load_api_key()
    if not api_key:
        raise RuntimeError("DART_API_KEY is not configured.")

    report_rows = select_report_rows(batch_id=batch_id, limit=limit, reprt_code=reprt_code)
    output_rows: list[dict[str, Any]] = []
    counters = {"success": 0, "failed": 0, "section_not_found": 0, "chunks": 0}

    print(f"[start] ver2 batch_id={batch_id}, reports={len(report_rows)}, limit={limit}", flush=True)

    for row_index, report_row in enumerate(report_rows, start=1):
        rcept_no = report_row.get("rcept_no", "")
        stock_code = report_row.get("stock_code", "")
        company_name = report_row.get("corp_name", "")

        try:
            zip_path = download_document_zip(api_key, rcept_no, force_refresh=force_refresh)
            full_text = read_zip_text(zip_path)
            section_title, section_text = extract_business_section(full_text)

            if not section_text:
                counters["section_not_found"] += 1
                print(f"[skip] {row_index}/{len(report_rows)} rcept_no={rcept_no} section_not_found", flush=True)
            else:
                rows = build_output_rows(
                    report_row=report_row,
                    section_title=section_title,
                    section_text=section_text,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
                output_rows.extend(rows)
                counters["success"] += 1
                counters["chunks"] += len(rows)
                print(
                    f"[ok] {row_index}/{len(report_rows)} stock_code={stock_code} "
                    f"company={company_name} chars={len(section_text)} chunks={len(rows)}",
                    flush=True,
                )

        except Exception as error:
            counters["failed"] += 1
            safe_error = sanitize_error_message(str(error))
            print(f"[fail] {row_index}/{len(report_rows)} rcept_no={rcept_no} error={safe_error}", flush=True)

        if sleep_interval > 0 and row_index < len(report_rows):
            time.sleep(sleep_interval)

    output_path = output_root / batch_id / "disclosure_business_sections_ver2.csv"
    write_csv_rows(output_path, output_rows)

    print(f"[done] output={output_path}", flush=True)
    print(f"[done] counters={counters}", flush=True)
    return counters


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export compact DART 'II. 사업의 내용' text chunks from existing reports.csv."
    )
    parser.add_argument("--batch-id", default="kospi_001")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--reprt-code", default="11011")
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
    export_disclosure_business_sections_ver2(
        batch_id=args.batch_id,
        limit=args.limit,
        reprt_code=args.reprt_code,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        sleep_interval=args.sleep_interval,
        force_refresh=args.force_refresh,
        output_root=Path(args.output_root),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
