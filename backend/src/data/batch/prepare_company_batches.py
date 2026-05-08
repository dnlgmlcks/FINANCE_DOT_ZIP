"""
OpenDART 기업개황 API 기준으로 상장사 master와 batch companies.csv를 준비합니다.

이 스크립트는 전체 재무제표 API(fnlttSinglAcntAll.json)를 호출하지 않습니다.
corpCode.xml에서 stock_code가 있는 상장 후보를 추출한 뒤, company.json으로
corp_cls, induty_code, acc_mt 같은 기업개황 정보를 보강합니다.

company.json 호출은 API 요청 수를 사용하므로 처음에는 반드시 --limit 20처럼
작은 제한값으로 테스트한 뒤 전체 실행 여부를 팀에서 승인해야 합니다.
--limit을 생략하거나 0으로 주면 제한 없이 전체 후보를 처리합니다.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

import requests
from dotenv import load_dotenv


BACKEND_SRC_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(BACKEND_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_SRC_ROOT))

from data.batch.create_batch_templates import CSV_HEADERS, EXPORT_ROOT  # noqa: E402


load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(PROJECT_ROOT / "backend" / ".env")
DART_API_BASE = "https://opendart.fss.or.kr/api"
DART_API_KEY = os.getenv("DART_API_KEY", "")
DATA_RAW_PATH = PROJECT_ROOT / "data" / "raw"
DATA_INTERIM_PATH = PROJECT_ROOT / "data" / "interim"


COMPANY_MASTER_ROOT = PROJECT_ROOT / "data" / "company_master"
LISTED_COMPANIES_MASTER_PATH = COMPANY_MASTER_ROOT / "listed_companies_master.csv"
COMPANY_MASTER_LOG_PATH = COMPANY_MASTER_ROOT / "company_master_log.csv"
COMPANY_BATCH_SUMMARY_PATH = COMPANY_MASTER_ROOT / "company_batch_summary.md"

COMPANY_MASTER_HEADERS = [
    "corp_code",
    "stock_code",
    "corp_name",
    "stock_name",
    "corp_cls",
    "market",
    "induty_code",
    "acc_mt",
    "source_api",
    "collected_at",
]

COMPANY_MASTER_LOG_HEADERS = [
    "corp_code",
    "stock_code",
    "corp_name",
    "status",
    "error_code",
    "error_message",
    "started_at",
    "finished_at",
]

CORP_CLS_TO_MARKET = {
    "Y": "KOSPI",
    "K": "KOSDAQ",
    "N": "KONEX",
    "E": "OTHER",
}

MARKET_BATCH_LIMITS = {
    "KOSPI": ["kospi_001", "kospi_002"],
    "KOSDAQ": ["kosdaq_001", "kosdaq_002", "kosdaq_003", "kosdaq_004"],
    "KONEX": ["konex_001"],
}


@dataclass
class ListedCandidate:
    """corpCode.xml에서 추출한 상장 후보 기업입니다."""

    corp_code: str
    stock_code: str
    corp_name: str


def map_corp_cls_to_market(corp_cls: str) -> str:
    """company.json의 corp_cls 값을 OpenDART 기준 시장명으로 변환합니다."""
    return CORP_CLS_TO_MARKET.get((corp_cls or "").strip().upper(), "OTHER")


def sanitize_error_message(message: str) -> str:
    """오류 메시지에 API 키가 포함되지 않도록 인증 파라미터를 마스킹합니다."""
    return re.sub(r"(crtfc_key=)[^&\s)]+", r"\1***", message or "")


def load_listed_candidates(force_refresh_corp_code: bool = False) -> list[ListedCandidate]:
    """corpCode.xml에서 stock_code가 있는 상장 후보 기업만 추출합니다."""
    xml_path = get_corp_code_xml(force_refresh=force_refresh_corp_code)
    corp_mapping = parse_corp_code_xml(xml_path)
    candidates = [
        ListedCandidate(
            corp_code=item.get("corp_code", ""),
            stock_code=stock_code,
            corp_name=item.get("corp_name", ""),
        )
        for stock_code, item in corp_mapping.items()
        if stock_code.strip() and item.get("corp_code")
    ]
    return sorted(candidates, key=lambda item: item.stock_code)


def get_corp_code_xml(force_refresh: bool = False) -> Path:
    """corpCode.xml ZIP을 준비하고 CORPCODE.xml 경로를 반환합니다."""
    zip_path = DATA_RAW_PATH / "corp_code.zip"
    xml_path = DATA_INTERIM_PATH / "CORPCODE.xml"

    if xml_path.exists() and not force_refresh:
        return xml_path

    if not zip_path.exists() or force_refresh:
        DATA_RAW_PATH.mkdir(parents=True, exist_ok=True)
        response = requests.get(
            f"{DART_API_BASE}/corpCode.xml",
            params={"crtfc_key": DART_API_KEY},
            timeout=20,
        )
        response.raise_for_status()
        zip_path.write_bytes(response.content)

    DATA_INTERIM_PATH.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zip_file:
        target_name = None
        for name in zip_file.namelist():
            if name.lower().endswith("corpcode.xml"):
                target_name = name
                break
        if not target_name:
            raise RuntimeError("corpCode ZIP 안에서 CORPCODE.xml을 찾지 못했습니다.")
        zip_file.extract(target_name, DATA_INTERIM_PATH)
        extracted_path = DATA_INTERIM_PATH / target_name

    if extracted_path != xml_path:
        extracted_path.replace(xml_path)

    return xml_path


def parse_corp_code_xml(xml_path: Path) -> dict[str, dict[str, str]]:
    """CORPCODE.xml을 stock_code 기준 dict로 파싱합니다."""
    mapping: dict[str, dict[str, str]] = {}
    tree = ET.parse(xml_path)
    root = tree.getroot()
    items = root.findall(".//list") or root.findall(".//item")

    for item in items:
        stock_code = (item.findtext("stock_code") or "").strip()
        corp_code = (item.findtext("corp_code") or "").strip()
        corp_name = (item.findtext("corp_name") or "").strip()
        if stock_code and corp_code:
            mapping[stock_code] = {
                "corp_code": corp_code,
                "corp_name": corp_name,
            }

    return mapping


def fetch_company_overview(corp_code: str, timeout: int = 20) -> dict[str, Any]:
    """OpenDART company.json 기업개황 API를 호출합니다."""
    url = f"{DART_API_BASE}/company.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code,
    }
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def build_master_row(candidate: ListedCandidate, overview: dict[str, Any], collected_at: str) -> dict[str, str]:
    """company.json 응답을 listed_companies_master.csv 행으로 변환합니다."""
    corp_cls = str(overview.get("corp_cls", "")).strip()
    return {
        "corp_code": candidate.corp_code,
        "stock_code": str(overview.get("stock_code") or candidate.stock_code).strip(),
        "corp_name": str(overview.get("corp_name") or candidate.corp_name).strip(),
        "stock_name": str(overview.get("stock_name", "")).strip(),
        "corp_cls": corp_cls,
        "market": map_corp_cls_to_market(corp_cls),
        "induty_code": str(overview.get("induty_code", "")).strip(),
        "acc_mt": str(overview.get("acc_mt", "")).strip(),
        "source_api": "company.json",
        "collected_at": collected_at,
    }


def write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    """CSV 헤더와 행을 UTF-8 BOM 형식으로 저장합니다."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})


def split_rows_by_market(rows: list[dict[str, str]], batch_size: int) -> dict[str, list[dict[str, str]]]:
    """market 기준으로 master 행을 나누고 지정된 마지막 batch에 나머지를 모두 배정합니다."""
    batches: dict[str, list[dict[str, str]]] = {}

    for market, batch_ids in MARKET_BATCH_LIMITS.items():
        market_rows = [row for row in rows if row.get("market") == market]
        for batch_index, batch_id in enumerate(batch_ids):
            start = batch_index * batch_size
            if batch_index == len(batch_ids) - 1:
                selected_rows = market_rows[start:]
            else:
                selected_rows = market_rows[start:start + batch_size]

            if not selected_rows:
                continue

            batch_rows = []
            for row in selected_rows:
                batch_rows.append({
                    "batch_id": batch_id,
                    "corp_code": row.get("corp_code", ""),
                    "stock_code": row.get("stock_code", ""),
                    "corp_name": row.get("corp_name", ""),
                    "stock_name": row.get("stock_name", ""),
                    "corp_cls": row.get("corp_cls", ""),
                    "market": row.get("market", ""),
                    "induty_code": row.get("induty_code", ""),
                    "acc_mt": row.get("acc_mt", ""),
                    "collected_at": row.get("collected_at", ""),
                })
            batches[batch_id] = batch_rows

    return batches


def reset_batch_companies_files() -> list[Path]:
    """전체 batch companies.csv를 헤더만 남긴 상태로 초기화합니다."""
    reset_paths: list[Path] = []
    company_headers = CSV_HEADERS["companies.csv"]

    for batch_ids in MARKET_BATCH_LIMITS.values():
        for batch_id in batch_ids:
            output_path = EXPORT_ROOT / batch_id / "companies.csv"
            write_csv(output_path, company_headers, [])
            reset_paths.append(output_path)

    return reset_paths


def write_batch_companies(
    rows: list[dict[str, str]],
    batch_size: int,
    force_refresh: bool,
) -> list[Path]:
    """시장별 batch 폴더의 companies.csv를 corp_cls 기반 market 분류로 채웁니다."""
    written_paths: list[Path] = []
    company_headers = CSV_HEADERS["companies.csv"]

    if force_refresh:
        reset_batch_companies_files()

    for batch_id, batch_rows in split_rows_by_market(rows, batch_size).items():
        batch_dir = EXPORT_ROOT / batch_id
        if not batch_dir.exists():
            continue

        output_path = batch_dir / "companies.csv"
        write_csv(output_path, company_headers, batch_rows)
        written_paths.append(output_path)

    return written_paths


def count_by_value(rows: list[dict[str, str]], key: str) -> dict[str, int]:
    """지정한 컬럼값별 행 개수를 계산합니다."""
    counts: dict[str, int] = {}
    for row in rows:
        value = row.get(key, "") or "EMPTY"
        counts[value] = counts.get(value, 0) + 1
    return counts


def choose_progress_interval(total_count: int) -> int:
    """전체 처리 건수에 따라 진행률 출력 간격을 정합니다."""
    return 10 if total_count <= 200 else 50


def write_company_batch_summary(
    master_rows: list[dict[str, str]],
    log_rows: list[dict[str, str]],
    written_paths: list[Path],
    limit: int | None,
    batch_size: int,
) -> None:
    """company master 생성 결과와 batch별 companies.csv 갱신 결과를 요약합니다."""
    market_counts = count_by_value(master_rows, "market")
    status_counts = count_by_value(log_rows, "status")

    lines = [
        "# Company Batch Summary",
        "",
        "## 실행 기준",
        f"- limit: {limit if limit is not None else 'none'}",
        f"- batch_size: {batch_size}",
        "- source: corpCode.xml, company.json",
        "- market 기준: company.json corp_cls",
        "",
        "## API 호출 범위",
        "- corpCode.xml: 상장 후보 기업의 corp_code, stock_code, corp_name 매핑용",
        "- company.json: corp_cls, stock_name, induty_code, acc_mt 보강용",
        "- fnlttSinglAcntAll.json: 호출하지 않음",
        "",
        "## 처리 결과",
        f"- master rows: {len(master_rows)}",
        f"- log rows: {len(log_rows)}",
        "",
        "## log status counts",
        *[f"- {status}: {count}" for status, count in sorted(status_counts.items())],
        "",
        "## market counts",
        *[f"- {market}: {count}" for market, count in sorted(market_counts.items())],
        "",
        "## updated batch companies files",
        *[f"- {path.relative_to(PROJECT_ROOT)}" for path in written_paths],
        "",
    ]

    COMPANY_BATCH_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    COMPANY_BATCH_SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")


def prepare_company_master(
    limit: int | None,
    batch_size: int,
    sleep_interval: float,
    force_refresh: bool,
    force_refresh_corp_code: bool,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[Path]]:
    """상장 후보를 company.json으로 보강하고 master/log/batch companies.csv를 생성합니다."""
    if not DART_API_KEY:
        raise RuntimeError("DART_API_KEY가 설정되지 않았습니다.")

    refresh_corp_code = force_refresh or force_refresh_corp_code
    candidates = load_listed_candidates(force_refresh_corp_code=refresh_corp_code)
    if limit is not None and limit > 0:
        candidates = candidates[:limit]

    master_rows: list[dict[str, str]] = []
    log_rows: list[dict[str, str]] = []
    total_count = len(candidates)
    progress_interval = choose_progress_interval(total_count)
    success_count = 0
    failed_count = 0

    print(
        "[start] "
        f"company master preparation: total={total_count}, "
        f"limit={limit if limit is not None else 'none'}, "
        f"batch_size={batch_size}, sleep_interval={sleep_interval}",
        flush=True,
    )

    for index, candidate in enumerate(candidates):
        current_number = index + 1
        print(
            "[current] "
            f"{current_number}/{total_count} "
            f"corp_name={candidate.corp_name}, "
            f"stock_code={candidate.stock_code}",
            flush=True,
        )

        started_at = datetime.now().isoformat(timespec="seconds")
        status = "success"
        error_code = ""
        error_message = ""

        try:
            overview = fetch_company_overview(candidate.corp_code)
            api_status = str(overview.get("status", "")).strip()
            if api_status and api_status != "000":
                status = "failed"
                error_code = api_status
                error_message = str(overview.get("message", "")).strip()
                print(
                    "[failed] "
                    f"corp_code={candidate.corp_code}, "
                    f"stock_code={candidate.stock_code}, "
                    f"corp_name={candidate.corp_name}, "
                    f"error_code={error_code}",
                    flush=True,
                )
            else:
                collected_at = datetime.now().isoformat(timespec="seconds")
                master_rows.append(build_master_row(candidate, overview, collected_at))
        except Exception as exc:
            status = "failed"
            error_message = sanitize_error_message(str(exc))
            print(
                "[failed] "
                f"corp_code={candidate.corp_code}, "
                f"stock_code={candidate.stock_code}, "
                f"corp_name={candidate.corp_name}, "
                "error_code=exception",
                flush=True,
            )

        if status == "success":
            success_count += 1
        else:
            failed_count += 1

        finished_at = datetime.now().isoformat(timespec="seconds")
        log_rows.append({
            "corp_code": candidate.corp_code,
            "stock_code": candidate.stock_code,
            "corp_name": candidate.corp_name,
            "status": status,
            "error_code": error_code,
            "error_message": error_message,
            "started_at": started_at,
            "finished_at": finished_at,
        })

        if current_number % progress_interval == 0 or current_number == total_count:
            print(
                "[progress] "
                f"{current_number}/{total_count} processed, "
                f"success={success_count}, failed={failed_count}",
                flush=True,
            )

        if index != len(candidates) - 1 and sleep_interval > 0:
            time.sleep(sleep_interval)

    write_csv(LISTED_COMPANIES_MASTER_PATH, COMPANY_MASTER_HEADERS, master_rows)
    write_csv(COMPANY_MASTER_LOG_PATH, COMPANY_MASTER_LOG_HEADERS, log_rows)
    written_paths = write_batch_companies(
        master_rows,
        batch_size=batch_size,
        force_refresh=force_refresh,
    )
    write_company_batch_summary(
        master_rows=master_rows,
        log_rows=log_rows,
        written_paths=written_paths,
        limit=limit,
        batch_size=batch_size,
    )

    market_counts = count_by_value(master_rows, "market")
    batch_counts = {
        path.parent.name: len(
            split_rows_by_market(master_rows, batch_size).get(path.parent.name, [])
        )
        for path in written_paths
    }

    print("[done] company master preparation finished", flush=True)
    print("[done] market counts", flush=True)
    for market, count in sorted(market_counts.items()):
        print(f"  - {market}: {count}", flush=True)

    print("[done] batch companies files", flush=True)
    for path in written_paths:
        batch_id = path.parent.name
        print(
            f"  - {path.relative_to(PROJECT_ROOT)} rows={batch_counts.get(batch_id, 0)}",
            flush=True,
        )

    return master_rows, log_rows, written_paths


def parse_args() -> argparse.Namespace:
    """명령행 옵션을 파싱합니다."""
    parser = argparse.ArgumentParser(
        description="Prepare listed company master and batch companies.csv from OpenDART company.json."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="테스트용 company.json 호출 제한 수입니다. 생략하거나 0이면 전체 후보를 처리합니다.",
    )
    parser.add_argument(
        "--no-limit",
        action="store_true",
        help="명시적으로 전체 후보를 처리합니다. --limit 0과 같습니다.",
    )
    parser.add_argument("--batch-size", type=int, default=500, help="batch 하나에 배정할 회사 수입니다.")
    parser.add_argument("--sleep-interval", type=float, default=1.0, help="company.json 호출 간 대기 시간입니다.")
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="company master와 모든 batch companies.csv를 재생성합니다.",
    )
    parser.add_argument(
        "--force-refresh-corp-code",
        action="store_true",
        help="corpCode.xml ZIP 캐시를 무시하고 새로 받습니다.",
    )
    return parser.parse_args()


def main() -> int:
    """company master와 batch companies.csv를 생성합니다."""
    args = parse_args()
    limit = None if args.no_limit or args.limit == 0 else args.limit
    master_rows, log_rows, written_paths = prepare_company_master(
        limit=limit,
        batch_size=args.batch_size,
        sleep_interval=args.sleep_interval,
        force_refresh=args.force_refresh,
        force_refresh_corp_code=args.force_refresh_corp_code,
    )

    print(f"master rows: {len(master_rows)}", flush=True)
    print(f"log rows: {len(log_rows)}", flush=True)
    print(f"batch companies files: {len(written_paths)}", flush=True)
    for path in written_paths:
        print(f"  - {path.relative_to(PROJECT_ROOT)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
