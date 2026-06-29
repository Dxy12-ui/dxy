from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import User


def login_view(request):
    if request.user.is_authenticated:
        return redirect("front_home")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_disabled:
                messages.error(request, "账号已被禁用，请联系管理员")
                return render(request, "login.html")
            login(request, user)
            messages.success(request, f"欢迎回来，{user.username}！")
            if user.role == "admin":
                return redirect("admin_dashboard")
            return redirect("front_home")
        else:
            messages.error(request, "用户名或密码错误")
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    messages.success(request, "已退出登录")
    return redirect("login")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("front_home")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        if not username or not password:
            messages.error(request, "用户名和密码不能为空")
        elif password != password2:
            messages.error(request, "两次密码输入不一致")
        elif len(password) < 6:
            messages.error(request, "密码长度至少6位")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "用户名已存在")
        else:
            user = User.objects.create_user(username=username, password=password, role="user")
            messages.success(request, "注册成功，请登录！")
            return redirect("login")
    return render(request, "register.html")


@login_required
def profile_view(request):
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "update_pwd":
            old_pwd = request.POST.get("old_password", "")
            new_pwd = request.POST.get("new_password", "")
            new_pwd2 = request.POST.get("new_password2", "")
            if not request.user.check_password(old_pwd):
                messages.error(request, "原密码错误")
            elif new_pwd != new_pwd2:
                messages.error(request, "两次新密码不一致")
            elif len(new_pwd) < 6:
                messages.error(request, "新密码长度至少6位")
            else:
                request.user.set_password(new_pwd)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "密码修改成功")
    return render(request, "profile.html")
