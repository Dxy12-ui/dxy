from django.core.management.base import BaseCommand
from django.core.management import call_command
from accounts.models import User
from library.models import PlantCategory, PlantInfo


class Command(BaseCommand):
    help = "初始化系统基础数据（Railway 首次部署用）"

    def handle(self, *args, **options):
        self.stdout.write("Initializing Plant System...")

        # 管理员
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(username="admin", password="admin123", role="admin")
            self.stdout.write(self.style.SUCCESS("Admin: admin/admin123"))

        # 测试用户
        if not User.objects.filter(username="user").exists():
            User.objects.create_user(username="user", password="user123", role="user")
            self.stdout.write(self.style.SUCCESS("User: user/user123"))

        # 分类
        categories_data = [
            ("观赏植物", None), ("药用植物", None), ("食用植物", None),
            ("珍稀植物", None), ("水生植物", None),
            ("多肉植物", "观赏植物"), ("花卉", "观赏植物"), ("乔木", "观赏植物"),
            ("草本药材", "药用植物"), ("木本药材", "药用植物"),
            ("水果", "食用植物"), ("蔬菜", "食用植物"),
            ("国家一级保护", "珍稀植物"), ("国家二级保护", "珍稀植物"),
        ]
        cat_map = {}
        for name, parent_name in categories_data:
            parent = cat_map.get(parent_name) if parent_name else None
            cat, _ = PlantCategory.objects.get_or_create(name=name, parent=parent, defaults={"sort_order": 0})
            cat_map[name] = cat

        # 植物数据
        if PlantInfo.objects.count() == 0:
            plants_data = [
                {"name_cn": "月季", "name_en": "Rosa chinensis", "alias": "月月红,长春花",
                 "category": cat_map["花卉"], "morphology": "常绿或半常绿低矮灌木，茎有刺。花单生或数朵簇生，花色丰富。",
                 "habitat": "喜温暖湿润、阳光充足，耐寒。适宜15-26℃。",
                 "cultivation": "春秋季种植。见干见湿，每月施肥1-2次。花后修剪残花。",
                 "value_desc": "花中皇后。庭院绿化、盆栽观赏、切花。花瓣可提取香精。", "status": "online"},
                {"name_cn": "银杏", "name_en": "Ginkgo biloba", "alias": "白果树,公孙树",
                 "category": cat_map["乔木"], "morphology": "落叶大乔木，高40米。叶扇形。雌雄异株。最古老裸子植物之一。",
                 "habitat": "喜光，耐寒耐旱。深根性，寿命极长。",
                 "cultivation": "播种或嫁接。秋季叶色金黄，优良观赏树种。",
                 "value_desc": "秋叶金黄。白果可食。叶提取物可改善心脑血管。",
                 "is_protected": True, "protection_level": "国家一级保护", "status": "online"},
                {"name_cn": "人参", "name_en": "Panax ginseng", "alias": "棒槌,地精",
                 "category": cat_map["草本药材"], "morphology": "多年生草本。主根肥大肉质。掌状复叶。",
                 "habitat": "喜阴凉湿润。野生于针阔混交林下。",
                 "cultivation": "搭棚遮阴。播种后3-4年收获。",
                 "value_desc": "名贵中药材。大补元气。含人参皂苷等活性成分。",
                 "is_protected": True, "protection_level": "国家二级保护", "status": "online"},
                {"name_cn": "夹竹桃", "name_en": "Nerium oleander", "alias": "柳叶桃,半年红",
                 "category": cat_map["花卉"], "morphology": "常绿大灌木，高5米。叶轮生，狭披针形。花漏斗形，有香气。",
                 "habitat": "喜温暖湿润、阳光充足。抗污染能力强。",
                 "cultivation": "扦插繁殖极易成活。耐修剪。",
                 "value_desc": "优良观赏和环保树种。吸收有害气体。",
                 "is_toxic": True, "toxicity_desc": "全株有毒，含强心苷。误食可致心律不齐，严重可致死。", "status": "online"},
                {"name_cn": "蓝莓", "name_en": "Vaccinium corymbosum", "alias": "越橘,蓝浆果",
                 "category": cat_map["水果"], "morphology": "多年生灌木。花钟形，白色。果实蓝色浆果。",
                 "habitat": "喜酸性土壤(pH 4.0-5.5)。喜光，耐寒。",
                 "cultivation": "改良土壤酸碱度。高畦种植。配置授粉品种。",
                 "value_desc": "富含花青素。抗氧化。保护视力。经济价值高。", "status": "online"},
                {"name_cn": "荷花", "name_en": "Nelumbo nucifera", "alias": "莲花,芙蓉",
                 "category": cat_map["水生植物"], "morphology": "多年生水生草本。叶盾圆形。花大美丽。",
                 "habitat": "喜温暖湿润。需充足阳光。适宜水深30-100cm。",
                 "cultivation": "分藕繁殖。春季栽种。定期施肥。",
                 "value_desc": "传统名花。藕和莲子可食。全株可入药。象征高洁。", "status": "online"},
                {"name_cn": "仙人掌", "name_en": "Opuntia dillenii", "alias": "仙巴掌,火焰",
                 "category": cat_map["多肉植物"], "morphology": "多年生肉质植物。茎节扁平。花黄色。",
                 "habitat": "喜温暖干燥、阳光充足。耐干旱，不耐寒。",
                 "cultivation": "扦插繁殖。宁干勿湿。生长期每月薄肥1次。",
                 "value_desc": "形态独特。果实可食。有吸收辐射的说法。", "status": "online"},
                {"name_cn": "红豆杉", "name_en": "Taxus chinensis", "alias": "紫杉,赤柏松",
                 "category": cat_map["国家一级保护"], "morphology": "常绿乔木，高30米。叶条形。种子坚果状。",
                 "habitat": "喜温暖湿润，耐阴。海拔1000-1200米山地。",
                 "cultivation": "种子或扦插繁殖。幼苗生长缓慢。",
                 "value_desc": "珍贵用材。可提取紫杉醇抗癌。观赏价值高。",
                 "is_toxic": True, "toxicity_desc": "除假种皮外全株有毒。紫杉醇需专业指导使用。",
                 "is_protected": True, "protection_level": "国家一级保护", "status": "online"},
            ]
            admin = User.objects.filter(role="admin").first()
            for data in plants_data:
                PlantInfo.objects.create(created_by=admin, updated_by=admin, **data)
            self.stdout.write(self.style.SUCCESS(f"Created {len(plants_data)} plants"))

        # 生成植物图片
        self.stdout.write("Generating plant images...")
        call_command("gen_plant_images")
        self.stdout.write(self.style.SUCCESS("Done! Plant system ready."))
