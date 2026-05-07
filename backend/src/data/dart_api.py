"""
OpenDART API 호출 및 데이터 처리
"""

import json
import re
import time
import zipfile
from pathlib import Path
from typing import Optional, Dict, Any
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

from core.config import DART_API_BASE, DART_API_KEY, DATA_RAW_PATH, DATA_INTERIM_PATH

class DartAPIClient:
    """OpenDART API 클라이언트"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = DART_API_BASE
        self.session = requests.Session()
        self.corp_code_cache = None
    
    def download_zip_api(
        self,
        endpoint: str,
        output_filename: str,
        params: Optional[Dict[str, Any]] = None,
        force_refresh: bool = False
    ) -> Optional[Path]:
        """
        ZIP 응답 API 호출 및 바이너리 저장
        """
        cache_path = DATA_RAW_PATH / output_filename
        if cache_path.exists() and not force_refresh:
            print(f"캐시된 ZIP 사용: {cache_path}")
            return cache_path

        try:
            print(f"{endpoint} ZIP 다운로드 중...")
            url = f"{self.base_url}/{endpoint}"
            request_params = {"crtfc_key": self.api_key}
            if params:
                request_params.update(params)

            response = self.session.get(url, params=request_params, timeout=20)
            response.raise_for_status()
            
            content = response.content
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "wb") as f:
                f.write(content)

            if not content.startswith(b"PK\x03\x04"):
                print(f"경고: {endpoint} 응답이 ZIP 형식이 아닐 수 있습니다. 첫 바이트: {content[:4]!r}")

            print(f"ZIP 저장: {cache_path}")
            return cache_path
        except Exception as e:
            print(f"{endpoint} 다운로드 실패: {e}")
            return None

    def get_corp_code_zip(self, force_refresh: bool = False) -> Optional[Path]:
        """
        corpCode.xml API를 ZIP으로 다운로드
        """
        return self.download_zip_api(
            endpoint="corpCode.xml",
            output_filename="corp_code.zip",
            force_refresh=force_refresh
        )

    def download_document_zip(
        self,
        rcept_no: str,
        output_filename: Optional[str] = None,
        force_refresh: bool = False
    ) -> Optional[Path]:
        """
        document.xml API를 ZIP으로 다운로드하는 기본 구조
        """
        filename = output_filename or f"document_{rcept_no}.zip"
        return self.download_zip_api(
            endpoint="document.xml",
            output_filename=filename,
            params={"rcept_no": rcept_no},
            force_refresh=force_refresh
        )

    def extract_zip_file(self, zip_path: Path, extract_dir: Path, target_filename: Optional[str] = None) -> Optional[Path]:
        """
        ZIP 파일 해제 및 내부 XML 파일 경로 반환
        """
        if not zip_path.exists():
            print(f"ZIP 파일이 존재하지 않습니다: {zip_path}")
            return None

        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                names = zf.namelist()
                if target_filename:
                    if target_filename not in names:
                        candidates = [name for name in names if name.lower().endswith(target_filename.lower())]
                        if not candidates:
                            print(f"ZIP 내부에 {target_filename} 파일이 없습니다. 내부 파일 목록: {names}")
                            return None
                        target_filename = candidates[0]
                    zf.extract(target_filename, extract_dir)
                    extracted_path = extract_dir / target_filename
                else:
                    zf.extractall(extract_dir)
                    extracted_path = extract_dir / names[0]

            print(f"ZIP 압축 해제 완료: {extracted_path}")
            return extracted_path
        except zipfile.BadZipFile as e:
            print(f"ZIP 압축 해제 실패: {e}")
            return None

    def parse_corp_code_xml(self, xml_path: Path) -> Dict[str, Dict[str, str]]:
        """
        CORPCODE.xml 파싱하여 stock_code -> 회사 정보 매핑 생성
        """
        mapping: Dict[str, Dict[str, str]] = {}

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except Exception as e:
            print(f"CORPCODE.xml 파싱 실패: {e}")
            return mapping

        items = root.findall('.//list')
        if not items:
            items = root.findall('.//item')

        for item in items:
            stock_code = item.findtext('stock_code')
            corp_code = item.findtext('corp_code')
            corp_name = item.findtext('corp_name')
            corp_eng_name = item.findtext('corp_eng_name')
            modify_date = item.findtext('modify_date')

            if stock_code:
                mapping[stock_code.strip()] = {
                    'corp_code': corp_code.strip() if corp_code else '',
                    'corp_name': corp_name.strip() if corp_name else '',
                    'corp_eng_name': corp_eng_name.strip() if corp_eng_name else '',
                    'modify_date': modify_date.strip() if modify_date else ''
                }

        print(f"stock_code 매핑 완료: {len(mapping)}개 회사")
        return mapping
    
    def get_corp_code_by_stock_code(self, stock_code: str, force_refresh: bool = False) -> Optional[str]:
        """
        stock_code로 corp_code 조회
        """
        if force_refresh:
            self.corp_code_cache = None

        if self.corp_code_cache is None:
            zip_path = self.get_corp_code_zip(force_refresh=force_refresh)
            if not zip_path:
                return None

            xml_path = self.extract_zip_file(zip_path, DATA_INTERIM_PATH, target_filename="CORPCODE.xml")
            if not xml_path:
                return None

            self.corp_code_cache = self.parse_corp_code_xml(xml_path)

        corp_info = self.corp_code_cache.get(stock_code)
        if corp_info:
            print(f"조회: {stock_code} -> {corp_info['corp_code']} ({corp_info['corp_name']})")
            return corp_info['corp_code']
        else:
            print(f"stock_code를 찾을 수 없음: {stock_code}")
            return None
    
    def get_fnltt_singl_acnt(
        self,
        corp_code: str,
        bsns_year: int,
        reprt_code: str = "11011"
    ) -> Optional[Dict[str, Any]]:
        """
        단일회사 주요계정 조회 (fnlttSinglAcnt.json)
        
        Args:
            corp_code: 기업 고유번호 (예: 00126380)
            bsns_year: 사업연도 (예: 2023)
            reprt_code: 보고서 코드 (11011: 사업보고서, 11012: 반기보고서 등)
            
        Returns:
            API 응답 (딕셔너리)
        """
        try:
            print(f"주요계정 조회: corp_code={corp_code}, year={bsns_year}, reprt_code={reprt_code}")
            url = f"{self.base_url}/fnlttSinglAcnt.json"
            params = {
                "crtfc_key": self.api_key,
                "corp_code": corp_code,
                "bsns_year": bsns_year,
                "reprt_code": reprt_code
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") == "000":
                print(f"조회 성공: {len(data.get('list', []))}개 계정 반환")
                return data
            else:
                error_msg = data.get("message", "알 수 없는 오류")
                print(f"API 오류: {error_msg}")
                return None
        
        except Exception as e:
            print(f"API 호출 실패: {e}")
            return None

    def fetch_single_company_all_accounts(
        self,
        corp_code: str,
        bsns_year: int,
        reprt_code: str = "11011",
        fs_div: str = "CFS"
    ) -> Optional[Dict[str, Any]]:
        """
        단일회사 전체 재무제표 API(fnlttSinglAcntAll.json)를 호출합니다.

        기존 주요계정 API(fnlttSinglAcnt.json)는 대표 계정만 반환하므로,
        재고자산, 매출채권, 차입금, 현금흐름 등 추가 분석 계정 후보를
        찾기 위해 전체 재무제표 API를 별도 함수로 분리했습니다.

        Args:
            corp_code: DART 고유 회사 코드입니다.
            bsns_year: 사업연도입니다.
            reprt_code: 보고서 코드입니다. 11011은 사업보고서입니다.
            fs_div: 재무제표 구분입니다. CFS는 연결재무제표입니다.

        Returns:
            OpenDART API 응답 JSON입니다. 정상 응답이 아니면 None을 반환합니다.
        """
        try:
            print(
                "전체 재무제표 조회: "
                f"corp_code={corp_code}, year={bsns_year}, "
                f"reprt_code={reprt_code}, fs_div={fs_div}"
            )
            url = f"{self.base_url}/fnlttSinglAcntAll.json"
            params = {
                "crtfc_key": self.api_key,
                "corp_code": corp_code,
                "bsns_year": bsns_year,
                "reprt_code": reprt_code,
                "fs_div": fs_div
            }

            response = self.session.get(url, params=params, timeout=20)
            response.raise_for_status()

            data = response.json()

            if data.get("status") == "000":
                print(f"전체 재무제표 조회 성공: {len(data.get('list', []))}개 계정 수신")
                return data

            error_msg = data.get("message", "알 수 없는 오류")
            print(f"전체 재무제표 API 오류: {error_msg}")
            return None

        except Exception as e:
            print(f"전체 재무제표 API 호출 실패: {e}")
            return None
    
    def save_response_to_file(self, data: Dict[str, Any], filename: str) -> Path:
        """
        API 응답을 JSON 파일로 저장
        
        Args:
            data: API 응답 데이터
            filename: 저장 파일명 (확장자 제외)
            
        Returns:
            저장된 파일 경로
        """
        output_path = DATA_RAW_PATH / f"{filename}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"결과 저장: {output_path}")
        return output_path
