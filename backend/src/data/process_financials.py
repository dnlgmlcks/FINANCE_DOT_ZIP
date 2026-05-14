"""
Raw JSON을 가공하여 보고서용 CSV/JSON을 생성하는 스크립트
"""

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND_ROOT))

from src.services.financial_processor import process_financial_data


def main():
    parser = argparse.ArgumentParser(
        description="OpenDART Raw JSON을 가공하여 CSV/JSON으로 저장합니다."
    )
    parser.add_argument(
        "--input",
        default="data/raw/samsung_electronics_2023_2019.json",
        help="가공할 원본 JSON 파일 경로"
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed",
        help="가공 결과를 저장할 디렉토리"
    )

    args = parser.parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)

    if not input_path.exists():
        print(f"입력 파일을 찾을 수 없습니다: {input_path}")
        return 1

    result = process_financial_data(input_path, output_dir)

    print("가공 완료")
    print(f"account inventory: {result['inventory_path']}")
    print(f"account availability: {result['availability_path']}")
    print(f"standard financials CSV: {result['standard_csv_path']}")
    print(f"standard financials JSON: {result['standard_json_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
