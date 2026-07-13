from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView

from checklist.selectors import get_today_checklist_items


class TodayChecklistView(LoginRequiredMixin, TemplateView):
    """오늘의 내 부서 체크리스트 조회 화면. (P3-03 / CHECKLIST_TECH_SPEC §12)

    조회 전용이다. 완료/취소 동작(POST)은 P3-04 에서 추가한다.
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
        entries = get_today_checklist_items(user, target_date=target_date)
        completed_count = sum(1 for entry in entries if entry.is_completed)
        context.update(
            {
                "checklist_date": target_date,
                "department": getattr(user, "department", None),
                "entries": entries,
                "total_count": len(entries),
                "completed_count": completed_count,
                "remaining_count": len(entries) - completed_count,
            }
        )
        return context
