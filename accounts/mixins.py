"""공통 권한 mixin. (P2-05)

역할(role) 기반 화면 접근 제어를 여러 앱이 재사용하도록 accounts 에 둔다.
권한 판단은 accounts.permissions 의 헬퍼(OS role 기준)를 사용하며,
Django is_staff / is_superuser 와는 무관하다.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from accounts.permissions import is_manager_or_above


class ManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """MANAGER 이상만 접근을 허용한다.

    - 비로그인 → 로그인 화면으로 redirect (LoginRequiredMixin).
    - 로그인했지만 MANAGER 미만(STAFF/TEAM_LEADER) → 403 (UserPassesTestMixin).

    권한 판단은 accounts.permissions.is_manager_or_above (OS role 기준)이다.

    주의: raise_exception 은 설정하지 않는다. raise_exception=True 로 두면
    비로그인 사용자도 403 이 되어 "비로그인 → 로그인 redirect" 규칙이 깨진다
    (LoginRequiredMixin 의 handle_no_permission 이 raise_exception 을 함께 본다).
    """

    def test_func(self):
        return is_manager_or_above(self.request.user)
