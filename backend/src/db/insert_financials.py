import sys
from pathlib import Path
import csv

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent.parent
BACKEND_ROOT = BASE_DIR.parent

sys.path.insert(0, str(BACKEND_ROOT))

from src.db.connection import get_connection
from src.services.financial_processor import find_standard_account_in_item


EXPORT_DIR = PROJECT_ROOT / "data" / "export"
BATCH_SIZE = 500


def parse_amount(value):
    if value is None:
        return None

    value = str(value).strip()

    if value == "" or value == "-":
        return None

    value = value.replace(",", "")

    try:
        return int(float(value))
    except ValueError:
        return None


def iter_raw_csv_files():
    if not EXPORT_DIR.exists():
        raise FileNotFoundError(f"export 폴더를 찾을 수 없습니다: {EXPORT_DIR}")

    return sorted(EXPORT_DIR.glob("*/financial_accounts_raw.csv"))


def pick_better_amount(old_amount, new_amount):
    """
    같은 stock_code + year + standard_account가 여러 개 있을 때 대표값 선택.
    결측이 아닌 값 우선, 둘 다 있으면 절대값이 큰 금액을 선택.
    """
    if old_amount is None:
        return new_amount

    if new_amount is None:
        return old_amount

    if abs(new_amount) > abs(old_amount):
        return new_amount

    return old_amount


def convert_raw_row_to_item(row):
    """
    financial_accounts_raw.csv의 한 행을
    financial_processor.find_standard_account_in_item()이 이해하는 형태로 변환.
    """
    return {
        "fs_div": row.get("fs_div", ""),
        "fs_nm": row.get("fs_nm", ""),
        "sj_div": row.get("sj_div", ""),
        "sj_nm": row.get("sj_nm", ""),
        "account_id": row.get("account_id", ""),
        "account_nm": row.get("account_nm", ""),
        "account_detail": row.get("account_detail", ""),
    }


def read_rows_from_raw_csv(csv_path):
    """
    raw CSV 1개에서 행을 읽고,
    financial_processor의 표준계정 매핑을 직접 적용한 뒤,
    stock_code + year + standard_account 기준으로 중복 제거.
    """
    deduped = {}
    skipped_no_mapping = 0
    skipped_invalid = 0

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            stock_code = row.get("stock_code")
            year = row.get("bsns_year")
            amount = parse_amount(
                row.get("amount") or row.get("thstrm_amount")
            )

            if not stock_code or not year:
                skipped_invalid += 1
                continue

            try:
                year = int(year)
            except ValueError:
                skipped_invalid += 1
                continue

            item = convert_raw_row_to_item(row)
            standard_account, matched_candidate, matched_field, match_type = find_standard_account_in_item(item)

            if not standard_account:
                skipped_no_mapping += 1
                continue

            key = (stock_code, year, standard_account)

            if key not in deduped:
                deduped[key] = amount
            else:
                deduped[key] = pick_better_amount(
                    deduped[key],
                    amount
                )

    rows = [
        (stock_code, year, standard_account, amount)
        for (stock_code, year, standard_account), amount in deduped.items()
    ]

    return rows, skipped_no_mapping, skipped_invalid


def insert_batch(cursor, batch):
    cursor.executemany(
        """
        INSERT INTO financials (
            stock_code,
            year,
            standard_account,
            thstrm_amount
        )
        VALUES (%s, %s, %s, %s)
        """,
        batch
    )


def insert_financials():
    csv_files = iter_raw_csv_files()

    if not csv_files:
        raise FileNotFoundError(
            f"financial_accounts_raw.csv 파일을 찾을 수 없습니다: {EXPORT_DIR}"
        )

    total_inserted = 0
    total_skipped_no_mapping = 0
    total_skipped_invalid = 0
    total_failed = 0

    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            print("[초기화] 기존 financials 데이터 삭제 중...")
            cursor.execute("DELETE FROM financials")
            conn.commit()
            print("[초기화 완료]")

            for csv_path in csv_files:
                print(f"[읽는 중] {csv_path}")

                rows, skipped_no_mapping, skipped_invalid = read_rows_from_raw_csv(csv_path)

                total_skipped_no_mapping += skipped_no_mapping
                total_skipped_invalid += skipped_invalid

                if not rows:
                    print(f"[건너뜀] 적재할 데이터 없음: {csv_path}")
                    continue

                print(f"  - 표준계정 매핑 후 {len(rows)}건 적재 예정")
                print(f"  - 매핑 제외 {skipped_no_mapping}건 / 유효하지 않은 행 {skipped_invalid}건")

                for i in range(0, len(rows), BATCH_SIZE):
                    batch = rows[i:i + BATCH_SIZE]

                    try:
                        conn.ping(reconnect=True)

                        with conn.cursor() as batch_cursor:
                            insert_batch(batch_cursor, batch)

                        conn.commit()
                        total_inserted += len(batch)

                        print(
                            f"  - {csv_path.parent.name}: "
                            f"{i + len(batch)} / {len(rows)}건 적재"
                        )

                    except Exception as e:
                        conn.rollback()
                        total_failed += len(batch)
                        print(f"[ERROR] 배치 적재 실패: {csv_path}")
                        print(type(e).__name__, str(e))

        print("financials 전체 적재 완료")
        print(f"읽은 RAW CSV 파일 수: {len(csv_files)}")
        print(f"INSERT 건수: {total_inserted}")
        print(f"매핑 제외 건수: {total_skipped_no_mapping}")
        print(f"유효하지 않은 행 수: {total_skipped_invalid}")
        print(f"실패 건수: {total_failed}")

    finally:
        conn.close()


if __name__ == "__main__":
    insert_financials()
