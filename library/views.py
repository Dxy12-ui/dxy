import json
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from .models import Category, Book, BorrowRecord
from accounts.models import User


# ==================== 权限装饰器 ====================

def student_required(view_func):
    """限制仅学生可访问"""
    def wrapper(request, *args, **kwargs):
        if request.user.role != "student":
            messages.error(request, "无权限访问")
            return redirect("home")
        return view_func(request, *args, **kwargs)
    return login_required(wrapper)


def admin_required(view_func):
    """限制仅管理员可访问"""
    def wrapper(request, *args, **kwargs):
        if request.user.role != "admin":
            messages.error(request, "无权限访问")
            return redirect("home")
        return view_func(request, *args, **kwargs)
    return login_required(wrapper)


# ==================== 学生端功能 ====================

@login_required
def book_detail(request, book_id):
    """图书详情页"""
    book = get_object_or_404(Book, id=book_id)
    # 检查当前用户是否已借此书且未归还
    has_borrowed = False
    if request.user.role == "student":
        has_borrowed = BorrowRecord.objects.filter(
            user=request.user, book=book, is_return=False
        ).exists()
    context = {
        "book": book,
        "has_borrowed": has_borrowed,
    }
    return render(request, "student/book_detail.html", context)


@student_required
def borrow_book(request, book_id):
    """借阅图书"""
    if request.method != "POST":
        return redirect("book_detail", book_id=book_id)
    
    book = get_object_or_404(Book, id=book_id)
    
    # 检查库存
    if book.stock <= 0:
        messages.error(request, "该书库存不足，无法借阅")
        return redirect("book_detail", book_id=book_id)
    
    # 检查是否已借此书
    already_borrowed = BorrowRecord.objects.filter(
        user=request.user, book=book, is_return=False
    ).exists()
    if already_borrowed:
        messages.error(request, "您已借阅此书，请先归还")
        return redirect("book_detail", book_id=book_id)
    
    # 检查单人最大借阅数量（默认5本）
    max_borrow = 5
    current_borrows = BorrowRecord.objects.filter(
        user=request.user, is_return=False
    ).count()
    if current_borrows >= max_borrow:
        messages.error(request, f"借阅已达上限（{max_borrow}本），请先归还部分图书")
        return redirect("book_detail", book_id=book_id)
    
    # 执行借阅
    book.stock -= 1
    book.save()
    BorrowRecord.objects.create(
        user=request.user,
        book=book,
        due_date=timezone.now() + timedelta(days=30),
    )
    messages.success(request, f"成功借阅《{book.title}》")
    return redirect("my_borrows")


@student_required
def my_borrows(request):
    """我的借阅列表"""
    records = BorrowRecord.objects.filter(user=request.user).order_by("-borrow_date")
    return render(request, "student/my_borrows.html", {"records": records, "current_time": timezone.now()})


@student_required
def return_book(request, record_id):
    """归还图书"""
    if request.method != "POST":
        return redirect("my_borrows")
    
    record = get_object_or_404(BorrowRecord, id=record_id, user=request.user, is_return=False)
    
    # 归还：库存+1，标记归还
    record.book.stock += 1
    record.book.save()
    record.is_return = True
    record.return_date = timezone.now()
    record.save()
    
    messages.success(request, f"成功归还《{record.book.title}》")
    return redirect("my_borrows")


@login_required
def profile_view(request):
    """个人信息查看"""
    return render(request, "profile.html")


# ==================== 管理员端功能 ====================

@admin_required
def admin_dashboard(request):
    """管理员仪表盘"""
    total_books = Book.objects.count()
    total_students = User.objects.filter(role="student").count()
    total_borrows = BorrowRecord.objects.count()
    active_borrows = BorrowRecord.objects.filter(is_return=False).count()
    
    # 库存不足图书（库存 <= 3）
    low_stock_books = Book.objects.filter(stock__lte=3).order_by("stock")
    
    # 热门图书 Top 10
    hot_books = Book.objects.annotate(
        borrow_count=Count("borrowrecord")
    ).order_by("-borrow_count")[:10]
    
    # 月度借阅趋势（最近6个月）
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_data = (
        BorrowRecord.objects.filter(borrow_date__gte=six_months_ago)
        .extra(select={"month": "strftime('%%Y-%%m', borrow_date)"})
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    
    context = {
        "total_books": total_books,
        "total_students": total_students,
        "total_borrows": total_borrows,
        "active_borrows": active_borrows,
        "low_stock_books": low_stock_books,
        "hot_books": hot_books,
        "monthly_data": list(monthly_data),
    }
    return render(request, "admin/dashboard.html", context)


@admin_required
def admin_book_list(request):
    """图书管理列表"""
    search_query = request.GET.get("q", "").strip()
    books = Book.objects.all()
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    paginator = Paginator(books.order_by("-create_time"), 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, "admin/book_list.html", {
        "page_obj": page_obj,
        "search_query": search_query,
        "categories": Category.objects.all(),
    })


@admin_required
def admin_book_add(request):
    """添加图书"""
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        author = request.POST.get("author", "").strip()
        category_id = request.POST.get("category")
        total_num = int(request.POST.get("total_num", 1))
        desc = request.POST.get("desc", "").strip()
        publish = request.POST.get("publish", "").strip()
        
        if not title or not author:
            messages.error(request, "书名和作者不能为空")
            return redirect("admin_book_add")
        
        category = None
        if category_id:
            category = get_object_or_404(Category, id=category_id)
        
        Book.objects.create(
            title=title,
            author=author,
            category=category,
            stock=total_num,
            total_num=total_num,
            desc=desc,
            publish=publish,
        )
        messages.success(request, "图书添加成功")
        return redirect("admin_book_list")
    
    categories = Category.objects.all()
    return render(request, "admin/book_form.html", {"categories": categories, "action": "添加"})


@admin_required
def admin_book_edit(request, book_id):
    """编辑图书"""
    book = get_object_or_404(Book, id=book_id)
    if request.method == "POST":
        book.title = request.POST.get("title", "").strip()
        book.author = request.POST.get("author", "").strip()
        category_id = request.POST.get("category")
        new_total = int(request.POST.get("total_num", book.total_num))
        diff = new_total - book.total_num
        book.total_num = new_total
        book.stock = book.stock + diff  # 库存同步调整
        book.desc = request.POST.get("desc", "").strip()
        book.publish = request.POST.get("publish", "").strip()
        
        if category_id:
            book.category = get_object_or_404(Category, id=category_id)
        else:
            book.category = None
        
        book.save()
        messages.success(request, "图书修改成功")
        return redirect("admin_book_list")
    
    categories = Category.objects.all()
    return render(request, "admin/book_form.html", {
        "book": book,
        "categories": categories,
        "action": "编辑",
    })


@admin_required
def admin_book_delete(request, book_id):
    """删除图书"""
    if request.method != "POST":
        return redirect("admin_book_list")
    book = get_object_or_404(Book, id=book_id)
    book.delete()
    messages.success(request, "图书已删除")
    return redirect("admin_book_list")


@admin_required
def admin_category_list(request):
    """分类管理"""
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            Category.objects.get_or_create(name=name)
            messages.success(request, "分类添加成功")
        return redirect("admin_category_list")
    
    categories = Category.objects.annotate(book_count=Count("book")).all()
    return render(request, "admin/category_list.html", {"categories": categories})


@admin_required
def admin_category_edit(request, cat_id):
    """编辑分类"""
    category = get_object_or_404(Category, id=cat_id)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            category.name = name
            category.save()
            messages.success(request, "分类修改成功")
        return redirect("admin_category_list")
    return redirect("admin_category_list")


@admin_required
def admin_category_delete(request, cat_id):
    """删除分类"""
    if request.method != "POST":
        return redirect("admin_category_list")
    category = get_object_or_404(Category, id=cat_id)
    category.delete()
    messages.success(request, "分类已删除")
    return redirect("admin_category_list")


@admin_required
def admin_borrow_records(request):
    """全校借阅记录"""
    records = BorrowRecord.objects.select_related("user", "book").all().order_by("-borrow_date")
    
    # 筛选
    status = request.GET.get("status", "")
    if status == "active":
        records = records.filter(is_return=False)
    elif status == "returned":
        records = records.filter(is_return=True)
    
    search = request.GET.get("q", "").strip()
    if search:
        records = records.filter(
            Q(user__username__icontains=search) |
            Q(book__title__icontains=search)
        )
    
    paginator = Paginator(records, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, "admin/borrow_records.html", {
        "page_obj": page_obj,
        "status": status, "search_query": search, "current_time": timezone.now(),
    })


@admin_required
def admin_force_return(request, record_id):
    """强制归还"""
    if request.method != "POST":
        return redirect("admin_borrow_records")
    
    record = get_object_or_404(BorrowRecord, id=record_id, is_return=False)
    record.book.stock += 1
    record.book.save()
    record.is_return = True
    record.return_date = timezone.now()
    record.save()
    messages.success(request, f"已强制归还《{record.book.title}》（借阅人：{record.user.username}）")
    return redirect("admin_borrow_records")


@admin_required
def admin_statistics(request):
    """借阅数据统计页面"""
    # 图书借阅热度
    hot_books = Book.objects.annotate(
        borrow_count=Count("borrowrecord")
    ).order_by("-borrow_count")[:20]
    
    hot_books_data = [
        {"title": b.title, "count": b.borrow_count} for b in hot_books
    ]
    
    # 学生借阅统计
    student_stats = User.objects.filter(role="student").annotate(
        borrow_count=Count("borrowrecord")
    ).order_by("-borrow_count")[:20]
    
    student_stats_data = [
        {"username": s.username, "count": s.borrow_count} for s in student_stats
    ]
    
    # 月度借阅趋势
    six_months_ago = timezone.now() - timedelta(days=180)
    monthly_data = (
        BorrowRecord.objects.filter(borrow_date__gte=six_months_ago)
        .extra(select={"month": "strftime('%%Y-%%m', borrow_date)"})
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    
    monthly_labels = [item["month"] for item in monthly_data]
    monthly_counts = [item["count"] for item in monthly_data]
    
    # 库存预警（库存 <= 3）
    low_stock = Book.objects.filter(stock__lte=3).order_by("stock")
    
    # 总借阅量
    total_borrow_count = BorrowRecord.objects.count()
    active_borrow_count = BorrowRecord.objects.filter(is_return=False).count()
    
    context = {
        "hot_books_json": json.dumps(hot_books_data, ensure_ascii=False),
        "student_stats_json": json.dumps(student_stats_data, ensure_ascii=False),
        "monthly_labels_json": json.dumps(monthly_labels),
        "monthly_counts_json": json.dumps(monthly_counts),
        "low_stock": low_stock,
        "total_borrow_count": total_borrow_count,
        "active_borrow_count": active_borrow_count,
    }
    return render(request, "admin/statistics.html", context)


@admin_required
def admin_user_list(request):
    """用户管理"""
    users = User.objects.filter(role="student").order_by("-create_time")
    paginator = Paginator(users, 20)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, "admin/user_list.html", {"page_obj": page_obj})

