# backend/app/urls.py
# 앱 상세 경로

# backend/app/urls.py
from django.urls import path
from .views import TestAPIView, InitDataAPIView

urlpatterns = [
    # config에서 이미 'api/'를 처리했으므로, 여기서는 그 뒤의 주소만 적습니다.
    # 최종 결과: http://localhost:8000/api/test/
    path('test/', TestAPIView.as_view()),
    path('initData/', InitDataAPIView.as_view()),
]