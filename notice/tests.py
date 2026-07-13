from datetime import timedelta

from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role
from core.factories import DEFAULT_PASSWORD, BaseFixtureTestCase, create_user
from core.models import OperationalBaseModel
from notice.models import Notice


class NoticeModelTest(BaseFixtureTestCase):
    """Notice 모델 필드·기본값·validation 확인. (P2-02)

    view/CRUD/첨부 테스트는 만들지 않는다. 모델 수준만 확인한다.
    """

    def test_basic_create(self):
        """제목/본문만으로 생성 가능하다."""
        notice = Notice.objects.create(title="공지", content="본문")
        self.assertEqual(notice.title, "공지")
        self.assertEqual(notice.content, "본문")

    def test_defaults(self):
        """status=draft / target_type=all / category=general / is_important=False / reference_url 빈값 / published_at None."""
        notice = Notice.objects.create(title="공지", content="본문")
        self.assertEqual(notice.status, Notice.Status.DRAFT)
        self.assertEqual(notice.target_type, Notice.TargetType.ALL)
        self.assertEqual(notice.category, Notice.Category.GENERAL)
        self.assertFalse(notice.is_important)
        self.assertEqual(notice.reference_url, "")
        self.assertIsNone(notice.published_at)

    def test_inherits_operational_base_model(self):
        """OperationalBaseModel 을 상속하고 공통 필드 5종을 가진다."""
        self.assertTrue(issubclass(Notice, OperationalBaseModel))
        field_names = {f.name for f in Notice._meta.get_fields()}
        for name in ("created_at", "updated_at", "created_by", "updated_by", "is_active"):
            self.assertIn(name, field_names)

    def test_is_active_default_true(self):
        """상속 필드 is_active 기본값은 True."""
        notice = Notice.objects.create(title="공지", content="본문")
        self.assertTrue(notice.is_active)

    def test_created_by_updated_by_nullable(self):
        """created_by / updated_by 는 지정 없이 생성 가능(null 허용)."""
        notice = Notice.objects.create(title="공지", content="본문")
        self.assertIsNone(notice.created_by)
        self.assertIsNone(notice.updated_by)

    def test_reference_url_can_be_blank(self):
        """reference_url 은 비워둘 수 있다(선택 입력)."""
        notice = Notice(title="공지", content="본문")
        notice.full_clean()  # 예외가 없어야 한다

    def test_all_with_department_is_invalid(self):
        """전체 공지에 대상 부서를 지정하면 validation error."""
        notice = Notice(
            title="공지",
            content="본문",
            target_type=Notice.TargetType.ALL,
            target_department=self.dept_skin,
        )
        with self.assertRaises(ValidationError):
            notice.full_clean()

    def test_department_without_target_is_invalid(self):
        """부서 대상 공지에 대상 부서가 없으면 validation error."""
        notice = Notice(
            title="공지",
            content="본문",
            target_type=Notice.TargetType.DEPARTMENT,
        )
        with self.assertRaises(ValidationError):
            notice.full_clean()

    def test_department_with_target_is_valid(self):
        """부서 대상 공지에 대상 부서가 있으면 통과한다."""
        notice = Notice(
            title="공지",
            content="본문",
            target_type=Notice.TargetType.DEPARTMENT,
            target_department=self.dept_skin,
        )
        notice.full_clean()  # 예외가 없어야 한다

    def test_category_has_no_important(self):
        """category choices 에 important 가 없다(중요 여부는 is_important 로만)."""
        values = {choice[0] for choice in Notice.Category.choices}
        self.assertNotIn("important", values)
        self.assertEqual(values, {"general", "operation", "education", "admin"})


class NoticeReadViewTest(BaseFixtureTestCase):
    """공지 목록/상세 조회 접근제어. (P2-03 / NOTICE_TECH_SPEC §8·§9)

    등록/수정/form/첨부 테스트는 만들지 않는다. 조회·접근제어만 확인한다.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # department 가 없는 일반 직원 (Phase 1.5: User.department nullable)
        cls.staff_no_dept = create_user(
            "staff_no_dept", role=Role.STAFF, department=None
        )

        cls.pub_all = Notice.objects.create(
            title="전체 게시", content="본문",
            status=Notice.Status.PUBLISHED, target_type=Notice.TargetType.ALL,
        )
        cls.pub_skin = Notice.objects.create(
            title="피부실 게시", content="본문",
            status=Notice.Status.PUBLISHED,
            target_type=Notice.TargetType.DEPARTMENT, target_department=cls.dept_skin,
        )
        cls.pub_treatment = Notice.objects.create(
            title="치료실 게시", content="본문",
            status=Notice.Status.PUBLISHED,
            target_type=Notice.TargetType.DEPARTMENT, target_department=cls.dept_treatment,
        )
        cls.manager_draft = Notice.objects.create(
            title="운영진 초안", content="본문",
            status=Notice.Status.DRAFT, target_type=Notice.TargetType.ALL,
            created_by=cls.manager,
        )
        cls.inactive = Notice.objects.create(
            title="비활성 게시", content="본문",
            status=Notice.Status.PUBLISHED, target_type=Notice.TargetType.ALL,
            is_active=False,
        )
        cls.important_ref = Notice.objects.create(
            title="중요 게시", content="본문",
            status=Notice.Status.PUBLISHED, target_type=Notice.TargetType.ALL,
            is_important=True, reference_url="https://drive.example.com/doc",
        )
        cls.staff_skin_own_draft = Notice.objects.create(
            title="본인 초안", content="본문",
            status=Notice.Status.DRAFT, target_type=Notice.TargetType.ALL,
            created_by=cls.staff_skin,
        )

    def _list_titles(self, username):
        self.client.login(username=username, password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("notice:list"))
        self.assertEqual(response.status_code, 200)
        return {n.title for n in response.context["notices"]}

    def _detail_status(self, username, notice):
        self.client.login(username=username, password=DEFAULT_PASSWORD)
        return self.client.get(reverse("notice:detail", args=[notice.pk])).status_code

    # --- URL / auth ---
    def test_list_anonymous_redirects_to_login(self):
        response = self.client.get(reverse("notice:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_list_authenticated_ok(self):
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("notice:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "notice/notice_list.html")

    def test_list_url_resolves(self):
        self.assertEqual(reverse("notice:list"), "/notices/")

    def test_detail_url_resolves(self):
        self.assertEqual(
            reverse("notice:detail", args=[self.pub_all.pk]),
            f"/notices/{self.pub_all.pk}/",
        )

    def test_home_card_links_to_list(self):
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("notice:list"))

    # --- 목록 접근제어 ---
    def test_staff_sees_published_all(self):
        self.assertIn("전체 게시", self._list_titles("staff_treatment"))

    def test_staff_does_not_see_draft(self):
        self.assertNotIn("운영진 초안", self._list_titles("staff_treatment"))

    def test_staff_does_not_see_inactive(self):
        self.assertNotIn("비활성 게시", self._list_titles("staff_treatment"))

    def test_staff_sees_own_department_notice(self):
        self.assertIn("피부실 게시", self._list_titles("staff_skin"))

    def test_staff_does_not_see_other_department_notice(self):
        self.assertNotIn("치료실 게시", self._list_titles("staff_skin"))

    def test_no_department_staff_sees_only_all(self):
        titles = self._list_titles("staff_no_dept")
        self.assertIn("전체 게시", titles)
        self.assertNotIn("피부실 게시", titles)
        self.assertNotIn("치료실 게시", titles)

    def test_manager_sees_draft_and_all_departments_but_not_inactive(self):
        titles = self._list_titles("manager")
        self.assertIn("운영진 초안", titles)
        self.assertIn("피부실 게시", titles)
        self.assertIn("치료실 게시", titles)
        self.assertNotIn("비활성 게시", titles)

    def test_admin_sees_draft(self):
        self.assertIn("운영진 초안", self._list_titles("admin"))

    def test_author_sees_own_draft(self):
        self.assertIn("본인 초안", self._list_titles("staff_skin"))

    def test_other_staff_does_not_see_someone_elses_draft(self):
        self.assertNotIn("본인 초안", self._list_titles("staff_treatment"))

    # --- 상세 접근제어 ---
    def test_detail_accessible_is_200(self):
        self.assertEqual(self._detail_status("staff_treatment", self.pub_all), 200)

    def test_detail_other_department_is_404(self):
        self.assertEqual(self._detail_status("staff_skin", self.pub_treatment), 404)

    def test_detail_draft_is_404_for_staff(self):
        self.assertEqual(self._detail_status("staff_treatment", self.manager_draft), 404)

    def test_detail_inactive_is_404(self):
        self.assertEqual(self._detail_status("staff_treatment", self.inactive), 404)

    def test_detail_manager_can_open_draft(self):
        self.assertEqual(self._detail_status("manager", self.manager_draft), 200)

    # --- 렌더링 ---
    def test_important_badge_shown_in_detail(self):
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("notice:detail", args=[self.important_ref.pk]))
        self.assertContains(response, "중요")

    def test_reference_url_shown_in_detail(self):
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("notice:detail", args=[self.important_ref.pk]))
        self.assertContains(response, "https://drive.example.com/doc")


class NoticeWriteViewTest(BaseFixtureTestCase):
    """공지 등록/수정 권한·서버측 필드·published_at 처리. (P2-04)

    삭제/첨부/읽음확인 테스트는 만들지 않는다.
    """

    def _login(self, username):
        self.client.login(username=username, password=DEFAULT_PASSWORD)

    def _form_data(self, **overrides):
        data = {
            "title": "새 공지",
            "content": "본문",
            "target_type": Notice.TargetType.ALL,
            "target_department": "",
            "status": Notice.Status.DRAFT,
            "category": Notice.Category.GENERAL,
            "reference_url": "",
        }
        data.update(overrides)
        return data

    def _make_notice(self, **kwargs):
        defaults = {
            "title": "기존 공지",
            "content": "본문",
            "created_by": self.admin,
            "updated_by": self.admin,
        }
        defaults.update(kwargs)
        return Notice.objects.create(**defaults)

    # --- 등록 접근 권한 ---
    def test_create_anonymous_redirects_to_login(self):
        resp = self.client.get(reverse("notice:create"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp.url)

    def test_create_staff_forbidden(self):
        self._login("staff_skin")
        self.assertEqual(self.client.get(reverse("notice:create")).status_code, 403)

    def test_create_team_leader_forbidden(self):
        self._login("team_leader_skin")
        self.assertEqual(self.client.get(reverse("notice:create")).status_code, 403)

    def test_create_manager_ok(self):
        self._login("manager")
        self.assertEqual(self.client.get(reverse("notice:create")).status_code, 200)

    # --- 등록 동작 ---
    def test_manager_can_create_and_redirects_to_detail(self):
        self._login("manager")
        resp = self.client.post(reverse("notice:create"), self._form_data(title="등록됨"))
        notice = Notice.objects.get(title="등록됨")
        self.assertRedirects(resp, reverse("notice:detail", args=[notice.pk]))

    def test_create_sets_created_and_updated_by(self):
        self._login("manager")
        self.client.post(reverse("notice:create"), self._form_data(title="작성자확인"))
        notice = Notice.objects.get(title="작성자확인")
        self.assertEqual(notice.created_by_id, self.manager.id)
        self.assertEqual(notice.updated_by_id, self.manager.id)

    def test_create_published_sets_published_at(self):
        self._login("manager")
        self.client.post(
            reverse("notice:create"),
            self._form_data(title="게시생성", status=Notice.Status.PUBLISHED),
        )
        notice = Notice.objects.get(title="게시생성")
        self.assertIsNotNone(notice.published_at)

    def test_create_draft_keeps_published_at_none(self):
        self._login("manager")
        self.client.post(
            reverse("notice:create"),
            self._form_data(title="초안생성", status=Notice.Status.DRAFT),
        )
        notice = Notice.objects.get(title="초안생성")
        self.assertIsNone(notice.published_at)

    # --- 수정 접근 권한 ---
    def test_update_staff_forbidden(self):
        notice = self._make_notice()
        self._login("staff_skin")
        self.assertEqual(
            self.client.get(reverse("notice:update", args=[notice.pk])).status_code, 403
        )

    def test_update_manager_ok(self):
        notice = self._make_notice()
        self._login("manager")
        self.assertEqual(
            self.client.get(reverse("notice:update", args=[notice.pk])).status_code, 200
        )

    def test_update_inactive_is_404(self):
        notice = self._make_notice(is_active=False)
        self._login("manager")
        self.assertEqual(
            self.client.get(reverse("notice:update", args=[notice.pk])).status_code, 404
        )

    # --- 수정 동작 ---
    def test_manager_can_update(self):
        notice = self._make_notice(title="원제목")
        self._login("manager")
        resp = self.client.post(
            reverse("notice:update", args=[notice.pk]),
            self._form_data(title="바뀐제목"),
        )
        self.assertRedirects(resp, reverse("notice:detail", args=[notice.pk]))
        notice.refresh_from_db()
        self.assertEqual(notice.title, "바뀐제목")

    def test_update_sets_updated_by_and_keeps_created_by(self):
        notice = self._make_notice(created_by=self.admin, updated_by=self.admin)
        self._login("manager")
        self.client.post(
            reverse("notice:update", args=[notice.pk]),
            self._form_data(title="기존 공지", content="바뀐본문"),
        )
        notice.refresh_from_db()
        self.assertEqual(notice.updated_by_id, self.manager.id)
        self.assertEqual(notice.created_by_id, self.admin.id)

    def test_update_draft_to_published_sets_published_at(self):
        notice = self._make_notice(status=Notice.Status.DRAFT)
        self.assertIsNone(notice.published_at)
        self._login("manager")
        self.client.post(
            reverse("notice:update", args=[notice.pk]),
            self._form_data(title="기존 공지", status=Notice.Status.PUBLISHED),
        )
        notice.refresh_from_db()
        self.assertIsNotNone(notice.published_at)

    def test_update_keeps_existing_published_at(self):
        original = timezone.now() - timedelta(days=3)
        notice = self._make_notice(status=Notice.Status.PUBLISHED, published_at=original)
        self._login("manager")
        self.client.post(
            reverse("notice:update", args=[notice.pk]),
            self._form_data(title="게시수정", status=Notice.Status.PUBLISHED),
        )
        notice.refresh_from_db()
        self.assertEqual(notice.published_at, original)

    def test_update_published_to_draft_keeps_published_at(self):
        original = timezone.now() - timedelta(days=3)
        notice = self._make_notice(status=Notice.Status.PUBLISHED, published_at=original)
        self._login("manager")
        self.client.post(
            reverse("notice:update", args=[notice.pk]),
            self._form_data(title="기존 공지", status=Notice.Status.DRAFT),
        )
        notice.refresh_from_db()
        self.assertEqual(notice.published_at, original)

    # --- form validation (target_type / target_department) ---
    def test_create_all_with_department_is_invalid(self):
        self._login("manager")
        resp = self.client.post(
            reverse("notice:create"),
            self._form_data(
                title="잘못1",
                target_type=Notice.TargetType.ALL,
                target_department=self.dept_skin.pk,
            ),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Notice.objects.filter(title="잘못1").exists())
        self.assertTrue(resp.context["form"].errors)

    def test_create_department_without_target_is_invalid(self):
        self._login("manager")
        resp = self.client.post(
            reverse("notice:create"),
            self._form_data(
                title="잘못2",
                target_type=Notice.TargetType.DEPARTMENT,
                target_department="",
            ),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Notice.objects.filter(title="잘못2").exists())
        self.assertTrue(resp.context["form"].errors)

    # --- 관리 버튼 노출 ---
    def test_manager_sees_manage_buttons(self):
        notice = self._make_notice(
            status=Notice.Status.PUBLISHED, target_type=Notice.TargetType.ALL
        )
        self._login("manager")
        list_resp = self.client.get(reverse("notice:list"))
        self.assertContains(list_resp, reverse("notice:create"))
        detail_resp = self.client.get(reverse("notice:detail", args=[notice.pk]))
        self.assertContains(detail_resp, reverse("notice:update", args=[notice.pk]))

    def test_staff_does_not_see_manage_buttons(self):
        notice = self._make_notice(
            status=Notice.Status.PUBLISHED, target_type=Notice.TargetType.ALL
        )
        self._login("staff_skin")
        list_resp = self.client.get(reverse("notice:list"))
        self.assertNotContains(list_resp, reverse("notice:create"))
        detail_resp = self.client.get(reverse("notice:detail", args=[notice.pk]))
        self.assertNotContains(detail_resp, reverse("notice:update", args=[notice.pk]))
