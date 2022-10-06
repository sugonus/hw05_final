import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from ..models import Post, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestsForms(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.user = User.objects.create(username='test-user')
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            text='тест',
            author=self.user
        )

    def test_create_post(self):
        """При отправке валидной формы со страницы создания поста создаётся
        новая запись в базе данных."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст поста',
            'image': uploaded
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст поста',
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        """При отправке валидной формы со страницы редактирования поста
        происходит изменение поста в базе данных."""
        new_post = Post.objects.create(
            text='Тестовый текст поста до редактирования',
            author=self.user
        )
        form_data = {'text': 'Тестовый текст поста после редактирования'}
        self.authorized_client.post(
            reverse('posts:post_edit', args=(f'{new_post.pk}',)),
            data=form_data,
            follow=True
        )
        edited_post = Post.objects.get(pk=new_post.pk)
        self.assertNotEqual(new_post.text, edited_post.text)

    def test_create_comment(self):
        """После успешной отправки комментарий появляется на странице поста."""
        comments_count = Comment.objects.count()
        form_data = {'text': 'Тестовый комментарий'}
        self.authorized_client.post(
            reverse('posts:add_comment', args=(f'{self.post.pk}')),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
