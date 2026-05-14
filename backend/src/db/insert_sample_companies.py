import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
BACKEND_ROOT = BASE_DIR.parent
sys.path.insert(0, str(BACKEND_ROOT))

from src.db.connection import get_connection


def insert_sample_companies():
    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                INSERT IGNORE INTO companies (
                    stock_code,
                    corp_code,
                    company_name
                )
                VALUES (%s, %s, %s)
                """,
                ("005930", "00126380", "삼성전자")
            )

            aliases = [
                "삼성전자",
                "삼성",
                "삼전",
                "samsung",
                "Samsung Electronics"
            ]

            for alias in aliases:
                cursor.execute(
                    """
                    INSERT INTO company_aliases (
                        stock_code,
                        alias_name
                    )
                    SELECT %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM company_aliases
                        WHERE stock_code = %s
                          AND alias_name = %s
                    )
                    """,
                    (
                        "005930",
                        alias,
                        "005930",
                        alias
                    )
                )

        conn.commit()

        print("샘플 기업 데이터 INSERT 완료")

    finally:
        conn.close()


if __name__ == "__main__":
    insert_sample_companies()
