from datetime import timedelta

from django.contrib import admin as django_admin
from django.db import IntegrityError, models, transaction
from django.db.models import ProtectedError
from django.urls import reverse
from django.utils import timezone

from checklist.admin import ChecklistRecordAdmin
from checklist.models import ChecklistItem, ChecklistRecord, DepartmentChecklistItem
from core.factories import DEFAULT_PASSWORD, BaseFixtureTestCase, create_user
from core.models import OperationalBaseModel


class ChecklistPlaceholderViewTest(BaseFixtureTestCase):
    """/checklists/ 가 checklist 앱 준비 중 화면으로 연결되는지 확인. (P3-01)

    모델/selector/완료·취소/누락 현황 테스트는 만들지 않는다(P3-02 이후).
    """

    def test_anonymous_redirects_to_login(self):
        """비로그인 사용자는 로그인 화면으로 리다이렉트된다."""
        response = self.client.get(reverse("checklist:today"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_authenticated_shows_placeholder(self):
        """로그인 사용자는 체크리스트 준비 중 화면을 200 으로 받는다."""
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("checklist:today"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "checklist/checklist_placeholder.html")
        self.assertContains(response, "체크리스트")
        self.assertContains(response, "준비 중")

    def test_today_resolves_to_checklists_url(self):
        """reverse('checklist:today') 가 /checklists/ 로 resolve 된다."""
        self.assertEqual(reverse("checklist:today"), "/checklists/")

    def test_home_card_links_to_checklist_today(self):
        """OS 홈 체크리스트 카드가 checklist:today 로 연결된다."""
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("checklist:today"))

    def test_home_card_still_preparing(self):
        """OS 홈 체크리스트 카드는 여전히 준비 중(disabled) 상태다."""
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("home"))
        self.assertContains(
            response, 'disabled" href="%s"' % reverse("checklist:today")
        )

    def test_other_core_placeholders_still_work(self):
        """core 의 manuals/requests/schedules placeholder 는 그대로 동작한다."""
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        for name in ("manual_placeholder", "request_placeholder", "schedule_placeholder"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "준비 중")


class ChecklistItemModelTest(BaseFixtureTestCase):
    """ChecklistItem 모델 확인. (P3-02)"""

    def test_inherits_operational_base_model(self):
        self.assertTrue(issubclass(ChecklistItem, OperationalBaseModel))
        field_names = {f.name for f in ChecklistItem._meta.get_fields()}
        for name in ("created_at", "updated_at", "created_by", "updated_by", "is_active"):
            self.assertIn(name, field_names)

    def test_frequency_default_daily(self):
        item = ChecklistItem.objects.create(title="데스크 마감 정산 금액을 확인한다")
        self.assertEqual(item.frequency, ChecklistItem.Frequency.DAILY)

    def test_frequency_choices(self):
        values = {c[0] for c in ChecklistItem.Frequency.choices}
        self.assertEqual(values, {"daily", "weekly", "monthly"})

    def test_str_returns_title(self):
        item = ChecklistItem.objects.create(title="침구류를 정리한다")
        self.assertEqual(str(item), "침구류를 정리한다")

    def test_is_active_default_true(self):
        item = ChecklistItem.objects.create(title="온장고 전원을 끈다")
        self.assertTrue(item.is_active)


class DepartmentChecklistItemModelTest(BaseFixtureTestCase):
    """DepartmentChecklistItem 모델·제약 확인. (P3-02)"""

    def setUp(self):
        self.item = ChecklistItem.objects.create(title="냉난방 전원을 끈다")

    def test_fks_are_protect(self):
        self.assertEqual(
            DepartmentChecklistItem._meta.get_field("item").remote_field.on_delete,
            models.PROTECT,
        )
        self.assertEqual(
            DepartmentChecklistItem._meta.get_field("department").remote_field.on_delete,
            models.PROTECT,
        )

    def test_sort_order_default_zero(self):
        dci = DepartmentChecklistItem.objects.create(
            item=self.item, department=self.dept_skin
        )
        self.assertEqual(dci.sort_order, 0)

    def test_duplicate_item_department_blocked(self):
        DepartmentChecklistItem.objects.create(item=self.item, department=self.dept_skin)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                DepartmentChecklistItem.objects.create(
                    item=self.item, department=self.dept_skin
                )

    def test_duplicate_blocked_even_if_inactive(self):
        DepartmentChecklistItem.objects.create(
            item=self.item, department=self.dept_skin, is_active=False
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                DepartmentChecklistItem.objects.create(
                    item=self.item, department=self.dept_skin
                )

    def test_same_item_different_department_allowed(self):
        DepartmentChecklistItem.objects.create(item=self.item, department=self.dept_skin)
        # 다른 부서 배정은 허용
        DepartmentChecklistItem.objects.create(
            item=self.item, department=self.dept_treatment
        )
        self.assertEqual(self.item.department_assignments.count(), 2)

    def test_item_delete_protected(self):
        DepartmentChecklistItem.objects.create(item=self.item, department=self.dept_skin)
        with self.assertRaises(ProtectedError):
            self.item.delete()

    def test_department_delete_protected(self):
        DepartmentChecklistItem.objects.create(item=self.item, department=self.dept_skin)
        with self.assertRaises(ProtectedError):
            self.dept_skin.delete()


class ChecklistRecordModelTest(BaseFixtureTestCase):
    """ChecklistRecord 모델·제약 확인. (P3-02)"""

    def setUp(self):
        self.item = ChecklistItem.objects.create(title="데스크 마감 정산 금액을 확인한다")
        self.dci = DepartmentChecklistItem.objects.create(
            item=self.item, department=self.dept_skin
        )
        self.today = timezone.localdate()

    def _record(self, **kwargs):
        defaults = {
            "department_item": self.dci,
            "date": self.today,
            "completed_at": timezone.now(),
        }
        defaults.update(kwargs)
        return ChecklistRecord.objects.create(**defaults)

    def test_fks_on_delete(self):
        self.assertEqual(
            ChecklistRecord._meta.get_field("department_item").remote_field.on_delete,
            models.PROTECT,
        )
        self.assertEqual(
            ChecklistRecord._meta.get_field("completed_by").remote_field.on_delete,
            models.SET_NULL,
        )

    def test_completed_by_nullable(self):
        record = self._record()
        self.assertIsNone(record.completed_by)

    def test_completed_at_stores_now(self):
        record = self._record()
        self.assertIsNotNone(record.completed_at)

    def test_duplicate_department_item_date_blocked(self):
        self._record()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._record()

    def test_duplicate_blocked_even_if_inactive(self):
        self._record(is_active=False)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._record()

    def test_different_date_allowed(self):
        self._record()
        self._record(date=self.today - timedelta(days=1))
        self.assertEqual(self.dci.records.count(), 2)

    def test_department_item_delete_protected(self):
        self._record()
        with self.assertRaises(ProtectedError):
            self.dci.delete()

    def test_completed_by_user_delete_keeps_record_sets_null(self):
        user = create_user("qa_recorder", department=self.dept_skin)
        record = self._record(completed_by=user)
        user.delete()
        record.refresh_from_db()
        self.assertIsNone(record.completed_by)

    def test_inactive_record_preserved(self):
        record = self._record(is_active=False)
        record.refresh_from_db()
        self.assertFalse(record.is_active)


class ChecklistAdminTest(BaseFixtureTestCase):
    """admin 등록·제한 확인. (P3-02)"""

    def test_three_models_registered(self):
        for model in (ChecklistItem, DepartmentChecklistItem, ChecklistRecord):
            self.assertIn(model, django_admin.site._registry)

    def test_record_admin_add_and_delete_disabled(self):
        record_admin = ChecklistRecordAdmin(ChecklistRecord, django_admin.site)
        self.assertFalse(record_admin.has_add_permission(None))
        self.assertFalse(record_admin.has_delete_permission(None))
