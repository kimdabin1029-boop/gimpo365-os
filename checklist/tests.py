from django.urls import reverse

from core.factories import DEFAULT_PASSWORD, BaseFixtureTestCase


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
