# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response

TEMP_COMPANY_DATA = [
    {"CORP_ID": "001", "CORP_NAME": "삼성전자", "TICKER": "005930"},
    {"CORP_ID": "002", "CORP_NAME": "SK하이닉스", "TICKER": "000660"},
    {"CORP_ID": "003", "CORP_NAME": "현대자동차", "TICKER": "005380"},
    {"CORP_ID": "004", "CORP_NAME": "LG화학", "TICKER": "051910"},
    {"CORP_ID": "005", "CORP_NAME": "카카오", "TICKER": "035720"},
]

class TestAPIView(APIView):
    def get(self, request):
        return Response({"data": "DRF GET 연결 성공!"})
    
    def post(self, request):
        return Response({"data": "DRF POST 연결 성공!"})
    
# 임시 데이터 반환 API (초기 화면에서 기업 리스트 받아올 때 사용)
class InitDataAPIView(APIView):
    def get(self, request):
        return Response({"data": TEMP_COMPANY_DATA})
    
    def post(self, request):
        return Response({"data": TEMP_COMPANY_DATA})
