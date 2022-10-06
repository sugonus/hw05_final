from django.test import TestCase, Client
from http import HTTPStatus
from django.contrib.auth import get_user_model
from ..models import Post, Group


User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()
        user = URLTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(user)

    def test_not_authorized_url_available(self):
        """Страницы, доступные любому пользователю."""
        url_names = (
            '/',
            '/group/test-slug/',
            f'/posts/{URLTests.post.pk}/',
            '/profile/test-user/'
        )
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_only_available(self):
        """Страницы, доступные только авторизированному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_author_only_available(self):
        """Страницы, доступные только автору."""
        response = self.authorized_client.get(
            f'/posts/{URLTests.post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_anonymous(self):
        """Страницы перенаправляют анонимного пользователя."""
        user = User.objects.create_user(username='not-author')
        not_author = Client()
        not_author.force_login(user)
        url_names = (
            '/create/',
            f'/posts/{URLTests.post.pk}/edit/',
            f'/posts/{URLTests.post.pk}/comment/'
        )
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_redirect_not_author(self):
        """Страница перенаправляет не автора."""
        not_author = Client()
        not_author.force_login(User.objects.create_user(username='not-author'))
        response = not_author.get(f'/posts/{URLTests.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_404(self):
        "Запрос к несуществующей странице"
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names = {
            '/': 'posts/index.html/',
            '/group/test-slug/': 'posts/group_list.html/',
            '/posts/1/': 'posts/post_detail.html/',
            '/profile/test-user/': 'posts/profile.html/',
            '/posts/1/edit/': 'posts/create_post.html/',
            '/create/': 'posts/create_post.html/'
        }
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
