# test_warning_trigger.py

"""
AI 파트의 Warning Trigger 모듈이 정상적으로 동작하는지 확인하기 위한 테스트 파일입니다.

테스트 목적:
1. sample_report_data.py에서 Mock 재무 데이터를 불러옵니다.
2. warning_trigger.py의 run_warning_trigger() 함수를 실행합니다.
3. 정상 케이스와 위험 케이스에서 alert_level과 signals가 의도대로 생성되는지 확인합니다.

실행 방법:
    cd backend
    python -m tests.test_warning_trigger

주의:
    이 파일은 backend 폴더를 기준으로 실행하는 것을 전제로 합니다.
    따라서 import 경로는 `src.ai...` 형식을 사용합니다.
"""

from src.ai.sample_report_data import get_sample_report_data
from src.ai.warning_trigger import run_warning_trigger


def print_warning_result(case: str) -> None:
    """
    지정한 테스트 케이스에 대해 Warning Trigger 결과를 출력합니다.

    Args:
        case: "normal" 또는 "warning"
    """

    report_data = get_sample_report_data(case=case)

    warning_result = run_warning_trigger(report_data)

    print(f"\n===== {case.upper()} CASE =====")
    print("Alert Level:", warning_result["alert_level"])
    print("Signal Count:", len(warning_result["signals"]))

    for idx, signal in enumerate(warning_result["signals"], start=1):
        print(f"\n[{idx}] {signal['signal']}")
        print("type:", signal["type"])
        print("severity:", signal["severity"])
        print("code:", signal["code"])
        print("description:", signal["description"])
        print("source:", signal["source"])


if __name__ == "__main__":
    print_warning_result("normal")
    print_warning_result("warning")