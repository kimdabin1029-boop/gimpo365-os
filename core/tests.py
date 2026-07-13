from django.db import IntegrityError, connection, models, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from core.factories import DEFAULT_PASSWORD, BaseFixtureTestCase
from core.models import Department, OperationalBaseModel


class DepartmentModelTest(TestCase):
    def test_name_unique(self):
        """4.1 Department.name unique 테스트"""
        Department.objects.create(name="피부실")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Department.objects.create(name="피부실")

    def test_name_strip_normalization(self):
        """4.11 Department.name strip 정규화 테스트"""
        dept = Department.objects.create(name="  치료실  ")
        dept.refresh_from_db()
        self.assertEqual(dept.name, "치료실")

    def test_defaults(self):
        dept = Department.objects.create(name="데스크")
        self.assertTrue(dept.is_active)
        self.assertTrue(dept.active_for_inventory)
        self.assertEqual(dept.memo, "")


class OperationalBaseModelTest(TestCase):
    """공통 abstract base model 메타데이터 확인. (P2-01.5 / OS_TECH_SPEC §17)

    구체 모델·DB 테이블을 새로 만들지 않고 클래스 메타데이터 수준에서만 확인한다.
    """

    def test_is_abstract(self):
        """abstract = True 이어야 한다(자체 테이블 없음)."""
        self.assertTrue(OperationalBaseModel._meta.abstract)

    def test_has_expected_fields(self):
        """공통 필드 5종이 정의되어 있다."""
        field_names = {f.name for f in OperationalBaseModel._meta.get_fields()}
        for name in ("created_at", "updated_at", "created_by", "updated_by", "is_active"):
            self.assertIn(name, field_names)

    def test_user_fks_are_set_null_and_nullable(self):
        """created_by / updated_by 는 User 삭제 시 기록을 남기도록 SET_NULL·nullable 이다."""
        for name in ("created_by", "updated_by"):
            field = OperationalBaseModel._meta.get_field(name)
            self.assertTrue(field.null)
            self.assertEqual(field.remote_field.on_delete, models.SET_NULL)


class DatabaseEngineTest(TestCase):
    def test_test_database_is_postgresql(self):
        """SQLite 테스트 방지: 테스트 DB 가 PostgreSQL 인지 확인한다. (TECH_SPEC §15)"""
        self.assertEqual(connection.vendor, "postgresql")
        self.assertIn("postgresql", connection.settings_dict["ENGINE"])


class FixtureSetupTest(BaseFixtureTestCase):
    def test_departments_created(self):
        """기본 부서 fixture 생성 확인"""
        self.assertEqual(Department.objects.count(), 3)
        self.assertTrue(self.dept_skin.active_for_inventory)
        self.assertTrue(self.dept_treatment.active_for_inventory)
        self.assertFalse(self.dept_decoction.active_for_inventory)

    def test_users_created(self):
        """기본 사용자 fixture 생성 확인"""
        self.assertEqual(self.staff_skin.role, Role.STAFF)
        self.assertEqual(self.staff_skin.department, self.dept_skin)

        self.assertEqual(self.team_leader_skin.role, Role.TEAM_LEADER)
        self.assertEqual(self.team_leader_skin.department, self.dept_skin)

        self.assertEqual(self.staff_treatment.role, Role.STAFF)
        self.assertEqual(self.staff_treatment.department, self.dept_treatment)

        self.assertEqual(self.manager.role, Role.MANAGER)
        self.assertFalse(self.manager.is_staff)
        self.assertFalse(self.manager.is_superuser)

        self.assertEqual(self.admin.role, Role.ADMIN)
        self.assertTrue(self.admin.is_staff)
        self.assertTrue(self.admin.is_superuser)


class OSHomeViewTest(BaseFixtureTestCase):
    """OS 홈(루트 /) 동작 확인. (Phase 1 / P1-01)"""

    def test_anonymous_redirects_to_login(self):
        """비로그인 사용자는 로그인 화면으로 리다이렉트된다."""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_authenticated_shows_os_home(self):
        """로그인 사용자는 OS 홈 template 을 200 으로 받는다."""
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/os_home.html")
        self.assertContains(response, "김포365OS")

    def test_home_links_to_inventory(self):
        """재고관리 카드가 실제 inventory 진입 링크를 가진다."""
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("inventory:dashboard"))

    def test_home_shows_preparing_modules(self):
        """미구현 모듈은 '준비 중'으로 표시된다."""
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "준비 중")

    def test_sidebar_shows_inventory_under_operations(self):
        """사이드바에서 재고관리가 '운영관리' 그룹 아래에 보인다. (P1-03)

        OS 홈과 inventory 화면 모두에서 '운영관리' 구분선과 재고관리 링크가 함께 노출된다.
        """
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        for url in (reverse("home"), reverse("inventory:dashboard")):
            response = self.client.get(url)
            self.assertContains(response, "운영관리")
            self.assertContains(response, reverse("inventory:dashboard"))

    def test_home_notice_card_is_active_module(self):
        """공지사항 카드는 실사용 모듈로 표시된다(준비 중 아님). (P2-06)

        - notice:list 로 연결된다.
        - 실사용 설명 문구가 보인다.
        - '준비 중' 뱃지(os-badge soon)는 남은 4개 모듈만 가진다(공지 제외).
        """
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("notice:list"))
        self.assertContains(response, "직원이 확인해야 할 공지")
        self.assertContains(response, "os-badge soon", count=4)

    def test_home_keeps_other_modules_preparing(self):
        """체크리스트/SOP/요청/근태 카드는 여전히 준비 중이다. (P2-06 / P3-01)

        체크리스트는 P3-01 에서 checklist 앱으로 이관되었으나 카드는 여전히 준비 중(disabled) 상태다.
        """
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("home"))
        # 체크리스트 카드는 checklist 앱으로 연결되지만 disabled(준비 중) 상태 유지
        self.assertContains(response, 'disabled" href="%s"' % reverse("checklist:today"))
        for name in ("manual_placeholder", "request_placeholder", "schedule_placeholder"):
            self.assertContains(response, reverse(name))

    def test_sidebar_has_notice_link(self):
        """사이드바에 공지사항 링크가 노출된다. (P2-06)"""
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "공지사항")
        self.assertContains(response, reverse("notice:list"))

    def test_sidebar_notice_active_on_notice_page(self):
        """notice 화면에서 사이드바 공지사항 메뉴가 active 로 표시된다. (P2-06)"""
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("notice:list"))
        self.assertContains(
            response, 'aria-current="page" href="%s"' % reverse("notice:list")
        )


class ModulePlaceholderViewTest(BaseFixtureTestCase):
    """미구현 모듈 '준비 중' placeholder 화면 확인. (Phase 1 / P1-04)

    공지사항은 P2-01, 체크리스트는 P3-01 에서 각 앱으로 이관되어 여기서 제외한다
    (notice/tests.py, checklist/tests.py 참조).
    """

    PLACEHOLDER_NAMES = [
        "manual_placeholder",
        "request_placeholder",
        "schedule_placeholder",
    ]

    def test_anonymous_redirects_to_login(self):
        """비로그인 사용자는 로그인 화면으로 리다이렉트된다."""
        response = self.client.get(reverse("manual_placeholder"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_authenticated_shows_placeholder(self):
        """로그인 사용자는 준비 중 안내 화면을 200 으로 받는다."""
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("manual_placeholder"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/module_placeholder.html")
        self.assertContains(response, "준비 중")
        self.assertContains(response, "SOP/업무 매뉴얼")

    def test_all_placeholders_render(self):
        """남은 준비 중 placeholder URL 이 모두 준비 중 화면으로 연결된다."""
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        for name in self.PLACEHOLDER_NAMES:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "준비 중")

    def test_home_cards_link_to_placeholders(self):
        """OS 홈의 준비 중 카드가 각 placeholder URL 을 가리킨다."""
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("home"))
        for name in self.PLACEHOLDER_NAMES:
            self.assertContains(response, reverse(name))
