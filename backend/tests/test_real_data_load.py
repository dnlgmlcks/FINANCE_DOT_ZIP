import sys
from pathlib import Path
from dotenv import load_dotenv

root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))
from src.vector_db.참고.pinecone_service import PineconeService

load_dotenv()

def test_samsung_news_ingestion():
    real_news_data = [
        {
            "title": "삼성전자 1분기 영업이익 6조6060억…반도체 부문 1.9조 '흑자 전환'",
            "content": """삼성전자가 올해 1분기 연결 기준 영업이익이 6조 6060억 원으로 전년 동기 대비 931.87% 증가했다고 공시했다. 
            특히 반도체(DS) 부문은 1조 9100억 원의 영업이익을 기록하며 2022년 4분기 이후 5분기 만에 흑자 전환에 성공했다. 
            HBM(고대역폭메모리) 등 AI 메모리 수요가 실적 개선을 견인한 것으로 분석된다.""",
            "url": "https://www.yna.co.kr/view/AKR20260430060200017?section=search",
            "published_date": "2026-04-30"
        },
        {
            "title": "엔비디아 훈풍 탄 삼성전자, HBM3E 양산 가속도로 시장 공략",
            "content": """삼성전자가 AI 가속기의 핵심 부품인 HBM3E 8단 제품의 양산을 시작했으며, 12단 제품도 2분기 내 양산할 계획이다. 
            글로벌 AI 서버 수요 폭증에 힘입어 메모리 가격 상승세가 이어지고 있으며, 파운드리 부문에서도 
            수율 개선과 고객사 확보를 통해 적자 폭을 줄여나가고 있다.""",
            "url": "https://www.hankyung.com/article/202605070554L",
            "published_date": "2026-05-07"
        }
    ]

    company_name = "삼성전자"
    service = PineconeService()

    print(f"🚀 {company_name} 최신 실적 데이터 적재 시뮬레이션 시작...")

    # PineconeService 내부의 전처리 및 적재 로직 호출
    service.upsert_filtered_news(real_news_data, company_name)

    print("\n" + "="*50)
    print("🔍 Retrieval 테스트: '반도체 흑자 전환과 HBM3E 전략' 쿼리")
    print("="*50)

    # 리포트 작성용 문맥 검색 실행
    context = service.get_context_for_report("반도체 흑자 전환 원인과 HBM3E 양산 계획", company_name)
    print(context)

if __name__ == "__main__":
    test_samsung_news_ingestion()