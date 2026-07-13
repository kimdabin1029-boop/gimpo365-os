"""checklist URL. (P3-05)

app_name = "checklist" namespace 로 오늘의 체크리스트·완료/취소·누락 현황을 담당한다.
"""

from django.urls import path

from checklist.views import (
    CancelChecklistItemView,
    ChecklistStatusView,
    CompleteChecklistItemView,
    TodayChecklistView,
)

app_name = "checklist"

urlpatterns = [
    path("", TodayChecklistView.as_view(), name="today"),
    path("status/", ChecklistStatusView.as_view(), name="status"),
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
