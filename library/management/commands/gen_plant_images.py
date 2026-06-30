"""
生成浅绿背景 + 动漫风格植物插画
"""
from django.core.management.base import BaseCommand
from library.models import PlantInfo
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os, math, random


def draw_rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    r = radius
    draw.ellipse([x1, y1, x1 + 2*r, y1 + 2*r], fill=fill)
    draw.ellipse([x2 - 2*r, y1, x2, y1 + 2*r], fill=fill)
    draw.ellipse([x1, y2 - 2*r, x1 + 2*r, y2], fill=fill)
    draw.ellipse([x2 - 2*r, y2 - 2*r, x2, y2], fill=fill)
    draw.rectangle([x1 + r, y1, x2 - r, y2], fill=fill)
    draw.rectangle([x1, y1 + r, x2, y2 - r], fill=fill)


def draw_anime_flower(draw, cx, cy, size, petal_color, center_color):
    """动漫风格花朵"""
    petals = 5
    for i in range(petals):
        angle = i * 2 * math.pi / petals - math.pi / 2
        px = cx + size * 0.25 * math.cos(angle)
        py = cy + size * 0.25 * math.sin(angle)
        # 花瓣 - 泪滴形椭圆
        pw = size * 0.35
        ph = size * 0.55
        draw.ellipse([px - pw, py - ph, px + pw, py + ph], fill=petal_color,
                     outline=tuple(max(0, c - 40) for c in petal_color), width=2)
    # 花心
    draw.ellipse([cx - size * 0.18, cy - size * 0.18, cx + size * 0.18, cy + size * 0.18],
                 fill=center_color, outline=(180, 140, 60), width=2)
    # 花心高光
    draw.ellipse([cx - size * 0.06, cy - size * 0.1, cx + size * 0.02, cy - size * 0.02],
                 fill=(255, 255, 255, 180))


def draw_anime_leaf(draw, cx, cy, size, angle, color):
    """动漫风格叶子"""
    # 主体
    w2 = size * 0.25
    h2 = size * 0.55
    pts = []
    for i in range(24):
        t = i / 23
        if t < 0.5:
            rx = w2 * math.sin(t * math.pi)
            ry = h2 * t
        else:
            rx = w2 * math.sin(t * math.pi)
            ry = h2 * (1 - t)
        x = cx + rx * math.cos(angle) - ry * math.sin(angle)
        y = cy + rx * math.sin(angle) + ry * math.cos(angle)
        pts.append((x, y))
    # 对称
    pts2 = []
    for i in range(24):
        t = i / 23
        if t < 0.5:
            rx = -w2 * math.sin(t * math.pi)
            ry = h2 * t
        else:
            rx = -w2 * math.sin(t * math.pi)
            ry = h2 * (1 - t)
        x = cx + rx * math.cos(angle) - ry * math.sin(angle)
        y = cy + rx * math.sin(angle) + ry * math.cos(angle)
        pts2.append((x, y))
    draw.polygon(pts + pts2[::-1], fill=color, outline=tuple(max(0, c - 30) for c in color))
    # 叶脉
    draw.line([cx, cy, cx + size * 0.9 * math.cos(angle), cy + size * 0.9 * math.sin(angle)],
             fill=tuple(max(0, c - 35) for c in color), width=2)


# 每种植物动漫配置
PLANTS = {
    "月季": {
        "bg": (232, 248, 232),
        "draw": lambda d: [
            (d, "stem", [(350, 380, 300, 230, 8, (60, 150, 60))]),
            (d, "leaf", [(270, 300, 50, -0.6, (80, 170, 80)), (400, 260, 45, 0.7, (80, 170, 80)), (320, 340, 40, -0.3, (80, 170, 80))]),
            (d, "flower", [(340, 170, 55, (255, 100, 120), (255, 230, 80))]),
            (d, "flower", [(290, 210, 40, (255, 130, 150), (255, 230, 80))]),
            (d, "flower", [(380, 195, 38, (255, 140, 160), (255, 230, 80))]),
        ],
        "emoji": "🌹"
    },
    "银杏": {
        "bg": (230, 248, 230),
        "draw": lambda d: [
            (d, "stem", [(340, 380, 310, 180, 8, (130, 100, 50))]),
            (d, "leaf", [(310, 200, 70, -0.5, (255, 220, 80))]),
            (d, "leaf", [(260, 250, 60, 0.3, (255, 200, 60))]),
            (d, "leaf", [(360, 240, 55, -0.8, (240, 210, 70))]),
            (d, "leaf", [(300, 160, 50, -0.2, (255, 225, 90))]),
            (d, "leaf", [(350, 170, 45, 0.5, (255, 215, 75))]),
        ],
        "emoji": "🍂"
    },
    "人参": {
        "bg": (228, 245, 228),
        "draw": lambda d: [
            (d, "stem", [(330, 350, 320, 200, 6, (60, 140, 60))]),
            (d, "leaf", [(320, 210, 70, -0.2, (70, 150, 70))]),
            (d, "leaf", [(270, 240, 60, -0.6, (70, 150, 70))]),
            (d, "leaf", [(370, 240, 60, 0.2, (70, 150, 70))]),
            (d, "leaf", [(320, 250, 55, 0.6, (70, 150, 70))]),
            (d, "flower", [(320, 150, 20, (255, 200, 200), (255, 230, 80))]),
            (d, "berry", [(310, 140, 6, (220, 50, 50)), (330, 135, 6, (225, 45, 45)), (320, 125, 5, (215, 55, 55))]),
        ],
        "emoji": "🌿"
    },
    "夹竹桃": {
        "bg": (232, 247, 232),
        "draw": lambda d: [
            (d, "stem", [(340, 370, 320, 220, 7, (50, 130, 50))]),
            (d, "leaf", [(290, 310, 55, -0.4, (60, 140, 60)), (370, 290, 50, 0.5, (60, 140, 60)), (310, 270, 45, 0.3, (60, 140, 60)), (360, 320, 48, -0.7, (60, 140, 60))]),
            (d, "flower", [(320, 170, 48, (255, 140, 180), (255, 220, 80))]),
            (d, "flower", [(270, 210, 38, (255, 150, 185), (255, 220, 80))]),
            (d, "flower", [(370, 200, 42, (255, 130, 175), (255, 220, 80))]),
        ],
        "emoji": "🌸"
    },
    "蓝莓": {
        "bg": (228, 246, 235),
        "draw": lambda d: [
            (d, "stem", [(340, 360, 330, 200, 6, (80, 130, 70))]),
            (d, "leaf", [(300, 290, 55, -0.3, (80, 150, 80)), (360, 270, 50, 0.4, (80, 150, 80)), (330, 310, 48, 0.1, (80, 150, 80))]),
            (d, "berry", [(330, 200, 16, (60, 80, 200)), (300, 220, 14, (55, 75, 195)), (360, 215, 15, (65, 85, 205)), (315, 180, 13, (50, 70, 190)), (345, 185, 14, (58, 78, 198))]),
        ],
        "emoji": "🫐"
    },
    "荷花": {
        "bg": (225, 245, 235),
        "draw": lambda d: [
            (d, "stem", [(340, 380, 330, 200, 7, (60, 150, 70))]),
            (d, "pad", [(290, 340, 90, (80, 180, 100))]),
            (d, "pad", [(360, 350, 70, (80, 180, 100))]),
            (d, "flower", [(330, 190, 55, (255, 160, 200), (255, 220, 80))]),
            (d, "flower", [(290, 220, 38, (255, 170, 210), (255, 220, 80))]),
        ],
        "emoji": "🪷"
    },
    "仙人掌": {
        "bg": (230, 247, 233),
        "draw": lambda d: [
            (d, "body", [(280, 120, 380, 350, (80, 170, 90))]),
            (d, "body2", [(260, 180, 290, 280, (70, 160, 80))]),
            (d, "body2", [(370, 160, 400, 250, (70, 160, 80))]),
            (d, "spines", []),
            (d, "flower", [(330, 120, 25, (255, 100, 70), (255, 220, 60))]),
            (d, "flower", [(275, 170, 20, (255, 120, 90), (255, 220, 60))]),
        ],
        "emoji": "🌵"
    },
    "红豆杉": {
        "bg": (225, 243, 230),
        "draw": lambda d: [
            (d, "trunk", [(340, 370, 310, 180, 12, (120, 80, 50))]),
            (d, "needle_cluster", [(310, 190, 80, (40, 100, 50))]),
            (d, "needle_cluster", [(280, 230, 65, (40, 100, 50))]),
            (d, "needle_cluster", [(350, 240, 60, (40, 100, 50))]),
            (d, "needle_cluster", [(310, 150, 55, (40, 100, 50))]),
            (d, "berry", [(310, 170, 10, (220, 35, 35)), (290, 190, 9, (215, 30, 30)), (330, 185, 10, (225, 40, 40)), (310, 145, 8, (210, 28, 28)), (290, 160, 9, (218, 33, 33))]),
        ],
        "emoji": "🌲"
    },
}


class Command(BaseCommand):
    help = "生成浅绿背景动漫风格植物插画"

    def handle(self, *args, **options):
        media_dir = "media/plants"
        os.makedirs(media_dir, exist_ok=True)
        count = 0

        for plant in PlantInfo.objects.filter(is_deleted=False):
            config = PLANTS.get(plant.name_cn)
            if not config:
                continue
            filename = f"plant_{plant.id}.png"
            filepath = os.path.join(media_dir, filename)
            self._draw_anime(filepath, config, plant.name_cn, plant.name_en)
            plant.cover_image = f"plants/{filename}"
            plant.save(update_fields=["cover_image"])
            count += 1
            self.stdout.write(f"  Drawn: {plant.name_cn}")

        self.stdout.write(self.style.SUCCESS(f"Done! {count} anime plant illustrations."))

    def _draw_anime(self, filepath, config, name_cn, name_en):
        w, h = 800, 500
        bg_color = config["bg"]

        # 背景
        img = Image.new("RGBA", (w, h), (bg_color[0], bg_color[1], bg_color[2], 255))
        draw = ImageDraw.Draw(img)

        # 装饰圆点（动漫风格常见背景纹理）
        for _ in range(15):
            dx = random.randint(30, w - 30)
            dy = random.randint(30, h - 80)
            dr = random.randint(20, 60)
            alpha = random.randint(5, 12)
            lighter = tuple(min(255, c + 10) for c in bg_color)
            draw.ellipse([dx - dr, dy - dr, dx + dr, dy + dr],
                        fill=lighter + (alpha,))

        # 装饰小十字星
        for _ in range(12):
            sx = random.randint(40, w - 40)
            sy = random.randint(40, h - 100)
            ss = random.randint(3, 7)
            draw.line([sx - ss, sy, sx + ss, sy], fill=(100, 180, 100, 60), width=1)
            draw.line([sx, sy - ss, sx, sy + ss], fill=(100, 180, 100, 60), width=1)

        # 绘制植物
        instructions = config["draw"](draw)
        for instr in instructions:
            self._exec_draw(draw, instr)

        # 标题卡片
        card_w, card_h = min(500, len(name_cn) * 24 + 80), 70
        card_x = (w - card_w) // 2
        card_y = h - 85
        draw_rounded_rect(draw, [card_x, card_y, card_x + card_w, card_y + card_h], 16,
                         fill=(255, 255, 255, 220))
        draw_rounded_rect(draw, [card_x + 1, card_y + 1, card_x + card_w - 1, card_y + card_h - 1], 15,
                         fill=(255, 255, 255, 235))

        # 文字
        try:
            font_cn = ImageFont.truetype("msyh.ttc", 28)
        except:
            try:
                font_cn = ImageFont.truetype("simsun.ttc", 28)
            except:
                font_cn = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), name_cn, font=font_cn)
        tx = card_x + (card_w - (bbox[2] - bbox[0])) // 2
        draw.text((tx, card_y + 10), name_cn, font=font_cn, fill=(40, 80, 40))

        if name_en:
            try:
                font_en = ImageFont.truetype("consola.ttf", 14)
            except:
                font_en = ImageFont.load_default()
            bbox2 = draw.textbbox((0, 0), name_en, font=font_en)
            tx2 = card_x + (card_w - (bbox2[2] - bbox2[0])) // 2
            draw.text((tx2, card_y + 42), name_en, font=font_en, fill=(100, 140, 100))

        img.save(filepath, "PNG", optimize=True)

    def _exec_draw(self, draw, instr):
        cmd = instr[0]
        args = instr[1]

        if cmd == "stem":
            x1, y1, x2, y2, w, color = args
            draw.line([x1, y1, x2, y2], fill=color, width=w)

        elif cmd == "flower":
            cx, cy, sz, pc, cc = args
            draw_anime_flower(draw, cx, cy, sz, pc, cc)

        elif cmd == "leaf":
            for leaf_args in args:
                cx, cy, sz, ang, color = leaf_args
                draw_anime_leaf(draw, cx, cy, sz, ang, color)

        elif cmd == "berry":
            for bx, by, br, color in args:
                draw.ellipse([bx - br, by - br, bx + br, by + br], fill=color)
                draw.ellipse([bx - br * 0.35, by - br * 0.5, bx + br * 0.1, by - br * 0.15],
                            fill=(255, 255, 255, 150))
                draw.ellipse([bx - br * 0.1, by + br * 0.2, bx + br * 0.15, by + br * 0.4],
                            fill=(255, 255, 255, 60))

        elif cmd == "body":
            x1, y1, x2, y2, color = args
            draw.ellipse([x1, y1, x2, y2], fill=color, outline=tuple(max(0, c - 30) for c in color), width=3)
            draw.line([(x1 + x2) // 2, y1 + 10, (x1 + x2) // 2, y2 - 10],
                     fill=tuple(max(0, c - 15) for c in color), width=2)

        elif cmd == "body2":
            x1, y1, x2, y2, color = args
            draw.ellipse([x1, y1, x2, y2], fill=color, outline=tuple(max(0, c - 30) for c in color), width=3)

        elif cmd == "spines":
            pass  # spines drawn elsewhere

        elif cmd == "pad":
            cx, cy, sz, color = args
            draw.ellipse([cx - sz * 0.7, cy - sz * 0.4, cx + sz * 0.7, cy + sz * 0.4],
                        fill=color, outline=tuple(max(0, c - 30) for c in color), width=2)
            notch = sz * 0.35
            draw.polygon([(cx, cy), (cx - notch, cy - notch), (cx + notch, cy - notch)],
                        fill=bg_color) if 'bg_color' in dir() else None
            draw.line([cx, cy, cx, cy - sz * 0.8], fill=tuple(max(0, c - 40) for c in color), width=2)

        elif cmd == "trunk":
            x1, y1, x2, y2, w, color = args
            draw.line([x1, y1, x2, y2], fill=color, width=w)

        elif cmd == "needle_cluster":
            cx, cy, sz, color = args
            for ni in range(20):
                na = ni * 2 * math.pi / 20 + random.uniform(-0.1, 0.1)
                nd = sz * random.uniform(0.3, 0.7)
                nx = cx + nd * math.cos(na)
                ny = cy + nd * math.sin(na)
                nl = sz * random.uniform(0.2, 0.4)
                draw.line([nx, ny, nx + nl * math.cos(na), ny + nl * math.sin(na)],
                         fill=color, width=2)
