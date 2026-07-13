from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.mixins import ManagerRequiredMixin
from accounts.permissions import is_manager_or_above
from notice.forms import NoticeForm
from notice.models import Notice
from notice.selectors import get_accessible_notice_queryset


def _ensure_published_at(notice):
    """게시 상태로 저장될 때 최초 게시 시각을 채운다. (P2-04 §5)

    - status=published 인데 published_at 이 비어 있으면 timezone.now() 로 설정한다.
    - 이미 published_at 이 있으면 유지한다.
    - draft 로 되돌려도 published_at 을 자동으로 지우지 않는다(상태 전환 이력은 MVP 범위 밖).
    """
    if notice.status == Notice.Status.PUBLISHED and notice.published_at is None:
        notice.published_at = timezone.now()


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage_notice"] = is_manager_or_above(self.request.user)
        return context


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_manage_notice"] = is_manager_or_above(self.request.user)
        return context


class NoticeCreateView(ManagerRequiredMixin, CreateView):
    """공지 등록. MANAGER 이상만 접근 가능. (P2-04)"""

    model = Notice
    form_class = NoticeForm
    template_name = "notice/notice_form.html"
    extra_context = {"form_title": "공지사항 등록"}

    def form_valid(self, form):
        # created_by / updated_by 는 서버에서 설정(폼 미노출).
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        _ensure_published_at(form.instance)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("notice:detail", args=[self.object.pk])


class NoticeUpdateView(ManagerRequiredMixin, UpdateView):
    """공지 수정. MANAGER 이상만 접근 가능. is_active=True 공지만 수정 대상. (P2-04)"""

    model = Notice
    form_class = NoticeForm
    template_name = "notice/notice_form.html"
    extra_context = {"form_title": "공지사항 수정"}

    def get_queryset(self):
        # 비활성(is_active=False) 공지는 수정 화면에서 조회하지 않는다 → 404.
        return Notice.objects.filter(is_active=True)

    def form_valid(self, form):
        # created_by 는 유지하고 updated_by 만 갱신한다.
        form.instance.updated_by = self.request.user
        _ensure_published_at(form.instance)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("notice:detail", args=[self.object.pk])
