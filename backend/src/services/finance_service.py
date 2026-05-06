from db.queries import fetch_financials_by_stock_code


def safe_divide(numerator, denominator, percent=True):
    if numerator is None or denominator in (None, 0):
        return None

    result = numerator / denominator

    if percent:
        result *= 100

    return round(result, 2)


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

        current_assets = data.get("유동자산")
        current_liabilities = data.get("유동부채")
        inventory = data.get("재고자산")
        receivables = data.get("매출채권")
        short_term_borrowings = data.get("단기차입금")
        long_term_borrowings = data.get("장기차입금")
        bonds = data.get("사채")
        interest_expense = data.get("이자비용")
        operating_cash_flow = data.get("영업활동현금흐름")

        operating_margin = safe_divide(operating_income, revenue)
        debt_ratio = safe_divide(total_liabilities, total_equity)
        roe = safe_divide(net_income, total_equity)
        roa = safe_divide(net_income, total_assets)

        current_ratio = safe_divide(current_assets, current_liabilities)
        quick_ratio = None
        if current_assets is not None and inventory is not None:
            quick_ratio = safe_divide(current_assets - inventory, current_liabilities)

        borrowings_dependency = None
        if (
            short_term_borrowings is not None
            or long_term_borrowings is not None
            or bonds is not None
        ):
            total_borrowings = (
                (short_term_borrowings or 0)
                + (long_term_borrowings or 0)
                + (bonds or 0)
            )
            borrowings_dependency = safe_divide(total_borrowings, total_assets)

        interest_coverage_ratio = safe_divide(
            operating_income,
            interest_expense,
            percent=False
        )

        receivables_turnover = safe_divide(
            revenue,
            receivables,
            percent=False
        )

        inventory_turnover = safe_divide(
            revenue,
            inventory,
            percent=False
        )

        item = {
            "year": year,
            "revenue": revenue,
            "operating_income": operating_income,
            "net_income": net_income,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "total_equity": total_equity,

            "operating_margin": operating_margin,
            "debt_ratio": debt_ratio,
            "roe": roe,
            "roa": roa,

            "current_ratio": current_ratio,
            "quick_ratio": quick_ratio,
            "borrowings_dependency": borrowings_dependency,
            "interest_coverage_ratio": interest_coverage_ratio,
            "receivables_turnover": receivables_turnover,
            "inventory_turnover": inventory_turnover,

            "operating_cash_flow": operating_cash_flow,

            "revenue_yoy": None,
            "operating_income_yoy": None,
            "debt_ratio_change": None,
            "receivables_turnover_yoy": None,
            "inventory_turnover_yoy": None,
            "borrowings_dependency_change": None,
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

            item["receivables_turnover_yoy"] = calculate_yoy(
                receivables_turnover,
                previous_item.get("receivables_turnover")
            )

            item["inventory_turnover_yoy"] = calculate_yoy(
                inventory_turnover,
                previous_item.get("inventory_turnover")
            )

            if (
                borrowings_dependency is not None
                and previous_item.get("borrowings_dependency") is not None
            ):
                item["borrowings_dependency_change"] = round(
                    borrowings_dependency - previous_item["borrowings_dependency"],
                    2
                )

        summary.append(item)
        previous_item = item

    return summary