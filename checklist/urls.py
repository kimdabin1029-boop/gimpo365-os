"""checklist URL. (P3-04)

app_name = "checklist" namespace 로 /checklists/ 오늘의 체크리스트와 완료/취소를 담당한다.
누락 현황(status) URL 은 P3-05 에서 추가한다.
"""

from django.urls import path

from checklist.views import (
    CancelChecklistItemView,
    CompleteChecklistItemView,
    TodayChecklistView,
)

app_name = "checklist"

urlpatterns = [
    path("", TodayChecklistView.as_view(), name="today"),
    path(
        "<int:department_item_pk>/complete/",
        CompleteChecklistItemView.as_view(),
        name="complete",
    ),
    path(
        "<int:department_item_pk>/cancel/",
        CancelChecklistItemView.as_view(),
        name="cancel",
    ),
]
