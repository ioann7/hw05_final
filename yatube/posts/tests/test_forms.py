import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='PostFormTests')
        Post.objects.create(
            text='first test post',
            author=cls.user
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_create_post(self):
        """Валидная форма создаёт новый пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'test post',
            'group': '',
        }
        expected_redirect = reverse(
            'posts:profile',
            kwargs={'username': PostFormTests.user.username}
        )

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, expected_redirect)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=PostFormTests.user,
                group=None
            ).exists()
        )

    def create_post_with_image(self):
        """Валидная форма с картинкой создаёт запись в бд."""
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
            'text': 'test post',
            'group': '',
            'image': uploaded,
        }
        expected_redirect = reverse(
            'posts:profile',
            kwargs={'username': PostFormTests.user.username}
        )

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, expected_redirect)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=PostFormTests.user,
                group=None,
                image=uploaded
            ).exists()
        )

    def test_guest_cant_create_post(self):
        """Не авторизованный пользователь не может создать новый пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'test post',
            'group': '',
        }
        expected_redirect = f'{reverse(settings.LOGIN_URL)}?next=/create/'

        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, expected_redirect)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
                author=PostFormTests.user,
                group=None
            ).exists()
        )

    def test_post_edit(self):
        """Валидная форма изменяет пост с тем же id."""
        posts_count = Post.objects.count()
        post = Post.objects.first()
        url = reverse(
            'posts:post_edit',
            kwargs={'post_id': post.id}
        )
        form_data = {'text': 'edited post'}
        expected_redirect = reverse(
            'posts:post_detail',
            kwargs={'post_id': post.id}
        )

        response = self.authorized_client.post(
            url,
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, expected_redirect)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                id=post.id,
                text=form_data['text'],
                group=None
            )
        )

    def test_create_comment(self):
        """Валидная форма создаст комментарий у поста."""
        comments_count = Comment.objects.count()
        post = Post.objects.first()
        form_data = {'text': 'test comment'}
        expected_redirect = reverse(
            'posts:post_detail',
            kwargs={'post_id': post.id}
        )

        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, expected_redirect)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
                author=self.user,
                post=post
            ).exists()
        )

    def test_guest_cant_create_comment(self):
        """Не авторизованный пользователь не сможет создать комментарий."""
        comments_count = Comment.objects.count()
        post = Post.objects.first()
        form_data = {'text': 'test comment'}
        next_url = f'/posts/{post.id}/comment/'
        expected_redirect = f'{reverse(settings.LOGIN_URL)}?next={next_url}'

        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, expected_redirect)
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertFalse(
            Comment.objects.filter(
                text=form_data['text'],
                author=self.user,
                post=post
            ).exists()
        )
