from django.test import TestCase, Client


class CoreURLTest(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_page_404_uses_correct_template(self):
        """Проверка шаблона несуществующей страницы."""

        response = self.guest_client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')
