"""checklist URL. (P3-03)

app_name = "checklist" namespace 로 /checklists/ 오늘의 체크리스트를 담당한다.
완료/취소(complete/cancel)·누락 현황(status) URL 은 P3-04 이후에 추가한다.
"""

from django.urls import path

from checklist.views import TodayChecklistView

app_name = "checklist"

urlpatterns = [
    path("", TodayChecklistView.as_view(), name="today"),
]
