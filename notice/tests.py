from django.core.exceptions import ValidationError
from django.urls import reverse

from core.factories import DEFAULT_PASSWORD, BaseFixtureTestCase
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


class NoticeListPlaceholderViewTest(BaseFixtureTestCase):
    """/notices/ 가 notice 앱 준비 중 화면으로 연결되는지 확인. (P2-01)"""

    def test_anonymous_redirects_to_login(self):
        """비로그인 사용자는 로그인 화면으로 리다이렉트된다."""
        response = self.client.get(reverse("notice:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_authenticated_shows_placeholder(self):
        """로그인 사용자는 공지사항 준비 중 화면을 200 으로 받는다."""
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("notice:list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "notice/notice_list_placeholder.html")
        self.assertContains(response, "공지사항")
        self.assertContains(response, "준비 중")

    def test_notice_list_resolves_to_notices_url(self):
        """reverse('notice:list') 가 /notices/ 로 resolve 된다."""
        self.assertEqual(reverse("notice:list"), "/notices/")

    def test_home_notice_card_links_to_notice_list(self):
        """OS 홈의 공지사항 카드가 notice:list 로 연결된다."""
        self.client.login(username="staff_skin", password=DEFAULT_PASSWORD)
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("notice:list"))
