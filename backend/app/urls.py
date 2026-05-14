from django.urls import path

from .views import (
    test_api,
    init_data,
    search_company,
    comprehensive_report,
    ai_comprehensive_report,
    report_chat,
)

urlpatterns = [
    path("test", test_api),
    path("initData", init_data),
    path("searchCompany", search_company),
    path("v1/report/comprehensive/<str:stock_code>", comprehensive_report),
    path("v1/report/comprehensive/<str:stock_code>/ai", ai_comprehensive_report),
    path("v1/report/comprehensive/<str:stock_code>/chat", report_chat),
]
