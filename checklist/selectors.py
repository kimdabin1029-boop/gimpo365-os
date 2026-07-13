"""오늘의 체크리스트 조회 접근제어/계산. (P3-03 / CHECKLIST_TECH_SPEC §9)

조회 전용. 레코드를 생성/수정하지 않는다. 완료/취소는 P3-04 service 가 담당한다.
"""

from dataclasses import dataclass
from typing import Optional

from django.utils import timezone

from checklist.models import ChecklistItem, ChecklistRecord, DepartmentChecklistItem


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

    return [
        TodayChecklistEntry(department_item=a, record=record_by_item.get(a.pk))
        for a in assignments
    ]
