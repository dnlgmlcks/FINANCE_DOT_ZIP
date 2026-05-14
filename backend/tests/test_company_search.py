import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.db.queries import search_companies


def test_company_search():
    result = search_companies("삼")

    print(result)

    assert isinstance(result, list)
