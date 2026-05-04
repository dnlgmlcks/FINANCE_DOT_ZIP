"""
재무제표 수집 파이프라인 메인 엔트리포인트
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import time

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    DART_API_KEY, TARGET_STOCK_CODE, TARGET_COMPANY_NAME, 
    TARGET_REPORT_CODE, TARGET_YEARS, ensure_data_dirs, validate_config
)
from dart_api import DartAPIClient

def main(args):
    """
    메인 파이프라인 실행
    """
    print("=" * 60)
    print("재무제표 수집 파이프라인 시작")
    print("=" * 60)
    
    # 설정 검증
    try:
        validate_config()
    except ValueError as e:
        print(f"오류: {e}")
        return False
    
    # 데이터 디렉토리 생성
    ensure_data_dirs()
    
    # DartAPIClient 초기화
    client = DartAPIClient(DART_API_KEY)
    
    # Step 1: corpCode.zip 다운로드 및 매핑
    print("\n[Step 1] corpCode.zip 다운로드 및 매핑")
    print("-" * 60)
    
    corp_code = client.get_corp_code_by_stock_code(TARGET_STOCK_CODE, force_refresh=args.refresh_corp_code)
    if not corp_code:
        print(f"기업 코드를 찾을 수 없음: {TARGET_STOCK_CODE}")
        return False
    
    print(f"기업명: {TARGET_COMPANY_NAME}")
    print(f"stock_code: {TARGET_STOCK_CODE}")
    print(f"corp_code: {corp_code}")
    
    # Step 3: 최근 5개년 주요계정 조회
    print("\n[Step 3] 주요계정 조회")
    print("-" * 60)
    
    all_results = {
        "meta": {
            "stock_code": TARGET_STOCK_CODE,
            "corp_code": corp_code,
            "company_name": TARGET_COMPANY_NAME,
            "report_code": TARGET_REPORT_CODE,
            "report_type": "사업보고서",
            "collected_at": datetime.now().isoformat(),
            "years": TARGET_YEARS
        },
        "data": {}
    }
    
    for year in TARGET_YEARS:
        print(f"\n조회 중: {year}년도")
        
        response = client.get_fnltt_singl_acnt(
            corp_code=corp_code,
            bsns_year=year,
            reprt_code=TARGET_REPORT_CODE
        )
        
        if response and response.get("status") == "000":
            all_results["data"][str(year)] = response.get("list", [])
            print(f"  -> {len(response.get('list', []))}개 계정 수집")
        else:
            print(f"  -> 조회 실패")
        
        # API 호출 간 대기 (서버 부하 방지)
        if year != TARGET_YEARS[-1]:
            time.sleep(1)
    
    # Step 4: 결과 저장
    print("\n[Step 4] 결과 저장")
    print("-" * 60)
    
    filename = f"samsung_electronics_{TARGET_YEARS[0]}_{TARGET_YEARS[-1]}"
    client.save_response_to_file(all_results, filename)
    
    # 요약 출력
    print("\n[실행 완료]")
    print(f"수집 기간: {TARGET_YEARS[0]}년 ~ {TARGET_YEARS[-1]}년")
    print(f"수집된 연도: {list(all_results['data'].keys())}")
    total_accounts = sum(len(accounts) for accounts in all_results['data'].values())
    print(f"총 계정 수: {total_accounts}개")
    
    print("\n" + "=" * 60)
    print("✓ 파이프라인 완료")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="OpenDART API를 이용한 재무제표 수집 파이프라인"
    )
    parser.add_argument(
        "--refresh-corp-code",
        action="store_true",
        help="corp_code.zip 재다운로드 (캐시 무시)"
    )
    
    args = parser.parse_args()
    
    success = main(args)
    sys.exit(0 if success else 1)
