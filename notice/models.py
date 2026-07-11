from django.core.exceptions import ValidationError
from django.db import models

from core.models import OperationalBaseModel


class Notice(OperationalBaseModel):
    """공지. (P2-02 / NOTICE_TECH_SPEC §5)

    core.OperationalBaseModel 에서 created_at / updated_at / created_by /
    updated_by / is_active 를 상속한다. 이 필드들을 여기서 반복 선언하지 않는다.

    is_active(논리 삭제·운영상 비활성)와 status(게시 상태 draft/published)는
    의미가 다르며 섞지 않는다.
    """

    class TargetType(models.TextChoices):
        ALL = "all", "전체"
        DEPARTMENT = "department", "부서"

    class Status(models.TextChoices):
        DRAFT = "draft", "임시저장"
        PUBLISHED = "published", "게시"

    class Category(models.TextChoices):
        GENERAL = "general", "일반"
        OPERATION = "operation", "운영"
        EDUCATION = "education", "교육"
        ADMIN = "admin", "행정"

    title = models.CharField(max_length=200)
    content = models.TextField()
    target_type = models.CharField(
        max_length=20,
        choices=TargetType.choices,
        default=TargetType.ALL,
    )
    target_department = models.ForeignKey(
        "core.Department",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="notices",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    is_important = models.BooleanField(default=False)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.GENERAL,
    )
    # 선택 입력 외부 링크(구글드라이브·NAS·외부 문서 등). 서버 fetch·미리보기·임베드 없음.
    # 첨부파일이 아니며 MEDIA 저장/백업과 무관하다. (NOTICE_TECH_SPEC §10)
    reference_url = models.URLField(blank=True, default="")
    # 게시 시각. 자동 설정 로직은 등록/수정 view 단계(P2-04 이후)에서 판단한다.
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "공지"
        verbose_name_plural = "공지"

    def __str__(self):
        return self.title

    def clean(self):
        """전체/부서 대상 정합성 검증. (NOTICE_TECH_SPEC §8)

        - 전체 공지(all)에는 대상 부서를 지정할 수 없다.
        - 부서 대상 공지(department)는 대상 부서가 반드시 있어야 한다.
        """
        super().clean()
        if self.target_type == self.TargetType.ALL and self.target_department_id:
            raise ValidationError(
                {"target_department": "전체 공지에는 대상 부서를 지정할 수 없습니다."}
            )
        if self.target_type == self.TargetType.DEPARTMENT and not self.target_department_id:
            raise ValidationError(
                {"target_department": "부서 대상 공지는 대상 부서가 필요합니다."}
            )
