from django.urls import path
from . import views

urlpatterns = [
    # 学生端
    path("book/<int:book_id>/", views.book_detail, name="book_detail"),
    path("book/<int:book_id>/borrow/", views.borrow_book, name="borrow_book"),
    path("my-borrows/", views.my_borrows, name="my_borrows"),
    path("return/<int:record_id>/", views.return_book, name="return_book"),
    
    # 管理员仪表盘
    path("manage/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    
    # 图书管理
    path("manage/books/", views.admin_book_list, name="admin_book_list"),
    path("manage/books/add/", views.admin_book_add, name="admin_book_add"),
    path("manage/books/<int:book_id>/edit/", views.admin_book_edit, name="admin_book_edit"),
    path("manage/books/<int:book_id>/delete/", views.admin_book_delete, name="admin_book_delete"),
    
    # 分类管理
    path("manage/categories/", views.admin_category_list, name="admin_category_list"),
    path("manage/categories/<int:cat_id>/edit/", views.admin_category_edit, name="admin_category_edit"),
    path("manage/categories/<int:cat_id>/delete/", views.admin_category_delete, name="admin_category_delete"),
    
    # 借阅记录
    path("manage/borrows/", views.admin_borrow_records, name="admin_borrow_records"),
    path("manage/borrows/<int:record_id>/force-return/", views.admin_force_return, name="admin_force_return"),
    
    # 统计
    path("manage/statistics/", views.admin_statistics, name="admin_statistics"),
    
    # 用户管理
    path("manage/users/", views.admin_user_list, name="admin_user_list"),
]
