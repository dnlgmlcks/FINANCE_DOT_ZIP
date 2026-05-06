import sys
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from db.connection import get_connection

JSON_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "standard_financials_2019_2023.json"
)

def insert_financials():

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        rows = json.load(f)

    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            for row in rows:

                cursor.execute(
                    """
                    INSERT INTO financials (
                        stock_code,
                        year,
                        standard_account,
                        thstrm_amount
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        row.get("stock_code"),
                        int(row.get("year")),
                        row.get("standard_account"),
                        row.get("thstrm_amount")
                    )
                )

        conn.commit()
        print("데이터 INSERT 완료")

    finally:
        conn.close()

if __name__ == "__main__":
    insert_financials()