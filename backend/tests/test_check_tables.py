from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from db.connection import get_connection


def check_tables():

    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute("SHOW TABLES")

            tables = cursor.fetchall()

            print("현재 테이블 목록:")
            print(tables)

    finally:
        conn.close()


if __name__ == "__main__":
    check_tables()