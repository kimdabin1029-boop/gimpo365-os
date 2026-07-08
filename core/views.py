from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class OSHomeView(LoginRequiredMixin, TemplateView):
    """OS 홈. 로그인 후 첫 화면이며 모듈 선택 화면이다. (Phase 1 / P1-01)

    - 비로그인 상태 → LoginRequiredMixin 이 settings.LOGIN_URL(accounts:login)로 보낸다.
    - 로그인 상태  → 모듈 카드 목록을 보여준다.
    - 재고관리만 실제 진입 가능하고, 나머지 모듈은 "준비 중"으로 표시한다.
    """

    template_name = "core/os_home.html"


class ModulePlaceholderView(LoginRequiredMixin, TemplateView):
    """미구현 모듈 공통 "준비 중" 안내 화면. (Phase 1 / P1-04)

    아직 실제 기능이 없는 모듈을 클릭했을 때, 입력 폼·데이터·저장 동작 없이
    준비 중임을 안내한다. 모듈명은 각 URL 에서 extra_context 로 주입해
    하나의 template 을 재사용한다.
    """

    template_name = "core/module_placeholder.html"
