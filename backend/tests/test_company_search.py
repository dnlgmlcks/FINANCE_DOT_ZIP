import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"

sys.path.insert(0, str(SRC_DIR))

from db.queries import search_companies


def test_company_search():
    result = search_companies("삼")

    print(result)

    assert isinstance(result, list)