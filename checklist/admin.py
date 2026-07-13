from django.contrib import admin

from checklist.models import ChecklistItem, ChecklistRecord, DepartmentChecklistItem


class _AuditAdminMixin:
    """admin 에서 항목/배정 생성·수정 시 created_by/updated_by 를 기록한다. (P3-02 §8)

    checklist 앱 로컬 mixin 이며, 전역 admin 공통 리팩터링을 하지 않는다.
    """

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ChecklistItem)
class ChecklistItemAdmin(_AuditAdminMixin, admin.ModelAdmin):
    list_display = ["title", "frequency", "is_active", "updated_at"]
    list_filter = ["frequency", "is_active"]
    search_fields = ["title"]
    ordering = ["title"]


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
