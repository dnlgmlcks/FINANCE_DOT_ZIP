from db.connection import get_connection


def fetch_financials_by_stock_code(stock_code: str):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    stock_code,
                    year,
                    standard_account,
                    thstrm_amount
                FROM financials
                WHERE stock_code = %s
                ORDER BY year ASC
                """,
                (stock_code,)
            )
            return cursor.fetchall()

    finally:
        conn.close()


def fetch_company_info_by_stock_code(stock_code: str):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    stock_code,
                    corp_code,
                    company_name,
                    induty_code
                FROM companies
                WHERE stock_code = %s
                LIMIT 1
                """,
                (stock_code,)
            )
            return cursor.fetchone()

    finally:
        conn.close()