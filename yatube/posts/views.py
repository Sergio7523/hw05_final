from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Follow, Group, Post, User
from .forms import CommentForm, PostForm
from .utils import get_page_context
from .constants import FIRST_30_TEXT_SYMBOLS


def index(request):
    page_obj = get_page_context(Post.objects.all(), request)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    page_obj = get_page_context(group.posts.all(), request)
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = User.objects.get(username=username)
    post_list = Post.objects.select_related('author').filter(author=author)
    posts_count = post_list.count()
    page_obj = get_page_context(post_list, request)
    following = False
    not_same_user = True
    if request.user.is_authenticated:
        if Follow.objects.filter(author=author, user=request.user).exists():
            following = True
        if request.user.get_username() == username:
            not_same_user = False
    context = {
        'posts_count': posts_count,
        'author': author,
        'page_obj': page_obj,
        'following': following,
        'not_same_user': not_same_user
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post_simbols_30 = post.text[:FIRST_30_TEXT_SYMBOLS]
    title = f'Пост {post_simbols_30}'
    comments = post.comments.all()
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'title': title,
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None,)

    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()
        return redirect('posts:profile', username=request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if request.user != post.author:
        return redirect('posts:post_detail', post.pk)

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.pk)

    return render(
        request,
        'posts/create_post.html',
        {'form': form, 'is_edit': is_edit}
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(
        author__following__user=request.user
    )
    page_obj = get_page_context(posts, request)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    if Follow.objects.filter(author=author, user=request.user).exists():
        return redirect('posts:profile', username)
    else:
        if request.user.get_username() != username:
            Follow.objects.create(
                user=request.user,
                author=User.objects.get(username=username)
            )
            return redirect('posts:profile', username)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = User.objects.get(username=username)
    Follow.objects.filter(author=author, user=request.user).delete()
    return redirect('posts:profile', username)
