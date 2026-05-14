"""
companies_for_db.csv를 MySQL companies 테이블에 적재/upsert하는 스크립트.

실행:
    cd backend
    python -m src.db.seed_companies
"""


import csv
from pathlib import Path

from src.db.connection import get_connection


CSV_PATH = Path(__file__).resolve().parents[3] / "data" / "company_master" / "companies_for_db.csv"


def clean_value(value):
    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    return value


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {CSV_PATH.resolve()}")

    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO companies (
        stock_code,
        corp_code,
        company_name,
        induty_code
    )
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        corp_code = VALUES(corp_code),
        company_name = VALUES(company_name),
        induty_code = VALUES(induty_code)
    """

    count = 0

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            stock_code = clean_value(row.get("stock_code"))
            corp_code = clean_value(row.get("corp_code"))
            company_name = clean_value(row.get("company_name"))
            induty_code = clean_value(row.get("induty_code"))

            if not stock_code or not company_name:
                continue

            cursor.execute(
                sql,
                (stock_code, corp_code, company_name, induty_code),
            )

            count += 1

    conn.commit()
    cursor.close()
    conn.close()

    print(f"companies 테이블 적재 완료: {count}건")


if __name__ == "__main__":
    main()