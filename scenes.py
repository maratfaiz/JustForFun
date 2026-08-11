"""Сцены маскота для приложения: облако, планета, наушники, реквизит и т.д.

Каждая сцена — запись в SCENES: поза, лицо, реквизит и слои окружения.
Персонажа рисует cute_star, здесь только «декорации».

    python3 scenes.py                    # -> scenes.png (контактный лист)
    python3 scenes.py --export assets    # -> assets/mascot-<name>.png
"""

from __future__ import annotations

import argparse
import math
import os

from PIL import Image, ImageDraw, ImageFilter

import cute_star as cs
from cute_star import s, sbox

# --- палитра декораций -------------------------------------------------------

CLOUD = (240, 244, 255)
CLOUD_SHADE = (214, 223, 246)
PLANET = (126, 110, 238)
PLANET_DARK = (96, 82, 200)
RING = (176, 166, 250)
ACCENT = (124, 108, 240)
METAL = (78, 86, 120)
METAL_LIGHT = (116, 126, 168)
PAPER = (250, 250, 253)
PAPER_LINE = (186, 196, 220)
INK = (96, 106, 140)
RED = (238, 96, 106)
GREEN = (96, 200, 156)
WOOD = (198, 154, 96)
STAR_LIGHT = (255, 226, 130)


def layer(img):
    """Новый прозрачный слой поверх картинки + его ImageDraw."""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    return lay, ImageDraw.Draw(lay)


def soft(img, color, alpha, painter, blur):
    img.alpha_composite(cs.soft_layer(img.size, color, alpha, painter, blur=blur))


def star4(d, cx, cy, size, color, alpha=255):
    """Четырёхлучевая искра."""
    a, b = size, size * 0.24
    d.polygon([*sbox([cx, cy - a]), *sbox([cx + b, cy - b]),
               *sbox([cx + a, cy]), *sbox([cx + b, cy + b]),
               *sbox([cx, cy + a]), *sbox([cx - b, cy + b]),
               *sbox([cx - a, cy]), *sbox([cx - b, cy - b])],
              fill=color + (alpha,))


def heart(d, cx, cy, size, color, alpha=255):
    r = size / 2
    d.ellipse(sbox([cx - r, cy - r * 0.9, cx, cy + r * 0.2]), fill=color + (alpha,))
    d.ellipse(sbox([cx, cy - r * 0.9, cx + r, cy + r * 0.2]), fill=color + (alpha,))
    d.polygon([*sbox([cx - r * 0.96, cy - r * 0.1]),
               *sbox([cx + r * 0.96, cy - r * 0.1]),
               *sbox([cx, cy + r])], fill=color + (alpha,))


# --- окружение (слой back) ---------------------------------------------------


def stars_around(img):
    """Звёздная россыпь вокруг персонажа."""
    lay, d = layer(img)
    for cx, cy, size in ((196, 268, 34), (1044, 214, 42), (312, 660, 22),
                         (964, 700, 26), (150, 486, 18), (1092, 462, 20),
                         (420, 150, 20), (830, 120, 26)):
        star4(d, cx, cy, size, STAR_LIGHT)
    img.alpha_composite(lay)


def floating_stars(img):
    """Звёзды по кругу — «парят» вокруг медитирующего."""
    lay, d = layer(img)
    for i in range(8):
        a = math.radians(-20 + i * 45)
        cx, cy = 620 + 470 * math.cos(a), 540 + 400 * math.sin(a)
        star4(d, cx, cy, 20 + 12 * (i % 3), STAR_LIGHT, 235)
    img.alpha_composite(lay)


def planet(img):
    """Планета под ногами: шар с кольцом. Заднюю дугу кольца рисуем до шара,
    переднюю — после, иначе кольцо читается как две отдельные линии."""
    cx, cy, r = 620, 1560, 660

    lay, d = layer(img)
    d.ellipse(sbox([cx - r, cy - r, cx + r, cy + r]), fill=PLANET + (255,))
    d.ellipse(sbox([cx - r + 40, cy - r + 30, cx + r - 40, cy + r]),
              fill=(140, 124, 246, 255))
    for kx, ky, kr in ((404, 1012, 54), (782, 1064, 38), (612, 972, 28),
                       (884, 986, 24)):
        d.ellipse(sbox([kx - kr, ky - kr * 0.62, kx + kr, ky + kr * 0.62]),
                  fill=PLANET_DARK + (255,))
    img.alpha_composite(lay)

    # тень персонажа на поверхности
    soft(img, PLANET_DARK, 150,
         lambda dd: dd.ellipse(sbox([454, 892, 786, 950]), fill=255), blur=s(16))




def aura(img):
    """Тёплое сияние вокруг фигуры — «умиротворение»."""
    soft(img, (255, 214, 96), 150,
         lambda d: d.ellipse(sbox([260, 210, 980, 930]), fill=255), blur=s(70))
    lay, d = layer(img)
    for i in range(12):
        a = math.radians(i * 30)
        cx, cy = 620 + 430 * math.cos(a), 560 + 400 * math.sin(a)
        star4(d, cx, cy, 16, STAR_LIGHT, 220)
    img.alpha_composite(lay)


def hearts_around(img):
    """Сердечки вокруг персонажа — «любовь к себе»."""
    lay, d = layer(img)
    ring = ((196, 352, 92), (1036, 306, 80), (150, 640, 60), (1094, 610, 68),
            (330, 148, 56), (902, 118, 70), (388, 962, 52), (872, 986, 58),
            (66, 452, 44), (1176, 452, 48))
    for i, (cx, cy, size) in enumerate(ring):
        color = RED if i % 2 == 0 else (255, 156, 176)
        heart(d, cx, cy, size, color, 255 if i % 2 == 0 else 225)
    img.alpha_composite(lay)


def sparkle_burst(img):
    """Салют из искр — радость и восторг."""
    lay, d = layer(img)
    for i in range(14):
        a = math.radians(-90 + i * 360 / 14)
        r = 430 + (60 if i % 2 else 0)
        cx, cy = 620 + r * math.cos(a) * 1.05, 540 + r * math.sin(a) * 0.95
        star4(d, cx, cy, 20 + 14 * (i % 3), STAR_LIGHT, 245)
    img.alpha_composite(lay)


def planets_small(img):
    """Маленькие планеты по углам — космический фон."""
    lay, d = layer(img)
    for cx, cy, r, col in ((172, 214, 62, ACCENT), (1064, 852, 78, RING),
                           (1108, 176, 44, GREEN)):
        d.ellipse(sbox([cx - r, cy - r, cx + r, cy + r]), fill=col + (255,))
        d.ellipse(sbox([cx - r * 1.7, cy - r * 0.42, cx + r * 1.7, cy + r * 0.42]),
                  outline=col + (170,), width=int(s(9)))
    img.alpha_composite(lay)


def mat(img):
    """Коврик-подушка под медитирующим."""
    lay, d = layer(img)
    d.ellipse(sbox([392, 806, 848, 950]), fill=ACCENT + (255,))
    d.ellipse(sbox([430, 826, 810, 920]), fill=RING + (255,))
    img.alpha_composite(lay)


def big_question(img):
    """Крупный знак вопроса у головы."""
    lay, d = layer(img)
    cs.stroke_arc(d, [852, 176, 1012, 336], 175, 20, ACCENT, 26)
    d.line(sbox([1000, 288, 936, 366]), fill=ACCENT + (255,), width=int(s(26)))
    d.ellipse(sbox([916, 398, 964, 446]), fill=ACCENT + (255,))
    img.alpha_composite(lay)


def small_question(img):
    """Небольшой знак вопроса слева от головы."""
    lay, d = layer(img)
    cs.stroke_arc(d, [214, 268, 334, 388], 175, 20, ACCENT, 20)
    d.line(sbox([324, 356, 276, 414]), fill=ACCENT + (255,), width=int(s(20)))
    d.ellipse(sbox([258, 440, 296, 478]), fill=ACCENT + (255,))
    img.alpha_composite(lay)


def think_bubble(img):
    """Пузырь размышления с сердцем внутри."""
    lay, d = layer(img)
    d.ellipse(sbox([812, 128, 1112, 368]), fill=CLOUD + (255,))
    d.ellipse(sbox([796, 386, 856, 446]), fill=CLOUD + (255,))
    d.ellipse(sbox([764, 462, 800, 498]), fill=CLOUD + (255,))
    heart(d, 962, 246, 128, RED)
    img.alpha_composite(lay)


# --- реквизит поверх персонажа (слой front) ----------------------------------


def cloud(img):
    """Облако, в котором персонаж сидит: рисуется поверх ножек."""
    lay, d = layer(img)
    for bx, by, rx, ry in ((620, 1002, 356, 128), (372, 1010, 188, 98),
                           (868, 1006, 194, 102), (490, 952, 156, 90),
                           (750, 956, 164, 92), (620, 936, 178, 86)):
        d.ellipse(sbox([bx - rx, by - ry, bx + rx, by + ry]), fill=CLOUD + (255,))
    for bx, by, rx, ry in ((452, 1070, 168, 40), (790, 1068, 176, 40)):
        d.ellipse(sbox([bx - rx, by - ry, bx + rx, by + ry]),
                  fill=CLOUD_SHADE + (255,))
    img.alpha_composite(lay)


def headphones(img):
    """Наушники: дуга через верхний луч и две чашки по бокам."""
    lay, d = layer(img)
    d.arc(sbox([382, 236, 858, 712]), 198, 342, fill=METAL + (255,),
          width=int(s(36)))
    for ex in (396, 844):
        d.rounded_rectangle(sbox([ex - 54, 398, ex + 54, 566]), radius=s(50),
                            fill=METAL + (255,))
        d.rounded_rectangle(sbox([ex - 34, 420, ex + 34, 544]), radius=s(32),
                            fill=METAL_LIGHT + (255,))
    img.alpha_composite(lay)


def music_notes(img):
    """Нотки рядом с головой."""
    lay, d = layer(img)
    for nx, ny, k in ((968, 300, 1.0), (1080, 420, 0.8), (232, 360, 0.9)):
        r = 34 * k
        d.ellipse(sbox([nx - r, ny - r * 0.8, nx + r, ny + r * 0.8]),
                  fill=ACCENT + (255,))
        d.rectangle(sbox([nx + r - 12 * k, ny - 128 * k, nx + r, ny]),
                    fill=ACCENT + (255,))
        d.ellipse(sbox([nx + r - 14 * k, ny - 138 * k, nx + r + 44 * k,
                        ny - 96 * k]), fill=ACCENT + (255,))
    img.alpha_composite(lay)


def nightcap(img):
    """Колпак для сна на верхнем луче."""
    lay, d = layer(img)
    d.polygon([*sbox([498, 398]), *sbox([742, 398]), *sbox([796, 168])],
              fill=ACCENT + (255,))
    d.rounded_rectangle(sbox([484, 368, 756, 436]), radius=s(34),
                        fill=CLOUD + (255,))
    d.ellipse(sbox([756, 122, 842, 208]), fill=CLOUD + (255,))
    img.alpha_composite(lay)


def beanie(img):
    """Шапочка — «стиль дня»."""
    lay, d = layer(img)
    d.pieslice(sbox([474, 156, 766, 402]), 180, 360, fill=ACCENT + (255,))
    d.rounded_rectangle(sbox([462, 326, 778, 386]), radius=s(28),
                        fill=RING + (255,))
    d.ellipse(sbox([588, 108, 652, 172]), fill=RING + (255,))
    img.alpha_composite(lay)


def press_hat(img):
    """Шляпа журналиста: поля, тулья и карточка PRESS."""
    lay, d = layer(img)
    d.rounded_rectangle(sbox([386, 344, 856, 400]), radius=s(28),
                        fill=METAL + (255,))
    d.rounded_rectangle(sbox([470, 168, 772, 358]), radius=s(40),
                        fill=METAL_LIGHT + (255,))
    d.rounded_rectangle(sbox([466, 300, 776, 352]), radius=s(20),
                        fill=METAL + (255,))
    d.rounded_rectangle(sbox([700, 292, 806, 356]), radius=s(12),
                        fill=PAPER + (255,))
    for i in range(3):
        d.line(sbox([714, 308 + i * 16, 792, 308 + i * 16]),
               fill=PAPER_LINE + (255,), width=int(s(6)))
    img.alpha_composite(lay)


def pillow(img):
    """Подушка, которую персонаж обнимает."""
    lay, d = layer(img)
    d.rounded_rectangle(sbox([336, 700, 904, 986]), radius=s(126),
                        fill=CLOUD + (255,))
    d.arc(sbox([396, 754, 844, 936]), 196, 344, fill=CLOUD_SHADE + (255,),
          width=int(s(12)))
    img.alpha_composite(lay)


def notepad(img):
    """Блокнот с карандашом в руках."""
    lay, d = layer(img)
    d.rounded_rectangle(sbox([446, 630, 780, 878]), radius=s(24),
                        fill=PAPER + (255,))
    d.rounded_rectangle(sbox([446, 630, 496, 878]), radius=s(24),
                        fill=ACCENT + (255,))
    for i in range(5):
        d.line(sbox([524, 690 + i * 40, 748, 690 + i * 40]),
               fill=PAPER_LINE + (255,), width=int(s(9)))
    d.line(sbox([806, 604, 742, 752]), fill=WOOD + (255,), width=int(s(22)))
    d.polygon([*sbox([736, 744]), *sbox([760, 756]), *sbox([734, 776])],
              fill=(60, 60, 70, 255))
    img.alpha_composite(lay)


def card(img):
    """Карточка с текстом-заглушкой."""
    lay, d = layer(img)
    d.rounded_rectangle(sbox([420, 636, 812, 880]), radius=s(28),
                        fill=PAPER + (255,))
    d.rounded_rectangle(sbox([420, 636, 812, 704]), radius=s(28),
                        fill=ACCENT + (255,))
    d.rectangle(sbox([420, 686, 812, 704]), fill=ACCENT + (255,))
    for i, w in enumerate((300, 250, 200)):
        d.rounded_rectangle(sbox([456, 736 + i * 44, 456 + w, 764 + i * 44]),
                            radius=s(14), fill=PAPER_LINE + (255,))
    img.alpha_composite(lay)


def letter(img):
    """Конверт и перо — «письмо себе»."""
    lay, d = layer(img)
    d.rounded_rectangle(sbox([436, 654, 800, 872]), radius=s(22),
                        fill=PAPER + (255,))
    d.polygon([*sbox([436, 668]), *sbox([618, 790]), *sbox([800, 668])],
              fill=CLOUD + (255,))
    d.line(sbox([436, 668, 618, 790, 800, 668]), fill=PAPER_LINE + (255,),
           width=int(s(8)), joint="curve")
    heart(d, 618, 826, 64, RED)
    img.alpha_composite(lay)


def big_heart(img):
    """Большое сердце в руках."""
    lay, d = layer(img)
    heart(d, 620, 726, 300, RED)
    heart(d, 566, 676, 78, (255, 178, 186))
    img.alpha_composite(lay)


def flag(img):
    """Флажок в поднятой руке — «план готов»."""
    lay, d = layer(img)
    d.line(sbox([958, 250, 958, 646]), fill=WOOD + (255,), width=int(s(20)))
    d.polygon([*sbox([966, 258]), *sbox([1158, 336]), *sbox([966, 414])],
              fill=GREEN + (255,))
    d.ellipse(sbox([936, 214, 982, 260]), fill=STAR_LIGHT + (255,))
    img.alpha_composite(lay)


def rocket(img):
    """Ракета рядом с персонажем."""
    lay, d = layer(img)
    cx = 966
    d.polygon([*sbox([cx, 236]), *sbox([cx + 82, 400]), *sbox([cx - 82, 400])],
              fill=RED + (255,))
    d.rounded_rectangle(sbox([cx - 82, 372, cx + 82, 744]), radius=s(60),
                        fill=PAPER + (255,))
    d.ellipse(sbox([cx - 44, 456, cx + 44, 544]), fill=ACCENT + (255,))
    d.polygon([*sbox([cx - 82, 620]), *sbox([cx - 168, 774]), *sbox([cx - 82, 744])],
              fill=RED + (255,))
    d.polygon([*sbox([cx + 82, 620]), *sbox([cx + 168, 774]), *sbox([cx + 82, 744])],
              fill=RED + (255,))
    d.polygon([*sbox([cx - 58, 744]), *sbox([cx + 58, 744]), *sbox([cx, 906])],
              fill=STAR_LIGHT + (255,))
    d.polygon([*sbox([cx - 30, 744]), *sbox([cx + 30, 744]), *sbox([cx, 846])],
              fill=(255, 236, 170, 255))
    img.alpha_composite(lay)


def clap_lines(img):
    """Дужки у сведённых ладоней — аплодисменты."""
    lay, d = layer(img)
    for r in (104, 148, 192):
        d.arc(sbox([620 - r, 706 - r, 620 + r, 706 + r]), 196, 252,
              fill=cs.MOTION + (255,), width=int(s(15)))
        d.arc(sbox([620 - r, 706 - r, 620 + r, 706 + r]), 288, 344,
              fill=cs.MOTION + (255,), width=int(s(15)))
    img.alpha_composite(lay)


def point_lines(img):
    """Штрихи у указывающей руки."""
    lay, d = layer(img)
    for r in (66, 98):
        d.arc(sbox([1010 - r, 560 - r, 1010 + r, 560 + r]), 300, 60,
              fill=cs.MOTION + (255,), width=int(s(12)))
    img.alpha_composite(lay)


# --- сцены -------------------------------------------------------------------
# pose/face/props — персонаж, back/front — декорации до и после него.

def F(**kw):                     # короткая запись лица
    return kw


SCENES: dict[str, dict] = {
    # основные экраны
    "splash": dict(pose="sit", face=F(mouth="wide"), title="Сплэш: сидит на облаке",
                   back=[stars_around, planets_small], front=[cloud], arm="wave"),
    "welcome": dict(pose="wave", face=F(mouth="wide"), title="Онбординг: приветствие",
                    back=[planet, stars_around, planets_small]),
    "home": dict(pose="idle", face=F(eyes="closed", brows="none", mouth="smile"),
                 title="Главный экран: в наушниках",
                 back=[music_notes], front=[headphones]),
    "profile": dict(pose="idle", face=F(eyes="wink", mouth="wide"),
                    title="Профиль: подмигивает", back=[planet, stars_around]),
    "obtrack": dict(pose="wave", face=F(mouth="wide"), title="План готов: с флагом",
                    motion=False, back=[planet, stars_around], front=[flag]),
    "lessoncomplete": dict(pose="sit_hold", face=F(eyes="sleepy", mouth="small"),
                           title="Урок пройден: спит с подушкой",
                           props=("zzz",), back=[pillow], front=[nightcap]),

    # онбординг
    "ob1": dict(pose="idle", face=F(eyes="wide", brows="raised", mouth="small"),
                title="Онбординг 1: задумчивая", back=[think_bubble, small_question]),
    "ob2": dict(pose="idle", face=F(eyes="wide", brows="raised", mouth="small"),
                title="Онбординг 2: вопрос", back=[big_question]),
    "ob3": dict(pose="idle", face=F(eyes="closed", brows="none", mouth="smile"),
                title="Онбординг 3 / курс / урок: в наушниках",
                back=[music_notes], front=[headphones]),
    "ob4": dict(pose="hold", face=F(eyes="closed", brows="none", mouth="smile"),
                title="Онбординг 4: держит сердце", blush=210,
                back=[hearts_around], front=[big_heart]),

    # упражнения
    "exercise-1": dict(pose="idle", face=F(brows="angry", mouth="sad"),
                       title="Упражнение: сердится"),
    "ex1": dict(pose="hold", face=F(mouth="smile"), title="С блокнотом",
                front=[notepad]),
    "ex2": dict(pose="idle", face=F(brows="sad", mouth="sad"), title="Грустная",
                props=("tear",)),
    "ex3": dict(pose="point", face=F(brows="raised", mouth="wide"),
                title="Указывает", front=[point_lines]),
    "ex4": dict(pose="idle", face=F(mouth="smile"), title="Шляпа журналиста",
                front=[press_hat]),
    "ex5a": dict(pose="hold", face=F(mouth="smile"), title="Держит карточку",
                 front=[card]),
    "ex5b": dict(pose="idle", face=F(eyes="closed", brows="none", mouth="wide"),
                 title="Улыбается"),
    "ex6": dict(pose="hug", face=F(eyes="closed", brows="none", mouth="smile"),
                title="Вокруг сердечки", back=[hearts_around], blush=215),
    "ex7": dict(pose="clap", face=F(eyes="closed", brows="none", mouth="open"),
                title="Аплодирует", back=[sparkle_burst], front=[clap_lines]),
    "ex8": dict(pose="hold", face=F(mouth="smile"), title="Пишет письмо",
                front=[letter]),
    "ex9": dict(pose="idle", face=F(eyes="sparkle", brows="raised", mouth="open"),
                title="С ракетой", back=[stars_around], front=[rocket]),
    "ex10": dict(pose="hold", face=F(eyes="closed", brows="none", mouth="smile"),
                 title="Держит сердце", blush=210,
                 back=[hearts_around], front=[big_heart]),

    # практики
    "breathcomplete": dict(pose="idle", face=F(eyes="sleepy", mouth="smile"),
                           title="Дыхание завершено", back=[aura]),
    "affirmcomplete": dict(pose="idle", face=F(eyes="closed", brows="none",
                                               mouth="smile"), blush=210,
                           title="Аффирмации завершены",
                           back=[aura, hearts_around]),
    "meditation": dict(pose="lotus", face=F(eyes="sleepy", mouth="smile"),
                       title="Медитация: лотос",
                       back=[floating_stars, planets_small, mat]),
    "meditationcomplete": dict(pose="lotus", face=F(eyes="closed", brows="none",
                                                    mouth="smile"),
                               title="Медитация завершена", back=[aura, mat]),

    # вспомогательные
    "home-wardrobe": dict(pose="idle", face=F(eyes="wink", mouth="wide"),
                          title="Гардероб: стиль дня", front=[beanie]),
    "crisis": dict(pose="idle", face=F(eyes="sleepy", mouth="smile"),
                   title="Кризисный экран: спокойная поддержка"),
}

# алиасы: один файл переиспользуется на нескольких экранах
ALIASES = {"coursepage": "ob3", "lesson": "ob3"}


def render_scene(name: str, size: int = 1024, transparent: bool = True):
    cfg = SCENES[ALIASES.get(name, name)]
    face = dict(cfg.get("face", {}))
    if "blush" in cfg:
        face["blush"] = cfg["blush"]

    # «машет» в сидячей позе: рука берётся из позы wave поверх sit
    pose = cfg["pose"]
    if cfg.get("arm") == "wave":
        cs.POSES["_sit_wave"] = ("down", "up", "sit")
        pose = "_sit_wave"

    return cs.render(size, transparent=transparent, shadow=not transparent,
                     pose=pose, face_override=face, props=cfg.get("props", ()),
                     motion=cfg.get("motion"),
                     back=cfg.get("back", ()), front=cfg.get("front", ()))


def export(folder: str, size: int) -> None:
    os.makedirs(folder, exist_ok=True)
    for name in SCENES:
        render_scene(name, size).save(os.path.join(folder, f"mascot-{name}.png"))
    for alias, target in ALIASES.items():
        render_scene(target, size).save(os.path.join(folder, f"mascot-{alias}.png"))
    print(f"Экспортировано в {folder}/: {len(SCENES) + len(ALIASES)} PNG по {size}px")


def contact_sheet(path: str = "scenes.png", cell: int = 460) -> None:
    from PIL import ImageFont
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    mono = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 20)

    names = list(SCENES)
    cols = 6
    rows = math.ceil(len(names) / cols)
    cw, ch = cell, cell + 76
    sheet = Image.new("RGB", (cols * cw + 40, rows * ch + 120), (18, 23, 42))
    d = ImageDraw.Draw(sheet)
    d.text((28, 44), "СЦЕНЫ МАСКОТА ДЛЯ ПРИЛОЖЕНИЯ", font=font, fill=(255, 255, 255))

    for i, name in enumerate(names):
        x = 20 + (i % cols) * cw
        y = 100 + (i // cols) * ch
        art = render_scene(name, cell - 20).convert("RGBA")
        sheet.paste(art, (x + 10, y), art)
        d.text((x + 12, y + cell - 6), SCENES[name]["title"], font=font,
               fill=(190, 200, 224))
        d.text((x + 12, y + cell + 24), f"mascot-{name}", font=mono,
               fill=(240, 196, 88))
    sheet.save(path)
    print(f"Готово: {path} ({sheet.width}x{sheet.height}), сцен: {len(names)}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Сцены маскота")
    ap.add_argument("--export", metavar="DIR", default=None)
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--sheet", default="scenes.png")
    args = ap.parse_args()

    contact_sheet(args.sheet)
    if args.export:
        export(args.export, args.size)


if __name__ == "__main__":
    main()
