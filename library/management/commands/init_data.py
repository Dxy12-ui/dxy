from django.core.management.base import BaseCommand
from accounts.models import User
from library.models import PlantCategory, PlantInfo, OperationLog


class Command(BaseCommand):
    help = "初始化系统基础数据"

    def handle(self, *args, **options):
        self.stdout.write("Initializing plant system data...")

        # 创建管理员
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin", password="admin123", role="admin"
            )
            self.stdout.write(self.style.SUCCESS("Admin user created: admin/admin123"))

        # 创建测试用户
        if not User.objects.filter(username="user").exists():
            User.objects.create_user(
                username="user", password="user123", role="user"
            )
            self.stdout.write(self.style.SUCCESS("Test user created: user/user123"))

        # 创建植物分类
        categories_data = [
            ("观赏植物", None),
            ("药用植物", None),
            ("食用植物", None),
            ("珍稀植物", None),
            ("水生植物", None),
            ("多肉植物", "观赏植物"),
            ("花卉", "观赏植物"),
            ("乔木", "观赏植物"),
            ("草本药材", "药用植物"),
            ("木本药材", "药用植物"),
            ("水果", "食用植物"),
            ("蔬菜", "食用植物"),
            ("国家一级保护", "珍稀植物"),
            ("国家二级保护", "珍稀植物"),
        ]
        created_categories = {}
        for name, parent_name in categories_data:
            parent = created_categories.get(parent_name) if parent_name else None
            cat, created = PlantCategory.objects.get_or_create(
                name=name, parent=parent,
                defaults={"sort_order": 0}
            )
            created_categories[name] = cat
            if created:
                self.stdout.write(f"  Category: {cat}")

        # 创建示例植物
        if PlantInfo.objects.count() == 0:
            plants_data = [
                {
                    "name_cn": "月季",
                    "name_en": "Rosa chinensis",
                    "alias": "月月红,长春花",
                    "category": created_categories["花卉"],
                    "morphology": "常绿或半常绿低矮灌木，茎有刺，奇数羽状复叶，小叶3-5片。花单生或数朵簇生，花色丰富，有红、粉、黄、白等多种颜色。花期4-10月，果期6-11月。",
                    "habitat": "喜温暖湿润、阳光充足的环境，耐寒性较强。适宜生长温度为15-26℃。对土壤要求不严，但以疏松肥沃、排水良好的微酸性土壤为佳。",
                    "cultivation": "春秋季为最佳种植时期。浇水见干见湿，避免积水。生长期每月施肥1-2次。花后及时修剪残花，冬季进行整形修剪。常见病虫害有白粉病、黑斑病、蚜虫等。",
                    "value_desc": "观赏价值极高，被称为'花中皇后'。可用于庭院绿化、盆栽观赏、切花。部分品种花瓣可提取香精，花蕾可入药。",
                    "is_toxic": False,
                    "is_protected": False,
                    "status": "online",
                },
                {
                    "name_cn": "银杏",
                    "name_en": "Ginkgo biloba",
                    "alias": "白果树,公孙树",
                    "category": created_categories["乔木"],
                    "morphology": "落叶大乔木，高达40米。叶片扇形，有长柄，在短枝上簇生。雌雄异株。种子核果状，外种皮肉质有臭味。是现存最古老的裸子植物之一。",
                    "habitat": "适应性强，喜光，耐寒，耐旱。对土壤要求不严，在酸性土、石灰性土中均可生长。深根性，寿命极长，可达千年以上。",
                    "cultivation": "播种或嫁接繁殖。种植宜选向阳处。幼苗期需适当遮阴，成年树管理粗放。秋季叶色金黄，是优良的观赏树种。",
                    "value_desc": "观赏树种，秋叶金黄。白果可食用，营养丰富。银杏叶提取物是重要药材，可用于改善心脑血管。木材优良，是珍贵用材树种。",
                    "is_toxic": False,
                    "is_protected": True,
                    "protection_level": "国家一级保护",
                    "status": "online",
                },
                {
                    "name_cn": "人参",
                    "name_en": "Panax ginseng",
                    "alias": "棒槌,地精",
                    "category": created_categories["草本药材"],
                    "morphology": "多年生草本，高30-60cm。主根肥大肉质，圆柱形或纺锤形。茎直立，叶为掌状复叶。伞形花序，花小，淡黄绿色。果实为浆果状核果，成熟时鲜红色。",
                    "habitat": "喜阴凉湿润环境，野生于海拔数百米的针阔混交林下。适宜生长温度15-25℃，要求土壤疏松肥沃、排水良好。忌强光直射和积水。",
                    "cultivation": "人工栽培需搭棚遮阴。播种后需3-4年才能收获。生长期需精细管理，注意防治立枯病、锈病等。",
                    "value_desc": "名贵中药材，有大补元气、复脉固脱、补脾益肺等功效。含有人参皂苷等多种活性成分。经济价值极高，是重要的药用植物资源。",
                    "is_toxic": False,
                    "is_protected": True,
                    "protection_level": "国家二级保护",
                    "status": "online",
                },
                {
                    "name_cn": "夹竹桃",
                    "name_en": "Nerium oleander",
                    "alias": "柳叶桃,半年红",
                    "category": created_categories["花卉"],
                    "morphology": "常绿大灌木，高可达5米。叶轮生，狭披针形，革质。聚伞花序顶生，花冠漏斗形，有粉红、白、黄等色，有香气。几乎全年可开花，夏秋为盛花期。",
                    "habitat": "喜温暖湿润、阳光充足的环境。耐半阴，不耐寒。对土壤要求不严，耐干旱瘠薄。抗污染能力强，适合城市绿化。",
                    "cultivation": "扦插繁殖为主，极易成活。生长迅速，需定期修剪。耐修剪，可做绿篱。适应性强，管理粗放。",
                    "value_desc": "优良的观赏植物和环保树种。对SO2、Cl2等有害气体有较强的吸收能力。园林中常用作行道树、绿篱。",
                    "is_toxic": True,
                    "toxicity_desc": "全株有毒，含强心苷类物质。误食可引起恶心、呕吐、腹痛、心律不齐等症状，严重者可致死亡。汁液接触皮肤可能引起过敏。请勿让儿童和宠物接触。",
                    "is_protected": False,
                    "status": "online",
                },
                {
                    "name_cn": "蓝莓",
                    "name_en": "Vaccinium corymbosum",
                    "alias": "越橘,蓝浆果",
                    "category": created_categories["水果"],
                    "morphology": "多年生灌木，高0.5-2米。叶片椭圆形至卵形，秋季变为红色。花钟形，白色或粉红色。果实为蓝色浆果，表面有白霜，直径5-16mm。",
                    "habitat": "喜酸性土壤（pH 4.0-5.5），要求土壤疏松、有机质丰富。喜光，耐寒。适宜生长温度15-25℃。需要充足的冷量才能正常开花结果。",
                    "cultivation": "种植前需改良土壤酸碱度。采用高畦种植，覆盖锯末或松针保持土壤酸性。需配置授粉品种。及时修剪更新老枝。",
                    "value_desc": "果实富含花青素，抗氧化能力强。可鲜食或加工成果酱、果汁等。具有保护视力、延缓衰老等保健功能。经济价值高，市场前景广阔。",
                    "is_toxic": False,
                    "is_protected": False,
                    "status": "online",
                },
                {
                    "name_cn": "荷花",
                    "name_en": "Nelumbo nucifera",
                    "alias": "莲花,芙蓉,水芙蓉",
                    "category": created_categories["水生植物"],
                    "morphology": "多年生水生草本。根状茎（藕）肥厚横走。叶盾圆形，挺出水面，直径可达60cm。花大而美丽，单生，有红、粉、白等色。花、果期6-9月。",
                    "habitat": "喜温暖湿润，生长适温22-30℃。需充足阳光，喜静水环境。适宜水深30-100cm。对土壤要求不严，但以富含有机质的黏土为佳。",
                    "cultivation": "分藕繁殖为主。春季栽种，选择健壮藕种。生长期需定期施肥，注意防治蚜虫和斜纹夜蛾。冬季保持一定水深防冻。",
                    "value_desc": "观赏价值极高，是传统名花。藕和莲子可食用，营养丰富。全株均可入药，荷叶、莲子、藕节各有功效。文化内涵丰富，象征高洁。",
                    "is_toxic": False,
                    "is_protected": False,
                    "status": "online",
                },
                {
                    "name_cn": "仙人掌",
                    "name_en": "Opuntia dillenii",
                    "alias": "仙巴掌,火焰",
                    "category": created_categories["多肉植物"],
                    "morphology": "多年生肉质植物。茎节扁平，椭圆形，绿色，表面有刺座。花黄色，漏斗状。果实梨形，成熟时紫红色，可食用。",
                    "habitat": "原产美洲热带和亚热带干旱地区。喜温暖干燥、阳光充足的环境。耐干旱，不耐寒。适宜生长温度20-30℃。",
                    "cultivation": "扦插繁殖，极易成活。栽培用土需排水良好，可用沙壤土。浇水宁干勿湿，冬季保持干燥。生长期每月施薄肥1次。",
                    "value_desc": "观赏植物，形态独特。果实可食用。茎可作饲料。有吸收辐射的说法，常放置于电脑旁。部分品种可入药，有清热解毒功效。",
                    "is_toxic": False,
                    "is_protected": False,
                    "status": "online",
                },
                {
                    "name_cn": "红豆杉",
                    "name_en": "Taxus chinensis",
                    "alias": "紫杉,赤柏松",
                    "category": created_categories["国家一级保护"],
                    "morphology": "常绿乔木，高可达30米。树皮红褐色，裂成条片。叶条形，螺旋状排列，排成二列。雌雄异株。种子坚果状，生于红色肉质杯状假种皮中。",
                    "habitat": "喜温暖湿润气候，耐阴。野生于海拔1000-1200米的山地。适宜生长温度15-25℃。要求土壤深厚肥沃、排水良好。",
                    "cultivation": "种子繁殖或扦插繁殖。幼苗生长缓慢，需遮阴。人工栽培需10年以上才能收获。对生态环境要求较高。",
                    "value_desc": "珍贵用材树种，木材纹理直，结构细。树皮和枝叶可提取紫杉醇，是重要的抗癌药物原料。观赏价值高，可作庭院树。",
                    "is_toxic": True,
                    "toxicity_desc": "除假种皮外全株有毒，含紫杉碱。误食可引起恶心、呕吐、呼吸困难等症状。紫杉醇药用需在专业指导下进行。",
                    "is_protected": True,
                    "protection_level": "国家一级保护",
                    "status": "online",
                },
            ]

            for data in plants_data:
                user = User.objects.filter(role="admin").first()
                plant = PlantInfo.objects.create(created_by=user, updated_by=user, **data)
                self.stdout.write(f"  Plant: {plant.name_cn}")

            self.stdout.write(self.style.SUCCESS(f"Created {len(plants_data)} sample plants"))

        self.stdout.write(self.style.SUCCESS("Initialization complete!"))
