"""오늘의 체크리스트 조회 접근제어/계산. (P3-03 / CHECKLIST_TECH_SPEC §9)

조회 전용. 레코드를 생성/수정하지 않는다. 완료/취소는 P3-04 service 가 담당한다.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Tuple

from django.core.exceptions import PermissionDenied
from django.utils import timezone

from accounts.models import Role
from accounts.permissions import has_role_at_least, is_manager_or_above
from checklist.models import ChecklistItem, ChecklistRecord, DepartmentChecklistItem
from core.models import Department

# 시기 정렬 순서: 오픈 → 특정 시점 → 마감. (P3-07.5)
# choices 에 없는 값은 맨 뒤로 밀어 안전하게 처리한다.
TIMING_ORDER = {
    ChecklistItem.Timing.OPENING: 0,
    ChecklistItem.Timing.SPECIFIC: 1,
    ChecklistItem.Timing.CLOSING: 2,
}


def _timing_rank(item):
    return TIMING_ORDER.get(item.timing, len(TIMING_ORDER))


@dataclass(frozen=True)
class TodayChecklistEntry:
    """부서 배정 항목 + 오늘의 완료 기록(없으면 None)."""

    department_item: DepartmentChecklistItem
    record: Optional[ChecklistRecord]

    @property
    def is_completed(self) -> bool:
        return self.record is not None


def get_today_checklist_items(user, target_date=None):
    """user 의 오늘(target_date) 내 부서 daily 체크리스트를 계산한다.

    조건(모두 만족하는 배정만):
      - user 로그인 + user.department 존재 + 그 부서가 활성
      - ChecklistItem.is_active=True, frequency=daily
      - DepartmentChecklistItem.is_active=True, department=user.department
    완료 여부: 같은 department_item + target_date 의 활성 ChecklistRecord 존재.

    무소속/비로그인/비활성 부서 사용자는 빈 목록([])을 돌려준다.
    쿼리는 항목 수와 무관하게 최대 2회(배정 1 + 완료기록 1)다.
    """
    if target_date is None:
        target_date = timezone.localdate()

    if user is None or not getattr(user, "is_authenticated", False):
        return []
    department_id = getattr(user, "department_id", None)
    if not department_id:
        return []

    # 비활성 부서는 department__is_active=True JOIN 조건으로 걸러 빈 목록이 된다
    # (user.department 를 따로 로드하지 않아 selector 쿼리를 2회로 유지).
    assignments = list(
        DepartmentChecklistItem.objects.filter(
            is_active=True,
            department_id=department_id,
            department__is_active=True,
            item__is_active=True,
            item__frequency=ChecklistItem.Frequency.DAILY,
        )
        .select_related("item", "department")
        .order_by("sort_order", "item__title", "pk")
    )
    if not assignments:
        return []

    records = ChecklistRecord.objects.filter(
        is_active=True,
        date=target_date,
        department_item_id__in=[a.pk for a in assignments],
    ).select_related("completed_by")
    record_by_item = {r.department_item_id: r for r in records}

    entries = [
        TodayChecklistEntry(department_item=a, record=record_by_item.get(a.pk))
        for a in assignments
    ]
    # 미완료 우선 → 시기 → sort_order → 제목 → pk 로 최종 정렬한다. (P3-07.5)
    # 완료(True)가 미완료(False)보다 뒤로 가므로 완료 항목이 하단에 모인다.
    entries.sort(
        key=lambda e: (
            e.is_completed,
            _timing_rank(e.department_item.item),
            e.department_item.sort_order,
            e.department_item.item.title,
            e.department_item.pk,
        )
    )
    return entries


@dataclass(frozen=True)
class DepartmentChecklistStatus:
    """한 부서의 오늘 daily 체크리스트 현황(누락 확인용)."""

    department: Department
    total_count: int
    completed_count: int
    remaining_count: int
    missing_items: Tuple[DepartmentChecklistItem, ...]


def get_checklist_status_for_user(user, target_date=None):
    """user 역할에 따른 부서별 오늘 누락 현황을 계산한다. (P3-05 / CHECKLIST_TECH_SPEC §13)

    - MANAGER / ADMIN: 전체 활성 부서(본인 소속 유무 무관).
    - TEAM_LEADER: 본인 소속 활성 부서 1곳(무소속·비활성 부서면 PermissionDenied).
    - STAFF / 비로그인: PermissionDenied.

    view 의 mixin 과 별개로 selector 에서도 역할·범위를 강제한다(조회 전용, DB 변경 없음).
    쿼리는 부서/항목 수와 무관하게 최대 3회(부서 1 + 배정 1 + 완료기록 1)다.
    """
    if target_date is None:
        target_date = timezone.localdate()

    if user is None or not getattr(user, "is_authenticated", False):
        raise PermissionDenied("로그인이 필요합니다.")

    if is_manager_or_above(user):
        departments = list(
            Department.objects.filter(is_active=True).order_by("name", "pk")
        )
    elif has_role_at_least(user, Role.TEAM_LEADER):
        department = (
            Department.objects.filter(pk=user.department_id, is_active=True).first()
            if user.department_id
            else None
        )
        if department is None:
            raise PermissionDenied("활성 부서 소속 팀장만 조회할 수 있습니다.")
        departments = [department]
    else:
        raise PermissionDenied("현황 조회 권한이 없습니다.")

    if not departments:
        return []

    department_ids = [d.pk for d in departments]
    assignments = list(
        DepartmentChecklistItem.objects.filter(
            is_active=True,
            department_id__in=department_ids,
            department__is_active=True,
            item__is_active=True,
            item__frequency=ChecklistItem.Frequency.DAILY,
        )
        .select_related("item", "department")
        .order_by("department_id", "sort_order", "item__title", "pk")
    )

    if assignments:
        completed_ids = set(
            ChecklistRecord.objects.filter(
                is_active=True,
                date=target_date,
                department_item_id__in=[a.pk for a in assignments],
            ).values_list("department_item_id", flat=True)
        )
    else:
        completed_ids = set()

    assignments_by_department = defaultdict(list)
    for assignment in assignments:
        assignments_by_department[assignment.department_id].append(assignment)

    statuses = []
    for department in departments:
        dept_assignments = assignments_by_department.get(department.pk, [])
        missing = tuple(
            sorted(
                (a for a in dept_assignments if a.pk not in completed_ids),
                # 시기 → sort_order → 제목 → pk 로 정렬한다. (P3-07.5)
                key=lambda a: (
                    _timing_rank(a.item),
                    a.sort_order,
                    a.item.title,
                    a.pk,
                ),
            )
        )
        total = len(dept_assignments)
        completed = total - len(missing)
        statuses.append(
            DepartmentChecklistStatus(
                department=department,
                total_count=total,
                completed_count=completed,
                remaining_count=len(missing),
                missing_items=missing,
            )
        )
    return statuses
