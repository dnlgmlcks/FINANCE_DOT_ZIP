def normalize_industry_code(induty_code):
    if induty_code is None:
        return ""

    return str(induty_code).strip()


def classify_industry(induty_code):
    """
    induty_code 기준 업종군 분류.

    반환값:
    - heavy_manufacturing: 중후장대형 제조
    - tech_equipment: 기술 및 장치 산업
    - facility_service: 장치형 서비스업
    - distribution_service: 유통 및 서비스
    - construction_order: 수주 및 건설
    - finance_real_estate: 금융 및 부동산업
    - unknown: 미분류
    """
    code = normalize_industry_code(induty_code)

    if not code:
        return {
            "industry_group": "unknown",
            "industry_group_name": "미분류",
            "is_excluded": False,
            "reason": "induty_code가 없습니다."
        }

    # 금융 및 부동산업
    if code.startswith(("64", "65", "66", "68")):
        return {
            "industry_group": "finance_real_estate",
            "industry_group_name": "금융 및 부동산업",
            "is_excluded": True,
            "reason": "금융/부동산 업종은 일반 제조·서비스 재무 Trigger와 별도 관리합니다."
        }

    # 수주 및 건설
    if code.startswith(("41", "42")):
        return {
            "industry_group": "construction_order",
            "industry_group_name": "수주 및 건설",
            "is_excluded": False,
            "reason": "건설/수주형 업종으로 분류되었습니다."
        }

    # 중후장대형 제조
    if code.startswith(("19", "20", "21", "22", "23", "24", "25", "29", "30", "31")):
        return {
            "industry_group": "heavy_manufacturing",
            "industry_group_name": "중후장대형 제조",
            "is_excluded": False,
            "reason": "제조업 기반 중후장대형 업종으로 분류되었습니다."
        }

    # 기술 및 장치 산업
    if code.startswith(("26", "27", "28", "58", "59", "60", "61", "62", "63")):
        return {
            "industry_group": "tech_equipment",
            "industry_group_name": "기술 및 장치 산업",
            "is_excluded": False,
            "reason": "전자/IT/통신/소프트웨어 중심 업종으로 분류되었습니다."
        }

    # 장치형 서비스업
    if code.startswith(("35", "36", "37", "38", "39", "49", "50", "51", "52", "55")):
        return {
            "industry_group": "facility_service",
            "industry_group_name": "장치형 서비스업",
            "is_excluded": False,
            "reason": "인프라·운송·숙박 등 장치형 서비스 업종으로 분류되었습니다."
        }

    # 유통 및 서비스
    if code.startswith(("45", "46", "47", "56", "70", "71", "72", "73", "74", "75", "85", "86", "90", "91", "94", "95", "96")):
        return {
            "industry_group": "distribution_service",
            "industry_group_name": "유통 및 서비스",
            "is_excluded": False,
            "reason": "유통/소비자 서비스 업종으로 분류되었습니다."
        }

    return {
        "industry_group": "unknown",
        "industry_group_name": "미분류",
        "is_excluded": False,
        "reason": f"정의되지 않은 induty_code입니다: {code}"
    }