# services/warning_trigger.py

"""
warning_trigger.py

재무 요약 데이터(finance_summary)를 기반으로 위험 신호를 탐지하는 모듈입니다.
AI 파트에서 사용하는 Warning Trigger 모듈입니다.

주요 역할:
1. Backend/Data 파트에서 warning_signals가 넘어오면 그대로 표준화해서 사용.
2. warning_signals가 아직 없으면 finance_summary를 기반으로 fallback warning signal을 생성.
3. 전년 대비 증감률 계산
4. 부채 비율, 영업 이익률, 당기 순이익, 유동 비율 기반 Warning Signal 탐지    # TODO: 일단 위험 신호 4개만 탐지. 추후 추가 예정(노션의 DART 데이터베이스 문서 참고)
5. Signal 개수와 심각도에 따라 Alert Level 산정

주의:
- 최종 서비스에서 재무 비율 및 전년 대비 증감률 계산은 Data 파트가 담당.
- 이 파일의 계산 로직은 DB/API 완성 전 AI 파트 독립 테스트를 위한 fallback 용도.

입력:
    finance_summary: 연도별 재무 요약 데이터 리스트

출력:
    {
        "alert_level": "LOW" | "MEDIUM" | "HIGH",
        "signals": [...]
    }
"""

from typing import Any, Dict, List, Optional


def calculate_yoy(current_value: Optional[float], previous_value: Optional[float]) -> Optional[float]:
    """
    fallback용 전년 대비 증감률을 계산 함수.
    Data 파트에서 yoy 값을 제공하면 사용하지 않아도 됨.

    예:
        current_value = 80
        previous_value = 100
        return -20
    """

    if current_value is None or previous_value is None:
        return None

    if previous_value == 0:
        return None

    return round(((current_value - previous_value) / abs(previous_value)) * 100, 2)


def sort_finance_summary(finance_summary: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    finance_summary를 최신 연도순으로 정렬하는 함수.
    """

    return sorted(finance_summary, key=lambda item: item.get('year', 0), reverse=True)


def make_signal(signal_type: str, severity: str, code: str, signal: str, description: str, metric: str,
                value: Optional[float], threshold: Optional[float], year: Optional[int], source: str) -> Dict[str, Any]:
    """
    Warning Signal 하나를 표준 형식으로 생성합니다.
    """

    return {
        "type": signal_type,
        "severity": severity,
        "code": code,
        "signal": signal,
        "description": description,
        "metric": metric,
        "value": value,
        "threshold": threshold,
        "year": year,
        "source": source,
    }


def normalize_backend_warning_signals(warning_signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Backend/Data 파트에서 전달받은 warning_signals를 AI 파트 표준 형식으로 맞춥니다.

    Backend에서 이미 signal을 넘겨주는 경우,
    AI 파트는 별도 계산 없이 이 데이터를 우선 사용합니다.
    """

    normalized_signals = []

    for signal in warning_signals:
        normalized_signals.append(
            make_signal(
                signal_type=signal.get("type", "neutral"),
                severity=signal.get("severity", "MEDIUM"),
                code=signal.get("code", "BACKEND_SIGNAL"),
                signal=signal.get("signal", "재무 변동 신호"),
                description=signal.get("description", ""),
                metric=signal.get("metric", ""),
                value=signal.get("value"),
                threshold=signal.get("threshold"),
                year=signal.get("year"),
                source="backend",
            )
        )

    return normalized_signals


def detect_fallback_warning_signals(finance_summary: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    finance_summary를 기반으로 fallback warning signal을 탐지하는 함수

    # TODO: 추후 Warning Signal 추가 및 변경 예정.
    MVP 기준:
    1. 부채 과다: debt_ratio > 200
    2. 수익성 악화: net_income < 0
    3. 단기 유동성 위험: current_ratio < 100
    4. 영업 이익률 급락: operating_margin_yoy < -20
    5. 매출 급감: revenue_yoy <= -30
    6. 영업이익 급감: operating_income_yoy <= -20
    """

    if not finance_summary:
        return []

    sorted_summary = sort_finance_summary(finance_summary)

    current = sorted_summary[0]
    previous = sorted_summary[1] if len(sorted_summary) >= 2 else None

    current_year = current.get('year', None)
    signals = []

    # 1. 부채 과다
    debt_ratio = current.get('debt_ratio', None)

    if debt_ratio is not None and debt_ratio > 200:
        signals.append(
            make_signal(
                signal_type="negative",
                severity="HIGH",
                code="HIGH_DEBT_RATIO",
                signal="부채 과다",
                description=f"부채비율이 {debt_ratio}%로 기준치 200%를 초과했습니다.",
                metric="debt_ratio",
                value=debt_ratio,
                threshold=200,
                year=current_year,
                source="fallback",
            )
        )

    # 2. 수익성 악화
    net_income = current.get('net_income', None)

    if net_income is not None and net_income < 0:
        signals.append(
            make_signal(
                signal_type="negative",
                severity="HIGH",
                code="NET_LOSS",
                signal="수익성 악화",
                description="당기순이익이 음수로 확인되어 적자 상태입니다.",
                metric="net_income",
                value=net_income,
                threshold=0,
                year=current_year,
                source="fallback",
            )
        )

    # 3. 단기 유동성 위험
    current_ratio = current.get('current_ratio',
                                None)
    if current_ratio is not None and current_ratio < 100:
        signals.append(
            make_signal(
                signal_type="negative",
                severity="HIGH",
                code="LOW_CURRENT_RATIO",
                signal="단기 유동성 위험",
                description=f"유동비율이 {current_ratio}%로 기준치 100% 미만입니다.",
                metric="current_ratio",
                value=current_ratio,
                threshold=100,
                year=current_year,
                source="fallback",
            )
        )

    # 전년도 데이터가 없으면 YoY 기반 신호는 평가하지 않음.
    if previous is None:
        return signals

    # 4. 영업 이익률 급락
    operating_margin_yoy = current.get('operating_margin_yoy', None)

    # 넘어온 데이터에 전년도 대비 증감률이 없다면 함수 실행해서 계산
    if operating_margin_yoy is None:
        operating_margin_yoy = calculate_yoy(current.get('operating_margin', None), previous.get('operating_margin', None))

    if operating_margin_yoy is not None and operating_margin_yoy < -20:
        signals.append(
            make_signal(
                signal_type="negative",
                severity="HIGH",
                code="OPERATING_MARGIN_DROP",
                signal="실적 급락",
                description=f"영업이익률이 전년 대비 {abs(operating_margin_yoy)}% 하락했습니다.",
                metric="operating_margin_yoy",
                value=operating_margin_yoy,
                threshold=-20,
                year=current_year,
                source="fallback",
            )
        )

    # 5. 매출 급감
    revenue_yoy = current.get('revenue_yoy', None)

    if revenue_yoy is None:
        revenue_yoy = calculate_yoy(current.get('revenue', None), previous.get('revenue', None))

    if revenue_yoy is not None and revenue_yoy <= -30:
        signals.append(
            make_signal(
                signal_type="negative",
                severity="HIGH",
                code="REVENUE_DROP",
                signal="매출 급감",
                description=f"매출액이 전년 대비 {abs(revenue_yoy)}% 감소했습니다.",
                metric="revenue_yoy",
                value=revenue_yoy,
                threshold=-30,
                year=current_year,
                source="fallback",
            )
        )

    # 6. 영업 이익 급감
    operating_income_yoy = current.get('operating_income_yoy', None)

    if operating_income_yoy is None:
        operating_income_yoy = calculate_yoy(current.get('operating_income', None), previous.get('operating_income', None))

    if operating_income_yoy is not None and operating_income_yoy <= -20:
        signals.append(
            make_signal(
                signal_type="negative",
                severity="HIGH",
                code="OPERATING_INCOME_DROP",
                signal="영업이익 급감",
                description=f"영업이익이 전년 대비 {abs(operating_income_yoy)}% 감소했습니다.",
                metric="operating_income_yoy",
                value=operating_income_yoy,
                threshold=-20,
                year=current_year,
                source="fallback",
            )
        )

    return signals


def get_alert_level(signals: List[Dict[str, Any]]) -> str:
    """
    Warning Signal 목록을 바탕으로 최종 Alert Level을 산정합니다.

    기준:
    - HIGH: negative signal이 3개 이상이거나 HIGH severity signal이 2개 이상
    - MEDIUM: negative signal이 1개 이상
    - LOW: 위험 신호 없음
    """

    negative_count = sum(
        1 for signal in signals
        if signal.get("type") == "negative"
    )

    high_severity_count = sum(
        1 for signal in signals
        if signal.get("severity") == "HIGH"
    )

    if negative_count >= 3 or high_severity_count >= 2:
        return "HIGH"

    if negative_count >= 1:
        return "MEDIUM"

    return "LOW"

def run_warning_trigger(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Warning Trigger 전체 실행 함수입니다.

    우선순위:
    1. report_data 안에 warning_signals가 있으면 Backend/Data 파트 결과를 사용
    2. 없으면 finance_summary 기반 fallback signal 생성
    """

    backend_warning_signals = report_data.get("warning_signals")

    if backend_warning_signals:
        signals = normalize_backend_warning_signals(backend_warning_signals)
    else:
        finance_summary = report_data.get("finance_summary", [])
        signals = detect_fallback_warning_signals(finance_summary)

    alert_level = get_alert_level(signals)

    return {
        "alert_level": alert_level,
        "signals": signals,
    }