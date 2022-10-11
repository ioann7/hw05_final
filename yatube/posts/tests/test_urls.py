from http import HTTPStatus

from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from posts.models import Group, Post


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='PostURLTests')
        cls.user_without_posts = User.objects.create_user(
            username='PostURLTests_another_user')
        cls.group = Group.objects.create(
            title='test title',
            slug='test-slug',
            description='test description'
        )
        cls.post = Post.objects.create(
            text='test text',
            author=cls.user,
            group=cls.group
        )
        cls.INDEX_URL = '/'
        cls.POST_URL = f'/posts/{cls.post.id}/'
        cls.POST_EDIT_URL = f'/posts/{cls.post.id}/edit/'
        cls.GROUP_URL = f'/group/{cls.group.slug}/'
        cls.PROFILE_URL = f'/profile/{cls.user.username}/'
        cls.CREATE_URL = '/create/'

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        self.authorized_client_without_posts = Client()
        self.authorized_client_without_posts.force_login(
            PostURLTests.user_without_posts)

    def test_guest_urls_exists_at_desired_location(self):
        """Страницы доступные любому пользователю."""
        urls = (
            self.INDEX_URL,
            self.GROUP_URL,
            self.PROFILE_URL,
            self.POST_URL,
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_desired_location(self):
        """
        Страница /posts/<post_id>/edit доступна
        для редактирования владельцу поста.
        """
        response = self.authorized_client.get(self.POST_EDIT_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_on_post_detail(self):
        """
        Страница /posts/<post_id>/edit перенаправляет
        пользователя если он не владелец поста.
        """
        response = self.authorized_client_without_posts.get(
            self.POST_EDIT_URL, follow=True)
        self.assertRedirects(response, self.POST_URL)

    def test_post_edit_url_redirect_anonymous_on_login_url(self):
        """
        Страница /posts/<post_id>/edit перенаправляет
        неавторизованного пользователя на страницу авторизации.
        """
        expected_url = f'/auth/login/?next={self.POST_EDIT_URL}'
        response = self.guest_client.get(self.POST_EDIT_URL, follow=True)
        self.assertRedirects(response, expected_url)

    def test_create_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get(self.CREATE_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirect_anonymous_on_login_url(self):
        """
        Страница /create/ перенаправляет неавторизованного
        пользователя на страницу авторизации.
        """
        response = self.guest_client.get(self.CREATE_URL)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_404_url(self):
        """Страница /unexisting_page/ выдаёт 404 ошибку."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_names_templates = {
            self.INDEX_URL: 'posts/index.html',
            self.GROUP_URL: 'posts/group_list.html',
            self.PROFILE_URL: 'posts/profile.html',
            self.POST_URL: 'posts/post_detail.html',
            self.POST_EDIT_URL: 'posts/create_post.html',
            self.CREATE_URL: 'posts/create_post.html',
        }
        for url, template in url_names_templates.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
