import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Group, Post, Comment, Follow


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


class PostPagesTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='PostPagesTests')
        self.group = Group.objects.create(
            title='test group',
            slug='test-group',
            description='test-description'
        )
        self.group_without_posts = Group.objects.create(
            title='test group without posts',
            slug='test-group-without-posts',
            description='test description'
        )
        posts_count = 5
        for _ in range(posts_count):
            Post.objects.create(
                text='test post text with group',
                author=self.user,
                group=self.group
            )
        self.post = Post.objects.first()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.INDEX_URL = reverse('posts:index')
        self.GROUP_POSTS_URL = reverse(
            'posts:group_posts',
            kwargs={'slug': self.group.slug}
        )
        self.PROFILE_URL = reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        )
        self.POST_DETAIL_URL = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        )
        self.POST_EDIT_URL = reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id}
        )
        self.POST_CREATE_URL = reverse('posts:post_create')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_post_not_in_unrelated_group(self):
        """Пост не попадает в группу к которой не принадлежит."""
        url = reverse(
            'posts:group_posts',
            kwargs={'slug': 'test-group-without-posts'}
        )

        response = self.authorized_client.get(url)

        self.assertNotIn(self.post, response.context['page_obj'])

    def test_created_post_is_displayed(self):
        """
        Созданный пост отображается на шаблонах:
        index, group_posts, profile.
        """
        names_urls = {
            'index': self.INDEX_URL,
            'group_posts': self.GROUP_POSTS_URL,
            'profile': self.PROFILE_URL,
        }
        new_post = Post.objects.create(
            text='new post',
            author=self.user,
            group=self.group
        )
        for name, url in names_urls.items():
            with self.subTest(name=name):
                response = self.authorized_client.get(url)
                self.assertEqual(response.context['page_obj'][0], new_post)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        pages_names_template = {
            self.INDEX_URL: 'posts/index.html',
            self.GROUP_POSTS_URL: 'posts/group_list.html',
            self.PROFILE_URL: 'posts/profile.html',
            self.POST_DETAIL_URL: 'posts/post_detail.html',
            self.POST_EDIT_URL: 'posts/create_post.html',
            self.POST_CREATE_URL: 'posts/create_post.html',
        }
        for reverse_name, template in pages_names_template.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        first_post = Post.objects.first()

        response = self.authorized_client.get(self.INDEX_URL)
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_created_0 = first_object.created
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        group_title_0 = post_group_0.title
        group_slug_0 = post_group_0.slug
        group_description_0 = post_group_0.description

        self.assertEqual(post_text_0, first_post.text)
        self.assertEqual(post_created_0, first_post.created)
        self.assertEqual(post_author_0, self.user)
        self.assertEqual(post_group_0, self.group)
        self.assertEqual(group_title_0, first_post.group.title)
        self.assertEqual(group_slug_0, first_post.group.slug)
        self.assertEqual(group_description_0, first_post.group.description)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        expected_group = self.group

        response = self.authorized_client.get(self.GROUP_POSTS_URL)

        self.assertEqual(response.context['group'], expected_group)
        for post in response.context['page_obj']:
            self.assertEqual(post.group, expected_group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        expected_author = self.user
        expected_posts_count = self.user.posts.count()

        response = self.authorized_client.get(self.PROFILE_URL)

        self.assertEqual(response.context['author'], expected_author)
        self.assertEqual(response.context['posts_count'], expected_posts_count)
        for post in response.context['page_obj']:
            self.assertEqual(post.author, expected_author)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        expected_post = self.post
        expected_posts_count = self.post.author.posts.count()

        response = self.authorized_client.get(self.POST_DETAIL_URL)

        self.assertEqual(response.context['post'], expected_post)
        self.assertEqual(response.context['posts_count'], expected_posts_count)

    def test_create_post_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        response = self.authorized_client.get(self.POST_CREATE_URL)

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        expected_post_id = self.post.id

        response = self.authorized_client.get(self.POST_EDIT_URL)

        self.assertEqual(response.context['post_id'], expected_post_id)
        self.assertEqual(response.context['is_edit'], True)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_created_comment_is_displayed(self):
        """Созданный комментарий отображается на шаблоне post_detail."""
        new_comment = Comment.objects.create(
            author=self.user,
            post=self.post,
            text='test comment'
        )
        response = self.authorized_client.get(self.POST_DETAIL_URL)
        self.assertEqual(response.context['comments'][0], new_comment)

    def test_cached_index_page(self):
        """
        При удалении записи из базы, она остаётся в response.content
        главной страницы до тех пор, пока кэш не будет очищен принудительно.
        """
        post_text = 'cached_index_page_post'
        post = Post.objects.create(
            text=post_text,
            author=self.user
        )

        response_before_post_delete = self.client.get(self.INDEX_URL)
        post.delete()
        response_before_clear_cache = self.client.get(self.INDEX_URL)
        cache.clear()
        response_after_clear_cache = self.client.get(self.INDEX_URL)

        self.assertIn(post_text, str(response_before_post_delete.content))
        self.assertIn(post_text, str(response_before_clear_cache.content))
        self.assertNotIn(post_text, str(response_after_clear_cache.content))
        self.assertEqual(response_before_post_delete.content,
                         response_before_clear_cache.content)
        self.assertNotEqual(response_before_clear_cache,
                            response_after_clear_cache)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='test group',
            slug='test-group',
            description='test description group'
        )
        cls.user = User.objects.create_user(username='PaginatorViewsTest')
        cls.POSTS_COUNT = 15
        for _ in range(cls.POSTS_COUNT):
            Post.objects.create(
                text='test post',
                author=cls.user,
                group=cls.group
            )

        cls.INDEX_URL = reverse('posts:index')
        cls.GROUP_POSTS = reverse(
            'posts:group_posts',
            kwargs={'slug': cls.group.slug}
        )
        cls.PROFILE_URL = reverse(
            'posts:profile',
            kwargs={'username': cls.user.username}
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_first_page_contains_10_records(self):
        """
        Первая страница шаблонов:
        index, group_posts, profile отображает 10 постов.
        """
        names_urls = {
            'index': self.INDEX_URL,
            'group_posts': self.GROUP_POSTS,
            'profile': self.PROFILE_URL,
        }
        for name, url in names_urls.items():
            with self.subTest(name=name):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), settings.POSTS_PER_PAGE)

    def test_second_page_contains_5_records(self):
        """
        Вторая страница шаблонов:
        index, group_posts, profile отображает 5 постов.
        """
        names_urls = {
            'index': self.INDEX_URL + '?page=2',
            'group_posts': self.GROUP_POSTS + '?page=2',
            'profile': self.PROFILE_URL + '?page=2',
        }
        posts_on_second_page = self.POSTS_COUNT - settings.POSTS_PER_PAGE
        for name, url in names_urls.items():
            with self.subTest(name=name):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), posts_on_second_page)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostImageViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='PostImageViewsTest')
        cls.group = Group.objects.create(
            title='PostImageViewsTest',
            slug='post_image_views_test'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='some text',
            author=cls.user,
            group=cls.group,
            image=cls.image
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_images_show_in_context(self):
        """
        Изображение передаётся на страницы:
        index, group_posts, profile, post_detail.
        """
        urls = (
            reverse('posts:index'),
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ),
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            ),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                page_obj = response.context.get('page_obj', [None])
                post = page_obj[0] or response.context.get('post')
                self.assertIsNotNone(post.image)


class FollowViewsTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='follow_views_test_user1')
        self.user2 = User.objects.create_user(
            username='follow_views_test_user2')
        self.user3 = User.objects.create_user(
            username='follow_views_test_user3')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user1)
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(self.user3)

        self.FOLLOW_URL = reverse(
            'posts:profile_follow',
            kwargs={'username': self.user2.username}
        )
        self.UNFOLLOW_URL = reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user2.username}
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_authorized_user_can_follow(self):
        """Авторизованный пользователь может подписываться."""
        self.authorized_client.get(self.FOLLOW_URL)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user1,
                author=self.user2
            )
        )

    def test_authorized_user_can_unfollow(self):
        """Авторизованный пользователь может отписываться."""
        Follow.objects.create(
            user=self.user1,
            author=self.user2
        )
        self.authorized_client.get(self.UNFOLLOW_URL)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user1,
                author=self.user2
            )
        )

    def test_new_posts_displayed_to_followers(self):
        """
        Новый пост отображается у подписчиков
        и не отображается у не подписчиков.
        """
        Follow.objects.create(
            user=self.user1,
            author=self.user2
        )
        post = Post.objects.create(
            text='test post',
            author=self.user2
        )
        url = reverse('posts:follow_index')

        response_by_follow_user = self.authorized_client.get(url)
        response_by_unfollow_user = self.another_authorized_client.get(url)

        self.assertIn(post, response_by_follow_user.context['page_obj'])
        self.assertNotIn(post, response_by_unfollow_user.context['page_obj'])
