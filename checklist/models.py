from django.conf import settings
from django.db import models

from core.models import Department, OperationalBaseModel


class ChecklistItem(OperationalBaseModel):
    """체크리스트 업무 항목 정의. (P3-02 / CHECKLIST_TECH_SPEC §5)

    업무 문구(title)·반복 주기(frequency)·시기(timing)를 정의한다. 부서 FK·개인 담당자 FK 는 없다.
    created_at/updated_at/created_by/updated_by/is_active 는 OperationalBaseModel 상속.

    timing 은 항목 정의에 속한다. 같은 항목을 여러 부서에 배정하면 동일한 timing 을 쓰며,
    부서별로 시기가 다르면 별도 ChecklistItem 으로 정의한다. 별도의 시각(시·분) 입력 필드는
    두지 않고, 특정 시각·상황은 title 에 문구로 적는다(P3-07.5).
    """

    class Frequency(models.TextChoices):
        DAILY = "daily", "매일"
        WEEKLY = "weekly", "매주"
        MONTHLY = "monthly", "매월"

    class Timing(models.TextChoices):
        OPENING = "opening", "오픈"
        SPECIFIC = "specific", "특정 시점"
        CLOSING = "closing", "마감"

    title = models.CharField(max_length=200)
    frequency = models.CharField(
        max_length=20,
        choices=Frequency.choices,
        default=Frequency.DAILY,
    )
    timing = models.CharField(
        max_length=20,
        choices=Timing.choices,
        default=Timing.SPECIFIC,
    )

    class Meta:
        verbose_name = "체크리스트 항목"
        verbose_name_plural = "체크리스트 항목"
        ordering = ["title", "pk"]

    def __str__(self):
        return self.title


class DepartmentChecklistItem(OperationalBaseModel):
    """체크리스트 항목의 부서 배정. (P3-02 / CHECKLIST_TECH_SPEC §5)

    정의된 항목(item)을 어느 부서(department)가 수행할지 배정한다.
    같은 항목을 같은 부서에 중복 배정할 수 없다(UniqueConstraint). 다른 부서 배정은 허용.
    """

    item = models.ForeignKey(
        ChecklistItem,
        on_delete=models.PROTECT,
        related_name="department_assignments",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="checklist_assignments",
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "부서 체크리스트 배정"
        verbose_name_plural = "부서 체크리스트 배정"
        ordering = ["department_id", "sort_order", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["item", "department"],
                name="checklist_unique_item_department",
            ),
        ]

    def __str__(self):
        return f"{self.department.name} - {self.item.title}"


class ChecklistRecord(OperationalBaseModel):
    """부서 배정 항목의 날짜별 완료 기록. (P3-02 / CHECKLIST_TECH_SPEC §5·§11)

    한 부서 배정 항목(department_item)은 하루(date)에 레코드 하나만 갖는다(UniqueConstraint).
    완료 취소는 hard delete 가 아니라 is_active=False, 재완료는 기존 레코드 재활성화(P3-04).
    completed_by 는 실제 수행자이며, base 의 created_by(감사)와 의미가 다르다.

    date / completed_at 에 자동 기본값을 넣지 않는다. 날짜는 P3-04 service 가
    timezone.localdate() 로, completed_at 은 완료 시각으로 명시적으로 설정한다.
    """

    department_item = models.ForeignKey(
        DepartmentChecklistItem,
        on_delete=models.PROTECT,
        related_name="records",
    )
    date = models.DateField()
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_checklist_records",
    )
    completed_at = models.DateTimeField()

    class Meta:
        verbose_name = "체크리스트 완료 기록"
        verbose_name_plural = "체크리스트 완료 기록"
        ordering = ["-date", "department_item_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["department_item", "date"],
                name="checklist_unique_department_item_date",
            ),
        ]

    def __str__(self):
        return f"{self.date} - {self.department_item}"
