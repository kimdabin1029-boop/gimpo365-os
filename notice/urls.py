"""notice URL. (P2-03)

app_name = "notice" namespace 로 /notices/ 목록과 /notices/<pk>/ 상세를 담당한다.
등록/수정(new/edit) URL 은 P2-04 이후에 추가한다.
"""

from django.urls import path

from notice.views import NoticeDetailView, NoticeListView

app_name = "notice"

urlpatterns = [
    path("", NoticeListView.as_view(), name="list"),
    path("<int:pk>/", NoticeDetailView.as_view(), name="detail"),
]
