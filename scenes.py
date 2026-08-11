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

from PIL import Image, ImageChops, ImageDraw, ImageFilter

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
    """Классическая кривая сердца — доли смыкаются без провала между ними."""
    k = size / 34.0
    pts = []
    for i in range(96):
        t = i * 2 * math.pi / 96
        x = 16 * math.sin(t) ** 3
        y = (13 * math.cos(t) - 5 * math.cos(2 * t)
             - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts += sbox([cx + x * k, cy - y * k])
    d.polygon(pts, fill=color + (alpha,))


# --- окружение (слой back) ---------------------------------------------------


def planet(img):
    """Планета под ногами: шар с кольцом. Заднюю дугу кольца рисуем до шара,
    переднюю — после, иначе кольцо читается как две отдельные линии."""
    cx, cy, r = 620, 1560, 660

    lay, d = layer(img)
    d.ellipse(sbox([cx - r, cy - r, cx + r, cy + r]), fill=PLANET + (255,))
    d.ellipse(sbox([cx - r + 40, cy - r + 30, cx + r - 40, cy + r]),
              fill=(140, 124, 246, 255))
    for kx, ky, kr in ((392, 1024, 82), (790, 1078, 60), (612, 968, 44),
                       (900, 992, 38), (540, 1120, 52)):
        d.ellipse(sbox([kx - kr, ky - kr * 0.62, kx + kr, ky + kr * 0.62]),
                  fill=PLANET_DARK + (255,))
    img.alpha_composite(lay)

    # тень персонажа на поверхности
    soft(img, PLANET_DARK, 150,
         lambda dd: dd.ellipse(sbox([454, 892, 786, 950]), fill=255), blur=s(16))




def hearts_around(img):
    """Сердечки вокруг персонажа — «любовь к себе»."""
    lay, d = layer(img)
    ring = ((214, 352, 112), (1032, 300, 92), (150, 676, 68), (1096, 654, 78),
            (376, 152, 62), (884, 176, 80), (438, 990, 58), (836, 966, 66))
    for i, (cx, cy, size) in enumerate(ring):
        color = RED if i % 2 == 0 else (255, 156, 176)
        heart(d, cx, cy, size, color, 255 if i % 2 == 0 else 225)
    img.alpha_composite(lay)


def planets_small(img):
    """Маленькие планеты по углам — космический фон."""
    lay, d = layer(img)
    for cx, cy, r, col in ((158, 206, 52, ACCENT), (1092, 806, 58, RING)):
        d.ellipse(sbox([cx - r, cy - r, cx + r, cy + r]), fill=col + (255,))
        d.ellipse(sbox([cx - r * 1.7, cy - r * 0.42, cx + r * 1.7, cy + r * 0.42]),
                  outline=col + (170,), width=int(s(9)))
    img.alpha_composite(lay)


def big_question(img):
    """Крупный знак вопроса у головы."""
    lay, d = layer(img)
    cs.stroke_arc(d, [872, 168, 1032, 328], 175, 20, ACCENT, 30)
    d.line(sbox([1016, 268, 952, 340]), fill=ACCENT + (255,), width=int(s(30)))
    d.ellipse(sbox([924, 374, 984, 434]), fill=ACCENT + (255,))
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
    # хвостик пузыря — выше грани луча, чтобы звезда на него не заходила
    d.ellipse(sbox([818, 368, 874, 424]), fill=CLOUD + (255,))
    # в пузыре — многоточие: персонаж задумался
    for k, dx in enumerate((-84, 0, 84)):
        r = 26
        d.ellipse(sbox([962 + dx - r, 248 - r, 962 + dx + r, 248 + r]),
                  fill=ACCENT + (255 - k * 30,))
    img.alpha_composite(lay)


# --- реквизит поверх персонажа (слой front) ----------------------------------


HAND = (228, 166, 8)          # цвет кисти: тело + тон конечности


def hands_over(img, arm="hold", dy=0.0, spread=0.0):
    """Руки целиком поверх предмета — он оказывается в руках, а не за ними.
    Рисуем те же капсулы, что в силуэте, поэтому это читается как руки,
    а не как отдельные «лапки»."""
    dx, cy, w, h, tilt = cs.ARMS[arm]
    m = Image.new("L", img.size, 0)
    cs.rotated_capsule(m, cs.CX - dx - spread, cy + dy, w, h, -tilt)
    cs.rotated_capsule(m, cs.CX + dx + spread, cy + dy, w, h, tilt)
    lay = Image.new("RGBA", img.size, HAND + (0,))
    lay.putalpha(m)
    img.alpha_composite(lay)


def hands_heart(img):
    hands_over(img)


def hands_notepad(img):
    hands_over(img)


LEG = (236, 176, 14)          # ноги светлее корпуса — не сливаются


def mat(img):
    """Подушка, на которой персонаж сидит: верх подушки заходит под ноги,
    сверху ложится тень от фигуры — иначе он «висит» над ней."""
    lay, d = layer(img)
    d.ellipse(sbox([332, 790, 908, 952]), fill=ACCENT + (255,))
    d.ellipse(sbox([374, 806, 866, 928]), fill=RING + (255,))
    img.alpha_composite(lay)

    soft(img, (86, 74, 178), 150,
         lambda dd: dd.ellipse(sbox([420, 800, 820, 892]), fill=255), blur=s(18))


def bed(img):
    """Изголовье кровати и подушка за спиной."""
    lay, d = layer(img)
    d.rounded_rectangle(sbox([168, 372, 1072, 1064]), radius=s(76),
                        fill=ACCENT + (255,))
    d.rounded_rectangle(sbox([214, 432, 1026, 1012]), radius=s(56),
                        fill=RING + (255,))
    d.rounded_rectangle(sbox([286, 520, 954, 812]), radius=s(112),
                        fill=CLOUD + (255,))
    img.alpha_composite(lay)


def blanket(img):
    """Одеяло поверх нижней части тела."""
    lay, d = layer(img)
    d.rounded_rectangle(sbox([168, 848, 1072, 1110]), radius=s(64),
                        fill=(150, 136, 244, 255))
    d.rounded_rectangle(sbox([168, 848, 1072, 928]), radius=s(44),
                        fill=CLOUD + (255,))
    img.alpha_composite(lay)


def lotus_legs(img):
    """Только скрещённые ноги: руки персонаж держит сам, из своих плеч."""
    legs = Image.new("L", img.size, 0)
    cs.rotated_capsule(legs, cs.CX - 66, 822, 168, 84, -10)
    cs.rotated_capsule(legs, cs.CX + 66, 834, 168, 84, 10)
    lay = Image.new("RGBA", img.size, LEG + (0,))
    lay.putalpha(legs)
    img.alpha_composite(lay)

    edge = cs.star_mask(img.size).filter(ImageFilter.GaussianBlur(s(18)))
    cs.tint(img, cs.LIMB_SHADE, 120, ImageChops.multiply(edge, legs))


def hands_clap(img):
    """Ладони поверх корпуса, одна чуть выше другой — движение хлопка."""
    dx, cy, w, h, tilt = cs.ARMS["clap"]
    m = Image.new("L", img.size, 0)
    cs.rotated_capsule(m, cs.CX - dx, cy - 22, w, h, -tilt - 10)
    cs.rotated_capsule(m, cs.CX + dx, cy + 18, w, h, tilt + 10)
    lay = Image.new("RGBA", img.size, HAND + (0,))
    lay.putalpha(m)
    img.alpha_composite(lay)


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
    d.arc(sbox([344, 216, 896, 796]), 186, 354, fill=METAL + (255,),
          width=int(s(44)))
    for ex in (344, 896):
        d.ellipse(sbox([ex - 124, 418, ex + 124, 666]), fill=METAL + (255,))
        d.ellipse(sbox([ex - 84, 458, ex + 84, 626]), fill=METAL_LIGHT + (255,))
    img.alpha_composite(lay)


def music_notes(img):
    """Нотки рядом с головой."""
    lay, d = layer(img)
    for nx, ny, k in ((1010, 296, 0.9), (232, 336, 0.8)):
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
    d.polygon([*sbox([448, 428]), *sbox([792, 428]), *sbox([742, 122])],
              fill=ACCENT + (255,))
    d.rounded_rectangle(sbox([436, 388, 804, 468]), radius=s(40),
                        fill=CLOUD + (255,))
    d.ellipse(sbox([694, 62, 792, 160]), fill=CLOUD + (255,))
    img.alpha_composite(lay)


def beanie(img):
    """Шапочка — «стиль дня»."""
    lay, d = layer(img)
    d.pieslice(sbox([474, 214, 766, 600]), 180, 360, fill=ACCENT + (255,))
    d.rounded_rectangle(sbox([458, 398, 782, 466]), radius=s(32),
                        fill=RING + (255,))
    d.ellipse(sbox([586, 176, 654, 244]), fill=RING + (255,))
    img.alpha_composite(lay)


def press_hat(img):
    """Шляпа журналиста: поля, тулья и карточка PRESS."""
    lay, d = layer(img)
    d.rounded_rectangle(sbox([362, 396, 878, 456]), radius=s(30),
                        fill=METAL + (255,))
    d.rounded_rectangle(sbox([454, 176, 786, 410]), radius=s(44),
                        fill=METAL_LIGHT + (255,))
    d.rounded_rectangle(sbox([450, 340, 790, 404]), radius=s(22),
                        fill=METAL + (255,))
    d.rounded_rectangle(sbox([694, 320, 848, 412]), radius=s(16),
                        fill=PAPER + (255,))
    for i in range(3):
        d.line(sbox([714, 344 + i * 22, 828, 344 + i * 22]),
               fill=PAPER_LINE + (255,), width=int(s(8)))
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
    d.rounded_rectangle(sbox([478, 678, 762, 886]), radius=s(24),
                        fill=PAPER + (255,))
    d.rounded_rectangle(sbox([478, 678, 528, 886]), radius=s(24),
                        fill=ACCENT + (255,))
    for i in range(4):
        d.line(sbox([556, 730 + i * 42, 730, 730 + i * 42]),
               fill=PAPER_LINE + (255,), width=int(s(10)))
    img.alpha_composite(lay)


def card(img):
    """Карточка с текстом-заглушкой."""
    lay, d = layer(img)
    d.rounded_rectangle(sbox([474, 680, 766, 888]), radius=s(26),
                        fill=PAPER + (255,))
    d.rounded_rectangle(sbox([474, 680, 766, 738]), radius=s(26),
                        fill=ACCENT + (255,))
    d.rectangle(sbox([474, 722, 766, 738]), fill=ACCENT + (255,))
    for i, w in enumerate((222, 182, 142)):
        d.rounded_rectangle(sbox([504, 772 + i * 38, 504 + w, 796 + i * 38]),
                            radius=s(12), fill=PAPER_LINE + (255,))
    img.alpha_composite(lay)


def letter(img):
    """Конверт и перо — «письмо себе»."""
    lay, d = layer(img)
    d.rounded_rectangle(sbox([478, 684, 762, 876]), radius=s(22),
                        fill=PAPER + (255,))
    d.polygon([*sbox([478, 698]), *sbox([620, 796]), *sbox([762, 698])],
              fill=CLOUD + (255,))
    d.line(sbox([478, 698, 620, 796, 762, 698]), fill=PAPER_LINE + (255,),
           width=int(s(8)), joint="curve")
    heart(d, 620, 836, 62, RED)
    img.alpha_composite(lay)


def big_heart(img):
    """Большое сердце в руках."""
    lay, d = layer(img)
    heart(d, 620, 796, 296, RED)
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
    cx = 962
    d.polygon([*sbox([cx, 196]), *sbox([cx + 82, 360]), *sbox([cx - 82, 360])],
              fill=RED + (255,))
    d.rounded_rectangle(sbox([cx - 82, 332, cx + 82, 704]), radius=s(60),
                        fill=PAPER + (255,))
    d.ellipse(sbox([cx - 44, 416, cx + 44, 504]), fill=ACCENT + (255,))
    d.polygon([*sbox([cx - 82, 580]), *sbox([cx - 168, 734]), *sbox([cx - 82, 704])],
              fill=RED + (255,))
    d.polygon([*sbox([cx + 82, 580]), *sbox([cx + 168, 734]), *sbox([cx + 82, 704])],
              fill=RED + (255,))
    d.polygon([*sbox([cx - 58, 704]), *sbox([cx + 58, 704]), *sbox([cx, 872])],
              fill=STAR_LIGHT + (255,))
    d.polygon([*sbox([cx - 30, 704]), *sbox([cx + 30, 704]), *sbox([cx, 810])],
              fill=(255, 236, 170, 255))
    img.alpha_composite(lay)


def clap_lines(img):
    """Дужки у сведённых ладоней — аплодисменты."""
    lay, d = layer(img)
    for cx, cy, a0, a1 in ((436, 706, 136, 224), (804, 748, 316, 44)):
        for r in (52, 84):
            d.arc(sbox([cx - r, cy - r, cx + r, cy + r]), a0, a1,
                  fill=cs.MOTION + (255,), width=int(s(14)))
    img.alpha_composite(lay)


def point_lines(img):
    """Штрихи у указывающей руки."""
    lay, d = layer(img)
    for r in (74, 112):
        d.arc(sbox([1074 - r, 556 - r, 1074 + r, 556 + r]), 302, 58,
              fill=cs.MOTION + (255,), width=int(s(13)))
    img.alpha_composite(lay)


# --- сцены -------------------------------------------------------------------
# pose/face/props — персонаж, back/front — декорации до и после него.

def F(**kw):                     # короткая запись лица
    return kw


SCENES: dict[str, dict] = {
    # основные экраны
    "splash": dict(pose="sit", face=F(mouth="wide"), title="Сплэш: сидит на облаке",
                   back=[planets_small], front=[cloud], arm="wave"),
    "welcome": dict(pose="wave", face=F(mouth="wide"), title="Онбординг: приветствие",
                    back=[planet, planets_small]),
    "home": dict(pose="idle", face=F(eyes="closed", brows="none", mouth="smile"),
                 title="Главный экран: в наушниках",
                 back=[music_notes], front=[headphones]),
    "profile": dict(pose="idle", face=F(eyes="wink", mouth="wide"),
                    title="Профиль: подмигивает", back=[planet]),
    "obtrack": dict(pose="wave", face=F(mouth="wide"), title="План готов: с флагом",
                    motion=False, back=[planet], front=[flag]),
    "lessoncomplete": dict(pose="sit_hold", face=F(eyes="sleepy", mouth="small"),
                           title="Урок пройден: спит с подушкой",
                           props=("zzz",), back=[pillow], front=[nightcap]),

    # онбординг
    "ob1": dict(pose="idle", face=F(eyes="up", brows="raised", mouth="think"),
                title="Онбординг 1: задумчивая", back=[think_bubble]),
    "ob2": dict(pose="idle", face=F(eyes="wide", brows="raised", mouth="small"),
                title="Онбординг 2: вопрос", back=[big_question]),
    "ob3": dict(pose="idle", face=F(eyes="closed", brows="none", mouth="smile"),
                title="Онбординг 3 / курс / урок: в наушниках",
                back=[music_notes], front=[headphones]),
    "ob4": dict(pose="hold", face=F(eyes="closed", brows="none", mouth="smile"),
                title="Онбординг 4: держит сердце", blush=210,
                front=[big_heart, hands_heart]),

    # упражнения
    "exercise-1": dict(pose="hug", face=F(brows="angry", mouth="sad"),
                       title="Упражнение: сердится"),
    "ex1": dict(pose="hold", face=F(mouth="smile"), title="С блокнотом",
                front=[notepad, hands_notepad]),
    "ex2": dict(pose="idle", face=F(brows="sad", mouth="sad"), title="Грустная",
                props=("tear",)),
    "ex3": dict(pose="point", face=F(brows="raised", mouth="wide"),
                title="Указывает"),
    "ex4": dict(pose="idle", face=F(mouth="smile"), title="Шляпа журналиста",
                front=[press_hat]),
    "ex5a": dict(pose="hold", face=F(mouth="smile"), title="Держит карточку",
                 front=[card, hands_notepad]),
    "ex5b": dict(pose="idle", face=F(eyes="closed", brows="none", mouth="wide"),
                 title="Улыбается"),
    "ex6": dict(pose="hug", face=F(eyes="closed", brows="none", mouth="smile"),
                title="Вокруг сердечки", back=[hearts_around], blush=215),
    "ex7": dict(pose="clap", face=F(eyes="closed", brows="none", mouth="open"),
                title="Аплодирует", front=[hands_clap, clap_lines]),
    "ex8": dict(pose="hold", face=F(mouth="smile"), title="Пишет письмо",
                front=[letter, hands_notepad]),
    "ex9": dict(pose="cheer", face=F(eyes="sparkle", brows="raised", mouth="open"),
                title="С ракетой", back=[rocket]),
    "ex10": dict(pose="hold", face=F(eyes="closed", brows="none", mouth="smile"),
                 title="Держит сердце", blush=210,
                 front=[big_heart, hands_heart]),

    # практики
    "breathcomplete": dict(pose="idle", face=F(eyes="sleepy", mouth="smile"),
                           title="Дыхание завершено"),
    "affirmcomplete": dict(pose="idle", face=F(eyes="closed", brows="none",
                                               mouth="smile"), blush=210,
                           title="Аффирмации завершены",
                           back=[hearts_around]),
    "meditation": dict(pose="lotus", face=F(eyes="sleepy", mouth="smile"),
                       title="Медитация: поза лотоса",
                       back=[planets_small, mat],
                       front=[lotus_legs]),
    "meditationcomplete": dict(pose="lotus", face=F(eyes="closed", brows="none",
                                                    mouth="smile"),
                               title="Медитация завершена",
                               back=[mat], front=[lotus_legs]),

    "sleeping": dict(pose="sit", face=F(eyes="sleepy", brows="normal",
                                        mouth="small"),
                     title="Дремлет в кровати", props=("zzz",),
                     back=[bed], front=[blanket, nightcap]),

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
