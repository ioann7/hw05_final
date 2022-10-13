from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

from posts.models import Post, Group, Follow


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='PostModelTest')
        cls.group = Group.objects.create(
            title='Тест название',
            slug='test-slug',
            description='тест описание',
        )
        cls.post = Post.objects.create(
            text='тест: текст который больше 15 символов',
            author=cls.user,
            group=cls.group,
        )

    def test_models_have_correct_objects_names(self):
        """Проверяем Post.__str__ выводит ли первые 15 символом поля text."""
        post = PostModelTest.post
        expected_value = post.text[:15]
        self.assertEqual(str(post), expected_value)

    def test_verbose_name(self):
        """Проверяем verbose_name."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст',
            'created': 'Дата создания',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """Проверяем help_text."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу, к которой относится пост',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='тестовый заголовок',
            slug='test-slug',
            description='тестовое описание'
        )

    def test_models_have_correct_names(self):
        """Метод Group.__str__ выводит Group.title."""
        group = GroupModelTest.group
        expected_value = group.title
        self.assertEqual(str(group), expected_value)

    def test_verbose_name(self):
        """Проверяем verbose_name."""
        group = GroupModelTest.group
        field_verboses = {
            'title': 'Заголовок',
            'slug': 'slug',
            'description': 'Описание',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """Проверяем help_text."""
        group = GroupModelTest.group
        field_help_texts = {
            'title': 'Введите заголовок группы',
            'description': 'Введите описание группы',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).help_text, expected)


class FollowModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='follow_model_test_user1')
        self.user2 = User.objects.create_user(
            username='follow_model_test_user2')

    def test_unique_follow(self):
        follows_count = Follow.objects.count()
        Follow.objects.create(
            user=self.user1,
            author=self.user2
        )
        self.assertEqual(Follow.objects.count(), follows_count + 1)
        with self.assertRaises(IntegrityError):
            Follow.objects.create(
                user=self.user1,
                author=self.user2
            )

    def test_prevent_self_following(self):
        with self.assertRaises(IntegrityError):
            Follow.objects.create(
                user=self.user1,
                author=self.user1
            )
