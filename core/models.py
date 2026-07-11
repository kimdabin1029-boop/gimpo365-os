from django.conf import settings
from django.db import models


class OperationalBaseModel(models.Model):
    """신규 운영 모듈이 공유하는 공통 abstract base model. (OS_TECH_SPEC §17)

    Notice / SOP·Manual / Request 등 신규 운영 모듈이 상속해
    created_at / updated_at / created_by / updated_by / is_active 를
    모듈마다 반복 선언하지 않도록 한다.

    abstract = True 이므로 자체 DB 테이블을 만들지 않는다. 이 모델 신설만으로는
    migration 이 발생하지 않으며, 실제 테이블은 이를 상속하는 구체 모델에서 생긴다.

    is_active 는 논리 삭제 또는 운영상 비활성을 뜻하며, 각 모듈의 게시 상태
    (예: Notice.status = draft/published)와 혼동하지 않는다.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_created_set",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_updated_set",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Department(models.Model):
    """부서. (TECH_SPEC §6.1)

    active_for_inventory=False 인 부서는 v0.1 재고관리 대상에서 제외된다.
    """

    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    active_for_inventory = models.BooleanField(default=True)
    memo = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "부서"
        verbose_name_plural = "부서"

    def save(self, *args, **kwargs):
        # 저장 전 name strip 정규화 (TECH_SPEC §6.1)
        if self.name:
            self.name = self.name.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
