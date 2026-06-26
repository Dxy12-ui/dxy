from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "管理员"),
        ("student", "学生"),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="student", verbose_name="角色")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="注册时间")

    class Meta:
        db_table = "user"
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def __str__(self):
        return f"{self.username}({self.get_role_display()})"
