from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class ChecklistPlaceholderView(LoginRequiredMixin, TemplateView):
    """체크리스트 준비 중 임시 화면. (P3-01)

    checklist 앱이 /checklists/ 라우트를 담당하도록 넘기는 전환 단계의 임시 view 다.
    실제 항목·완료 상태·버튼 없이 준비 중임을 안내한다.
    실제 '오늘의 체크리스트'(TodayChecklistView)는 모델 신설(P3-02) 이후 P3-03 에서 구현한다.
    """

    template_name = "checklist/checklist_placeholder.html"
