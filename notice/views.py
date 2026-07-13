from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView

from notice.models import Notice
from notice.selectors import get_accessible_notice_queryset


class NoticeListView(LoginRequiredMixin, ListView):
    """공지 목록. (P2-03 / NOTICE_TECH_SPEC §8)

    접근 가능한 공지만 노출한다(접근제어는 selectors.get_accessible_notice_queryset).
    정렬은 모델 Meta.ordering(-created_at)을 따른다. is_important 는 뱃지 표시용이며
    상단 고정 정렬은 하지 않는다(MVP 제외).
    """

    model = Notice
    template_name = "notice/notice_list.html"
    context_object_name = "notices"

    def get_queryset(self):
        return get_accessible_notice_queryset(self.request.user)


class NoticeDetailView(LoginRequiredMixin, DetailView):
    """공지 상세. (P2-03 / NOTICE_TECH_SPEC §8)

    목록과 동일한 접근제어 queryset 을 사용한다. 접근 권한이 없는 pk 로 접근하면
    404 가 된다(403 을 쓰지 않는다 — 공지 존재 자체를 노출하지 않기 위함).
    """

    model = Notice
    template_name = "notice/notice_detail.html"
    context_object_name = "notice"

    def get_queryset(self):
        return get_accessible_notice_queryset(self.request.user)
