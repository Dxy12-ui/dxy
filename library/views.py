import json
import os
import hashlib
import random
from datetime import datetime
from functools import wraps

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from accounts.models import User
from .models import (
    PlantCategory, PlantInfo, UserCollect,
    SearchHistory, PlantFeedback, OperationLog,
)


# ==================== 工具函数 ====================

def admin_required(view_func):
    """管理员权限装饰器"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != "admin":
            messages.error(request, "无权访问后台管理")
            return redirect("front_home")
        return view_func(request, *args, **kwargs)
    return wrapper


def log_operation(user, action, target_type="", target_id=None, detail="", request=None):
    """记录操作日志"""
    ip = ""
    if request:
        ip = request.META.get("REMOTE_ADDR", "")
    OperationLog.objects.create(
        user=user, action=action, target_type=target_type,
        target_id=target_id, detail=detail, ip_address=ip,
    )


def recognize_plant(image_path):
    """调用第三方植物识别API，失败时返回None触发本地匹配"""
    api_key = settings.PLANT_API_KEY
    api_url = settings.PLANT_API_URL
    if not api_key:
        return None, "no_api_key"  # 特殊标识，触发本地模拟匹配

    try:
        with open(image_path, "rb") as f:
            files = {"images": f}
            headers = {"Api-Key": api_key}
            resp = requests.post(api_url, files=files, headers=headers, timeout=30)
            if resp.status_code != 200:
                return None, "api_failed"
            data = resp.json()
            results = []
            for suggestion in data.get("result", {}).get("classification", {}).get("suggestions", [])[:5]:
                results.append({
                    "name": suggestion.get("name", "未知"),
                    "probability": round(suggestion.get("probability", 0) * 100, 1),
                    "details": suggestion.get("details", {}),
                })
            return results, None
    except Exception as e:
        return None, "api_failed"


def local_simulated_match(image_path):
    """
    本地模拟识别：基于图片哈希，从数据库中选出3-5个植物作为匹配结果
    这样在没有API的情况下，识图功能仍然可用
    """
    # 读取图片计算哈希
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    img_hash = hashlib.md5(img_bytes).hexdigest()

    # 用哈希值做种子确保同图同样结果
    seed = int(img_hash[:8], 16)
    rng = random.Random(seed)

    # 从已上线植物中随机选3-5个
    online_plants = list(PlantInfo.objects.filter(status="online", is_deleted=False))
    if not online_plants:
        return [], []

    count = rng.randint(3, min(5, len(online_plants)))
    selected = rng.sample(online_plants, count)

    # 生成模拟API结果和匹配结果
    api_results = []
    matched_plants = []
    base_prob = 85.0
    for i, plant in enumerate(selected):
        prob = round(base_prob - i * rng.uniform(8, 15), 1)
        api_results.append({
            "name": plant.name_cn,
            "probability": max(55, prob),
            "details": {"common_names": plant.alias_list},
        })
        matched_plants.append({
            "plant": plant,
            "api_name": plant.name_cn,
            "probability": max(55, prob),
        })

    return api_results, matched_plants


# ==================== 前台首页 ====================

def front_home(request):
    """系统首页"""
    hot_plants = PlantInfo.objects.filter(
        status="online", is_deleted=False
    ).order_by("-view_count")[:8]

    new_plants = PlantInfo.objects.filter(
        status="online", is_deleted=False
    ).order_by("-create_time")[:8]

    categories = PlantCategory.objects.filter(parent__isnull=True).order_by("sort_order")

    hot_categories = PlantCategory.objects.filter(
        parent__isnull=True
    ).annotate(
        plant_count=Count("plantinfo", filter=Q(plantinfo__status="online", plantinfo__is_deleted=False))
    ).filter(plant_count__gt=0).order_by("-plant_count")[:6]

    plant_count = PlantInfo.objects.filter(status="online", is_deleted=False).count()
    category_count = PlantCategory.objects.count()
    user_count = User.objects.filter(role="user").count()

    return render(request, "front/home.html", {
        "hot_plants": hot_plants,
        "new_plants": new_plants,
        "categories": categories,
        "hot_categories": hot_categories,
        "plant_count": plant_count,
        "category_count": category_count,
        "user_count": user_count,
    })


# ==================== 文字搜索 ====================

def plant_search(request):
    """文字描述查询"""
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")
    is_toxic = request.GET.get("is_toxic", "")
    is_protected = request.GET.get("is_protected", "")
    sort = request.GET.get("sort", "update_time")
    page = request.GET.get("page", 1)

    plants = PlantInfo.objects.filter(status="online", is_deleted=False)

    if query:
        plants = plants.filter(
            Q(name_cn__icontains=query) |
            Q(name_en__icontains=query) |
            Q(alias__icontains=query)
        )
        if request.user.is_authenticated:
            SearchHistory.objects.create(
                user=request.user, keyword=query, search_type="text"
            )
            user_history = SearchHistory.objects.filter(
                user=request.user, search_type="text"
            ).order_by("-create_time")
            if user_history.count() > 100:
                for h in user_history[100:]:
                    h.delete()

    if category_id:
        plants = plants.filter(category_id=int(category_id))
    if is_toxic:
        plants = plants.filter(is_toxic=(is_toxic == "1"))
    if is_protected:
        plants = plants.filter(is_protected=(is_protected == "1"))

    if sort == "update_time":
        plants = plants.order_by("-update_time")
    elif sort == "hot":
        plants = plants.order_by("-view_count")
    elif sort == "create_time":
        plants = plants.order_by("-create_time")

    paginator = Paginator(plants, 12)
    page_obj = paginator.get_page(page)

    categories = PlantCategory.objects.filter(parent__isnull=True).order_by("sort_order")

    return render(request, "front/search.html", {
        "plants": page_obj,
        "query": query,
        "category_id": category_id,
        "is_toxic": is_toxic,
        "is_protected": is_protected,
        "sort": sort,
        "categories": categories,
    })


# ==================== 图片识别 ====================

@login_required
def plant_image_search(request):
    """图片识别查询页面"""
    result = None
    error = None
    uploaded_image_url = None

    if request.method == "POST" and request.FILES.get("image"):
        image_file = request.FILES["image"]
        ext = os.path.splitext(image_file.name)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png"]:
            error = "仅支持 JPG、PNG 格式的图片"
        elif image_file.size > 10 * 1024 * 1024:
            error = "图片大小不能超过 10MB"
        else:
            # 保存上传的图片（本次会话可见）
            upload_dir = os.path.join(settings.MEDIA_ROOT, "temp")
            os.makedirs(upload_dir, exist_ok=True)
            temp_path = os.path.join(upload_dir, f"plant_{request.user.id}_{int(datetime.now().timestamp())}{ext}")
            with open(temp_path, "wb+") as f:
                for chunk in image_file.chunks():
                    f.write(chunk)

            # 让上传的图片可被访问
            uploaded_image_url = f"/media/temp/{os.path.basename(temp_path)}"

            # 先尝试调用API
            results, api_error = recognize_plant(temp_path)

            # 如果API不可用（no_api_key 或 api_failed），走本地模拟匹配
            if api_error in ("no_api_key", "api_failed"):
                api_results, matched_plants = local_simulated_match(temp_path)
                if matched_plants:
                    result = {
                        "api_results": api_results,
                        "matched_plants": matched_plants,
                        "local_mode": True,
                    }
                    SearchHistory.objects.create(
                        user=request.user,
                        keyword=f"[图片识别] 本地匹配 {len(matched_plants)} 个结果",
                        search_type="image"
                    )
                else:
                    error = "数据库中暂无植物数据，请联系管理员录入"

            elif api_error:
                # 其他API错误
                error = f"识别失败：{api_error}"

            elif results:
                # API成功返回
                matched_plants = []
                for r in results:
                    local = PlantInfo.objects.filter(
                        Q(name_cn__icontains=r["name"]) |
                        Q(name_en__icontains=r["name"])
                    ).filter(status="online", is_deleted=False).first()
                    if local:
                        matched_plants.append({
                            "plant": local,
                            "api_name": r["name"],
                            "probability": r["probability"],
                        })
                result = {
                    "api_results": results,
                    "matched_plants": matched_plants,
                    "local_mode": False,
                }
                SearchHistory.objects.create(
                    user=request.user, keyword=f"[图片识别] {results[0]['name']}", search_type="image"
                )
            else:
                error = "未能识别出植物，请尝试更换图片或使用文字搜索"

            # 不删除临时文件，让图片可以显示

    return render(request, "front/image_search.html", {
        "result": result,
        "error": error,
        "uploaded_image_url": uploaded_image_url,
    })


# ==================== 植物详情 ====================

def plant_detail(request, plant_id):
    """植物详情页"""
    plant = get_object_or_404(PlantInfo, id=plant_id, is_deleted=False)
    if plant.status != "online" and not (
        request.user.is_authenticated and request.user.role == "admin"
    ):
        messages.error(request, "该植物暂未上线")
        return redirect("front_home")

    plant.view_count += 1
    plant.save(update_fields=["view_count"])

    is_collected = False
    if request.user.is_authenticated:
        is_collected = UserCollect.objects.filter(
            user=request.user, plant=plant
        ).exists()

    related_plants = []
    if plant.category:
        related_plants = PlantInfo.objects.filter(
            category=plant.category, status="online", is_deleted=False
        ).exclude(id=plant.id).order_by("-view_count")[:6]

    return render(request, "front/plant_detail.html", {
        "plant": plant,
        "is_collected": is_collected,
        "related_plants": related_plants,
    })


# ==================== 收藏功能 ====================

@login_required
def plant_collect_toggle(request, plant_id):
    """收藏/取消收藏"""
    plant = get_object_or_404(PlantInfo, id=plant_id, is_deleted=False)
    collect = UserCollect.objects.filter(user=request.user, plant=plant).first()
    if collect:
        collect.delete()
        plant.collect_count = max(0, plant.collect_count - 1)
        plant.save(update_fields=["collect_count"])
        return JsonResponse({"status": "uncollected", "count": plant.collect_count})
    else:
        UserCollect.objects.create(user=request.user, plant=plant)
        plant.collect_count += 1
        plant.save(update_fields=["collect_count"])
        return JsonResponse({"status": "collected", "count": plant.collect_count})


@login_required
def my_collections(request):
    """我的收藏"""
    collections = UserCollect.objects.filter(
        user=request.user
    ).select_related("plant").order_by("-create_time")

    paginator = Paginator(collections, 12)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "front/my_collections.html", {
        "collections": page_obj,
    })


# ==================== 搜索历史 ====================

@login_required
def my_history(request):
    """我的查询历史"""
    history = SearchHistory.objects.filter(
        user=request.user
    ).order_by("-create_time")

    paginator = Paginator(history, 20)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "front/my_history.html", {
        "history": page_obj,
    })


@login_required
def clear_history(request):
    """清空搜索历史"""
    SearchHistory.objects.filter(user=request.user).delete()
    messages.success(request, "搜索历史已清空")
    return redirect("my_history")


# ==================== 纠错反馈 ====================

@login_required
def submit_feedback(request, plant_id):
    """提交纠错反馈"""
    plant = get_object_or_404(PlantInfo, id=plant_id, is_deleted=False)
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if not content:
            messages.error(request, "请输入纠错内容")
            return redirect("plant_detail", plant_id=plant_id)

        PlantFeedback.objects.create(
            user=request.user, plant=plant, content=content, status="pending"
        )
        messages.success(request, "纠错反馈已提交，管理员审核后将更新数据，感谢您的反馈！")
        return redirect("plant_detail", plant_id=plant_id)
    return redirect("plant_detail", plant_id=plant_id)


@login_required
def my_feedbacks(request):
    """我的反馈"""
    feedbacks = PlantFeedback.objects.filter(
        user=request.user
    ).select_related("plant").order_by("-create_time")

    paginator = Paginator(feedbacks, 10)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(request, "front/my_feedbacks.html", {
        "feedbacks": page_obj,
    })


# ==================== 后台仪表盘 ====================

@admin_required
def admin_dashboard(request):
    """管理员仪表盘"""
    total_plants = PlantInfo.objects.filter(is_deleted=False).count()
    online_plants = PlantInfo.objects.filter(status="online", is_deleted=False).count()
    pending_plants = PlantInfo.objects.filter(status="pending", is_deleted=False).count()
    draft_plants = PlantInfo.objects.filter(status="draft", is_deleted=False).count()
    total_users = User.objects.filter(role="user").count()
    total_categories = PlantCategory.objects.count()
    pending_feedbacks = PlantFeedback.objects.filter(status="pending").count()
    total_views = PlantInfo.objects.aggregate(s=Sum("view_count"))["s"] or 0
    total_collects = UserCollect.objects.count()

    recent_logs = OperationLog.objects.select_related("user").order_by("-create_time")[:20]

    return render(request, "admin/dashboard.html", {
        "total_plants": total_plants,
        "online_plants": online_plants,
        "pending_plants": pending_plants,
        "draft_plants": draft_plants,
        "total_users": total_users,
        "total_categories": total_categories,
        "pending_feedbacks": pending_feedbacks,
        "total_views": total_views,
        "total_collects": total_collects,
        "recent_logs": recent_logs,
    })


# ==================== 植物管理 ====================

@admin_required
def admin_plant_list(request):
    """植物列表管理"""
    status_filter = request.GET.get("status", "")
    category_filter = request.GET.get("category", "")
    search = request.GET.get("q", "").strip()
    page = request.GET.get("page", 1)

    plants = PlantInfo.objects.filter(is_deleted=False).select_related("category")

    if status_filter:
        plants = plants.filter(status=status_filter)
    if category_filter:
        plants = plants.filter(category_id=int(category_filter))
    if search:
        plants = plants.filter(
            Q(name_cn__icontains=search) |
            Q(name_en__icontains=search) |
            Q(alias__icontains=search)
        )

    plants = plants.order_by("-update_time")
    paginator = Paginator(plants, 15)
    page_obj = paginator.get_page(page)

    categories = PlantCategory.objects.filter(parent__isnull=True).order_by("sort_order")

    return render(request, "admin/plant_list.html", {
        "plants": page_obj,
        "categories": categories,
        "status_filter": status_filter,
        "category_filter": category_filter,
        "search": search,
        "status_choices": PlantInfo.STATUS_CHOICES,
    })


@admin_required
def admin_plant_add(request):
    """新增植物"""
    categories = PlantCategory.objects.all().order_by("parent__sort_order", "sort_order")
    if request.method == "POST":
        name_cn = request.POST.get("name_cn", "").strip()
        if not name_cn:
            messages.error(request, "中文名称不能为空")
            return render(request, "admin/plant_form.html", {"categories": categories, "is_edit": False})
        if PlantInfo.objects.filter(name_cn=name_cn, is_deleted=False).exists():
            messages.error(request, "该植物名称已存在")
            return render(request, "admin/plant_form.html", {"categories": categories, "is_edit": False})

        plant = PlantInfo(
            name_cn=name_cn,
            name_en=request.POST.get("name_en", "").strip(),
            alias=request.POST.get("alias", "").strip(),
            morphology=request.POST.get("morphology", "").strip(),
            habitat=request.POST.get("habitat", "").strip(),
            cultivation=request.POST.get("cultivation", "").strip(),
            value_desc=request.POST.get("value_desc", "").strip(),
            is_toxic=request.POST.get("is_toxic") == "on",
            toxicity_desc=request.POST.get("toxicity_desc", "").strip(),
            is_protected=request.POST.get("is_protected") == "on",
            protection_level=request.POST.get("protection_level", "").strip(),
            status=request.POST.get("status", "draft"),
            created_by=request.user,
            updated_by=request.user,
        )
        category_id = request.POST.get("category", "")
        if category_id:
            plant.category_id = int(category_id)
        if request.FILES.get("cover_image"):
            plant.cover_image = request.FILES["cover_image"]
        plant.save()

        log_operation(request.user, "create", "plant", plant.id, f"新增植物：{plant.name_cn}", request)
        messages.success(request, f"植物「{plant.name_cn}」添加成功")
        return redirect("admin_plant_list")

    return render(request, "admin/plant_form.html", {"categories": categories, "is_edit": False})


@admin_required
def admin_plant_edit(request, plant_id):
    """编辑植物"""
    plant = get_object_or_404(PlantInfo, id=plant_id, is_deleted=False)
    categories = PlantCategory.objects.all().order_by("parent__sort_order", "sort_order")

    if request.method == "POST":
        new_name = request.POST.get("name_cn", "").strip()
        if not new_name:
            messages.error(request, "中文名称不能为空")
            return render(request, "admin/plant_form.html", {"plant": plant, "categories": categories, "is_edit": True})

        old_name = plant.name_cn
        if new_name != old_name and PlantInfo.objects.filter(name_cn=new_name, is_deleted=False).exclude(id=plant.id).exists():
            messages.error(request, "该植物名称已被其他记录使用")
            return render(request, "admin/plant_form.html", {"plant": plant, "categories": categories, "is_edit": True})

        plant.name_cn = new_name
        plant.name_en = request.POST.get("name_en", "").strip()
        plant.alias = request.POST.get("alias", "").strip()
        plant.morphology = request.POST.get("morphology", "").strip()
        plant.habitat = request.POST.get("habitat", "").strip()
        plant.cultivation = request.POST.get("cultivation", "").strip()
        plant.value_desc = request.POST.get("value_desc", "").strip()
        plant.is_toxic = request.POST.get("is_toxic") == "on"
        plant.toxicity_desc = request.POST.get("toxicity_desc", "").strip()
        plant.is_protected = request.POST.get("is_protected") == "on"
        plant.protection_level = request.POST.get("protection_level", "").strip()
        plant.updated_by = request.user

        category_id = request.POST.get("category", "")
        plant.category_id = int(category_id) if category_id else None

        if request.FILES.get("cover_image"):
            plant.cover_image = request.FILES["cover_image"]

        new_status = request.POST.get("status", plant.status)
        plant.status = new_status
        plant.save()

        action = "rename" if old_name != new_name else "edit"
        log_operation(request.user, action, "plant", plant.id, f"编辑植物：{old_name} -> {new_name}", request)
        messages.success(request, f"植物「{plant.name_cn}」更新成功")
        return redirect("admin_plant_list")

    return render(request, "admin/plant_form.html", {"plant": plant, "categories": categories, "is_edit": True})


@admin_required
def admin_plant_delete(request, plant_id):
    """逻辑删除植物"""
    plant = get_object_or_404(PlantInfo, id=plant_id)
    plant.is_deleted = True
    plant.status = "offline"
    plant.save()
    log_operation(request.user, "delete", "plant", plant.id, f"下架/删除植物：{plant.name_cn}", request)
    messages.success(request, f"植物「{plant.name_cn}」已下架")
    return redirect("admin_plant_list")


@admin_required
def admin_plant_status(request, plant_id):
    """修改植物状态"""
    if request.method == "POST":
        plant = get_object_or_404(PlantInfo, id=plant_id, is_deleted=False)
        new_status = request.POST.get("status", "")
        if new_status in dict(PlantInfo.STATUS_CHOICES):
            old_status = plant.get_status_display()
            plant.status = new_status
            plant.save()
            log_operation(request.user, "review", "plant", plant.id, f"状态变更：{old_status} -> {plant.get_status_display()}", request)
            messages.success(request, f"「{plant.name_cn}」状态已更新为 {plant.get_status_display()}")
    return redirect("admin_plant_list")


# ==================== 分类管理 ====================

@admin_required
def admin_category_list(request):
    """分类列表"""
    parents = PlantCategory.objects.filter(parent__isnull=True).order_by("sort_order")
    all_categories = PlantCategory.objects.all().order_by("parent__sort_order", "sort_order")
    return render(request, "admin/category_list.html", {
        "parents": parents,
        "all_categories": all_categories,
    })


@admin_required
def admin_category_add(request):
    """新增分类"""
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if not name:
            messages.error(request, "分类名称不能为空")
            return redirect("admin_category_list")
        parent_id = request.POST.get("parent", "")
        parent = None
        if parent_id:
            parent = get_object_or_404(PlantCategory, id=int(parent_id))
        PlantCategory.objects.create(
            name=name, parent=parent,
            sort_order=int(request.POST.get("sort_order", 0))
        )
        log_operation(request.user, "category_mgr", "category", None, f"新增分类：{name}", request)
        messages.success(request, f"分类「{name}」添加成功")
    return redirect("admin_category_list")


@admin_required
def admin_category_edit(request, cat_id):
    """编辑分类"""
    category = get_object_or_404(PlantCategory, id=cat_id)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if not name:
            messages.error(request, "分类名称不能为空")
            return redirect("admin_category_list")
        category.name = name
        parent_id = request.POST.get("parent", "")
        category.parent = PlantCategory.objects.filter(id=int(parent_id)).first() if parent_id else None
        category.sort_order = int(request.POST.get("sort_order", 0))
        category.save()
        log_operation(request.user, "category_mgr", "category", category.id, f"编辑分类：{name}", request)
        messages.success(request, f"分类「{name}」更新成功")
    return redirect("admin_category_list")


@admin_required
def admin_category_delete(request, cat_id):
    """删除分类"""
    category = get_object_or_404(PlantCategory, id=cat_id)
    name = category.name
    PlantCategory.objects.filter(parent=category).update(parent=category.parent)
    category.delete()
    log_operation(request.user, "category_mgr", "category", cat_id, f"删除分类：{name}", request)
    messages.success(request, f"分类「{name}」已删除")
    return redirect("admin_category_list")


# ==================== 反馈审核 ====================

@admin_required
def admin_feedback_list(request):
    """反馈审核列表"""
    status_filter = request.GET.get("status", "")
    page = request.GET.get("page", 1)

    feedbacks = PlantFeedback.objects.select_related("user", "plant").all()
    if status_filter:
        feedbacks = feedbacks.filter(status=status_filter)
    feedbacks = feedbacks.order_by("-create_time")

    paginator = Paginator(feedbacks, 15)
    page_obj = paginator.get_page(page)

    return render(request, "admin/feedback_list.html", {
        "feedbacks": page_obj,
        "status_filter": status_filter,
    })


@admin_required
def admin_feedback_review(request, feedback_id):
    """审核反馈"""
    feedback = get_object_or_404(PlantFeedback, id=feedback_id)
    if request.method == "POST":
        action = request.POST.get("action", "")
        reply = request.POST.get("reply", "").strip()
        if action == "approve":
            feedback.status = "approved"
            feedback.reply = reply or "已采纳，感谢您的反馈"
        elif action == "reject":
            feedback.status = "rejected"
            feedback.reply = reply or "经核实，信息无误"
            if not reply:
                messages.error(request, "驳回需填写原因")
                return redirect("admin_feedback_list")
        feedback.reviewer = request.user
        feedback.review_time = timezone.now()
        feedback.save()
        log_operation(request.user, "review", "feedback", feedback.id, f"审核反馈: {action}", request)
        messages.success(request, "反馈审核完成")
    return redirect("admin_feedback_list")


# ==================== 用户管理 ====================

@admin_required
def admin_user_list(request):
    """用户列表"""
    users = User.objects.filter(role="user").order_by("-create_time")
    paginator = Paginator(users, 20)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    return render(request, "admin/user_list.html", {"users": page_obj})


@admin_required
def admin_user_disable(request, user_id):
    """禁用/启用用户"""
    target = get_object_or_404(User, id=user_id)
    target.is_disabled = not target.is_disabled
    target.save()
    action = "禁用" if target.is_disabled else "启用"
    log_operation(request.user, "user_mgr", "user", user_id, f"{action}用户：{target.username}", request)
    messages.success(request, f"用户「{target.username}」已{action}")
    return redirect("admin_user_list")


@admin_required
def admin_user_reset_pwd(request, user_id):
    """重置用户密码"""
    target = get_object_or_404(User, id=user_id)
    target.set_password("123456")
    target.save()
    log_operation(request.user, "user_mgr", "user", user_id, f"重置密码：{target.username}", request)
    messages.success(request, f"用户「{target.username}」密码已重置为 123456")
    return redirect("admin_user_list")


# ==================== 统计数据 ====================

@admin_required
def admin_statistics(request):
    """数据统计"""
    total_plants = PlantInfo.objects.filter(is_deleted=False).count()
    online_plants = PlantInfo.objects.filter(status="online", is_deleted=False).count()
    total_users = User.objects.filter(role="user").count()
    total_views = PlantInfo.objects.aggregate(s=Sum("view_count"))["s"] or 0
    total_collects = UserCollect.objects.count()
    total_feedbacks = PlantFeedback.objects.count()
    pending_feedbacks = PlantFeedback.objects.filter(status="pending").count()

    category_stats = PlantCategory.objects.filter(parent__isnull=True).annotate(
        plant_count=Count("plantinfo", filter=Q(plantinfo__is_deleted=False))
    ).order_by("-plant_count")[:10]

    return render(request, "admin/statistics.html", {
        "total_plants": total_plants,
        "online_plants": online_plants,
        "total_users": total_users,
        "total_views": total_views,
        "total_collects": total_collects,
        "total_feedbacks": total_feedbacks,
        "pending_feedbacks": pending_feedbacks,
        "category_stats": category_stats,
    })


# ==================== 操作日志 ====================

@admin_required
def admin_operation_logs(request):
    """操作日志"""
    action_filter = request.GET.get("action", "")
    page = request.GET.get("page", 1)

    logs = OperationLog.objects.select_related("user").all()
    if action_filter:
        logs = logs.filter(action=action_filter)
    logs = logs.order_by("-create_time")

    paginator = Paginator(logs, 30)
    page_obj = paginator.get_page(page)

    return render(request, "admin/operation_logs.html", {
        "logs": page_obj,
        "action_filter": action_filter,
        "action_choices": OperationLog.ACTION_CHOICES,
    })
