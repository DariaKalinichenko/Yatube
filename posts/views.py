from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm
from django.shortcuts import redirect
import datetime as dt
from django.core.paginator import Paginator

def index(request):
    post_list = Post.objects.select_related('author').order_by("-pub_date").all()
    paginator = Paginator(post_list, 10)  # показывать по 10 записей на странице.

    page_number = request.GET.get('page')  
    page = paginator.get_page(page_number)  
    return render(request, 'index.html', {'page': page, 'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)

    posts = Post.objects.filter(group=group).select_related('author').order_by("-pub_date")[:12]
    paginator = Paginator(posts,4)  
    page_number = request.GET.get('page')  
    page = paginator.get_page(page_number)  
    return render(request, "group.html", {"group": group, 'page': page, 'paginator': paginator})


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = dt.datetime.now()
            post.save()
            return redirect('index')
    form = PostForm()
    return render(request, 'new.html', {'form': form})


def profile(request, username):
    username = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=username).select_related('author').order_by("-pub_date").all()
    paginator = Paginator(posts, 4) 
    count = Post.objects.filter(author=username).select_related('author').count()
    page_number = request.GET.get('page')  
    page = paginator.get_page(page_number)

    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user).filter(author=username).select_related('author')
        if not following:
            following = None
        else:
            following = True
        return render(request, "profile.html", {'username': username, 'page': page, 'paginator': paginator, 'count': count, 'following': following})
    return render(request, "profile.html", {'username': username, 'page': page, 'paginator': paginator, 'count': count})


def post_view(request, username, post_id):
    username = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id)
    count = Post.objects.filter(author=username).select_related('author').count()
    items = Comment.objects.filter(post=post_id).select_related('author')
    form = CommentForm(request.POST)
    return render(request, "post.html", {'post': post, 'username': username, 'count': count, 'items':items, 'form':form})


@login_required
def post_edit(request, username, post_id):

    post = get_object_or_404(Post, pk=post_id)
    if request.user.username != post.author.username:
        return redirect('post', username, post_id)
    if request.method == "POST":
        form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = dt.datetime.now()
            post.save()
            return redirect('post', username, post_id)
    else:
        form = PostForm(instance=post)

    return render(request, "new.html", {'post':post,'form': form, 'username':username})

@login_required
def add_comment(request, post_id, username):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            form = form.save(commit=False)
            form.author = request.user
            form.post = post
            form.save()
            return redirect('post', username, post_id)
        return render(request, 'comments.html', {'form': form})
    return render(request, 'comments.html', {'form':form, 'post':post})


@login_required
def follow_index(request):
    """
    выведены посты авторов, на которых подписан текущий пользователь.
    """
    follows = Follow.objects.filter(user=request.user).values('author')
    following_list = Post.objects.filter(author_id__in=follows).select_related('author').order_by("-pub_date")
    paginator = Paginator(following_list, 10)  

    page_number = request.GET.get('page')  
    page = paginator.get_page(page_number)  
    return render(request, 'follow.html', {'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    """
    Подписаться на  автора
    """

    user = get_object_or_404(User, username=username)
    if request.user != user:
        Follow.objects.get_or_create(user=request.user, author=user)
        return redirect('profile', username)

    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    """
    Отписаться от автора

    """
    user = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user).filter(author=user).delete()
    return redirect('profile', username)


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)
