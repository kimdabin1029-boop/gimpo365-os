from datetime import timedelta

from django.contrib import admin as django_admin
from django.db import IntegrityError, models, transaction
from django.db.models import ProtectedError
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role
from checklist.admin import ChecklistRecordAdmin
from checklist.models import ChecklistItem, ChecklistRecord, DepartmentChecklistItem
from checklist.selectors import get_today_checklist_items
from core.factories import (
    DEFAULT_PASSWORD,
    BaseFixtureTestCase,
    create_department,
    create_user,
)
from core.models import OperationalBaseModel


class ChecklistTodaySelectorTest(BaseFixtureTestCase):
    """get_today_checklist_items 계산 확인. (P3-03 / CHECKLIST_TECH_SPEC §9)

    조회 전용: 레코드를 생성/수정하지 않는다.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.today = timezone.localdate()
        cls.yesterday = cls.today - timedelta(days=1)
        cls.inactive_dept = create_department("폐과", is_active=False)
        cls.no_dept_user = create_user("qa_no_dept", role=Role.STAFF, department=None)
        cls.inactive_dept_user = create_user(
            "qa_inactive", role=Role.STAFF, department=cls.inactive_dept
        )

        daily = ChecklistItem.Frequency.DAILY
        weekly = ChecklistItem.Frequency.WEEKLY
        monthly = ChecklistItem.Frequency.MONTHLY

        def make_item(title, frequency=daily, is_active=True):
            return ChecklistItem.objects.create(
                title=title, frequency=frequency, is_active=is_active
            )

        cls.d1 = make_item("가 항목")
        cls.d2 = make_item("나 항목")
        cls.d3 = make_item("다 항목")
        cls.d4 = make_item("라 항목")
        cls.d_item_inactive = make_item("마 항목", is_active=False)
        cls.d_assign_inactive = make_item("바 항목")
        cls.wk = make_item("사 항목", frequency=weekly)
        cls.mo = make_item("아 항목", frequency=monthly)

        def assign(item, dept, sort_order=0, is_active=True):
            return DepartmentChecklistItem.objects.create(
                item=item, department=dept, sort_order=sort_order, is_active=is_active
            )

        cls.a1 = assign(cls.d1, cls.dept_skin, sort_order=1)
        cls.a2 = assign(cls.d2, cls.dept_skin, sort_order=0)
        cls.a3 = assign(cls.d3, cls.dept_skin, sort_order=2)
        cls.a4 = assign(cls.d4, cls.dept_skin, sort_order=3)
        assign(cls.d_item_inactive, cls.dept_skin)  # 항목 비활성 → 제외
        assign(cls.d_assign_inactive, cls.dept_skin, is_active=False)  # 배정 비활성 → 제외
        assign(cls.wk, cls.dept_skin)  # weekly → 제외
        assign(cls.mo, cls.dept_skin)  # monthly → 제외
        assign(cls.d1, cls.dept_treatment)  # 다른 부서 → skin 사용자에게 제외

        def record(assignment, date, is_active=True, completed_by=None):
            return ChecklistRecord.objects.create(
                department_item=assignment,
                date=date,
                is_active=is_active,
                completed_at=timezone.now(),
                completed_by=completed_by,
            )

        record(cls.a1, cls.today, completed_by=cls.staff_skin)  # a1 완료
        record(cls.a2, cls.today, is_active=False)  # a2 비활성 기록 → 미완료
        record(cls.a3, cls.yesterday)  # a3 어제 기록 → 오늘 미완료
        record(cls.a4, cls.today, completed_by=None)  # a4 완료(수행자 NULL)

    def _entries(self, user, target_date=None):
        return get_today_checklist_items(user, target_date=target_date)

    def _entry_map(self, user, target_date=None):
        return {e.department_item.pk: e for e in self._entries(user, target_date)}

    def test_no_department_user_empty(self):
        self.assertEqual(self._entries(self.no_dept_user), [])

    def test_inactive_department_user_empty(self):
        self.assertEqual(self._entries(self.inactive_dept_user), [])

    def test_only_own_department(self):
        depts = {e.department_item.department_id for e in self._entries(self.staff_skin)}
        self.assertEqual(depts, {self.dept_skin.id})

    def test_active_daily_assignments_only(self):
        titles = {e.department_item.item.title for e in self._entries(self.staff_skin)}
        self.assertEqual(titles, {"가 항목", "나 항목", "다 항목", "라 항목"})
        # 비활성 항목 / 비활성 배정 / weekly / monthly 제외
        for excluded in ("마 항목", "바 항목", "사 항목", "아 항목"):
            self.assertNotIn(excluded, titles)

    def test_ordering_by_sort_order_then_title(self):
        pks = [e.department_item.pk for e in self._entries(self.staff_skin)]
        self.assertEqual(pks, [self.a2.pk, self.a1.pk, self.a3.pk, self.a4.pk])

    def test_completed_when_today_active_record(self):
        self.assertTrue(self._entry_map(self.staff_skin)[self.a1.pk].is_completed)

    def test_yesterday_record_not_completed_today(self):
        self.assertFalse(self._entry_map(self.staff_skin)[self.a3.pk].is_completed)

    def test_inactive_record_not_completed(self):
        self.assertFalse(self._entry_map(self.staff_skin)[self.a2.pk].is_completed)

    def test_null_completed_by_still_completed(self):
        entry = self._entry_map(self.staff_skin)[self.a4.pk]
        self.assertTrue(entry.is_completed)
        self.assertIsNone(entry.record.completed_by)

    def test_target_date_param(self):
        entries = self._entry_map(self.staff_skin, target_date=self.yesterday)
        self.assertTrue(entries[self.a3.pk].is_completed)  # 어제 완료
        self.assertFalse(entries[self.a1.pk].is_completed)  # 어제 기준 미완료

    def test_selector_does_not_mutate_records(self):
        before = ChecklistRecord.objects.count()
        self._entries(self.staff_skin)
        self.assertEqual(ChecklistRecord.objects.count(), before)

    def test_query_count_is_two(self):
        with self.assertNumQueries(2):
            get_today_checklist_items(self.staff_skin, target_date=self.today)


class TodayChecklistViewTest(BaseFixtureTestCase):
    """오늘의 체크리스트 조회 화면 확인. (P3-03)"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.empty_dept = create_department("빈부서")
        cls.empty_dept_user = create_user(
            "qa_empty", role=Role.STAFF, department=cls.empty_dept
        )
        cls.no_dept_user = create_user("qa_no_dept2", role=Role.STAFF, department=None)
        cls.manager_treat = create_user(
            "qa_mgr_treat", role=Role.MANAGER, department=cls.dept_treatment
        )

        cls.item_done = ChecklistItem.objects.create(title="완료될 항목")
        cls.item_null = ChecklistItem.objects.create(title="수행자없음 항목")
        cls.item_todo = ChecklistItem.objects.create(title="미완료 항목")
        cls.item_treat = ChecklistItem.objects.create(title="치료실 항목")

        cls.a_done = DepartmentChecklistItem.objects.create(
            item=cls.item_done, department=cls.dept_skin, sort_order=0
        )
        cls.a_null = DepartmentChecklistItem.objects.create(
            item=cls.item_null, department=cls.dept_skin, sort_order=1
        )
        cls.a_todo = DepartmentChecklistItem.objects.create(
            item=cls.item_todo, department=cls.dept_skin, sort_order=2
        )
        cls.a_treat = DepartmentChecklistItem.objects.create(
            item=cls.item_treat, department=cls.dept_treatment
        )

        today = timezone.localdate()
        ChecklistRecord.objects.create(
            department_item=cls.a_done,
            date=today,
            completed_at=timezone.now(),
            completed_by=cls.staff_skin,
        )
        ChecklistRecord.objects.create(
            department_item=cls.a_null,
            date=today,
            completed_at=timezone.now(),
            completed_by=None,
        )

    def _login(self, username):
        self.client.login(username=username, password=DEFAULT_PASSWORD)

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(reverse("checklist:today"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_authenticated_uses_today_template(self):
        self._login("staff_skin")
        response = self.client.get(reverse("checklist:today"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "checklist/today.html")

    def test_context_checklist_date_is_localdate(self):
        self._login("staff_skin")
        response = self.client.get(reverse("checklist:today"))
        self.assertEqual(response.context["checklist_date"], timezone.localdate())
        self.assertEqual(response.context["total_count"], 3)
        self.assertEqual(response.context["completed_count"], 2)
        self.assertEqual(response.context["remaining_count"], 1)

    def test_shows_own_department_items_not_others(self):
        self._login("staff_skin")
        response = self.client.get(reverse("checklist:today"))
        self.assertContains(response, "완료될 항목")
        self.assertContains(response, "미완료 항목")
        self.assertNotContains(response, "치료실 항목")

    def test_shows_completed_and_uncompleted_status(self):
        self._login("staff_skin")
        response = self.client.get(reverse("checklist:today"))
        self.assertContains(response, "완료")
        self.assertContains(response, "미완료")

    def test_shows_completed_by(self):
        self._login("staff_skin")
        response = self.client.get(reverse("checklist:today"))
        self.assertContains(response, self.staff_skin.display_name)

    def test_null_completed_by_shows_placeholder_without_error(self):
        self._login("staff_skin")
        response = self.client.get(reverse("checklist:today"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "완료자 정보 없음")

    def test_no_department_user_sees_guidance(self):
        self._login("qa_no_dept2")
        response = self.client.get(reverse("checklist:today"))
        self.assertContains(response, "소속 부서가 설정되지 않아")

    def test_department_without_items_sees_empty_message(self):
        self._login("qa_empty")
        response = self.client.get(reverse("checklist:today"))
        self.assertContains(response, "오늘 등록된 체크리스트가 없습니다")

    def test_manager_sees_only_own_department(self):
        self._login("qa_mgr_treat")
        response = self.client.get(reverse("checklist:today"))
        self.assertContains(response, "치료실 항목")
        self.assertNotContains(response, "완료될 항목")

    def test_get_does_not_change_records(self):
        before = ChecklistRecord.objects.count()
        self._login("staff_skin")
        self.client.get(reverse("checklist:today"))
        self.assertEqual(ChecklistRecord.objects.count(), before)

    def test_no_complete_form_or_button(self):
        """완료/취소용 checkbox·form 이 없다(공통 navbar 의 로그아웃 form 은 무관). (P3-03 §6)"""
        self._login("staff_skin")
        response = self.client.get(reverse("checklist:today"))
        self.assertNotContains(response, 'type="checkbox"')
        self.assertNotContains(response, 'action="/checklists/')

    def test_home_card_still_preparing_and_no_sidebar_link(self):
        """OS 홈 카드 준비 중 유지 + sidebar 에 체크리스트 링크 없음. (P3-03 §8)"""
        self._login("staff_skin")
        home = self.client.get(reverse("home"))
        self.assertContains(home, 'disabled" href="%s"' % reverse("checklist:today"))
        page = self.client.get(reverse("checklist:today"))
        self.assertNotContains(page, 'class="sidebar-link" href="/checklists/"')
        self.assertNotContains(
            page, 'class="sidebar-link active" aria-current="page" href="/checklists/"'
        )


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
