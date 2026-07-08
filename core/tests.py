from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from core.factories import DEFAULT_PASSWORD, BaseFixtureTestCase
from core.models import Department


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


class ModulePlaceholderViewTest(BaseFixtureTestCase):
    """미구현 모듈 '준비 중' placeholder 화면 확인. (Phase 1 / P1-04)"""

    PLACEHOLDER_NAMES = [
        "notice_placeholder",
        "checklist_placeholder",
        "manual_placeholder",
        "request_placeholder",
        "schedule_placeholder",
    ]

    def test_anonymous_redirects_to_login(self):
        """비로그인 사용자는 로그인 화면으로 리다이렉트된다."""
        response = self.client.get(reverse("notice_placeholder"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_authenticated_shows_placeholder(self):
        """로그인 사용자는 준비 중 안내 화면을 200 으로 받는다."""
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("notice_placeholder"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/module_placeholder.html")
        self.assertContains(response, "준비 중")
        self.assertContains(response, "공지사항")

    def test_all_placeholders_render(self):
        """5개 placeholder URL 이 모두 준비 중 화면으로 연결된다."""
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
