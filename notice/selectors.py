"""Notice 조회 접근제어. (P2-03 / NOTICE_TECH_SPEC §8·§9)

목록(NoticeListView)과 상세(NoticeDetailView)가 동일한 접근 기준을 공유하도록
접근 가능 queryset 을 한 곳에서 만든다.
"""

from django.db.models import Q

from accounts.permissions import is_manager_or_above
from notice.models import Notice


def get_accessible_notice_queryset(user):
    """user 가 목록/상세에서 조회할 수 있는 Notice queryset 을 돌려준다.

    공통: is_active=True 인 공지만 대상으로 한다(논리 삭제/비활성 제외).

    - MANAGER 이상: draft / published 관계없이 전체 active 공지를 본다.
    - STAFF / TEAM_LEADER:
        · published 이고 대상이 전체(all)인 공지
        · published 이고 대상이 본인 부서(department)인 공지
        · 본인이 작성한 draft 공지
      department 가 없는 사용자는 부서 대상 공지를 볼 수 없다.
      (user.department 가 None 일 때 target_department IS NULL 조건이 생기지 않도록,
       department_id 가 있을 때만 부서 조건을 추가한다.)
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return Notice.objects.none()

    active = Notice.objects.filter(is_active=True)

    if is_manager_or_above(user):
        return active

    visible = Q(target_type=Notice.TargetType.ALL)
    if user.department_id:
        visible |= Q(
            target_type=Notice.TargetType.DEPARTMENT,
            target_department_id=user.department_id,
        )

    published = Q(status=Notice.Status.PUBLISHED) & visible
    own_draft = Q(status=Notice.Status.DRAFT, created_by=user)

    return active.filter(published | own_draft)
