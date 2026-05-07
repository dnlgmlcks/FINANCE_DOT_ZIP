import pymysql
from dotenv import load_dotenv
from pathlib import Path
import os

# .env 로드
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

try:
    conn = pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        charset="utf8mb4",
        ssl={"ssl": {}}
    )

    print("DB 연결 성공!")

    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()

        print("\n현재 테이블:")
        for table in tables:
            print(table)

    conn.close()

except Exception as e:
    print("DB 연결 실패")
    print(e)