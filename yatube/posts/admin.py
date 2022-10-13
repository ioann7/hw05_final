from django.contrib import admin
from django.conf import settings

from .models import Group, Post, Comment, Follow


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'created', 'author', 'group')
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('created',)
    empty_value_display = settings.ADMIN_EMPTY_VALUE_DISPLAY


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'author', 'post')
    search_fields = ('text',)
    empty_value_display = settings.ADMIN_EMPTY_VALUE_DISPLAY


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'author')


admin.site.register(Group)
