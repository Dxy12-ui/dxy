from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "管理员"),
        ("user", "普通用户"),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user", verbose_name="角色")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True, verbose_name="头像")
    is_disabled = models.BooleanField(default=False, verbose_name="是否禁用")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="注册时间")

    class Meta:
        db_table = "user_info"
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def __str__(self):
        return f"{self.username}({self.get_role_display()})"
