from django.test import TestCase, Client
from http import HTTPStatus


class URLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_404(self):
        "Запрос к несуществующей странице"
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
