from django.test import Client, TestCase


class ViewsTests(TestCase):
    def test_pages_uses_correct_template(self):
        """Страницы используют корректный шаблон."""
        guest_client = Client()
        response = guest_client.get('/unexisting-page/')
        template = 'core/404.html'
        self.assertTemplateUsed(response, template)
