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


def search_companies(keyword: str):
    conn = get_connection()

    try:
        with conn.cursor() as cursor:
            search_word = f"{keyword}%"

            cursor.execute(
                """
                SELECT DISTINCT
                    c.stock_code,
                    c.corp_code,
                    c.company_name,
                    a.alias_name
                FROM companies c
                LEFT JOIN company_aliases a
                    ON c.stock_code = a.stock_code
                WHERE c.company_name LIKE %s
                   OR a.alias_name LIKE %s
                ORDER BY c.company_name ASC
                LIMIT 10
                """,
                (search_word, search_word)
            )

            return cursor.fetchall()

    finally:
        conn.close()