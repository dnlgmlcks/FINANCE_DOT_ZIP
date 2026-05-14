import sys
from pathlib import Path

# backend/src 경로 추가
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.services.report_service import build_report_response


def test_build_report_response():
    result = build_report_response("005930")

    print(result)

    assert result["status"] == "success"
    assert "data" in result
    assert "finance_summary" in result["data"]
