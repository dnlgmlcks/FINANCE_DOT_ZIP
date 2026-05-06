import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from db.connection import get_connection


def check_data():

    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                SELECT *
                FROM financials
                LIMIT 10
                """
            )

            rows = cursor.fetchall()

            print("financials 데이터:")
            print(rows)

    finally:
        conn.close()


if __name__ == "__main__":
    check_data()