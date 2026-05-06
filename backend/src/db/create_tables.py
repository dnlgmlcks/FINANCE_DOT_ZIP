from pathlib import Path
import sys

# src 폴더 경로 추가
BASE_DIR = Path(__file__).resolve().parents[1]

# 가장 우선순위로 추가
sys.path.insert(0, str(BASE_DIR))

from db.connection import get_connection


def create_tables():
    schema_path = Path(__file__).with_name("schema.sql")

    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    conn = get_connection()

    try:
        with conn.cursor() as cursor:

            for statement in sql.split(";"):
                statement = statement.strip()

                if statement:
                    cursor.execute(statement)

        conn.commit()
        print("테이블 생성 완료")

    finally:
        conn.close()


if __name__ == "__main__":
    create_tables()