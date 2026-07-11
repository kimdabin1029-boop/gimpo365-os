"""notice URL. (P2-01)

app_name = "notice" namespace 로 /notices/ 를 담당한다.
현재는 준비 중 화면(name="list")만 연결하고, 상세/등록/수정 URL 은
모델·CRUD 단계(P2-03 이후)에서 추가한다.
"""

from django.urls import path

from notice.views import NoticeListPlaceholderView

app_name = "notice"

urlpatterns = [
    path("", NoticeListPlaceholderView.as_view(), name="list"),
]
