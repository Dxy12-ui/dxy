from django.core.management.base import BaseCommand
from accounts.models import User
from library.models import Category, Book

class Command(BaseCommand):
    help = "初始化系统数据：创建管理员、测试学生、图书分类和测试图书"

    def handle(self, *args, **options):
        self.stdout.write("开始初始化数据...")

        # 创建管理员
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin", password="admin123", role="admin"
            )
            self.stdout.write(self.style.SUCCESS("管理员账号已创建：admin / admin123"))
        else:
            self.stdout.write("管理员账号已存在，跳过")

        # 创建测试学生
        students = [
            ("zhangsan", "123456"),
            ("lisi", "123456"),
            ("wangwu", "123456"),
        ]
        for username, password in students:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username, password=password, role="student"
                )
                self.stdout.write(self.style.SUCCESS(f"学生账号已创建：{username} / {password}"))

        # 创建图书分类
        categories_data = [
            "计算机科学", "文学小说", "历史哲学", "自然科学",
            "经济管理", "外语学习", "艺术设计", "教育心理",
        ]
        categories = {}
        for name in categories_data:
            cat, created = Category.objects.get_or_create(name=name)
            categories[name] = cat
            if created:
                self.stdout.write(f"分类已创建：{name}")

        # 创建测试图书
        books_data = [
            ("Python编程：从入门到实践", "Eric Matthes", "计算机科学", 10, "Python入门经典书籍，涵盖基础语法到项目实战。"),
            ("深入理解计算机系统", "Randal E. Bryant", "计算机科学", 5, "从程序员视角理解计算机系统核心概念。"),
            ("算法导论", "Thomas H. Cormen", "计算机科学", 8, "算法领域的标准教材，全面覆盖经典算法。"),
            ("活着", "余华", "文学小说", 12, "讲述了农村人福贵悲惨的人生遭遇。"),
            ("百年孤独", "加西亚·马尔克斯", "文学小说", 7, "魔幻现实主义文学的代表作。"),
            ("三体", "刘慈欣", "文学小说", 15, "中国科幻文学的里程碑之作。"),
            ("围城", "钱钟书", "文学小说", 6, "中国现代文学经典，被誉为新儒林外史。"),
            ("人类简史", "尤瓦尔·赫拉利", "历史哲学", 9, "从认知革命到科学革命的人类发展史。"),
            ("苏菲的世界", "乔斯坦·贾德", "历史哲学", 4, "以小说的形式讲述西方哲学史。"),
            ("时间简史", "史蒂芬·霍金", "自然科学", 8, "讲述宇宙的起源、结构和终极命运。"),
            ("上帝掷骰子吗", "曹天元", "自然科学", 6, "量子物理史话，通俗易懂的科普佳作。"),
            ("经济学原理", "曼昆", "经济管理", 10, "全球最流行的经济学入门教材。"),
            ("从0到1", "彼得·蒂尔", "经济管理", 5, "关于创业与创新的商业经典。"),
            ("新概念英语2", "亚历山大", "外语学习", 20, "经典英语学习教材，适合初中级学习者。"),
            ("设计中的设计", "原研哉", "艺术设计", 3, "日本设计大师关于设计本质的思考。"),
            ("教育心理学", "陈琦", "教育心理", 6, "教育心理学领域权威教材。"),
            ("数据结构与算法分析", "Mark Allen Weiss", "计算机科学", 7, "经典数据结构教材，C语言描述。"),
            ("计算机网络", "谢希仁", "计算机科学", 11, "国内高校广泛使用的计算机网络教材。"),
            ("小王子", "安托万·德·圣-埃克苏佩里", "文学小说", 8, "全球最畅销的童话哲学作品。"),
            ("平凡的世界", "路遥", "文学小说", 5, "全景式展现中国当代城乡社会生活。"),
        ]

        created_count = 0
        for title, author, cat_name, stock, desc in books_data:
            if not Book.objects.filter(title=title).exists():
                Book.objects.create(
                    title=title,
                    author=author,
                    category=categories.get(cat_name),
                    stock=stock,
                    total_num=stock,
                    desc=desc,
                    publish="出版社",
                )
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"测试图书已创建：{created_count} 本"))

        # 再添加一些库存为0的图书用于测试
        zero_stock_books = [
            ("设计模式", "GoF", "计算机科学", 0),
            ("红楼梦", "曹雪芹", "文学小说", 0),
        ]
        for title, author, cat_name, stock in zero_stock_books:
            if not Book.objects.filter(title=title).exists():
                Book.objects.create(
                    title=title,
                    author=author,
                    category=categories.get(cat_name),
                    stock=stock,
                    total_num=3,
                    desc=f"《{title}》经典著作（库存不足测试）",
                    publish="出版社",
                )
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"库存为0的测试图书已创建：{len(zero_stock_books)} 本"))
        self.stdout.write(self.style.SUCCESS("=== 数据初始化完成 ==="))
        self.stdout.write(f"管理员：admin / admin123")
        self.stdout.write(f"测试学生：zhangsan/123456, lisi/123456, wangwu/123456")
