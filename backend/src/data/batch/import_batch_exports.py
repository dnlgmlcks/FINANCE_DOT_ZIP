"""
batch export CSV 검증 스크립트의 기본 틀입니다.

이 스크립트는 data/export 하위 batch 폴더를 읽어서
필수 CSV 파일 존재 여부와 헤더 일치 여부만 검증합니다.
아직 DB insert는 구현하지 않았으며, 실제 DB에 연결하지도 않습니다.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

if __package__:
    from .create_batch_templates import BATCHES, CSV_HEADERS, EXPORT_ROOT, PROJECT_ROOT
else:
    from create_batch_templates import BATCHES, CSV_HEADERS, EXPORT_ROOT, PROJECT_ROOT


@dataclass
class ValidationIssue:
    """검증 중 발견한 문제를 사람이 읽기 쉬운 형태로 보관합니다."""

    batch_id: str
    file_name: str
    message: str


def read_csv_header(path: Path) -> list[str]:
    """CSV 첫 줄만 읽어서 헤더를 반환합니다."""
    with path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.reader(csv_file)
        try:
            return next(reader)
        except StopIteration:
            return []


def validate_batch(batch_id: str) -> list[ValidationIssue]:
    """하나의 batch 폴더가 필수 CSV와 정확한 헤더를 갖는지 확인합니다."""
    issues: list[ValidationIssue] = []
    batch_dir = EXPORT_ROOT / batch_id

    if not batch_dir.exists():
        return [
            ValidationIssue(
                batch_id=batch_id,
                file_name="",
                message="batch folder is missing",
            )
        ]

    for file_name, expected_header in CSV_HEADERS.items():
        csv_path = batch_dir / file_name

        if not csv_path.exists():
            issues.append(
                ValidationIssue(
                    batch_id=batch_id,
                    file_name=file_name,
                    message="required CSV file is missing",
                )
            )
            continue

        actual_header = read_csv_header(csv_path)
        if actual_header != expected_header:
            issues.append(
                ValidationIssue(
                    batch_id=batch_id,
                    file_name=file_name,
                    message=(
                        "CSV header mismatch. "
                        f"expected={expected_header}, actual={actual_header}"
                    ),
                )
            )

    return issues


def validate_all_exports() -> list[ValidationIssue]:
    """정의된 모든 batch 폴더를 순회하며 CSV 템플릿 상태를 확인합니다."""
    issues: list[ValidationIssue] = []

    for batch_id in BATCHES:
        issues.extend(validate_batch(batch_id))

    return issues


def main() -> int:
    """검증 결과를 출력하고, 문제가 있으면 종료 코드를 1로 반환합니다."""
    parser = argparse.ArgumentParser(
        description="Validate batch export CSV files without DB insert."
    )
    parser.add_argument(
        "--export-root",
        default=str(EXPORT_ROOT),
        help="검증 대상 export root 경로입니다. 기본값은 data/export 입니다.",
    )
    args = parser.parse_args()

    # 현재는 프로젝트 표준 경로 검증을 우선으로 둡니다.
    # 인자가 다른 경로로 들어오면 이후 확장 시 EXPORT_ROOT를 주입하도록 개선할 수 있습니다.
    export_root_arg = Path(args.export_root).resolve()
    if export_root_arg != EXPORT_ROOT.resolve():
        print(
            "warning: custom export root is not wired yet; "
            f"using {EXPORT_ROOT.relative_to(PROJECT_ROOT)}"
        )

    issues = validate_all_exports()
    if issues:
        print("batch export validation failed")
        for issue in issues:
            location = issue.batch_id
            if issue.file_name:
                location = f"{location}/{issue.file_name}"
            print(f"- {location}: {issue.message}")
        return 1

    print("batch export validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
