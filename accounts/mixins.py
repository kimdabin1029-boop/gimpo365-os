"""공통 권한 mixin. (P2-05)

역할(role) 기반 화면 접근 제어를 여러 앱이 재사용하도록 accounts 에 둔다.
권한 판단은 accounts.permissions 의 헬퍼(OS role 기준)를 사용하며,
Django is_staff / is_superuser 와는 무관하다.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from accounts.models import Role
from accounts.permissions import has_role_at_least, is_manager_or_above


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


class TeamLeaderRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """TEAM_LEADER 이상만 접근을 허용한다.

    ManagerRequiredMixin 과 같은 동작 규약을 따른다:
    - 비로그인 → 로그인 화면으로 redirect.
    - 로그인했지만 STAFF → 403.
    권한 판단은 accounts.permissions.has_role_at_least(Role.TEAM_LEADER) (OS role 기준)이다.
    raise_exception 은 설정하지 않는다(위 ManagerRequiredMixin 주의와 동일).

    부서 범위(본인 부서 vs 전체)는 mixin 이 아니라 selector 에서 role 로 결정·강제한다.
    """

    def test_func(self):
        return has_role_at_least(self.request.user, Role.TEAM_LEADER)
