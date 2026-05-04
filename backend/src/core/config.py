"""
환경 변수 및 설정 관리
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent.parent

# .env 파일 로드
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    # .env가 없으면 .env.example을 기반으로 안내
    print(f"경고: {env_file}이 없습니다.")
    print(f"     .env.example을 복사하여 .env를 만들고 API 키를 입력해주세요.")

# OpenDART API 설정
DART_API_KEY = os.getenv("DART_API_KEY", "")

# 대상 기업 설정
TARGET_STOCK_CODE = os.getenv("TARGET_STOCK_CODE", "005930")
TARGET_COMPANY_NAME = os.getenv("TARGET_COMPANY_NAME", "삼성전자")

# 보고서 설정
TARGET_REPORT_CODE = os.getenv("TARGET_REPORT_CODE", "11011")  # 사업보고서
TARGET_REPORT_TYPE = os.getenv("TARGET_REPORT_TYPE", "사업보고서")
TARGET_FS_DIV = os.getenv("TARGET_FS_DIV", "CFS")  # CFS: 연결재무제표, OFS: 별도재무제표

# 조회 기간
target_years_str = os.getenv("TARGET_YEARS", "2023,2022,2021,2020,2019")
TARGET_YEARS = [int(y.strip()) for y in target_years_str.split(",")]

# 데이터 저장 경로
DATA_RAW_PATH = Path(os.getenv("DATA_RAW_PATH", "data/raw"))
DATA_INTERIM_PATH = Path(os.getenv("DATA_INTERIM_PATH", "data/interim"))
DATA_PROCESSED_PATH = Path(os.getenv("DATA_PROCESSED_PATH", "data/processed"))

# OpenDART API 기본 URL
DART_API_BASE = "https://opendart.fss.or.kr/api"

def ensure_data_dirs():
    """데이터 저장 디렉토리 생성"""
    DATA_RAW_PATH.mkdir(parents=True, exist_ok=True)
    DATA_INTERIM_PATH.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

def validate_config():
    """설정 검증"""
    if not DART_API_KEY:
        raise ValueError("DART_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
    return True
