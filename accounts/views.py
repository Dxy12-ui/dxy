from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import User
from library.models import Book


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "用户名或密码错误")
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        if not username or not password:
            messages.error(request, "用户名和密码不能为空")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "用户名已存在")
        elif password != password2:
            messages.error(request, "两次密码输入不一致")
        elif len(password) < 6:
            messages.error(request, "密码长度至少6位")
        else:
            user = User.objects.create_user(username=username, password=password, role="student")
            messages.success(request, "注册成功，请登录")
            return redirect("login")
    return render(request, "register.html")


@login_required
def home(request):
    user = request.user
    search_query = request.GET.get("q", "").strip()
    books = Book.objects.all()
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    if user.role == "admin":
        return redirect("admin_dashboard")
    else:
        from django.core.paginator import Paginator
        paginator = Paginator(books.order_by("-create_time"), 20)
        page_number = request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)
        context = {
            "page_obj": page_obj,
            "search_query": search_query,
        }
        return render(request, "student/dashboard.html", context)


@login_required
def profile_view(request):
    return render(request, "profile.html")
