import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from fastapi import APIRouter

from services.report_service import build_report_response
from db.queries import search_companies

router = APIRouter()


@router.get("/report/comprehensive/{stock_code}")
def get_comprehensive_report(stock_code: str):
    return build_report_response(stock_code)


@router.get("/company/search")
def search_company(keyword: str):
    return {
        "status": "success",
        "data": search_companies(keyword)
    }