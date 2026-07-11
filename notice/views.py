from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class NoticeListPlaceholderView(LoginRequiredMixin, TemplateView):
    """공지사항 준비 중 임시 화면. (P2-01)

    notice 앱이 /notices/ 라우트를 담당하도록 넘기는 전환 단계의 임시 view 다.
    입력 폼·데이터·저장 동작 없이 준비 중임을 안내한다.
    실제 목록(NoticeListView)은 모델 신설(P2-02) 이후 P2-03 에서 구현한다.
    """

    template_name = "notice/notice_list_placeholder.html"
