import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.urls import reverse
from django.conf import settings
from django import forms
from ..models import Post, Group, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(ViewsTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html/',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html/',
            reverse(
                'posts:profile',
                kwargs={'username': 'test-user'}
            ): 'posts/profile.html/',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': '1'}
            ): 'posts/post_detail.html/',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}
            ): 'posts/create_post.html/',
            reverse('posts:post_create'): 'posts/create_post.html/'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_create_page_show_correct_context(self):
        """Шаблон view-функции post_create
        сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_field = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_field.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон view-функции post_edit
        сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': '1'}))
        form_field = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_field.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон view-функции post_detail
        сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': '1'})
        )
        object = response.context['post']
        post_detail_text = object.text
        post_detail_author = object.author
        self.assertEqual('Тестовый текст', post_detail_text)
        self.assertEqual(ViewsTests.user, post_detail_author)

    def test_specify_group_when_adding_post(self):
        """Если при создании поста указать группу,
        то пост появляется на страницах."""
        new_post = Post.objects.create(
            text='Тестовый текст',
            author=ViewsTests.user,
            group=ViewsTests.group
        )
        responses = (
            self.authorized_client.get(reverse('posts:index')),
            self.authorized_client.get(reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            )),
            self.authorized_client.get(reverse(
                'posts:profile',
                kwargs={'username': 'test-user'}
            ))
        )
        for response in responses:
            with self.subTest(response=response):
                response_post = response.context['page_obj'][0]
                self.assertEqual(response_post.text, new_post.text)

    def test_post_is_not_in_group_for_which_it_was_not_intended(self):
        """Проверка, что пост не попал в группу,
        для которой не был предназначен."""
        Group.objects.create(
            title='Тестовое название 2',
            slug='test-slug-2',
            description='Тестовое описание'
        )
        Post.objects.create(
            text='Тестовый текст',
            author=ViewsTests.user,
            group=ViewsTests.group
        )
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug-2'}
        ))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_image_context(self):
        """Проверяет, что при выводе поста с картинкой изображение
        передаётся в словаре context."""
        responses = (
            self.authorized_client.get('/'),
            self.authorized_client.get(reverse(
                'posts:profile',
                kwargs={'username': 'test-user'}
            )),
            self.authorized_client.get(reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ))
        )
        for response in responses:
            with self.subTest(response=response):
                gif = response.context['page_obj'][0].image
                self.assertEqual(gif, 'posts/small.gif')

    def test_post_detail_image_context(self):
        """Проверяет, что при выводе поста с картинкой на страницу post_detail
        изображение передаётся в словаре context."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': ViewsTests.post.pk}
        ))
        gif = response.context['post'].image
        self.assertEqual(gif, 'posts/small.gif')

    def test_cache_index(self):
        """Тестирование кеширования главной страницы."""
        post = Post.objects.create(
            text='Тест кеша',
            author=ViewsTests.user,
        )
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotContains(response, post)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertContains(response, post)

    def test_authorized_client_create_comment(self):
        """После успешной отправки комментарий появляется на странице поста,
        если пользователь был авторизован."""
        text = 'Тестовый комментарий'
        self.authorized_client.post(
            reverse('posts:add_comment', args=(f'{self.post.pk}')),
            data={'text': text},
            follow=True
        )
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            args=(f'{self.post.pk}')
        ))
        self.assertContains(response, text)

    def test_guest_client_create_comment(self):
        """После успешной отправки комментарий не появляется на странице поста,
        если пользователь не был авторизован."""
        text = 'Тестовый комментарий'
        self.guest_client.post(
            reverse('posts:add_comment', args=(f'{self.post.pk}')),
            data={'text': text},
            follow=True
        )
        response = self.guest_client.get(reverse(
            'posts:post_detail',
            args=(f'{self.post.pk}')
        ))
        self.assertNotContains(response, text)


class TestSubscriptions(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
        )

    def setUp(self):
        self.follower = User.objects.create_user(username='follower')
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)
        self.not_follower_client = Client()
        self.not_follower_client.force_login(
            User.objects.create_user(username='not-follower')
        )
        self.follower_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': TestSubscriptions.author}
        ))

    def test_authorized_user_can_subscribe(self):
        """Авторизованный пользователь может подписываться
        на других пользователей."""
        follower = Follow.objects.filter(
            user=self.follower,
            author=TestSubscriptions.author
        )
        self.assertTrue(follower.exists())

    def test_authorized_user_can_unsubscribe(self):
        """Авторизованный пользователь может отписываться
        от других пользователей."""
        self.follower_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': TestSubscriptions.author}
        ))
        follower = Follow.objects.filter(
            user=self.follower,
            author=TestSubscriptions.author
        )
        self.assertFalse(follower.exists())

    def test_new_user_post_appears_in_feed_of_those_who_follow(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан."""
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_new_user_post_dont_appear_in_feed_of_those_who_arent_follow(self):
        """Новая запись пользователя не появляется в ленте тех,
        кто на него не подписан."""
        response = self.not_follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_cant_follow_same_user_twice(self):
        """Нельзя подписаться на одного и того же пользователя дважды."""
        count_1 = len(Follow.objects.all())
        self.follower_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': TestSubscriptions.author}
        ))
        count_2 = len(Follow.objects.all())
        self.assertEqual(count_1, count_2)

    def test_cant_unfollow_someone_dont_follow(self):
        """Нельзя отписаться от того, на кого не подписан"""
        count_1 = len(Follow.objects.all())
        self.not_follower_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': TestSubscriptions.author}
        ))
        count_2 = len(Follow.objects.all())
        self.assertEqual(count_1, count_2)


class PaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.PAGE_TEST_OFFSET = 3
        for i in range(settings.NUMBER_OF_POSTS + cls.PAGE_TEST_OFFSET):
            Post.objects.create(
                text='Тестовый пост номер ' + str(i),
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        user = PaginatorViewsTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(user)

    def test_first_page_contains_num_records(self):
        """Количество постов на первой странице равно NUMBER_OF_POSTS."""
        responses = (
            self.authorized_client.get(reverse('posts:index')),
            self.authorized_client.get(reverse(
                'posts:profile',
                kwargs={'username': 'test-user'}
            )),
            self.authorized_client.get(reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ))
        )
        for response in responses:
            with self.subTest(response=response):
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.NUMBER_OF_POSTS
                )

    def test_second_page_contains_offset_records(self):
        """Количество постов на второй странице равно PAGE_TEST_OFFSET."""
        responses = (
            self.authorized_client.get(reverse('posts:index') + '?page=2'),
            self.authorized_client.get(reverse(
                'posts:profile',
                kwargs={'username': 'test-user'}
            ) + '?page=2'),
            self.authorized_client.get(reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'}
            ) + '?page=2')
        )
        for response in responses:
            with self.subTest(response=response):
                self.assertEqual(
                    len(response.context['page_obj']),
                    PaginatorViewsTests.PAGE_TEST_OFFSET
                )
