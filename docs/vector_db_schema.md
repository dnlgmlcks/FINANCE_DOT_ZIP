# Vector DB Metadata Schema

## Overview

리포트 자동 생성 시스템의 검색 엔진 역할을 하는 Pinecone 벡터 데이터베이스의
데이터 저장 구조와 메타데이터 규격을 정의합니다.

---

# 1. 인덱스 및 네임스페이스 구성

- **Index Name**: `finance-dot-news`
- **Dimension**: 1536 (OpenAI `text-embedding-3-small` 모델 기준)
- **Metric**: `cosine` (금융 문서 유사도 측정에 최적화)
- **Namespace Strategy**: **종목코드(Stock Code)** 사용 (6자리 숫자)
  - 예: 삼성전자 데이터는 `005930` 네임스페이스에 격리 저장됨
  - 이점: 특정 기업 검색 시 다른 기업 데이터와의 간섭을 원천 차단하고 검색 속도를 향상시킴

---

# 2. 데이터 레코드 구조

각 뉴스 텍스트 조각(Chunk)은 아래와 같은 고유 ID 및 메타데이터와 함께 벡터화되어 저장됩니다.

```json
{
  "id": "{base_id}_{chunk_index}",
  "values": [0.0123, -0.0456, "..."],
  "metadata": {
    "text": "전처리 및 정규화가 완료된 뉴스 텍스트 본문 조각",
    "source": "https://news.example.com/article/123",
    "company_name": "삼성전자",
    "stock_code": "005930",
    "stock_codes": ["005930"],
    "date": "2026-05-11",
    "signal_type": "negative",
    "signal_code": "EARNINGS_DROP",
    "industry_group": "tech_equipment",
    "data_type": "disclosure"
  }
}
```

---

# 3. 메타데이터 필드 상세

| 필드명 | 타입 | 설명 | 비고 |
|:---|:---|:---|:---|
| text | string | 청킹된 뉴스 본문. 용어 정규화 완료 상태 | Retrieval 결과값 |
| source | string | 뉴스 기사의 원본 URL | 레퍼런스 및 중복 체크용 |
| company_name | string | 대상 기업명 (대표 기업) | 확인용 |
| stock_code | string | 종목코드 (단일) | Namespace 기준값 |
| stock_codes | List[string] | 해당 뉴스에 언급된 모든 종목코드 리스트 | $in 연산자로 필터링 |
| date | string | 발행 일자 (형식: YYYY-MM-DD) | Range Filter 가능 |
| signal_type | string | positive / negative | Signal 분류 |
| signal_code | string | Signal 코드 | detected_changes 연동 |
| industry_group | string | 산업 그룹 코드 | 산업별 필터링 |
| data_type | string | disclosure / news | 데이터 유형 구분 |

---

# 4. 지원 Metadata Filtering

- stock_code
- stock_codes (`$in` 연산자)
- company_name
- date (Range Filter)
- signal_type
- signal_code
- industry_group
- data_type

---

# 5. Filtering Example

```python
build_metadata_filter(
    stock_code="005930",
    year=2023,
    signal_code="EARNINGS_DROP"
)
```

---

# 6. Retrieval Structure

```text
detected_changes
    ↓
query_hint 생성
    ↓
metadata filtering
    ↓
Vector DB retrieval
```

---

# 7. 데이터 무결성 및 중복 방지 로직

- **ID 생성**: `hashlib.md5(url).hexdigest() + "_" + chunk_index`
  - URL이 같으면 종목코드와 상관없이 동일한 ID를 가짐
- **Deduplication**: 동일 URL 재입력 시 동일 ID로 인식하여 자동 **Upsert** 처리
- **다중 엔티티 대응**: 한 기사에 여러 회사가 포함될 경우 `stock_codes` 리스트에 모두 담아 단일 레코드로 관리