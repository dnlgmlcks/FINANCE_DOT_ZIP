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
