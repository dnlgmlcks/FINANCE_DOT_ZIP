# 전체 스키마를 포함한 MD 파일 내용 정의
full_schema_md = """# Pinecone Vector DB Schema 명세 (finance-dot-news)

본 문서는 리포트 자동 생성 시스템의 검색 엔진 역할을 하는 Pinecone 벡터 데이터베이스의 데이터 저장 구조와 메타데이터 규격을 정의합니다.

## 1. 인덱스 및 네임스페이스 구성
- **Index Name**: `finance-dot-news`
- **Dimension**: 1536 (OpenAI `text-embedding-3-small` 모델 기준)
- **Metric**: `cosine` (금융 문서 유사도 측정에 최적화)
- **Namespace Strategy**: **종목코드(Stock Code)** 사용 (6자리 숫자)
  - 예: 삼성전자 데이터는 `005930` 네임스페이스에 격리 저장됨.
  - 이점: 특정 기업 검색 시 다른 기업 데이터와의 간섭을 원천 차단하고 검색 속도를 향상시킴.

## 2. 데이터 레코드 구조 (JSON)
각 뉴스 텍스트 조각(Chunk)은 아래와 같은 고유 ID 및 메타데이터와 함께 벡터화되어 저장됩니다.

```json
{
  "id": "{base_id}_{chunk_index}",
  "values": [0.0123, -0.0456, ...], 
  "metadata": {
    "text": "전처리 및 정규화가 완료된 뉴스 텍스트 본문 조각",
    "source": "[https://news.example.com/article/123](https://news.example.com/article/123)",
    "company_name": "삼성전자",
    "stock_code": "005930",
    "date": "2026-05-11"
  }
}
```

## 3. 메타데이터 필드 상세 (Filtering Specification)
팀원들이 `detected_changes` 또는 기간 필터링 로직을 구축할 때 참조할 필드 정의입니다.

| 필드명 (Key) | 타입 | 설명 | 비고 |
| :--- | :--- | :--- | :--- |
| **text** | string | 청킹된 뉴스 본문. 용어 정규화 완료 상태. | Retrieval 결과값 |
| **source** | string | 뉴스 기사의 원본 URL. | 레퍼런스 및 중복 체크용 |
| **company_name** | string | 대상 기업명. | 확인용 |
| **stock_code** | string | **[핵심]** 6자리 표준 종목코드. | **Namespace 매칭 필수값** |
| **date** | string | 발행 일자 (형식: `YYYY-MM-DD`). | **Range Filter 가능** |

## 4. 데이터 무결성 및 중복 방지 로직
- **ID 생성**: `hashlib.md5(url).hexdigest() + "_" + chunk_index`
- **Deduplication**: 동일한 URL을 가진 기사가 재입력될 경우, 동일 ID로 인식하여 Pinecone 내에서 자동으로 **Overwrite(Upsert)** 처리됩니다.
- **최신성 유지**: 뉴스 내용이 수정되어 다시 수집되더라도 최신 기사 조각이 기존 데이터를 대체하여 데이터 무결성을 유지합니다.