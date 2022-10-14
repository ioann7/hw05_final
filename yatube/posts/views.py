from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.core.exceptions import PermissionDenied

from .models import Post, Group, User, Follow
from .forms import CommentForm, PostForm
from .utils import get_posts_page_obj


@cache_page(20, key_prefix='index_page')
def index(request):
    posts = Post.objects.select_related('author', 'group')
    page_obj = get_posts_page_obj(request, posts)
    context = {
        'page_obj': page_obj,
        'index': True,
    }
    return render(request, 'posts/index.html', context)


@login_required
def follow_index(request):
    posts = Post.objects.filter(
        author__following__user=request.user
    ).select_related('author', 'group')
    page_obj = get_posts_page_obj(request, posts)
    context = {
        'page_obj': page_obj,
        'follow': True,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author').all()
    page_obj = get_posts_page_obj(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            user=request.user,
            author=author
        ).exists()
    else:
        is_following = False
    posts = author.posts.select_related('group').all()
    page_obj = get_posts_page_obj(request, posts)
    context = {
        'author': author,
        'posts_count': posts.count(),
        'page_obj': page_obj,
        'following': is_following,
    }
    return render(request, 'posts/profile.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    is_follow = Follow.objects.filter(
        user=request.user,
        author=author
    ).exists()
    if author == request.user or is_follow:
        raise PermissionDenied()
    Follow.objects.create(
        user=request.user,
        author=author
    )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    follow = get_object_or_404(
        Follow, user=request.user, author__username=username
    )
    follow.delete()
    return redirect('posts:profile', username)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related(
            'author',
            'group'
        ).prefetch_related(
            'comments'
        ), id=post_id)
    posts_count = post.author.posts.count()
    context = {
        'post': post,
        'posts_count': posts_count,
        'comment_form': CommentForm(),
        'comments': post.comments.all(),
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if request.method == 'POST' and form.is_valid():
        post_obj = form.save(commit=False)
        post_obj.author = request.user
        post_obj.save()
        return redirect('posts:profile', username=post_obj.author.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    instance = get_object_or_404(
        Post.objects.select_related('author', 'group'), id=post_id)
    if request.user != instance.author:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=instance
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect(instance)

    context = {
        'post_id': post_id,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(
        Post, id=post_id
    )
    form = CommentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect(post)
