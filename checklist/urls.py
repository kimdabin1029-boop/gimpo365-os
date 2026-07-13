"""checklist URL. (P3-01)

app_name = "checklist" namespace 로 /checklists/ 를 담당한다.
현재는 준비 중 화면(name="today")만 연결하고, 완료/취소·누락 현황 URL 은
모델·기능 단계(P3-03 이후)에서 추가한다. name="today" 는 최종 역할이
로그인 사용자의 '오늘의 체크리스트' 화면이기 때문이다.
"""

from django.urls import path

from checklist.views import ChecklistPlaceholderView

app_name = "checklist"

urlpatterns = [
    path("", ChecklistPlaceholderView.as_view(), name="today"),
]
