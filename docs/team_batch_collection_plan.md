# Team Batch Collection Plan

## 목적

전체 상장사 재무제표 수집을 여러 팀원이 batch 단위로 나누어 진행하기 위한 작업 규칙입니다. 각 팀원은 자신에게 할당된 `data/export/<batch_id>/` 폴더 안에서만 CSV 결과와 요약 문서를 채웁니다.

## Batch 할당 기준

| batch_id | 시장 | 범위 |
| --- | --- | --- |
| kospi_001 | KOSPI | 1~500 |
| kospi_002 | KOSPI | 501~끝 |
| kosdaq_001 | KOSDAQ | 1~500 |
| kosdaq_002 | KOSDAQ | 501~1000 |
| kosdaq_003 | KOSDAQ | 1001~1500 |
| kosdaq_004 | KOSDAQ | 1501~끝 |
| konex_001 | KONEX | 전체 |

팀원별 담당 batch_id는 PR 또는 이슈에서 명시합니다. 한 사람이 여러 batch를 맡을 수 있지만, 한 PR에서는 가능한 한 하나의 batch만 변경하는 방식을 권장합니다.

## 회사 목록 준비 방식

상장 후보 기업 목록은 OpenDART `corpCode.xml`에서 `stock_code`가 있는 회사를 추출해 만듭니다. `corpCode.xml`은 `corp_code`, `stock_code`, `corp_name` 매핑을 얻기 위한 기준 자료이며, 이 파일만으로는 KOSPI, KOSDAQ, KONEX 시장 구분을 정확히 확정하지 않습니다.

시장 구분과 기업개황 보강은 OpenDART `company.json` 응답을 사용합니다. `company.json`의 `corp_cls` 값은 OpenDART 기준 시장 구분으로 사용합니다.

| corp_cls | market | 설명 |
| --- | --- | --- |
| Y | KOSPI | 유가증권 |
| K | KOSDAQ | 코스닥 |
| N | KONEX | 코넥스 |
| E | OTHER | 기타 |

`company.json`은 `corp_cls` 외에도 `induty_code`, `acc_mt`, `stock_name` 같은 기업개황 정보를 보강하는 데 사용합니다. KRX 별도 상장사 목록은 필수 입력이 아니며, 필요할 때 OpenDART 기준 결과를 교차검증하는 보조 자료로만 사용할 수 있습니다.

회사 master와 batch별 `companies.csv`는 아래 스크립트로 준비합니다. `company.json` 호출은 API 요청 수를 사용하므로 처음에는 반드시 작은 `--limit` 값으로 테스트합니다. `--limit`을 생략하거나 `--limit 0` 또는 `--no-limit`을 사용하면 전체 후보를 처리합니다.

```bash
# 테스트 실행
python backend/src/data/batch/prepare_company_batches.py --limit 20 --batch-size 500

# 전체 실행
python backend/src/data/batch/prepare_company_batches.py --batch-size 500 --force-refresh --sleep-interval 1.0

# 전체 실행을 명시적으로 표현
python backend/src/data/batch/prepare_company_batches.py --batch-size 500 --force-refresh --sleep-interval 1.0 --no-limit
```

## 작업 규칙

- 각 팀원은 자기 batch 폴더만 수정합니다.
- 공통 CSV 하나에 append하지 않습니다.
- 모든 batch 폴더는 동일한 CSV 헤더를 유지합니다.
- CSV 헤더를 변경해야 할 때는 먼저 팀 합의를 거친 뒤 전체 batch 템플릿을 함께 갱신합니다.
- `collection_log.csv`에는 성공뿐 아니라 실패, no_data, skipped, rate_limited 상태도 남깁니다.
- PR을 올리기 전에 자기 batch 폴더 외 파일이 변경되었는지 확인합니다.
- API 키, `.env` 값, 개인 인증 정보는 어떤 파일에도 기록하지 않습니다.

## Raw JSON과 CSV의 역할

Raw JSON은 OpenDART 응답 원문을 보존하기 위한 자료입니다. API 응답 구조를 다시 확인하거나 매핑 오류를 추적할 때 사용합니다.

CSV는 DB import와 검증을 위한 정규화된 자료입니다. 팀원이 수집한 결과를 나중에 병합하고, 헤더 검증을 거친 뒤 DB 저장 로직으로 넘기기 위한 기준 형식입니다.

Raw JSON까지 GitHub에 올릴지는 팀 결정 사항입니다. 파일 크기가 커지거나 원본 보존 파일이 많아지면 raw JSON은 Drive, 사내 공유폴더, 오브젝트 스토리지 등 별도 저장소로 분리할 수 있습니다. 이 경우 CSV에는 원본을 추적할 수 있는 접수번호, 회사코드, 사업연도, 보고서 코드, source_api 값을 빠짐없이 남깁니다.

## 추천 작업 흐름

1. 담당 batch_id를 이슈 또는 팀 문서에서 확인합니다.
2. `data/export/<batch_id>/batch_summary.md`에 담당자와 수집 기준을 기록합니다.
3. 수집 결과를 자기 batch 폴더 안의 CSV 파일에만 채웁니다.
4. 수집 실패나 데이터 없음은 `collection_log.csv`에 상태와 사유를 기록합니다.
5. `python backend/src/data/batch/import_batch_exports.py`로 CSV 파일 존재 여부와 헤더를 검증합니다.
6. PR에서 자기 batch 폴더만 변경되었는지 확인합니다.

## PR 체크리스트

- 내 batch 폴더만 변경했습니다.
- 공통 CSV에 append하지 않았습니다.
- CSV 헤더를 변경하지 않았습니다.
- 실패, no_data, skipped, rate_limited 상태를 `collection_log.csv`에 기록했습니다.
- raw JSON 업로드 여부를 팀 규칙에 맞게 처리했습니다.
- API 키 또는 `.env` 값을 포함하지 않았습니다.
