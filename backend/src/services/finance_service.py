from db.queries import fetch_financials_by_stock_code


def safe_divide(numerator, denominator):
    if numerator is None or denominator in (None, 0):
        return None

    return round((numerator / denominator) * 100, 2)


def calculate_yoy(current, previous):
    if current is None or previous in (None, 0):
        return None

    return round(((current - previous) / previous) * 100, 2)


def group_by_year(rows):
    result = {}

    for row in rows:
        year = row["year"]
        account = row["standard_account"]
        amount = row["thstrm_amount"]

        if year not in result:
            result[year] = {}

        result[year][account] = amount

    return result


def calculate_finance_summary(stock_code: str):
    rows = fetch_financials_by_stock_code(stock_code)
    yearly_data = group_by_year(rows)

    summary = []

    previous_item = None

    for year in sorted(yearly_data.keys()):
        data = yearly_data[year]

        revenue = data.get("매출액")
        operating_income = data.get("영업이익")
        net_income = data.get("당기순이익")
        total_assets = data.get("자산총계")
        total_liabilities = data.get("부채총계")
        total_equity = data.get("자본총계")

        operating_margin = safe_divide(operating_income, revenue)
        debt_ratio = safe_divide(total_liabilities, total_equity)
        roe = safe_divide(net_income, total_equity)
        roa = safe_divide(net_income, total_assets)

        item = {
            "year": year,
            "revenue": revenue,
            "operating_income": operating_income,
            "net_income": net_income,
            "operating_margin": operating_margin,
            "debt_ratio": debt_ratio,
            "roe": roe,
            "roa": roa,
            "revenue_yoy": None,
            "operating_income_yoy": None,
            "debt_ratio_change": None,
        }

        if previous_item:
            item["revenue_yoy"] = calculate_yoy(
                revenue,
                previous_item.get("revenue")
            )

            item["operating_income_yoy"] = calculate_yoy(
                operating_income,
                previous_item.get("operating_income")
            )

            if debt_ratio is not None and previous_item.get("debt_ratio") is not None:
                item["debt_ratio_change"] = round(
                    debt_ratio - previous_item["debt_ratio"],
                    2
                )

        summary.append(item)
        previous_item = item

    return summary