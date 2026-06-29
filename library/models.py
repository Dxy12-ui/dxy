from django.db import models
from django.conf import settings


class PlantCategory(models.Model):
    """植物分类表 - 支持两级分类"""
    name = models.CharField(max_length=100, verbose_name="分类名称")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True,
        related_name="children", verbose_name="上级分类"
    )
    sort_order = models.IntegerField(default=0, verbose_name="排序")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        db_table = "plant_category"
        verbose_name = "植物分类"
        verbose_name_plural = "植物分类"
        ordering = ["sort_order", "id"]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    @property
    def is_parent(self):
        return self.parent is None


class PlantInfo(models.Model):
    """植物信息表"""
    STATUS_CHOICES = (
        ("draft", "草稿"),
        ("pending", "待审核"),
        ("online", "已上线"),
        ("offline", "已下架"),
    )
    # 基础名称
    name_cn = models.CharField(max_length=200, unique=True, verbose_name="中文名称")
    name_en = models.CharField(max_length=300, blank=True, default="", verbose_name="拉丁学名")
    alias = models.CharField(max_length=500, blank=True, default="", verbose_name="别名（逗号分隔）")

    # 分类
    category = models.ForeignKey(
        PlantCategory, on_delete=models.SET_NULL, null=True,
        blank=True, verbose_name="所属分类"
    )

    # 科普信息
    morphology = models.TextField(blank=True, default="", verbose_name="形态特征")
    habitat = models.TextField(blank=True, default="", verbose_name="生长习性")
    cultivation = models.TextField(blank=True, default="", verbose_name="栽培养护")
    value_desc = models.TextField(blank=True, default="", verbose_name="主要价值")

    # 毒性与保护
    is_toxic = models.BooleanField(default=False, verbose_name="是否有毒")
    toxicity_desc = models.TextField(blank=True, default="", verbose_name="毒性说明")
    is_protected = models.BooleanField(default=False, verbose_name="是否保护植物")
    protection_level = models.CharField(max_length=50, blank=True, default="", verbose_name="保护级别")

    # 图片
    cover_image = models.ImageField(upload_to="plants/", blank=True, null=True, verbose_name="封面图片")
    images = models.TextField(blank=True, default="", verbose_name="更多图片（JSON数组路径）")

    # 状态
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft", verbose_name="状态")
    is_deleted = models.BooleanField(default=False, verbose_name="是否逻辑删除")

    # 统计
    view_count = models.IntegerField(default=0, verbose_name="浏览次数")
    collect_count = models.IntegerField(default=0, verbose_name="收藏次数")
    search_count = models.IntegerField(default=0, verbose_name="搜索命中次数")

    # 操作者与时间
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="created_plants", verbose_name="创建者"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name="updated_plants", verbose_name="最后修改者"
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "plant_info"
        verbose_name = "植物信息"
        verbose_name_plural = "植物信息"
        ordering = ["-update_time"]
        indexes = [
            models.Index(fields=["name_cn"]),
            models.Index(fields=["name_en"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.name_cn

    @property
    def alias_list(self):
        if self.alias:
            return [a.strip() for a in self.alias.split(",") if a.strip()]
        return []

    @property
    def image_list(self):
        import json
        if self.images:
            try:
                return json.loads(self.images)
            except json.JSONDecodeError:
                return []
        return []


class UserCollect(models.Model):
    """用户收藏表"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="collections", verbose_name="用户"
    )
    plant = models.ForeignKey(
        PlantInfo, on_delete=models.CASCADE,
        related_name="collections", verbose_name="植物"
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="收藏时间")

    class Meta:
        db_table = "user_collect"
        verbose_name = "用户收藏"
        verbose_name_plural = "用户收藏"
        unique_together = ["user", "plant"]

    def __str__(self):
        return f"{self.user.username} 收藏 {self.plant.name_cn}"


class SearchHistory(models.Model):
    """搜索历史表"""
    SEARCH_TYPE = (
        ("text", "文字搜索"),
        ("image", "图片识别"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="search_history", verbose_name="用户"
    )
    keyword = models.CharField(max_length=500, verbose_name="搜索关键词")
    search_type = models.CharField(max_length=10, choices=SEARCH_TYPE, default="text", verbose_name="搜索类型")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="搜索时间")

    class Meta:
        db_table = "search_history"
        verbose_name = "搜索历史"
        verbose_name_plural = "搜索历史"
        ordering = ["-create_time"]


class PlantFeedback(models.Model):
    """植物纠错反馈表"""
    STATUS_CHOICES = (
        ("pending", "待审核"),
        ("approved", "已采纳"),
        ("rejected", "已驳回"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="feedbacks", verbose_name="反馈用户"
    )
    plant = models.ForeignKey(
        PlantInfo, on_delete=models.CASCADE,
        related_name="feedbacks", verbose_name="相关植物"
    )
    content = models.TextField(verbose_name="纠错内容")
    images = models.TextField(blank=True, default="", verbose_name="纠错配图（JSON数组）")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="审核状态")
    reply = models.TextField(blank=True, default="", verbose_name="管理员回复")
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        blank=True, related_name="reviewed_feedbacks", verbose_name="审核人"
    )
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="提交时间")
    review_time = models.DateTimeField(null=True, blank=True, verbose_name="审核时间")

    class Meta:
        db_table = "plant_feedback"
        verbose_name = "纠错反馈"
        verbose_name_plural = "纠错反馈"
        ordering = ["-create_time"]


class OperationLog(models.Model):
    """操作日志表"""
    ACTION_CHOICES = (
        ("create", "新增植物"),
        ("rename", "修改名称"),
        ("edit", "编辑信息"),
        ("delete", "删除/下架"),
        ("review", "审核操作"),
        ("user_mgr", "用户管理"),
        ("category_mgr", "分类管理"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        verbose_name="操作者"
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="操作类型")
    target_type = models.CharField(max_length=50, blank=True, default="", verbose_name="操作对象类型")
    target_id = models.IntegerField(null=True, blank=True, verbose_name="操作对象ID")
    detail = models.TextField(blank=True, default="", verbose_name="操作详情")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP地址")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="操作时间")

    class Meta:
        db_table = "operation_log"
        verbose_name = "操作日志"
        verbose_name_plural = "操作日志"
        ordering = ["-create_time"]
