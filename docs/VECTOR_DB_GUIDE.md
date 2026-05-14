# VECTOR DB GUIDE

## 사용 기술

- Vector DB: Pinecone
- Embedding Model: text-embedding-3-small
- Framework: LangChain
- Search 방식:
  - similarity_search
  - metadata filtering 기반 retrieval

---

# 폴더 구조

```text
src/vector_db
├── __init__.py
├── context_merger.py
├── document_builder.py
├── metadata_filter.py
├── metadata_schema.py
├── news_preprocessor.py
├── query_builder.py
├── retriever.py
├── upsert_pipeline.py
├── vector_store.py
└── 참고
    ├── entity_extractor.py
    └── finance_synonyms.py
```

---

# 주요 파일 설명

## metadata_schema.py

Vector DB metadata schema 정의.

공시 / 뉴스 모두 동일 schema 사용.

### 주요 metadata

- data_type
- stock_code
- company_name
- year
- signal_type
- signal_code
- industry_group
- source
- source_url

---

## document_builder.py

뉴스 / 공시 데이터를 LangChain Document 객체로 변환.

### 주요 함수

```python
build_documents_from_news_list(news_list)
build_documents_from_disclosure_rows(rows)
```

---

## vector_store.py

Pinecone Vector Store 연결 및 upsert 수행.

### 주요 함수

```python
upsert_documents(documents)
get_vector_store()
```

---

## upsert_pipeline.py

Vector DB 적재 파이프라인.

### 지원 기능

- 공시 CSV 적재
- 실시간 뉴스 article 적재
- metadata 통합
- detected_change 기반 metadata 보강

### 주요 함수

```python
upsert_disclosure_folder()
upsert_disclosure_csv()
upsert_news_articles()
```

---

## retriever.py

Vector DB 검색 수행.

### 지원 기능

- similarity search
- metadata filtering
- score 반환
- data_type filtering

### 주요 함수

```python
search_similar_documents()
print_search_results()
```

---

## metadata_filter.py

metadata filter 생성 유틸.

### 지원 filter

- stock_code
- company_name
- year
- signal_type
- signal_code
- industry_group
- data_type

---

## news_preprocessor.py

뉴스 데이터 전처리.

### 주요 기능

- 텍스트 정규화
- 특수문자 제거
- finance synonym 치환
- chunk 전처리

### 주요 함수

```python
normalize_news_text()
preprocess_news_article()
```

---

## query_builder.py

detected_changes 기반 검색 query 생성 유틸.

실제 Tavily Search / LLM 호출은 수행하지 않음.

### 주요 함수

```python
build_query_from_change()
build_queries_from_changes()
```

### 예시

```python
{
    "company_name": "삼성전자",
    "signal_code": "OPERATING_INCOME_DROP_HIGH"
}
```

↓

```text
삼성전자 영업이익 급감 원인
```

---

## context_merger.py

검색 결과를 사람이 읽기 쉬운 context 문자열로 변환.

실제 Prompt 구성 및 Report 생성은 AI/Agent 파트 담당.

### 주요 함수

```python
merge_documents_as_context()
```

---

# 공시 데이터 적재 방법

## 실행

```bash
python -m src.vector_db.upsert_pipeline
```

## 적재 대상 경로

```text
data/export/disclosure
```

## 지원 파일

```text
major_event_occurrences.csv
major_event_occurrences_all.csv
```

---

# Retrieval 테스트

## 실행

```bash
python -m src.vector_db.retriever
```

## 예시

```python
results = search_similar_documents(
    query="합병 결정 공시",
    stock_code="091700",
    data_type="disclosure",
    top_k=5,
    with_score=True,
)
```

---

# 환경 변수

`.env`

```env
PINECONE_API_KEY=
OPENAI_API_KEY=
OPENAI_MODEL_NAME=gpt-4o-mini
```

---

# 설치 패키지

```bash
pip install pinecone
pip install langchain-openai
pip install langchain-pinecone
pip install langchain-core
pip install langchain-text-splitters
pip install python-dotenv
```

---

# 현재 적용 사항

- 공시 CSV Vector DB 적재 완료
- metadata schema 통일 완료
- retrieval metadata filtering 적용 완료
- similarity search 테스트 완료
- news article 실시간 적재 구조 반영 완료
