"""core URL: OS 홈 + 미구현 모듈 준비 중 placeholder. (P1-01, P1-04)

placeholder 는 공통 ModulePlaceholderView 를 재사용하고, 모듈명만 extra_context 로 주입한다.
신규 Django 앱·모델·migration 없이 화면 안내만 담당한다.
"""

from django.urls import path

from core.views import ModulePlaceholderView, OSHomeView

urlpatterns = [
    path("", OSHomeView.as_view(), name="home"),
    # /notices/ 는 P2-01 에서 notice 앱(notice.urls)으로 이관했다. core placeholder 아님.
    path(
        "checklists/",
        ModulePlaceholderView.as_view(
            extra_context={"module_name": "오픈/마감 체크리스트"}
        ),
        name="checklist_placeholder",
    ),
    path(
        "manuals/",
        ModulePlaceholderView.as_view(
            extra_context={"module_name": "SOP/업무 매뉴얼"}
        ),
        name="manual_placeholder",
    ),
    path(
        "requests/",
        ModulePlaceholderView.as_view(extra_context={"module_name": "내부 요청/결재"}),
        name="request_placeholder",
    ),
    path(
        "schedules/",
        ModulePlaceholderView.as_view(extra_context={"module_name": "근태/근무표"}),
        name="schedule_placeholder",
    ),
]
