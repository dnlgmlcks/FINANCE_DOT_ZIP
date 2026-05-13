"""
industry_analysis_rules.py

업종별 재무 해석 가이드를 관리하는 모듈입니다.

역할:
1. 백엔드 API의 industry_info.industry_group 값을 기준으로 업종별 분석 규칙을 선택합니다.
2. report_writer_chain.py에 전달할 industry_analysis_instruction 문자열을 반환합니다.
3. LLM이 업종별 특성을 고려해 최종 리포트를 작성하도록 돕습니다.

주의:
- 이 모듈은 새로운 재무 수치를 계산하지 않습니다.
- 입력 데이터에 없는 지표를 LLM이 임의로 추론하지 않도록 제한 문구를 함께 반환합니다.
- 최종 리포트 작성 시 참고용 instruction으로만 사용합니다.
"""


from typing import Any, Dict


# ---------------------------------------------------------------------
# 1. 공통 안전 가이드
# ---------------------------------------------------------------------

COMMON_INDUSTRY_ANALYSIS_GUARDRAIL = """
공통 제한 규칙:
- 아래 업종별 분석 가이드는 재무 해석 우선순위를 정하기 위한 참고 기준입니다.
- 입력 데이터에 없는 지표는 임의로 추정하지 마세요.
- 특정 지표가 제공되지 않은 경우 "추가 확인이 필요하다"고 작성하세요.
- 뉴스 또는 공시 근거가 없는 내용을 원인으로 단정하지 마세요.
- 투자 추천, 매수, 매도, 보유, 목표주가 판단은 작성하지 마세요.
- 재무 변화와 외부 요인의 관계는 "가능한 배경", "관련 요인", "추가 검토 필요" 수준으로 표현하세요.
"""


# ---------------------------------------------------------------------
# 2. 업종별 분석 규칙
# ---------------------------------------------------------------------

INDUSTRY_ANALYSIS_RULES = {
    "tech_equipment": {
        "industry_group_name": "기술 및 장치 산업",
        "instruction": """
기술 및 장치 산업 분석 가이드:
- 이 업종은 기술 투자, 설비 투자, 연구개발, 제품 사이클, 수요 변동에 따라 수익성이 크게 흔들릴 수 있습니다.
- Capa 확대, 설비 투자 확대, 생산능력 증가 신호가 감지될 경우 영업활동현금흐름과 함께 해석하세요.
- 영업활동현금흐름이 음수이거나 크게 악화된 상태에서 투자가 늘어난다면 자금 부담 또는 현금 소진 리스크로 해석할 수 있습니다.
- 영업활동현금흐름이 양호한 상태에서 투자가 늘어난다면 시장 선점, 상용화 확대, 장기 성장 투자 가능성으로 해석할 수 있습니다.
- 영업이익률, 영업이익, 순이익이 급감한 경우 단순 비용 증가뿐 아니라 업황 둔화, 수요 감소, 재고 부담, 가격 하락 가능성을 함께 검토하세요.
- 단, Capa 확대나 투자 관련 데이터가 입력에 없으면 해당 내용을 추정하지 말고 추가 확인이 필요하다고 작성하세요.
""",
    },
    "asset_service": {
        "industry_group_name": "장치형 서비스업",
        "instruction": """
장치형 서비스업 분석 가이드:
- 항공, 운송, 물류, 숙박 등 고정비 비중이 큰 업종은 자산 가동률과 회전율이 수익성에 큰 영향을 줍니다.
- 자산 가동률 또는 회전율 상승이 매출 증가율보다 가파르면 고정비 부담이 완화되며 영업 레버리지 효과가 나타날 수 있습니다.
- 매출이 증가해도 가동률, 회전율, 영업이익률이 함께 개선되지 않으면 수익성 개선으로 단정하지 마세요.
- 고정비 부담이 큰 업종에서는 매출 증가보다 영업이익률 개선 여부를 함께 검토하세요.
- 단, 가동률 또는 회전율 데이터가 입력에 없으면 해당 내용을 추정하지 말고 추가 확인이 필요하다고 작성하세요.
""",
    },
    "retail_service": {
        "industry_group_name": "유통 및 서비스업",
        "instruction": """
유통 및 서비스업 분석 가이드:
- 유통업은 현금 회전 속도, 매출채권회전율, 재고자산회전율, 영업이익률의 조합을 함께 해석해야 합니다.
- 이익률이 낮더라도 매출채권회전율 또는 재고자산회전율이 개선되면 시장 점유율 확대 또는 회전율 중심 전략으로 해석할 수 있습니다.
- 매출채권회전율과 영업이익률이 동시에 악화되면 가격 경쟁력 약화, 수요 둔화, 시장 지배력 저하 가능성을 검토하세요.
- 매출 증가만으로 긍정적으로 판단하지 말고, 회전율과 이익률이 함께 개선되는지 확인하세요.
- 단, 회전율 관련 데이터가 입력에 없으면 해당 내용을 추정하지 말고 추가 확인이 필요하다고 작성하세요.
""",
    },
    "construction_order": {
        "industry_group_name": "수주 및 건설업",
        "instruction": """
수주 및 건설업 분석 가이드:
- 건설, 조선, 플랜트 등 수주형 산업에서는 장부상 매출과 실제 현금 유입을 구분해서 해석해야 합니다.
- 매출이 크게 증가하더라도 매출채권 증가율이 더 높다면 미회수 위험 또는 운전자본 부담 가능성을 검토하세요.
- 매출 증가율보다 영업활동현금흐름 증가율이 더 높다면 과거 미수금 회수 또는 재무 구조 개선 가능성을 검토할 수 있습니다.
- 수주형 산업에서는 영업이익보다 현금흐름, 매출채권, 부채 부담을 함께 보는 것이 중요합니다.
- 단, 매출채권 증가율 또는 영업활동현금흐름 데이터가 입력에 없으면 해당 내용을 추정하지 말고 추가 확인이 필요하다고 작성하세요.
""",
    },
}


# ---------------------------------------------------------------------
# 3. 기본 분석 규칙
# ---------------------------------------------------------------------

DEFAULT_INDUSTRY_ANALYSIS_RULE = {
    "industry_group_name": "일반 산업",
    "instruction": """
일반 산업 분석 가이드:
- 업종별 특수 규칙이 제공되지 않은 경우, 매출 성장성, 수익성, 안정성, 유동성, 현금흐름을 균형 있게 해석하세요.
- 매출, 영업이익, 순이익의 방향이 서로 다를 경우 비용 구조나 일회성 요인 가능성을 함께 검토하세요.
- 부채비율, 유동비율, 차입금의존도, 영업활동현금흐름을 함께 보며 재무 안정성을 판단하세요.
- 단, 입력 데이터와 근거 자료에 없는 요인은 임의로 추정하지 마세요.
""",
}


# ---------------------------------------------------------------------
# 4. 대표 함수
# ---------------------------------------------------------------------

def get_industry_group(industry_info: Dict[str, Any]) -> str:
    """
    industry_info에서 industry_group 값을 안전하게 추출합니다.
    """

    if not industry_info:
        return ""

    return str(industry_info.get("industry_group", "") or "")


def get_industry_group_name(industry_info: Dict[str, Any]) -> str:
    """
    industry_info에서 industry_group_name 값을 안전하게 추출합니다.
    """

    if not industry_info:
        return ""

    return str(industry_info.get("industry_group_name", "") or "")


def get_industry_analysis_rule(industry_group: str) -> Dict[str, str]:
    """
    industry_group에 해당하는 업종별 분석 규칙 dict를 반환합니다.

    Args:
        industry_group: 예: tech_equipment

    Returns:
        {
            "industry_group_name": "...",
            "instruction": "..."
        }
    """

    if not industry_group:
        return DEFAULT_INDUSTRY_ANALYSIS_RULE

    return INDUSTRY_ANALYSIS_RULES.get(
        industry_group,
        DEFAULT_INDUSTRY_ANALYSIS_RULE,
    )


def build_industry_analysis_instruction(industry_info: Dict[str, Any]) -> str:
    """
    report_writer_chain.py에 주입할 최종 업종별 분석 instruction을 생성합니다.

    Args:
        industry_info: 백엔드 API에서 전달된 industry_info

    Returns:
        업종별 분석 가이드 문자열
    """

    industry_group = get_industry_group(industry_info)
    industry_group_name = get_industry_group_name(industry_info)

    rule = get_industry_analysis_rule(industry_group)

    resolved_group_name = (
        industry_group_name
        or rule.get("industry_group_name")
        or "일반 산업"
    )

    instruction = rule.get("instruction", DEFAULT_INDUSTRY_ANALYSIS_RULE["instruction"])

    return f"""
분석 대상 업종:
- industry_group: {industry_group or "unknown"}
- industry_group_name: {resolved_group_name}

{instruction}

{COMMON_INDUSTRY_ANALYSIS_GUARDRAIL}
""".strip()


# ---------------------------------------------------------------------
# 5. 단독 실행 테스트
# ---------------------------------------------------------------------

if __name__ == "__main__":
    sample_industry_info = {
        "industry_group": "tech_equipment",
        "industry_group_name": "기술 및 장치 산업",
    }

    print("[Industry Analysis Instruction Test]")
    print(build_industry_analysis_instruction(sample_industry_info))
