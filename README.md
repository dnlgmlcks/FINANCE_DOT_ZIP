# FINANCE_DOT_ZIP

OpenDART API를 이용한 기업 재무제표 수집 및 분석 파이프라인

## 프로젝트 개요

이 프로젝트는 다음을 목표로 합니다:

1. **재무제표 수집**: OpenDART API를 통해 특정 기업(삼성전자)의 최근 5개년 재무제표 데이터 자동 수집
2. **데이터 정규화**: 재무상태표(BS), 손익계산서(IS) 계정 추출 및 매핑
3. **재무비율 계산**: 영업이익률, 순이익률, 부채비율, 유동비율, YoY 등 계산
4. **데이터베이스 저장**: 정규화된 데이터 SQL DB 저장 (향후)
5. **텍스트 분석**: 사업보고서 원문에서 "II. 사업의 내용" 섹션 추출 및 벡터 DB 적재 준비 (향후)

## MVP 범위

현재 1차 MVP는 다음까지 구현되었습니다:

- ✓ OpenDART API 연결 테스트
- ✓ 삼성전자 2019-2023년 사업보고서 주요계정 수집
- ✓ 수집 데이터를 JSON으로 저장
- ⏳ DB 저장 (다음 단계)
- ⏳ 보고서 원문 파싱 (다음 단계)
- ⏳ 벡터 DB 적재 (다음 단계)

## 설치 및 실행

### 1. 준비

#### 1-1. 가상환경 생성

```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# 또는 macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 1-2. 의존 패키지 설치

```bash
pip install -r requirements.txt
```

#### 1-3. .env 파일 생성

`.env.example`을 복사하여 `.env` 파일을 만들고, **DART_API_KEY**에 발급받은 API 키를 입력하세요:

```bash
# .env.example 복사 (Windows)
copy .env.example .env

# 또는 (macOS/Linux)
cp .env.example .env
```

`.env` 파일의 내용:

```
DART_API_KEY=your_api_key_here
TARGET_STOCK_CODE=005930
TARGET_COMPANY_NAME=삼성전자
TARGET_REPORT_CODE=11011
TARGET_FS_DIV=CFS
TARGET_YEARS=2023,2022,2021,2020,2019
DATA_RAW_PATH=data/raw
DATA_PROCESSED_PATH=data/processed
```

### 2. OpenDART API 키 발급

1. https://opendart.fss.or.kr/에 접속
2. 회원가입 및 로그인
3. "API 신청" 섹션에서 API 키 발급받기
4. `.env` 파일의 `DART_API_KEY`에 입력

### 3. 파이프라인 실행

```bash
# 기본 실행 (캐시된 corp_code.zip 사용)
python src/main.py

# corp_code.zip 재다운로드 (캐시 무시)
python src/main.py --refresh-corp-code
```

## 프로젝트 구조

```
FINANCE_DOT_ZIP/
├─ src/
│  ├─ __init__.py
│  ├─ config.py          # 환경 변수 및 설정 관리
│  ├─ dart_api.py        # OpenDART API 클라이언트
│  └─ main.py            # 메인 파이프라인
├─ data/
│  ├─ raw/               # API 응답 원본 데이터 (JSON)
│  └─ processed/         # 처리된 데이터 (향후)
├─ tests/                # 단위 테스트 (향후)
├─ .gitignore
├─ .env.example          # 환경 변수 템플릿
├─ requirements.txt      # 의존 패키지
└─ README.md
```

## 실행 결과

파이프라인 실행 후 다음 파일이 생성됩니다:

```
data/raw/
├─ corp_code.zip                          # 기업 코드 ZIP 응답 캐시
└─ samsung_electronics_2023_2019.json    # 수집 데이터

data/interim/
└─ CORPCODE.xml                          # ZIP 압축 해제 후 추출 XML
```

### 출력 예시

```
============================================================
재무제표 수집 파이프라인 시작
============================================================

[Step 1] corp_code.zip 다운로드 및 매핑
------------------------------------------------------------
corpCode.xml ZIP 다운로드 중...
corp_code.zip 저장: data/raw\corp_code.zip

[Step 2] 삼성전자 기업 코드 조회
------------------------------------------------------------
조회: 005930 -> 00126380 (삼성전자)
기업명: 삼성전자
stock_code: 005930
corp_code: 00126380

[Step 3] 주요계정 조회
------------------------------------------------------------

조회 중: 2023년도
주요계정 조회: corp_code=00126380, year=2023, reprt_code=11011
조회 성공: 16개 계정 반환
  -> 16개 계정 수집

조회 중: 2022년도
...

[Step 4] 결과 저장
------------------------------------------------------------
결과 저장: data/raw\samsung_electronics_2023_2019.json

[실행 완료]
수집 기간: 2023년 ~ 2019년
수집된 연도: ['2023', '2022', '2021', '2020', '2019']
총 계정 수: 80개

============================================================
✓ 파이프라인 완료
============================================================
```

## 주요 계정 항목

현재 수집되는 주요 계정:

### 재무상태표 (Balance Sheet, BS)
- 유동자산, 비유동자산, 자산총계
- 유동부채, 비유동부채, 부채총계
- 자본총계

### 손익계산서 (Income Statement, IS)
- 매출액
- 영업이익
- 법인세차감전순이익
- 당기순이익

## 다음 단계 (향후 구현)

1. **재무비율 계산**
   - 영업이익률, 순이익률, 부채비율, 유동비율
   - Year-over-Year (YoY) 성장률

2. **SQL 데이터베이스 저장**
   - 정규화된 테이블 구조 설계
   - SQLite 초기 구현 후 PostgreSQL 확장

3. **사업보고서 원문 파싱**
   - "II. 사업의 내용" 섹션 추출
   - 텍스트 청킹 및 메타데이터 관리

4. **벡터 DB 적재**
   - Chroma/Milvus 등을 이용한 벡터 DB 저장
   - 임베딩 모델 적용

5. **다중 기업 지원**
   - 동적 기업 코드 입력
   - 배치 처리 능력

## API 명세

### corpCode.xml
- **URL**: `{DART_API_BASE}/corpCode.xml`
- **용도**: stock_code와 corp_code 매핑
- **캐시**: 첫 다운로드 후 `data/raw/corp_code.zip`에 저장, 내부 `CORPCODE.xml` 추출

### fnlttSinglAcnt.json
- **URL**: `{DART_API_BASE}/fnlttSinglAcnt.json`
- **파라미터**:
  - `corp_code`: 기업 고유번호
  - `bsns_year`: 사업연도 (예: 2023)
  - `reprt_code`: 보고서 코드 (11011 = 사업보고서)

## 문제 해결

### "DART_API_KEY가 설정되지 않았습니다" 오류

1. `.env` 파일이 존재하는지 확인
2. `DART_API_KEY=` 다음에 실제 API 키가 입력되었는지 확인
3. 공백 문자가 없는지 확인

### "corpCode.xml 다운로드 실패" 오류

1. 인터넷 연결 확인
2. API 키가 유효한지 확인
3. OpenDART 서버 상태 확인 (https://opendart.fss.or.kr)

### 권한 오류 (Windows)

Windows에서 `venv\Scripts\Activate.ps1` 실행이 안 되는 경우:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
