"""
Export OpenDART business-description disclosure text for vector DB ingestion.

The script reads an existing batch reports.csv, downloads each disclosure
document ZIP through OpenDART document.xml, extracts only "II. 사업의 내용",
and writes chunk-level rows to disclosure_business_sections.csv.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv


def find_project_root(start: Path) -> Path:
    for path in [start, *start.parents]:
        if (path / "backend").exists() and (path / "data").exists():
            return path
    raise RuntimeError("Project root not found.")


PROJECT_ROOT = find_project_root(Path(__file__).resolve())
BACKEND_ROOT = PROJECT_ROOT / "backend"
EXPORT_ROOT = PROJECT_ROOT / "data" / "export"
DISCLOSURE_EXPORT_ROOT = EXPORT_ROOT / "disclosure"
RAW_DISCLOSURE_ROOT = PROJECT_ROOT / "data" / "raw" / "disclosures"
DART_API_BASE = "https://opendart.fss.or.kr/api"
SOURCE_API = "document.xml"


CSV_HEADERS = [
    "title",
    "content",
    "raw_content",
    "url",
    "published_date",
    "source_type",
    "source_api",
    "company_name",
    "stock_code",
    "ticker",
    "corp_code",
    "report_name",
    "rcept_no",
    "report_date",
    "bsns_year",
    "reprt_code",
    "section_title",
    "document_id",
    "chunk_id",
    "chunk_index",
    "chunk_count",
    "batch_id",
    "char_count",
    "collected_at",
]


SECTION_START_RE = re.compile(
    r"(?:^|\n)\s*(?:II|Ⅱ|2)\s*[\.\)]?\s*사업의\s*내용\b",
    re.IGNORECASE,
)
SECTION_END_RE = re.compile(
    r"(?:^|\n)\s*(?:III|Ⅲ|3)\s*[\.\)]?\s*(?:재무에\s*관한\s*사항|재무제표|이사의\s*경영진단)",
    re.IGNORECASE,
)


def load_api_key() -> str:
    """Load DART_API_KEY from .env files, tolerating a line-wrapped value."""
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(BACKEND_ROOT / ".env")

    api_key = os.getenv("DART_API_KEY", "").strip()
    if api_key:
        return api_key

    env_path = BACKEND_ROOT / ".env"
    if not env_path.exists():
        return ""

    lines = env_path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if not line.strip().startswith("DART_API_KEY="):
            continue

        inline_value = line.split("=", 1)[1].strip()
        if inline_value:
            return inline_value

        if index + 1 < len(lines):
            next_line = lines[index + 1].strip()
            if re.fullmatch(r"[A-Za-z0-9]{40}", next_line):
                return next_line

    return ""


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in CSV_HEADERS})


def report_date_from_rcept_no(rcept_no: str) -> str:
    if re.fullmatch(r"\d{14}", rcept_no or ""):
        return f"{rcept_no[:4]}-{rcept_no[4:6]}-{rcept_no[6:8]}"
    return ""


def disclosure_url(rcept_no: str) -> str:
    return f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"


def download_document_zip(api_key: str, rcept_no: str, force_refresh: bool = False) -> Path:
    zip_path = RAW_DISCLOSURE_ROOT / f"{rcept_no}.zip"
    if zip_path.exists() and not force_refresh:
        return zip_path

    RAW_DISCLOSURE_ROOT.mkdir(parents=True, exist_ok=True)
    response = requests.get(
        f"{DART_API_BASE}/{SOURCE_API}",
        params={"crtfc_key": api_key, "rcept_no": rcept_no},
        timeout=30,
    )
    response.raise_for_status()

    content = response.content
    zip_path.write_bytes(content)

    if not content.startswith(b"PK"):
        message = extract_open_dart_error(content)
        raise ValueError(f"OpenDART did not return a ZIP for {rcept_no}: {message}")

    return zip_path


def extract_open_dart_error(content: bytes) -> str:
    text = decode_bytes(content)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:300] if text else repr(content[:80])


def sanitize_error_message(message: str) -> str:
    """Hide API keys from request exception strings."""
    message = message or ""
    return re.sub(r"(crtfc_key=)[^&\s)]+", r"\1***", message)


def decode_bytes(content: bytes) -> str:
    for encoding in ("utf-8", "cp949", "euc-kr"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def read_zip_text(zip_path: Path) -> str:
    parts: list[str] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            lower_name = name.lower()
            if not lower_name.endswith((".xml", ".html", ".htm", ".txt")):
                continue

            content = zf.read(name)
            text = decode_bytes(content)
            parts.append(html_to_text(text))

    return "\n".join(part for part in parts if part.strip())


def html_to_text(text: str) -> str:
    soup = BeautifulSoup(text, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    visible_text = soup.get_text("\n")
    return normalize_text(visible_text)


def normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()


def extract_business_section(full_text: str) -> tuple[str, str]:
    start_match = SECTION_START_RE.search(full_text)
    if not start_match:
        return "", ""

    section_start = start_match.start()
    end_match = SECTION_END_RE.search(full_text, pos=start_match.end())
    section_end = end_match.start() if end_match else len(full_text)

    section_text = normalize_text(full_text[section_start:section_end])
    first_line = section_text.splitlines()[0].strip() if section_text else "II. 사업의 내용"
    return first_line, section_text


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if chunk_size <= 0:
        return [text]
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def build_output_rows(
    report_row: dict[str, str],
    section_title: str,
    section_text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[dict[str, Any]]:
    batch_id = report_row.get("batch_id", "")
    rcept_no = report_row.get("rcept_no", "")
    stock_code = report_row.get("stock_code", "")
    company_name = report_row.get("corp_name", "")
    bsns_year = report_row.get("bsns_year", "")
    report_date = report_date_from_rcept_no(rcept_no)
    title = f"{company_name} {bsns_year} 사업보고서 II. 사업의 내용".strip()
    chunks = chunk_text(section_text, chunk_size, chunk_overlap)
    collected_at = datetime.now().isoformat(timespec="seconds")
    document_id = f"dart_{rcept_no}_business"

    rows: list[dict[str, Any]] = []
    for index, chunk in enumerate(chunks):
        rows.append(
            {
                "batch_id": batch_id,
                "source_type": "disclosure",
                "source_api": SOURCE_API,
                "rcept_no": rcept_no,
                "corp_code": report_row.get("corp_code", ""),
                "stock_code": stock_code,
                "ticker": stock_code,
                "company_name": company_name,
                "report_name": report_row.get("report_name", "") or "사업보고서",
                "report_date": report_date,
                "published_date": report_date,
                "bsns_year": bsns_year,
                "reprt_code": report_row.get("reprt_code", ""),
                "section_title": section_title,
                "title": title,
                "url": disclosure_url(rcept_no),
                "content": chunk,
                "raw_content": section_text if index == 0 else "",
                "document_id": document_id,
                "chunk_id": f"{document_id}_{index:04d}",
                "chunk_index": index,
                "chunk_count": len(chunks),
                "char_count": len(chunk),
                "collected_at": collected_at,
            }
        )
    return rows


def select_report_rows(batch_id: str, limit: int, reprt_code: str) -> list[dict[str, str]]:
    reports_path = EXPORT_ROOT / batch_id / "reports.csv"
    rows = read_csv_rows(reports_path)
    selected = [
        row
        for row in rows
        if row.get("rcept_no") and (not reprt_code or row.get("reprt_code") == reprt_code)
    ]
    return selected[:limit] if limit > 0 else selected


def export_disclosure_business_sections(
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

    print(f"[start] batch_id={batch_id}, reports={len(report_rows)}, limit={limit}", flush=True)

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

    output_path = output_root / batch_id / "disclosure_business_sections.csv"
    write_csv_rows(output_path, output_rows)

    print(f"[done] output={output_path}", flush=True)
    print(f"[done] counters={counters}", flush=True)
    return counters


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export DART 'II. 사업의 내용' text chunks from existing reports.csv."
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
    export_disclosure_business_sections(
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
