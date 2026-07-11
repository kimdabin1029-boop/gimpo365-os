from django.contrib import admin

from notice.models import Notice


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    """Notice 기본 관리 화면. (P2-02)

    조회·필터·검색 중심의 최소 등록. custom action / 파일·첨부 기능은 두지 않는다.
    """

    list_display = (
        "title",
        "status",
        "target_type",
        "target_department",
        "category",
        "is_important",
        "is_active",
        "created_at",
    )
    list_filter = ("status", "target_type", "category", "is_important", "is_active")
    search_fields = ("title", "content")
    readonly_fields = ("created_at", "updated_at")
