"""
팀 단위 재무제표 수집을 위한 batch export 템플릿 생성 스크립트입니다.

이 스크립트는 실제 OpenDART API를 호출하지 않습니다.
각 팀원이 맡은 batch 폴더에 CSV 결과를 채울 수 있도록,
헤더만 들어 있는 CSV 템플릿과 batch_summary.md 파일만 생성합니다.
이미 존재하는 파일은 덮어쓰지 않고 건너뜁니다.
"""

from __future__ import annotations

import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]
EXPORT_ROOT = PROJECT_ROOT / "data" / "export"


# batch_id는 파일명과 코드 식별자에서 안전하게 사용할 수 있도록 ASCII만 사용합니다.
BATCHES = {
    "kospi_001": {"market": "KOSPI", "range": "1~500"},
    "kospi_002": {"market": "KOSPI", "range": "501~end"},
    "kosdaq_001": {"market": "KOSDAQ", "range": "1~500"},
    "kosdaq_002": {"market": "KOSDAQ", "range": "501~1000"},
    "kosdaq_003": {"market": "KOSDAQ", "range": "1001~1500"},
    "kosdaq_004": {"market": "KOSDAQ", "range": "1501~end"},
    "konex_001": {"market": "KONEX", "range": "all"},
}


# 모든 batch 폴더가 동일한 CSV 헤더를 갖도록 한 곳에서 정의합니다.
CSV_HEADERS = {
    "companies.csv": [
        "batch_id",
        "corp_code",
        "stock_code",
        "corp_name",
        "stock_name",
        "corp_cls",
        "market",
        "induty_code",
        "acc_mt",
        "collected_at",
    ],
    "reports.csv": [
        "batch_id",
        "rcept_no",
        "corp_code",
        "stock_code",
        "corp_name",
        "bsns_year",
        "reprt_code",
        "fs_div",
        "report_name",
        "source_api",
        "collected_at",
    ],
    "financial_accounts_raw.csv": [
        "batch_id",
        "corp_code",
        "stock_code",
        "corp_name",
        "bsns_year",
        "reprt_code",
        "fs_div",
        "fs_nm",
        "sj_div",
        "sj_nm",
        "account_id",
        "account_nm",
        "account_detail",
        "thstrm_nm",
        "thstrm_amount",
        "frmtrm_nm",
        "frmtrm_amount",
        "bfefrmtrm_nm",
        "bfefrmtrm_amount",
        "ord",
        "currency",
        "rcept_no",
        "source_api",
        "collected_at",
    ],
    "financial_accounts_standard.csv": [
        "batch_id",
        "corp_code",
        "stock_code",
        "corp_name",
        "bsns_year",
        "reprt_code",
        "fs_div",
        "sj_div",
        "standard_account",
        "account_nm",
        "account_id",
        "amount",
        "currency",
        "mapping_status",
        "is_proxy",
        "proxy_reason",
        "rcept_no",
        "collected_at",
    ],
    "account_availability.csv": [
        "batch_id",
        "corp_code",
        "stock_code",
        "corp_name",
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
    "signal_account_availability.csv": [
        "batch_id",
        "corp_code",
        "stock_code",
        "corp_name",
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
    "collection_log.csv": [
        "batch_id",
        "market",
        "stock_code",
        "corp_code",
        "corp_name",
        "bsns_year",
        "reprt_code",
        "fs_div",
        "status",
        "error_code",
        "error_message",
        "retry_count",
        "started_at",
        "finished_at",
    ],
}


def build_batch_summary(batch_id: str, market: str, batch_range: str) -> str:
    """팀원이 수집 결과와 특이사항을 기록할 batch 요약 문서를 만듭니다."""
    return f"""# Batch Summary: {batch_id}

## batch_id
- {batch_id}

## 담당자
-

## 시장
- {market}

## 배치 범위
- {batch_range}

## 실행 명령
-

## 수집 기준
- 사업연도:
- 보고서 코드:
- 재무제표 구분:
- 사용 API:

## 완료 여부
- [ ] 완료

## 성공 건수
- 0

## 실패 건수
- 0

## no_data 건수
- 0

## 특이사항
-

## PR 체크리스트
- [ ] 내 batch 폴더만 수정했습니다.
- [ ] CSV 헤더를 변경하지 않았습니다.
- [ ] collection_log.csv에 실패/스킵 사유를 기록했습니다.
- [ ] raw JSON 업로드 여부를 팀 규칙에 맞게 확인했습니다.
- [ ] API 키 또는 .env 값을 커밋하지 않았습니다.
"""


def write_csv_template(path: Path, headers: list[str]) -> bool:
    """헤더만 포함한 CSV 템플릿을 생성하고, 기존 파일은 보존합니다."""
    if path.exists():
        return False

    with path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
    return True


def write_text_template(path: Path, content: str) -> bool:
    """기존 문서를 덮어쓰지 않고 새 템플릿 문서만 생성합니다."""
    if path.exists():
        return False

    path.write_text(content, encoding="utf-8")
    return True


def create_templates() -> tuple[list[Path], list[Path]]:
    """모든 batch 폴더와 템플릿 파일을 생성합니다."""
    created: list[Path] = []
    skipped: list[Path] = []

    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)

    for batch_id, metadata in BATCHES.items():
        batch_dir = EXPORT_ROOT / batch_id
        batch_dir.mkdir(parents=True, exist_ok=True)

        for filename, headers in CSV_HEADERS.items():
            target_path = batch_dir / filename
            if write_csv_template(target_path, headers):
                created.append(target_path)
            else:
                skipped.append(target_path)

        summary_path = batch_dir / "batch_summary.md"
        summary_content = build_batch_summary(
            batch_id=batch_id,
            market=metadata["market"],
            batch_range=metadata["range"],
        )
        if write_text_template(summary_path, summary_content):
            created.append(summary_path)
        else:
            skipped.append(summary_path)

    return created, skipped


def main() -> int:
    """명령행에서 실행할 때 생성/건너뜀 결과를 간단히 출력합니다."""
    created, skipped = create_templates()

    print(f"created: {len(created)}")
    for path in created:
        print(f"  + {path.relative_to(PROJECT_ROOT)}")

    print(f"skipped: {len(skipped)}")
    for path in skipped:
        print(f"  - {path.relative_to(PROJECT_ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
