from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from accounts.mixins import TeamLeaderRequiredMixin
from accounts.models import Role
from accounts.permissions import has_role_at_least, is_manager_or_above
from checklist.models import ChecklistItem, DepartmentChecklistItem
from checklist.selectors import (
    get_checklist_status_for_user,
    get_today_checklist_items,
)
from checklist.services import (
    ChecklistActionNotAllowed,
    cancel_checklist_item,
    complete_checklist_item,
)


class TodayChecklistView(LoginRequiredMixin, TemplateView):
    """오늘의 내 부서 체크리스트 조회 화면. (P3-03 / CHECKLIST_TECH_SPEC §12)

    조회 + 완료/취소 버튼 노출. 실제 상태 변경은 POST 전용 view(P3-04)가 담당한다.
    STAFF/TEAM_LEADER/MANAGER/ADMIN 모두 본인 소속 Department 항목만 본다
    (전체 부서 누락 현황은 P3-05 에서 별도 구현).
    """

    template_name = "checklist/today.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        # 기준 날짜는 요청당 한 번만 계산해 selector·context 에 동일하게 전달한다
        # (자정 경계에서 값이 어긋나지 않도록).
        target_date = timezone.localdate()
        department = getattr(user, "department", None)
        entries = get_today_checklist_items(user, target_date=target_date)
        completed_count = sum(1 for entry in entries if entry.is_completed)
        # 현황 링크 노출(편의). 실제 접근제어는 ChecklistStatusView/selector 가 강제한다.
        # MANAGER 이상은 소속과 무관하게, TEAM_LEADER 는 활성 부서 소속일 때만 노출한다
        # (무소속·비활성 부서 팀장은 클릭해도 403 이므로 링크를 감춘다. P3-06 §7).
        can_view_status = is_manager_or_above(user) or (
            has_role_at_least(user, Role.TEAM_LEADER)
            and department is not None
            and department.is_active
        )
        context.update(
            {
                "checklist_date": target_date,
                "department": department,
                "entries": entries,
                "total_count": len(entries),
                "completed_count": completed_count,
                "remaining_count": len(entries) - completed_count,
                "can_view_checklist_status": can_view_status,
            }
        )
        return context


def _get_today_assignment_or_404(department_item_pk):
    """오늘 처리 가능한(활성 배정·활성 항목·daily) 배정만 조회한다.

    비활성 배정/항목·weekly/monthly 는 처리 대상이 아니므로 404. 부서 일치는 service 가
    PermissionDenied(403)로 검증한다(타 부서 배정은 여기서 404 로 감추지 않는다).
    """
    return get_object_or_404(
        DepartmentChecklistItem.objects.select_related("item", "department").filter(
            is_active=True,
            item__is_active=True,
            item__frequency=ChecklistItem.Frequency.DAILY,
        ),
        pk=department_item_pk,
    )


class CompleteChecklistItemView(LoginRequiredMixin, View):
    """오늘 항목 완료 처리(POST 전용). (P3-04)"""

    def post(self, request, department_item_pk):
        department_item = _get_today_assignment_or_404(department_item_pk)
        try:
            _, changed = complete_checklist_item(
                user=request.user, department_item=department_item
            )
        except ChecklistActionNotAllowed:
            raise Http404("처리할 수 없는 항목입니다.")
        if changed:
            messages.success(request, "체크리스트를 완료했습니다.")
        else:
            messages.info(request, "이미 완료된 체크리스트입니다.")
        return redirect("checklist:today")


class CancelChecklistItemView(LoginRequiredMixin, View):
    """오늘 항목 완료 취소(POST 전용). (P3-04)"""

    def post(self, request, department_item_pk):
        department_item = _get_today_assignment_or_404(department_item_pk)
        try:
            _, changed = cancel_checklist_item(
                user=request.user, department_item=department_item
            )
        except ChecklistActionNotAllowed:
            raise Http404("처리할 수 없는 항목입니다.")
        if changed:
            messages.success(request, "체크리스트 완료를 취소했습니다.")
        else:
            messages.info(request, "이미 미완료 상태입니다.")
        return redirect("checklist:today")


class ChecklistStatusView(TeamLeaderRequiredMixin, TemplateView):
    """오늘의 부서별 체크리스트 누락 현황(조회 전용). (P3-05 / CHECKLIST_TECH_SPEC §13)

    TEAM_LEADER: 본인 부서 1곳. MANAGER/ADMIN: 전체 활성 부서. STAFF: 403(mixin).
    부서 범위·무소속/비활성 부서 팀장 차단은 selector 가 PermissionDenied 로 강제한다.
    완료/취소 기능은 없다(누락 확인만).
    """

    template_name = "checklist/status.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target_date = timezone.localdate()
        statuses = get_checklist_status_for_user(
            self.request.user, target_date=target_date
        )
        context.update(
            {
                "checklist_date": target_date,
                "department_statuses": statuses,
                "department_count": len(statuses),
                "total_count": sum(s.total_count for s in statuses),
                "completed_count": sum(s.completed_count for s in statuses),
                "remaining_count": sum(s.remaining_count for s in statuses),
            }
        )
        return context
