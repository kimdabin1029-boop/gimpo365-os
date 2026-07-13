"""config root URL. (TECH_SPEC §13)"""

from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("inventory/", include("inventory.urls")),
    path("notices/", include("notice.urls")),
    path("checklists/", include("checklist.urls")),
]

# 개발환경(DEBUG=True)에서 /static/ (Django Admin CSS/JS 포함)을 staticfiles finders
# 로 직접 서빙한다. collectstatic 없이 admin 정적 파일이 제공된다.
# 운영(DEBUG=False)에서는 추가되지 않으며, 별도 정적 파일 서빙(웹서버/콜렉트)을 사용한다.
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
