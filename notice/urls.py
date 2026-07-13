"""notice URL. (P2-04)

app_name = "notice" namespace 로 /notices/ 목록·등록과 /notices/<pk>/ 상세·수정을 담당한다.
삭제(delete) URL 은 만들지 않는다.
"""

from django.urls import path

from notice.views import (
    NoticeCreateView,
    NoticeDetailView,
    NoticeListView,
    NoticeUpdateView,
)

app_name = "notice"

urlpatterns = [
    path("", NoticeListView.as_view(), name="list"),
    path("new/", NoticeCreateView.as_view(), name="create"),
    path("<int:pk>/", NoticeDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", NoticeUpdateView.as_view(), name="update"),
]
