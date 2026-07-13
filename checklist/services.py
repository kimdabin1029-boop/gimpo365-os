"""체크리스트 완료/취소 상태 전이. (P3-04 / CHECKLIST_TECH_SPEC §11·§15)

- 부서 단위: 같은 활성 부서 소속 사용자가 수행/취소한다(개인 담당자 없음).
- 완료 취소는 hard delete 가 아니라 is_active=False, 재완료는 기존 unique 레코드 재활성화.
- transaction.atomic + DepartmentChecklistItem select_for_update 로 동시 요청을 직렬화하고,
  UniqueConstraint(department_item, date)를 최종 DB 안전장치로 둔다.
"""

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from checklist.models import ChecklistItem, ChecklistRecord, DepartmentChecklistItem


class ChecklistActionNotAllowed(Exception):
    """처리 대상이 아닌 배정에 대한 완료/취소 시도(비활성 배정/항목, daily 아님).

    권한 문제(무소속/비활성 부서/타 부서)는 PermissionDenied 로 구분한다.
    """


def _validate_checklist_action(*, user, department_item):
    """완료/취소 공통 업무 규칙 검증.

    권한 실패(무소속/비활성 부서/타 부서) → PermissionDenied(403).
    처리 대상 아님(비활성 배정/항목, daily 아님) → ChecklistActionNotAllowed.
    view 는 처리 대상 아님을 queryset 으로 404 처리하지만, service 도 방어적으로 재검증한다.
    """
    if user is None or not getattr(user, "is_authenticated", False):
        raise PermissionDenied("로그인이 필요합니다.")
    department = getattr(user, "department", None)
    if department is None or not department.is_active:
        raise PermissionDenied("활성 부서 소속만 처리할 수 있습니다.")
    if department_item.department_id != user.department_id:
        raise PermissionDenied("본인 부서의 체크리스트만 처리할 수 있습니다.")

    if not department_item.is_active:
        raise ChecklistActionNotAllowed("비활성 배정입니다.")
    if not department_item.item.is_active:
        raise ChecklistActionNotAllowed("비활성 항목입니다.")
    if department_item.item.frequency != ChecklistItem.Frequency.DAILY:
        raise ChecklistActionNotAllowed("daily 항목만 처리할 수 있습니다.")


def _lock_department_item(department_item):
    """동시 요청 직렬화용으로 배정 행을 잠그고 item/department 를 함께 로드한다."""
    return (
        DepartmentChecklistItem.objects.select_for_update()
        .select_related("item", "department")
        .get(pk=department_item.pk)
    )


def complete_checklist_item(*, user, department_item, target_date=None):
    """오늘(target_date) 완료 처리. 반환 (record, changed).

    changed=True: 최초 완료 또는 취소 기록 재활성화. changed=False: 이미 완료(멱등).
    """
    if target_date is None:
        target_date = timezone.localdate()

    with transaction.atomic():
        locked = _lock_department_item(department_item)
        _validate_checklist_action(user=user, department_item=locked)

        record = (
            ChecklistRecord.objects.select_for_update()
            .filter(department_item=locked, date=target_date)
            .first()
        )
        if record is None:
            record = ChecklistRecord.objects.create(
                department_item=locked,
                date=target_date,
                completed_by=user,
                completed_at=timezone.now(),
                created_by=user,
                updated_by=user,
                is_active=True,
            )
            return record, True

        if record.is_active:
            # 이미 완료 → 멱등(최초 수행자 정보 유지)
            return record, False

        # 취소 기록 재활성화(같은 행 재사용, created_by/date 유지)
        record.is_active = True
        record.completed_by = user
        record.completed_at = timezone.now()
        record.updated_by = user
        record.save(
            update_fields=[
                "is_active",
                "completed_by",
                "completed_at",
                "updated_by",
                "updated_at",
            ]
        )
        return record, True


def cancel_checklist_item(*, user, department_item, target_date=None):
    """오늘(target_date) 완료 취소. 반환 (record_or_none, changed).

    changed=True: 활성 기록을 비활성화. changed=False: 기록 없음 또는 이미 비활성(멱등).
    completed_by/completed_at/created_by/date 는 보존하고 updated_by 만 취소 사용자로 남긴다.
    """
    if target_date is None:
        target_date = timezone.localdate()

    with transaction.atomic():
        locked = _lock_department_item(department_item)
        _validate_checklist_action(user=user, department_item=locked)

        record = (
            ChecklistRecord.objects.select_for_update()
            .filter(department_item=locked, date=target_date)
            .first()
        )
        if record is None:
            return None, False
        if not record.is_active:
            return record, False

        record.is_active = False
        record.updated_by = user
        record.save(update_fields=["is_active", "updated_by", "updated_at"])
        return record, True
