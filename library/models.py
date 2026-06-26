from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="分类名称")

    class Meta:
        db_table = "category"
        verbose_name = "图书分类"
        verbose_name_plural = "图书分类"

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200, verbose_name="图书名称")
    author = models.CharField(max_length=100, verbose_name="作者")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name="分类")
    stock = models.IntegerField(default=0, verbose_name="当前库存")
    total_num = models.IntegerField(default=0, verbose_name="总入库数量")
    desc = models.TextField(blank=True, default="", verbose_name="图书简介")
    publish = models.CharField(max_length=200, blank=True, default="", verbose_name="出版社")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="入库时间")

    class Meta:
        db_table = "book"
        verbose_name = "图书"
        verbose_name_plural = "图书"

    def __str__(self):
        return self.title

    @property
    def is_available(self):
        return self.stock > 0


class BorrowRecord(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="借阅学生"
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, verbose_name="借阅图书")
    borrow_date = models.DateTimeField(auto_now_add=True, verbose_name="借阅日期")
    return_date = models.DateTimeField(null=True, blank=True, verbose_name="归还日期")
    is_return = models.BooleanField(default=False, verbose_name="是否归还")
    due_date = models.DateTimeField(null=True, blank=True, verbose_name="到期时间")

    class Meta:
        db_table = "borrow_record"
        verbose_name = "借阅记录"
        verbose_name_plural = "借阅记录"

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"
