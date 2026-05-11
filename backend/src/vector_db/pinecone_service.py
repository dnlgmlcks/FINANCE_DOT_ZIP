"""
pinecone_service.py

Tavily를 통해 수집되고 news_evidence_filter로 검증된 뉴스 데이터를 
Pinecone 벡터 데이터베이스에 전처리 및 적재하고, 리포트 생성에 필요한 문맥을 검색하는 서비스 모듈입니다.

주요 역할:
1. 뉴스 텍스트 전처리: 정규표현식으로 노이즈를 제거하고 FINANCE_TERMS 기반 용어 정규화를 수행합니다.
2. 데이터 적재 및 청킹: 긴 뉴스를 RecursiveCharacterTextSplitter로 최적화된 크기로 쪼개어 저장합니다.
3. 중복 방지(Deduplication): 뉴스 URL/제목 기반의 해시 ID를 생성하여 동일 기사의 중복 적재를 방지합니다.
4. 데이터 격리 및 최적화: 종목코드(stock_code)를 Namespace로 활용하여 기업 간 데이터를 격리하고 검색 속도를 높입니다.

기술 스펙:
- Vector DB: Pinecone (Serverless)
- Embedding Model: OpenAI text-embedding-3-small (1536 Dimensions)
- Search Metric: Cosine Similarity
- Chunk Strategy: 500 characters with 50 overlap

주의사항:
- 이 모듈을 사용하기 전, setup_pinecone.py를 통해 인덱스가 생성되어 있어야 합니다.
- EntityExtractor 모듈과 FINANCE_TERMS 정의 파일이 필요합니다.
"""

import os
import re
from typing import List, Dict, Any
from pinecone import Pinecone
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.vector_db.finance_synonyms import FINANCE_TERMS
from src.vector_db.entity_extractor import EntityExtractor
import hashlib

class PineconeService:
    def __init__(self, index_name: str = "finance-dot-news"):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = index_name
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # 엔티티 추출기 초기화
        self.extractor = EntityExtractor()
        
        self.vector_store = PineconeVectorStore(
            index_name=self.index_name, 
            embedding=self.embeddings
        )

        # 청킹 설정: 500자 내외로 쪼개고, 문맥 유지를 위해 50자 정도 겹치게(overlap) 설정
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            is_separator_regex=False,
        )

    def _normalize_text(self, text: str) -> str:
        """
        기업명 치환 반복문을 제거하고, 재무 용어 정규화만 수행
        기업명은 이미 Namespace로 분리되어 있으므로 본문 내 치환의 중요도가 낮아졌습니다.
        """
        text = text.upper()
        
        # 재무/기술 용어 정규화
        for category_dict in FINANCE_TERMS.values():
            for standard, synonyms in category_dict.items():
                for synonym in synonyms:
                    if synonym in text:
                        text = text.replace(synonym, standard)

        return text

    def _preprocess_content(self, title: str, content: str) -> str:
        full_text = f"제목: {title}\n본문: {content}"
        
        # 노이즈 제거
        full_text = re.sub(r'[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '', full_text)
        full_text = re.sub(r'\(.*?\)|\[.*?\]', '', full_text)
        
        # 용어 정규화
        full_text = self._normalize_text(full_text)
        
        # 특수문자 및 공백 정제
        full_text = re.sub(r'[^\w\s\.]', '', full_text)
        full_text = re.sub(r'\s+', ' ', full_text).strip()
        
        return full_text

    def _get_stock_code(self, company_name: str) -> str:
        """
        EntityExtractor를 사용하여 어떤 별칭이 들어와도 정확한 종목코드(Namespace)를 반환합니다.
        """
        code = self.extractor.extract_stock_code(company_name)
        return code if code else "000000" # 못 찾을 경우 기본 네임스페이스

    def upsert_filtered_news(self, evidence_news: List[Dict[str, Any]], company_name: str):
            """중복 방지 및 Chunking 적용 후 뉴스 적재"""
            stock_code = self._get_stock_code(company_name)
            
            all_chunks = []
            all_ids = []    # 각 조각의 고유 ID를 담을 리스트
            
            for news in evidence_news:
                url = news.get("url", "")
                title = news.get("title", "")
                processed_text = self._preprocess_content(title, news.get('content', ''))
                
                # 1. 뉴스 기사의 고유 ID 생성 (URL이 있으면 URL로, 없으면 제목으로 해싱)
            # 기사 하나가 여러 조각(Chunk)으로 나뉘므로, 조각마다 고유번호를 붙입니다.
                base_id = hashlib.md5(url.encode() if url else title.encode()).hexdigest()

                # 메타데이터에 리스트 형태로 저장 (예: ["005930", "000660"])
                metadata = {
                    "source": url,
                    "company_name": company_name,
                    "stock_codes": [stock_code], # 리스트로 관리
                    "date": news.get("published_date", "Unknown")
                }
                
                chunks = self.text_splitter.create_documents(
                    texts=[processed_text], 
                    metadatas=[metadata]
                )
                
                # 예: "해시값_0", "해시값_1" 식으로 ID 부여
                for i, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    all_ids.append(f"{base_id}_{i}")

            if all_chunks:
                # ids 파라미터를 넘겨주면 Pinecone이 중복 ID를 체크해서 덮어쓰기합니다.
                self.vector_store.add_documents(
                    documents=all_chunks, 
                    ids=all_ids 
                )
                print(f"📦 [Pinecone] {company_name} 데이터 통합 공간(Default) 적재 완료")

    def get_context_for_report(self, query: str, company_name: str, k: int = 10) -> str:
            """Metadata 필터링으로 검색"""
            stock_code = self._get_stock_code(company_name)
            
            # 1. stock_codes 리스트 안에 해당 코드가 포함되어 있는지 필터링하여 검색
            docs = self.vector_store.similarity_search(
                query, 
                k=k, 
                filter={"stock_codes": {"$in": [stock_code]}} 
            )
            
            # 2. 검색 결과가 없을 경우 메시지 반환
            if not docs: 
                return f"'{company_name}'({stock_code}) 관련 근거를 찾을 수 없습니다."
                
            # 3. 검색된 문서들을 하나의 컨텍스트 문자열로 합쳐서 리턴
            return "\n\n".join([f"--- 기사 근거 ---\n{d.page_content}" for d in docs])