"""
setup_pinecone.py

프로젝트 시작 시 Pinecone 벡터 데이터베이스의 인덱스를 초기 생성하고 설정하는 스크립트입니다.

주요 역할:
1. 인덱스 존재 여부 확인: 지정된 이름(finance-dot-news)의 인덱스가 있는지 체크합니다.
2. 서버리스 인덱스 생성: 인덱스가 없을 경우, OpenAI 임베딩 모델(1536 차원)에 최적화된 설정으로 새 인덱스를 생성합니다.
3. 상태 모니터링: 인덱스가 생성되어 'Ready' 상태가 될 때까지 대기하여 즉시 사용 가능한 상태를 보장합니다.

설정 정보:
- Dimension: 1536 (text-embedding-3-small 대응)
- Metric: Cosine (금융 문서 유사도 검색에 최적)
- Cloud/Region: AWS (us-east-1)

사용 방법:
- 개발 환경 구축 시 또는 인덱스 초기화가 필요할 때 1회 실행합니다.
"""

import os
import time
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# 프로젝트 루트의 .env를 찾기 위해 경로 설정
load_dotenv()

def initialize_pinecone():
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("에러: .env 파일에 PINECONE_API_KEY가 설정되지 않았습니다.")
        return

    pc = Pinecone(api_key=api_key)
    index_name = "finance-dot-news"
    
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    
    if index_name not in existing_indexes:
        print(f"'{index_name}' 인덱스 생성을 시작합니다...")
        pc.create_index(
            name=index_name,
            dimension=1536, # text-embedding-3-small
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws', 
                region='us-east-1'
            )
        )
        
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(2)
        print(f"[성공] {index_name} 인덱스가 준비되었습니다.")
    else:
        print(f"[안내] '{index_name}' 인덱스가 이미 존재합니다.")

if __name__ == "__main__":
    initialize_pinecone()