from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

from core.models import CreatedModel


User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        'Заголовок',
        help_text='Введите заголовок группы',
        max_length=200
    )
    slug = models.SlugField(
        'slug',
        unique=True
    )
    description = models.TextField(
        'Описание',
        help_text='Введите описание группы'
    )

    class Meta:
        verbose_name = 'group'
        verbose_name_plural = 'groups'

    def __str__(self):
        return self.title


class Post(CreatedModel):
    text = models.TextField(
        'Текст',
        help_text='Введите текст поста'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Выберите группу, к которой относится пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        verbose_name = 'post'
        verbose_name_plural = 'posts'
        ordering = ('-created',)

    def __str__(self) -> str:
        return self.text[:15]

    def get_absolute_url(self):
        return reverse("posts:post_detail", kwargs={"post_id": self.id})


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост',
        help_text='Выберите пост к которому принадлежит комментарий'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор'
    )
    text = models.TextField(
        'Текст',
        help_text='Введите текст комментария'
    )

    class Meta:
        verbose_name = 'comment'
        verbose_name_plural = 'comments'
        ordering = ('-created',)

    def __str__(self) -> str:
        return self.text[:10]
