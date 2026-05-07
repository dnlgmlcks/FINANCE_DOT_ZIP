# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view

TEMP_COMPANY_DATA = [
    {"CORP_ID": "001", "CORP_NAME": "삼성전자", "TICKER": "005930"},
    {"CORP_ID": "002", "CORP_NAME": "SK하이닉스", "TICKER": "000660"},
    {"CORP_ID": "003", "CORP_NAME": "현대자동차", "TICKER": "005380"},
    {"CORP_ID": "004", "CORP_NAME": "LG화학", "TICKER": "051910"},
    {"CORP_ID": "005", "CORP_NAME": "카카오", "TICKER": "035720"},
]

@api_view(['GET', 'POST'])
def test_api(request):

    method = request.method
    return Response({"data": f"DRF {method} 연결 성공!"})
    
@api_view(['GET', 'POST'])
# 임시 데이터 반환 API (초기 화면에서 기업 리스트 받아올 때 사용)
def init_data(request):
    # 데이
    return Response({"data": TEMP_COMPANY_DATA})
    
# 기업 조회
@api_view(['GET', 'POST'])
def search_company(request):
    # get
    if request.method == "GET":
        # print(f'DEBUG | search_company | request: {request.query_params=}')
        inputVal = request.query_params.keyword

    else :
        # print(f'DEBUG | search_company | request: {request.data=}')
        inputVal = request.data.keyword
    
    # 클래스를 조회하는 로직 추가
    return Response({"data": "test" })    