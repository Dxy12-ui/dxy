from django.urls import path
from . import views

urlpatterns = [
    # ========== 前台 ==========
    path("", views.front_home, name="front_home"),
    path("search/", views.plant_search, name="plant_search"),
    path("image-search/", views.plant_image_search, name="plant_image_search"),
    path("plant/<int:plant_id>/", views.plant_detail, name="plant_detail"),
    # 收藏
    path("plant/<int:plant_id>/collect/", views.plant_collect_toggle, name="plant_collect_toggle"),
    path("my-collections/", views.my_collections, name="my_collections"),
    # 搜索历史
    path("my-history/", views.my_history, name="my_history"),
    path("my-history/clear/", views.clear_history, name="clear_history"),
    # 纠错反馈
    path("plant/<int:plant_id>/feedback/", views.submit_feedback, name="submit_feedback"),
    path("my-feedbacks/", views.my_feedbacks, name="my_feedbacks"),

    # ========== 后台管理 ==========
    path("manage/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    # 植物管理
    path("manage/plants/", views.admin_plant_list, name="admin_plant_list"),
    path("manage/plants/add/", views.admin_plant_add, name="admin_plant_add"),
    path("manage/plants/<int:plant_id>/edit/", views.admin_plant_edit, name="admin_plant_edit"),
    path("manage/plants/<int:plant_id>/delete/", views.admin_plant_delete, name="admin_plant_delete"),
    path("manage/plants/<int:plant_id>/status/", views.admin_plant_status, name="admin_plant_status"),
    # 分类管理
    path("manage/categories/", views.admin_category_list, name="admin_category_list"),
    path("manage/categories/add/", views.admin_category_add, name="admin_category_add"),
    path("manage/categories/<int:cat_id>/edit/", views.admin_category_edit, name="admin_category_edit"),
    path("manage/categories/<int:cat_id>/delete/", views.admin_category_delete, name="admin_category_delete"),
    # 反馈审核
    path("manage/feedbacks/", views.admin_feedback_list, name="admin_feedback_list"),
    path("manage/feedbacks/<int:feedback_id>/review/", views.admin_feedback_review, name="admin_feedback_review"),
    # 用户管理
    path("manage/users/", views.admin_user_list, name="admin_user_list"),
    path("manage/users/<int:user_id>/disable/", views.admin_user_disable, name="admin_user_disable"),
    path("manage/users/<int:user_id>/reset-pwd/", views.admin_user_reset_pwd, name="admin_user_reset_pwd"),
    # 统计
    path("manage/statistics/", views.admin_statistics, name="admin_statistics"),
    # 操作日志
    path("manage/logs/", views.admin_operation_logs, name="admin_operation_logs"),
]
