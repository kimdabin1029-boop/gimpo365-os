from django.contrib import admin
from django.db.models import Prefetch

from checklist.models import ChecklistItem, ChecklistRecord, DepartmentChecklistItem


class _AuditAdminMixin:
    """admin 에서 항목/배정 생성·수정 시 created_by/updated_by 를 기록한다. (P3-02 §8)

    checklist 앱 로컬 mixin 이며, 전역 admin 공통 리팩터링을 하지 않는다.

    감사 4필드(created_by/updated_by/created_at/updated_at)는 읽기 전용으로 노출한다
    (사용자 선택 dropdown 금지). created_by/updated_by 실제 값은 save_model 이 현재
    로그인 관리자로 자동 기록한다: 신규는 둘 다, 수정은 updated_by 만 갱신한다(P3-07.5).
    """

    readonly_fields = ["created_by", "updated_by", "created_at", "updated_at"]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ChecklistItem)
class ChecklistItemAdmin(_AuditAdminMixin, admin.ModelAdmin):
    list_display = [
        "title",
        "frequency",
        "timing",
        "assigned_departments",
        "is_active",
        "updated_at",
    ]
    list_filter = ["frequency", "timing", "is_active"]
    search_fields = ["title"]
    ordering = ["title"]

    def get_queryset(self, request):
        # 목록의 배정 부서 표시를 위해 활성 배정(활성 부서)만 prefetch 한다.
        # 항목마다 별도 query 를 실행하지 않도록 to_attr 로 캐싱한다(N+1 방지). (P3-07.5)
        active_assignments = Prefetch(
            "department_assignments",
            queryset=DepartmentChecklistItem.objects.filter(
                is_active=True,
                department__is_active=True,
            )
            .select_related("department")
            .order_by("department__name", "department_id"),
            to_attr="active_department_assignments",
        )
        return super().get_queryset(request).prefetch_related(active_assignments)

    @admin.display(description="배정 부서")
    def assigned_departments(self, obj):
        # get_queryset 에서 prefetch 한 활성 배정만 사용한다(추가 query 없음).
        assignments = getattr(obj, "active_department_assignments", [])
        names = [a.department.name for a in assignments]
        return ", ".join(names) if names else "미배정"


@admin.register(DepartmentChecklistItem)
class DepartmentChecklistItemAdmin(_AuditAdminMixin, admin.ModelAdmin):
    list_display = ["item", "department", "sort_order", "is_active", "updated_at"]
    list_filter = ["department", "is_active"]
    search_fields = ["item__title", "department__name"]
    autocomplete_fields = ["item", "department"]


@admin.register(ChecklistRecord)
class ChecklistRecordAdmin(admin.ModelAdmin):
    """완료 기록은 OS service(P3-04)가 관리하는 운영 기록이다.

    admin 에서는 확인 전용: 신규 추가/삭제 금지, 모든 필드 읽기 전용.
    완료/취소의 정상 경로는 P3-04 의 OS 화면/service 다(is_active 포함 직접 수정 불가).
    """

    list_display = ["date", "department_item", "completed_by", "completed_at", "is_active"]
    list_filter = ["date", "is_active", "department_item__department"]
    search_fields = [
        "department_item__item__title",
        "department_item__department__name",
        "completed_by__username",
    ]
    readonly_fields = [
        "department_item",
        "date",
        "completed_by",
        "completed_at",
        "is_active",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
