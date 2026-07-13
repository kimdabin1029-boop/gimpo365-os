from django import forms

from notice.models import Notice


class NoticeForm(forms.ModelForm):
    """공지 등록/수정 폼. (P2-04)

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
