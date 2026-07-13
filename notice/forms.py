from django import forms
from django.db.models import Q

from core.models import Department
from notice.models import Notice


class NoticeForm(forms.ModelForm):
    """공지 등록/수정 폼. (P2-04, 라벨·위젯·부서 선택지 정리 P2-05)

    created_by / updated_by 는 view 에서 request.user 로, published_at 은 status 기준으로
    서버 측에서 설정하므로 폼에 노출하지 않는다. is_active(논리 삭제/비활성)도 제외한다.

    target_type / target_department 정합성은 Notice.clean() 이 form.is_valid() 단계에서
    검증한다(ModelForm 이 instance.full_clean() 을 호출).
    """

    class Meta:
        model = Notice
        fields = [
            "title",
            "content",
            "target_type",
            "target_department",
            "status",
            "is_important",
            "category",
            "reference_url",
        ]
        labels = {
            "title": "제목",
            "content": "내용",
            "target_type": "대상",
            "target_department": "대상 부서",
            "status": "게시 상태",
            "is_important": "중요 표시",
            "category": "분류",
            "reference_url": "외부 링크",
        }
        help_texts = {
            "target_department": "대상이 '부서'일 때만 선택합니다.",
            "reference_url": "구글드라이브, NAS, 외부 문서 링크가 있을 때 입력합니다.",
        }
        widgets = {
            "title": forms.TextInput(),
            "content": forms.Textarea(attrs={"rows": 8}),
            "reference_url": forms.URLInput(attrs={"placeholder": "https://..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 대상 부서 선택지는 활성 부서(is_active=True)만 노출한다.
        # 단, 수정 중인 공지가 이미 비활성 부서를 대상으로 갖고 있으면 현재 값이
        # 사라지지 않도록 그 부서는 선택지에 포함한다(폼이 깨지지 않게).
        current_department_id = getattr(self.instance, "target_department_id", None)
        department_filter = Q(is_active=True)
        if current_department_id:
            department_filter |= Q(pk=current_department_id)
        self.fields["target_department"].queryset = Department.objects.filter(
            department_filter
        )
