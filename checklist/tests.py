from datetime import timedelta

from django.contrib import admin as django_admin
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, models, transaction
from django.db.models import ProtectedError
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role
from checklist.admin import ChecklistRecordAdmin
from checklist.models import ChecklistItem, ChecklistRecord, DepartmentChecklistItem
from checklist.selectors import (
    get_checklist_status_for_user,
    get_today_checklist_items,
)
from checklist.services import (
    ChecklistActionNotAllowed,
    cancel_checklist_item,
    complete_checklist_item,
)
from core.factories import (
    DEFAULT_PASSWORD,
    BaseFixtureTestCase,
    create_department,
    create_user,
)
from core.models import Department, OperationalBaseModel


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

    def test_completion_uses_post_button_not_checkbox(self):
        """완료/취소는 checkbox 자동 전송이 아니라 POST 버튼이다. (P3-04 §10)

        POST form 자체는 P3-04 에서 추가되며(ChecklistCompletionViewTest 에서 검증),
        여기서는 checkbox 방식이 아님만 확인한다.
        """
        self._login("staff_skin")
        response = self.client.get(reverse("checklist:today"))
        self.assertNotContains(response, 'type="checkbox"')

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

    def test_record_admin_is_active_readonly(self):
        record_admin = ChecklistRecordAdmin(ChecklistRecord, django_admin.site)
        self.assertIn("is_active", record_admin.readonly_fields)


class ChecklistCompletionServiceTest(BaseFixtureTestCase):
    """complete/cancel service 확인. (P3-04 / CHECKLIST_TECH_SPEC §11)"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.today = timezone.localdate()
        cls.skin_a = create_user("qa_skin_a", role=Role.STAFF, department=cls.dept_skin)
        cls.skin_b = create_user("qa_skin_b", role=Role.STAFF, department=cls.dept_skin)
        cls.skin_leader = create_user(
            "qa_skin_leader", role=Role.TEAM_LEADER, department=cls.dept_skin
        )
        cls.skin_manager = create_user(
            "qa_skin_mgr", role=Role.MANAGER, department=cls.dept_skin
        )
        cls.skin_admin = create_user(
            "qa_skin_admin", role=Role.ADMIN, department=cls.dept_skin
        )
        cls.no_dept = create_user("qa_nodept3", role=Role.STAFF, department=None)
        cls.inactive_dept = create_department("폐과", is_active=False)
        cls.inactive_dept_user = create_user(
            "qa_inact", role=Role.STAFF, department=cls.inactive_dept
        )

        cls.item = ChecklistItem.objects.create(title="가 daily")
        cls.assign = DepartmentChecklistItem.objects.create(
            item=cls.item, department=cls.dept_skin
        )
        cls.treat_assign = DepartmentChecklistItem.objects.create(
            item=ChecklistItem.objects.create(title="나 daily"),
            department=cls.dept_treatment,
        )
        cls.inactive_item_assign = DepartmentChecklistItem.objects.create(
            item=ChecklistItem.objects.create(title="다 항목", is_active=False),
            department=cls.dept_skin,
        )
        cls.inactive_assign = DepartmentChecklistItem.objects.create(
            item=ChecklistItem.objects.create(title="라 daily"),
            department=cls.dept_skin,
            is_active=False,
        )
        cls.weekly_assign = DepartmentChecklistItem.objects.create(
            item=ChecklistItem.objects.create(
                title="마 weekly", frequency=ChecklistItem.Frequency.WEEKLY
            ),
            department=cls.dept_skin,
        )
        cls.monthly_assign = DepartmentChecklistItem.objects.create(
            item=ChecklistItem.objects.create(
                title="바 monthly", frequency=ChecklistItem.Frequency.MONTHLY
            ),
            department=cls.dept_skin,
        )

    def _get_record(self):
        return ChecklistRecord.objects.get(department_item=self.assign, date=self.today)

    # --- 완료 ---
    def test_first_complete_creates_record(self):
        record, changed = complete_checklist_item(
            user=self.skin_a, department_item=self.assign
        )
        self.assertTrue(changed)
        self.assertEqual(record.date, self.today)
        self.assertEqual(record.completed_by_id, self.skin_a.id)
        self.assertEqual(record.created_by_id, self.skin_a.id)
        self.assertEqual(record.updated_by_id, self.skin_a.id)
        self.assertTrue(record.is_active)
        self.assertIsNotNone(record.completed_at.tzinfo)
        self.assertEqual(ChecklistRecord.objects.count(), 1)

    def test_already_completed_is_idempotent(self):
        complete_checklist_item(user=self.skin_a, department_item=self.assign)
        record, changed = complete_checklist_item(
            user=self.skin_b, department_item=self.assign
        )
        self.assertFalse(changed)
        # 최초 수행자 정보 유지(덮어쓰지 않음)
        self.assertEqual(record.completed_by_id, self.skin_a.id)
        self.assertEqual(ChecklistRecord.objects.count(), 1)

    def test_recomplete_reactivates_same_record(self):
        rec1, _ = complete_checklist_item(user=self.skin_a, department_item=self.assign)
        cancel_checklist_item(user=self.skin_b, department_item=self.assign)
        rec2, changed = complete_checklist_item(
            user=self.skin_b, department_item=self.assign
        )
        self.assertTrue(changed)
        self.assertEqual(rec1.pk, rec2.pk)  # 같은 행 재사용
        rec2.refresh_from_db()
        self.assertTrue(rec2.is_active)
        self.assertEqual(rec2.completed_by_id, self.skin_b.id)  # 재완료자
        self.assertEqual(rec2.created_by_id, self.skin_a.id)  # 최초 생성자 유지
        self.assertEqual(rec2.updated_by_id, self.skin_b.id)
        self.assertEqual(ChecklistRecord.objects.count(), 1)

    # --- 취소 ---
    def test_cancel_deactivates_and_preserves_completion(self):
        complete_checklist_item(user=self.skin_a, department_item=self.assign)
        record, changed = cancel_checklist_item(
            user=self.skin_b, department_item=self.assign
        )
        self.assertTrue(changed)
        record.refresh_from_db()
        self.assertFalse(record.is_active)
        self.assertEqual(record.completed_by_id, self.skin_a.id)  # 원 완료자 보존
        self.assertIsNotNone(record.completed_at)  # 완료 시각 보존
        self.assertEqual(record.created_by_id, self.skin_a.id)
        self.assertEqual(record.updated_by_id, self.skin_b.id)  # 취소 사용자

    def test_cancel_without_record_is_noop(self):
        record, changed = cancel_checklist_item(
            user=self.skin_a, department_item=self.assign
        )
        self.assertIsNone(record)
        self.assertFalse(changed)
        self.assertEqual(ChecklistRecord.objects.count(), 0)

    def test_repeated_cancel_is_idempotent(self):
        complete_checklist_item(user=self.skin_a, department_item=self.assign)
        cancel_checklist_item(user=self.skin_b, department_item=self.assign)
        _, changed = cancel_checklist_item(
            user=self.skin_a, department_item=self.assign
        )
        self.assertFalse(changed)
        self.assertEqual(ChecklistRecord.objects.count(), 1)

    # --- 멱등/단일 레코드 ---
    def test_repeated_complete_keeps_single_record(self):
        for user in (self.skin_a, self.skin_b, self.skin_a):
            complete_checklist_item(user=user, department_item=self.assign)
        self.assertEqual(ChecklistRecord.objects.count(), 1)

    # --- 권한 (403) ---
    def test_all_roles_in_active_department_can_complete(self):
        for user in (self.skin_a, self.skin_leader, self.skin_manager, self.skin_admin):
            cancel_checklist_item(user=user, department_item=self.assign)  # 초기화
            record, changed = complete_checklist_item(
                user=user, department_item=self.assign
            )
            self.assertTrue(changed)
            self.assertEqual(record.completed_by_id, user.id)

    def test_other_department_forbidden(self):
        with self.assertRaises(PermissionDenied):
            complete_checklist_item(user=self.skin_a, department_item=self.treat_assign)
        with self.assertRaises(PermissionDenied):
            cancel_checklist_item(user=self.skin_a, department_item=self.treat_assign)

    def test_no_department_forbidden(self):
        with self.assertRaises(PermissionDenied):
            complete_checklist_item(user=self.no_dept, department_item=self.assign)

    def test_inactive_department_forbidden(self):
        with self.assertRaises(PermissionDenied):
            complete_checklist_item(
                user=self.inactive_dept_user, department_item=self.assign
            )

    # --- 처리 대상 아님 (도메인 예외) ---
    def test_inactive_assignment_not_allowed(self):
        with self.assertRaises(ChecklistActionNotAllowed):
            complete_checklist_item(user=self.skin_a, department_item=self.inactive_assign)

    def test_inactive_item_not_allowed(self):
        with self.assertRaises(ChecklistActionNotAllowed):
            complete_checklist_item(
                user=self.skin_a, department_item=self.inactive_item_assign
            )

    def test_weekly_not_allowed(self):
        with self.assertRaises(ChecklistActionNotAllowed):
            complete_checklist_item(user=self.skin_a, department_item=self.weekly_assign)

    def test_monthly_not_allowed(self):
        with self.assertRaises(ChecklistActionNotAllowed):
            complete_checklist_item(user=self.skin_a, department_item=self.monthly_assign)

    def test_target_date_param(self):
        yesterday = self.today - timedelta(days=1)
        record, _ = complete_checklist_item(
            user=self.skin_a, department_item=self.assign, target_date=yesterday
        )
        self.assertEqual(record.date, yesterday)

    # --- 팀 단위 행동 ---
    def test_team_flow_a_completes_b_cancels_and_recompletes(self):
        complete_checklist_item(user=self.skin_a, department_item=self.assign)  # A 완료
        cancel_checklist_item(user=self.skin_b, department_item=self.assign)  # B 취소
        record = self._get_record()
        self.assertFalse(record.is_active)
        self.assertEqual(record.completed_by_id, self.skin_a.id)  # 취소 후에도 A
        self.assertEqual(record.updated_by_id, self.skin_b.id)  # 취소자 B
        complete_checklist_item(user=self.skin_b, department_item=self.assign)  # B 재완료
        record.refresh_from_db()
        self.assertTrue(record.is_active)
        self.assertEqual(record.completed_by_id, self.skin_b.id)  # 재완료자 B
        self.assertEqual(ChecklistRecord.objects.count(), 1)  # 항상 1개


class ChecklistCompletionViewTest(BaseFixtureTestCase):
    """완료/취소 POST view 및 오늘 화면 버튼 확인. (P3-04)"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.skin_a = create_user("qa_v_skin_a", role=Role.STAFF, department=cls.dept_skin)
        cls.item_todo = ChecklistItem.objects.create(title="미완료 항목")
        cls.item_done = ChecklistItem.objects.create(title="완료 항목")
        cls.a_todo = DepartmentChecklistItem.objects.create(
            item=cls.item_todo, department=cls.dept_skin, sort_order=0
        )
        cls.a_done = DepartmentChecklistItem.objects.create(
            item=cls.item_done, department=cls.dept_skin, sort_order=1
        )
        cls.treat_assign = DepartmentChecklistItem.objects.create(
            item=ChecklistItem.objects.create(title="치료실 항목"),
            department=cls.dept_treatment,
        )
        cls.inactive_item_assign = DepartmentChecklistItem.objects.create(
            item=ChecklistItem.objects.create(title="비활성 항목", is_active=False),
            department=cls.dept_skin,
        )

    def _login(self, username):
        self.client.login(username=username, password=DEFAULT_PASSWORD)

    def _complete_url(self, assign):
        return reverse("checklist:complete", args=[assign.pk])

    def _cancel_url(self, assign):
        return reverse("checklist:cancel", args=[assign.pk])

    def test_anonymous_post_redirects_login(self):
        response = self.client.post(self._complete_url(self.a_todo))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_complete_get_is_405(self):
        self._login("qa_v_skin_a")
        response = self.client.get(self._complete_url(self.a_todo))
        self.assertEqual(response.status_code, 405)

    def test_cancel_get_is_405(self):
        self._login("qa_v_skin_a")
        response = self.client.get(self._cancel_url(self.a_todo))
        self.assertEqual(response.status_code, 405)

    def test_complete_post_redirects_to_today(self):
        self._login("qa_v_skin_a")
        response = self.client.post(self._complete_url(self.a_todo))
        self.assertRedirects(response, reverse("checklist:today"))

    def test_cancel_post_redirects_to_today(self):
        self._login("qa_v_skin_a")
        self.client.post(self._complete_url(self.a_todo))
        response = self.client.post(self._cancel_url(self.a_todo))
        self.assertRedirects(response, reverse("checklist:today"))

    def test_today_shows_complete_and_cancel_buttons(self):
        self._login("qa_v_skin_a")
        self.client.post(self._complete_url(self.a_done))  # a_done 완료 상태로
        response = self.client.get(reverse("checklist:today"))
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertContains(response, 'action="%s"' % self._complete_url(self.a_todo))
        self.assertContains(response, 'action="%s"' % self._cancel_url(self.a_done))

    def test_post_changes_completion_state(self):
        self._login("qa_v_skin_a")
        self.assertFalse(
            ChecklistRecord.objects.filter(
                department_item=self.a_todo, is_active=True
            ).exists()
        )
        self.client.post(self._complete_url(self.a_todo))
        self.assertTrue(
            ChecklistRecord.objects.filter(
                department_item=self.a_todo, date=timezone.localdate(), is_active=True
            ).exists()
        )

    def test_other_department_post_is_403(self):
        self._login("qa_v_skin_a")
        response = self.client.post(self._complete_url(self.treat_assign))
        self.assertEqual(response.status_code, 403)

    def test_inactive_item_post_is_404(self):
        self._login("qa_v_skin_a")
        response = self.client.post(self._complete_url(self.inactive_item_assign))
        self.assertEqual(response.status_code, 404)


class _StatusDataMixin:
    """P3-05 현황 테스트 공통 데이터.

    치료실: daily 2개(1 완료) + 제외 대상(비활성 항목/배정, weekly, monthly).
    피부실: daily 1개(완료) → 모두 완료. 탕전실: daily 배정 0개 → 항목 없음.
    비활성부서(폐과): daily 1개(관리자 현황에서 제외). 정렬부서: 미완료 3개.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.today = timezone.localdate()
        cls.yesterday = cls.today - timedelta(days=1)
        cls.inactive_dept = create_department("폐과", is_active=False)
        cls.order_dept = create_department("정렬부서")

        cls.treat_leader = create_user(
            "qa_treat_leader", role=Role.TEAM_LEADER, department=cls.dept_treatment
        )
        cls.skin_leader = create_user(
            "qa_skin_leader", role=Role.TEAM_LEADER, department=cls.dept_skin
        )
        cls.order_leader = create_user(
            "qa_order_leader", role=Role.TEAM_LEADER, department=cls.order_dept
        )
        cls.nodept_leader = create_user(
            "qa_nodept_leader", role=Role.TEAM_LEADER, department=None
        )
        cls.inactive_leader = create_user(
            "qa_inact_leader", role=Role.TEAM_LEADER, department=cls.inactive_dept
        )
        cls.nodept_manager = create_user(
            "qa_nodept_mgr", role=Role.MANAGER, department=None
        )
        cls.nodept_admin = create_user(
            "qa_nodept_admin", role=Role.ADMIN, department=None
        )

        daily = ChecklistItem.Frequency.DAILY

        def item(title, frequency=daily, is_active=True):
            return ChecklistItem.objects.create(
                title=title, frequency=frequency, is_active=is_active
            )

        def assign(the_item, dept, sort_order=0, is_active=True):
            return DepartmentChecklistItem.objects.create(
                item=the_item, department=dept, sort_order=sort_order, is_active=is_active
            )

        def record(dci, is_active=True, date=None):
            return ChecklistRecord.objects.create(
                department_item=dci,
                date=date or cls.today,
                is_active=is_active,
                completed_at=timezone.now(),
            )

        # 치료실: t1 완료, t2 미완료 + 제외 대상들
        cls.t1 = assign(item("치료실 항목1"), cls.dept_treatment, sort_order=0)
        cls.t2 = assign(item("치료실 항목2"), cls.dept_treatment, sort_order=1)
        record(cls.t1)  # 오늘 완료
        record(cls.t2, date=cls.yesterday)  # 전날 기록 → 오늘 미완료
        record(cls.t2, is_active=False)  # 오늘 취소 기록 → 미완료
        assign(item("치료실 비활성항목", is_active=False), cls.dept_treatment)
        assign(item("치료실 비활성배정"), cls.dept_treatment, is_active=False)
        assign(
            item("치료실 weekly", frequency=ChecklistItem.Frequency.WEEKLY),
            cls.dept_treatment,
        )
        assign(
            item("치료실 monthly", frequency=ChecklistItem.Frequency.MONTHLY),
            cls.dept_treatment,
        )

        # 피부실: 1개 완료 → 모두 완료
        cls.s1 = assign(item("피부실 항목1"), cls.dept_skin, sort_order=0)
        record(cls.s1)

        # 탕전실: 배정 0개 (fixture dept_decoction, active)

        # 정렬부서: 미완료 3개(sort_order 2/0/1)
        cls.od_c = assign(item("정렬 C"), cls.order_dept, sort_order=2)
        cls.od_a = assign(item("정렬 A"), cls.order_dept, sort_order=0)
        cls.od_b = assign(item("정렬 B"), cls.order_dept, sort_order=1)

        # 비활성부서: daily 1개 (관리자 현황에서 제외되어야 함)
        assign(item("폐과 항목"), cls.inactive_dept)


class ChecklistStatusSelectorTest(_StatusDataMixin, BaseFixtureTestCase):
    """get_checklist_status_for_user 확인. (P3-05 / CHECKLIST_TECH_SPEC §13)"""

    def _by_dept(self, user):
        return {
            s.department.pk: s
            for s in get_checklist_status_for_user(user)
        }

    def test_team_leader_sees_only_own_department(self):
        statuses = get_checklist_status_for_user(self.treat_leader)
        self.assertEqual(len(statuses), 1)
        status = statuses[0]
        self.assertEqual(status.department.pk, self.dept_treatment.id)
        self.assertEqual(status.total_count, 2)
        self.assertEqual(status.completed_count, 1)
        self.assertEqual(status.remaining_count, 1)
        self.assertEqual(
            [a.item.title for a in status.missing_items], ["치료실 항목2"]
        )

    def test_manager_sees_all_active_departments_not_inactive(self):
        by_dept = self._by_dept(self.manager)
        self.assertIn(self.dept_treatment.id, by_dept)
        self.assertIn(self.dept_skin.id, by_dept)
        self.assertIn(self.dept_decoction.id, by_dept)
        self.assertIn(self.order_dept.id, by_dept)
        self.assertNotIn(self.inactive_dept.id, by_dept)

    def test_admin_sees_all_active_departments(self):
        by_dept = self._by_dept(self.admin)
        self.assertIn(self.dept_treatment.id, by_dept)
        self.assertNotIn(self.inactive_dept.id, by_dept)

    def test_nodept_manager_sees_all_active(self):
        by_dept = self._by_dept(self.nodept_manager)
        self.assertIn(self.dept_treatment.id, by_dept)
        self.assertIn(self.dept_skin.id, by_dept)

    def test_empty_department_included_with_zero(self):
        status = self._by_dept(self.manager)[self.dept_decoction.id]
        self.assertEqual(status.total_count, 0)
        self.assertEqual(status.remaining_count, 0)
        self.assertEqual(status.missing_items, ())

    def test_all_done_vs_empty_distinguished(self):
        by_dept = self._by_dept(self.manager)
        skin = by_dept[self.dept_skin.id]  # 모두 완료
        decoction = by_dept[self.dept_decoction.id]  # 항목 없음
        self.assertEqual(skin.total_count, 1)
        self.assertEqual(skin.remaining_count, 0)
        self.assertEqual(skin.missing_items, ())
        self.assertEqual(decoction.total_count, 0)

    def test_weekly_monthly_inactive_excluded_from_total(self):
        status = self._by_dept(self.manager)[self.dept_treatment.id]
        self.assertEqual(status.total_count, 2)  # daily 활성 2개만

    def test_yesterday_and_inactive_record_not_completed(self):
        status = self._by_dept(self.treat_leader)[self.dept_treatment.id]
        missing_pks = {a.pk for a in status.missing_items}
        self.assertIn(self.t2.pk, missing_pks)

    def test_missing_items_ordered_by_sort_order(self):
        status = get_checklist_status_for_user(self.order_leader)[0]
        self.assertEqual(
            [a.pk for a in status.missing_items],
            [self.od_a.pk, self.od_b.pk, self.od_c.pk],
        )

    def test_departments_ordered_by_name_pk(self):
        statuses = get_checklist_status_for_user(self.manager)
        expected = list(
            Department.objects.filter(is_active=True)
            .order_by("name", "pk")
            .values_list("pk", flat=True)
        )
        self.assertEqual([s.department.pk for s in statuses], expected)

    def test_staff_permission_denied(self):
        with self.assertRaises(PermissionDenied):
            get_checklist_status_for_user(self.staff_skin)

    def test_nodept_team_leader_permission_denied(self):
        with self.assertRaises(PermissionDenied):
            get_checklist_status_for_user(self.nodept_leader)

    def test_inactive_dept_team_leader_permission_denied(self):
        with self.assertRaises(PermissionDenied):
            get_checklist_status_for_user(self.inactive_leader)

    def test_selector_does_not_mutate_records(self):
        before = ChecklistRecord.objects.count()
        get_checklist_status_for_user(self.manager)
        self.assertEqual(ChecklistRecord.objects.count(), before)

    def test_query_count_at_most_three(self):
        with self.assertNumQueries(3):
            get_checklist_status_for_user(self.manager)


class ChecklistStatusViewTest(_StatusDataMixin, BaseFixtureTestCase):
    """/checklists/status/ 및 오늘 화면 현황 링크. (P3-05)"""

    def _login(self, username):
        self.client.login(username=username, password=DEFAULT_PASSWORD)

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(reverse("checklist:status"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_staff_is_403(self):
        self._login("staff_skin")
        self.assertEqual(self.client.get(reverse("checklist:status")).status_code, 403)

    def test_team_leader_ok_uses_status_template(self):
        self._login("qa_treat_leader")
        response = self.client.get(reverse("checklist:status"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "checklist/status.html")

    def test_manager_and_admin_ok(self):
        for username in ("manager", "admin", "qa_nodept_mgr"):
            self._login(username)
            self.assertEqual(
                self.client.get(reverse("checklist:status")).status_code, 200
            )

    def test_nodept_and_inactive_leader_403(self):
        for username in ("qa_nodept_leader", "qa_inact_leader"):
            self._login(username)
            self.assertEqual(
                self.client.get(reverse("checklist:status")).status_code, 403
            )

    def test_team_leader_sees_own_department_aggregation(self):
        self._login("qa_treat_leader")
        response = self.client.get(reverse("checklist:status"))
        self.assertContains(response, "치료실")
        self.assertContains(response, "미완료 항목")
        self.assertContains(response, "치료실 항목2")  # 미완료 항목 제목
        self.assertNotContains(response, "피부실 항목1")  # 다른 부서 미노출

    def test_manager_shows_all_done_and_empty_states(self):
        self._login("manager")
        response = self.client.get(reverse("checklist:status"))
        self.assertContains(response, "모든 체크리스트 항목을 완료했습니다.")
        self.assertContains(response, "등록된 daily 체크리스트 항목이 없습니다.")

    def test_status_page_has_no_action_form(self):
        self._login("manager")
        response = self.client.get(reverse("checklist:status"))
        self.assertNotContains(response, 'action="/checklists/')
        self.assertNotContains(response, 'type="checkbox"')

    def test_status_view_does_not_change_records(self):
        before = ChecklistRecord.objects.count()
        self._login("manager")
        self.client.get(reverse("checklist:status"))
        self.assertEqual(ChecklistRecord.objects.count(), before)

    def test_staff_today_has_no_status_link(self):
        self._login("staff_skin")
        response = self.client.get(reverse("checklist:today"))
        self.assertNotContains(response, reverse("checklist:status"))

    def test_team_leader_today_has_status_link(self):
        self._login("qa_treat_leader")
        response = self.client.get(reverse("checklist:today"))
        self.assertContains(response, reverse("checklist:status"))
