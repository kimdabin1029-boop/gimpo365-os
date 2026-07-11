from django.urls import reverse

from core.factories import DEFAULT_PASSWORD, BaseFixtureTestCase


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
