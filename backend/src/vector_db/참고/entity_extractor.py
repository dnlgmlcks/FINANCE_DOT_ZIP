"""
entity_extractor.py

사용자의 자연어 질문이나 뉴스 본문에서 특정 금융 엔티티(기업명)를 추출하고 
이를 표준화된 종목코드(Stock Code)로 변환하는 엔티티 추출 모듈입니다.

주요 역할:
1. 별칭 매핑(Alias Mapping): '삼전', '삼성전자', 'SEC' 등 다양한 형태의 기업 호출을 하나의 종목코드로 통일합니다.
2. 역색인 사전 구축: COMPANY_MAP을 기반으로 효율적인 검색을 위한 별칭-코드 사전(alias_to_code)을 생성합니다.
3. 정밀 매칭: 긴 단어 우선 매칭(Longest Match First) 원칙을 적용하여 '카카오뱅크'를 '카카오'로 오인식하는 문제를 방지합니다.
4. Namespace 결정: Pinecone 적재 및 검색 시 사용할 ASCII 기반의 안전한 Namespace(종목코드)를 제공합니다.

기술적 특징:
- 대소문자 구분 없는(Case-insensitive) 매칭 지원
- 정렬된 별칭 리스트를 활용한 고속 루프 기반 매칭
"""

from src.vector_db.참고.finance_synonyms import COMPANY_MAP

class EntityExtractor:
    def __init__(self):
        # 1. 역색인 사전 구축: 별칭 -> 종목코드
        self.alias_to_code = {}
        for code, aliases in COMPANY_MAP.items():
            for alias in aliases:
                # 대소문자 구분 없이 처리하기 위해 upper() 적용
                self.alias_to_code[alias.upper()] = code
        
        # 2. 매칭 우선순위를 위해 긴 단어부터 정렬 (예: '삼성'보다 '삼성전자'를 먼저 찾도록)
        self.sorted_aliases = sorted(self.alias_to_code.keys(), key=len, reverse=True)

    def extract_stock_code(self, query: str) -> str:
        """
        사용자의 질문 텍스트에서 종목코드를 추출합니다.
        '삼전'이라고 입력해도 '005930'을 반환합니다.
        """
        if not query:
            return None
            
        query_upper = query.upper()
        
        # 긴 별칭부터 하나씩 대조 (가장 정확한 매칭을 위해)
        for alias in self.sorted_aliases:
            if alias in query_upper:
                return self.alias_to_code[alias]
        
        return None