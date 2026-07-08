from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class OSHomeView(LoginRequiredMixin, TemplateView):
    """OS 홈. 로그인 후 첫 화면이며 모듈 선택 화면이다. (Phase 1 / P1-01)

    - 비로그인 상태 → LoginRequiredMixin 이 settings.LOGIN_URL(accounts:login)로 보낸다.
    - 로그인 상태  → 모듈 카드 목록을 보여준다.
    - 재고관리만 실제 진입 가능하고, 나머지 모듈은 "준비 중"으로 표시한다.
    """

    template_name = "core/os_home.html"
