from django.conf import settings
from django.shortcuts import redirect

def custom_404_handler(request, exception):
    # 프론트엔드 주소로 리다이렉트 (예: http://localhost:3000)
    return redirect(settings.FRONTEND_URL)