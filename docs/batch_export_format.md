# Batch Export Format

## 개요

`data/export/<batch_id>/` 하위 CSV 파일은 팀별 수집 결과를 나중에 병합하고 DB import 후보로 검증하기 위한 표준 형식입니다. 모든 batch 폴더는 동일한 파일명과 동일한 헤더를 사용합니다.

## Status 값

`collection_log.csv`의 `status` 값은 아래 중 하나를 사용합니다.

| status | 의미 |
| --- | --- |
| pending | 아직 수집 전입니다. |
| running | 수집이 진행 중입니다. |
| success | 정상 수집되었습니다. |
| failed | API 오류, 파싱 오류, 저장 오류 등으로 실패했습니다. |
| no_data | API 호출은 가능했지만 해당 조건의 데이터가 없습니다. |
| skipped | 중복, 대상 제외, 팀 규칙 등으로 수집하지 않았습니다. |
| rate_limited | 호출 제한 또는 과도한 요청 방지를 위해 중단했습니다. |

## DB import 대상

| CSV 파일 | 예상 DB 대상 | 설명 |
| --- | --- | --- |
| companies.csv | companies, company_aliases 후보 | 회사 기본 정보와 시장 구분을 저장하기 위한 후보 데이터입니다. |
| reports.csv | 별도 reports 테이블 후보 | 보고서 접수번호, 사업연도, 보고서 코드, 재무제표 구분을 추적합니다. |
| financial_accounts_raw.csv | 원본 계정 저장 테이블 후보 | OpenDART 원본 계정 행을 최대한 보존합니다. |
| financial_accounts_standard.csv | financials 또는 표준 계정 테이블 후보 | DB 분석과 재무비율 계산에 사용할 표준 계정 금액입니다. |
| account_availability.csv | 검증용 또는 품질 점검 테이블 후보 | 표준 계정별 수집 가능 여부를 확인합니다. |
| signal_account_availability.csv | 시그널 계산 준비도 점검 테이블 후보 | Warning/Positive Signal 계산에 필요한 계정이 있는지 확인합니다. |
| collection_log.csv | 수집 로그 테이블 후보 | 수집 상태, 오류, 재시도 횟수를 기록합니다. |

현재 프로젝트의 기존 DB insert 로직은 `backend/src/db/insert_financials.py`가 `financials` 테이블에 표준 계정 데이터를 넣는 구조입니다. 이 문서는 batch export 형식을 정의할 뿐이며, 실제 DB insert 구현은 아직 포함하지 않습니다.

## 회사 master 생성 기준

상장 후보 회사 목록은 OpenDART `corpCode.xml`에서 `stock_code`가 있는 항목을 추출해 만듭니다. `corpCode.xml`은 `corp_code`, `stock_code`, `corp_name` 매핑용 기준 자료입니다.

시장 구분과 기업개황 보강은 OpenDART `company.json` 응답을 사용합니다. `company.json`의 `corp_cls` 값을 아래처럼 `market`으로 매핑합니다.

| corp_cls | market | 설명 |
| --- | --- | --- |
| Y | KOSPI | 유가증권 |
| K | KOSDAQ | 코스닥 |
| N | KONEX | 코넥스 |
| E | OTHER | 기타 |

`listed_companies_master.csv`의 `market` 컬럼과 `data/export/<batch_id>/companies.csv`의 `market` 컬럼은 이 `corp_cls` 기준 매핑값을 사용합니다. KRX 별도 목록은 필수 자료가 아니며, 필요할 때 교차검증용으로만 사용할 수 있습니다.

## financial_accounts_raw.csv

OpenDART API 응답의 원본 계정 행을 보존하는 CSV입니다. 원본 필드명을 최대한 유지하여 나중에 매핑 오류나 누락을 추적할 수 있게 합니다.

| 컬럼 | 설명 |
| --- | --- |
| batch_id | 수집 batch 식별자입니다. |
| corp_code | DART 고유 회사 코드입니다. |
| stock_code | 종목 코드입니다. |
| corp_name | DART 회사명입니다. |
| bsns_year | 사업연도입니다. |
| reprt_code | 보고서 코드입니다. |
| fs_div | 연결/별도 재무제표 구분입니다. |
| fs_nm | 재무제표 이름입니다. |
| sj_div | 재무제표 종류 코드입니다. |
| sj_nm | 재무제표 종류 이름입니다. |
| account_id | 원본 계정 ID입니다. |
| account_nm | 원본 계정명입니다. |
| account_detail | 원본 상세 계정 정보입니다. |
| thstrm_nm | 당기 기간명입니다. |
| thstrm_amount | 당기 금액입니다. |
| frmtrm_nm | 전기 기간명입니다. |
| frmtrm_amount | 전기 금액입니다. |
| bfefrmtrm_nm | 전전기 기간명입니다. |
| bfefrmtrm_amount | 전전기 금액입니다. |
| ord | 원본 표시 순서입니다. |
| currency | 통화 단위입니다. |
| rcept_no | 보고서 접수번호입니다. |
| source_api | 사용한 OpenDART API 이름입니다. |
| collected_at | 수집 시각입니다. |

## financial_accounts_standard.csv

분석과 DB import에 사용할 표준 계정 단위 CSV입니다. 원본 계정명을 프로젝트 표준 계정으로 매핑한 결과를 저장합니다.

| 컬럼 | 설명 |
| --- | --- |
| batch_id | 수집 batch 식별자입니다. |
| corp_code | DART 고유 회사 코드입니다. |
| stock_code | 종목 코드입니다. |
| corp_name | DART 회사명입니다. |
| bsns_year | 사업연도입니다. |
| reprt_code | 보고서 코드입니다. |
| fs_div | 연결/별도 재무제표 구분입니다. |
| sj_div | 재무제표 종류 코드입니다. |
| standard_account | 프로젝트에서 사용하는 표준 계정명입니다. |
| account_nm | 매핑에 사용한 원본 계정명입니다. |
| account_id | 매핑에 사용한 원본 계정 ID입니다. |
| amount | 표준 계정 금액입니다. |
| currency | 통화 단위입니다. |
| mapping_status | exact, alias, proxy, missing 등 매핑 상태입니다. |
| is_proxy | 대체 계정 사용 여부입니다. |
| proxy_reason | 대체 계정을 사용한 이유입니다. |
| rcept_no | 보고서 접수번호입니다. |
| collected_at | 수집 시각입니다. |

`financial_accounts_raw.csv`는 원본 보존용이고, `financial_accounts_standard.csv`는 분석과 DB import 후보입니다. raw에는 OpenDART에서 온 다양한 계정이 들어갈 수 있고, standard에는 재무비율과 시그널 계산에 필요한 표준 계정 중심의 행이 들어갑니다.

## companies.csv

| 컬럼 | 설명 |
| --- | --- |
| batch_id | 수집 batch 식별자입니다. |
| corp_code | DART 고유 회사 코드입니다. |
| stock_code | 종목 코드입니다. |
| corp_name | DART 회사명입니다. |
| stock_name | 상장 종목명입니다. |
| corp_cls | `company.json`의 DART 법인 구분입니다. Y, K, N, E 값을 사용합니다. |
| market | `corp_cls`를 기준으로 매핑한 시장 구분입니다. KOSPI, KOSDAQ, KONEX, OTHER 중 하나입니다. |
| induty_code | 업종 코드입니다. |
| acc_mt | 결산월입니다. |
| collected_at | 수집 시각입니다. |

## reports.csv

| 컬럼 | 설명 |
| --- | --- |
| batch_id | 수집 batch 식별자입니다. |
| rcept_no | 보고서 접수번호입니다. |
| corp_code | DART 고유 회사 코드입니다. |
| stock_code | 종목 코드입니다. |
| corp_name | DART 회사명입니다. |
| bsns_year | 사업연도입니다. |
| reprt_code | 보고서 코드입니다. |
| fs_div | 연결/별도 재무제표 구분입니다. |
| report_name | 보고서 이름입니다. |
| source_api | 사용한 OpenDART API 이름입니다. |
| collected_at | 수집 시각입니다. |

## account_availability.csv

표준 계정이 원본 데이터에서 발견되었는지 확인하는 품질 점검 CSV입니다.

| 컬럼 | 설명 |
| --- | --- |
| batch_id | 수집 batch 식별자입니다. |
| corp_code | DART 고유 회사 코드입니다. |
| stock_code | 종목 코드입니다. |
| corp_name | DART 회사명입니다. |
| standard_account | 확인 대상 표준 계정명입니다. |
| category | 계정 분류입니다. |
| found | 발견 여부입니다. |
| years_found | 발견된 사업연도 목록입니다. |
| sj_divs | 발견된 재무제표 종류 코드 목록입니다. |
| matched_names | 매칭된 원본 계정명 목록입니다. |
| matched_account_ids | 매칭된 원본 계정 ID 목록입니다. |
| status | 가능, 대체 필요, 누락 등 점검 상태입니다. |
| recommended_action | 사람이 확인해야 할 후속 조치입니다. |

## signal_account_availability.csv

Warning/Positive Signal 계산에 필요한 계정이 준비되었는지 확인하는 CSV입니다.

| 컬럼 | 설명 |
| --- | --- |
| batch_id | 수집 batch 식별자입니다. |
| corp_code | DART 고유 회사 코드입니다. |
| stock_code | 종목 코드입니다. |
| corp_name | DART 회사명입니다. |
| signal_name | 계산 대상 시그널 이름입니다. |
| required_account | 시그널 계산에 필요한 계정입니다. |
| found | 발견 여부입니다. |
| matched_account_nm | 매칭된 원본 계정명입니다. |
| matched_account_id | 매칭된 원본 계정 ID입니다. |
| years_found | 발견된 사업연도 목록입니다. |
| sj_divs | 발견된 재무제표 종류 코드 목록입니다. |
| fs_divs | 발견된 재무제표 구분 목록입니다. |
| status | 가능, 대체 필요, 원문 확인 필요 등 준비 상태입니다. |
| recommended_action | 사람이 확인해야 할 후속 조치입니다. |

`account_availability.csv`는 표준 계정 전체의 수집 가능 여부를 보는 파일입니다. `signal_account_availability.csv`는 시그널 계산에 필요한 계정 조합이 준비되었는지 보는 파일입니다.

## collection_log.csv

| 컬럼 | 설명 |
| --- | --- |
| batch_id | 수집 batch 식별자입니다. |
| market | 시장 구분입니다. |
| stock_code | 종목 코드입니다. |
| corp_code | DART 고유 회사 코드입니다. |
| corp_name | DART 회사명입니다. |
| bsns_year | 사업연도입니다. |
| reprt_code | 보고서 코드입니다. |
| fs_div | 연결/별도 재무제표 구분입니다. |
| status | pending, running, success, failed, no_data, skipped, rate_limited 중 하나입니다. |
| error_code | 실패 또는 제한 상태의 오류 코드입니다. |
| error_message | 실패 또는 제한 상태의 오류 설명입니다. |
| retry_count | 재시도 횟수입니다. |
| started_at | 수집 시작 시각입니다. |
| finished_at | 수집 종료 시각입니다. |
