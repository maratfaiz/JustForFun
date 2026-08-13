#!/usr/bin/env python3
"""Набор UI-иконок в стиле Луми.

Иконки рисуются кодом (Pillow) в одной сетке 512x512 с единой толщиной
линии, поэтому весь набор выглядит как одно целое. Экспорт — PNG с
прозрачным фоном, силуэт одним цветом (по умолчанию чёрный): цвет
накладывается в приложении через template rendering.

    python3 icons.py                              # -> icons.png, лист набора
    python3 icons.py --export assets/icons        # все PNG, 1024 px
    python3 icons.py --export assets/icons --colored   # с запечённым цветом
    python3 icons.py --one icon-streak --out /tmp/f.png
"""

from __future__ import annotations

import argparse
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFont

from cute_star import round_polygon

# ── сетка ──────────────────────────────────────────────────────────────
SS = 4                     # суперсэмплинг
CANVAS = 512.0             # логический холст
N = int(CANVAS * SS)       # рабочий холст
C = CANVAS / 2             # центр
W = 38.0                   # базовая толщина линии для всего набора


def s(v: float) -> float:
    return v * SS


def sbox(box):
    return [s(v) for v in box]


# ── примитивы (все рисуют в L-маску; v=0 стирает) ──────────────────────
def line(d, pts, w=W, closed=False, v=255):
    p = [(s(x), s(y)) for x, y in pts]
    if closed:
        p = p + [p[0]]
    d.line(p, fill=v, width=int(round(s(w))), joint="curve")
    if not closed:
        r = s(w) / 2
        for x, y in (p[0], p[-1]):
            d.ellipse([x - r, y - r, x + r, y + r], fill=v)


def disc(d, cx, cy, r, v=255):
    d.ellipse(sbox([cx - r, cy - r, cx + r, cy + r]), fill=v)


def ring(d, cx, cy, r, w=W, v=255):
    """Кольцо со средней линией по радиусу r (PIL рисует толщину внутрь)."""
    o = r + w / 2
    d.ellipse(sbox([cx - o, cy - o, cx + o, cy + o]),
              outline=v, width=int(round(s(w))))


def arc(d, cx, cy, r, a0, a1, w=W, caps=True, v=255):
    o = r + w / 2
    d.arc(sbox([cx - o, cy - o, cx + o, cy + o]), a0, a1,
          fill=v, width=int(round(s(w))))
    if caps:
        for a in (a0, a1):
            disc(d, cx + r * math.cos(math.radians(a)),
                 cy + r * math.sin(math.radians(a)), w / 2, v)


def rrect(d, box, radius, w=None, v=255):
    if w is None:
        d.rounded_rectangle(sbox(box), radius=s(radius), fill=v)
    else:
        d.rounded_rectangle(sbox(box), radius=s(radius),
                            outline=v, width=int(round(s(w))))


def poly(d, pts, radius=0.0, v=255):
    """radius — одно число на все углы или список по вершинам."""
    p = [(s(x), s(y)) for x, y in pts]
    if radius:
        rr = radius if isinstance(radius, (list, tuple)) else [radius] * len(p)
        p = round_polygon(p, [s(r) for r in rr])
    d.polygon(p, fill=v)


def heart_pts(cx, cy, size, n=120):
    """Параметрическое сердце — без стыка между «половинками»."""
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        y = (13 * math.cos(t) - 5 * math.cos(2 * t)
             - 2 * math.cos(3 * t) - math.cos(4 * t))
        out.append((cx + x * size / 16.0, cy - y * size / 16.0))
    return out


def sparkle(d, cx, cy, r, v=255):
    k = 0.26
    poly(d, [(cx, cy - r), (cx + r * k, cy - r * k), (cx + r, cy),
             (cx + r * k, cy + r * k), (cx, cy + r), (cx - r * k, cy + r * k),
             (cx - r, cy), (cx - r * k, cy - r * k)], radius=r * 0.12, v=v)


def merged(m, painter, angle=0.0, center=(C, C)):
    """Рисует painter в отдельную маску, поворачивает и подмешивает в m."""
    tmp = Image.new("L", (N, N), 0)
    painter(ImageDraw.Draw(tmp))
    if angle:
        tmp = tmp.rotate(angle, resample=Image.BICUBIC,
                         center=(s(center[0]), s(center[1])))
    m.paste(ImageChops.lighter(m, tmp), (0, 0))


def clipped(m, painter, clip_painter):
    """Подмешивает painter, обрезанный по маске clip_painter."""
    tmp = Image.new("L", (N, N), 0)
    painter(ImageDraw.Draw(tmp))
    clip = Image.new("L", (N, N), 0)
    clip_painter(ImageDraw.Draw(clip))
    m.paste(ImageChops.lighter(m, ImageChops.multiply(tmp, clip)), (0, 0))


# ── приоритет 1 ────────────────────────────────────────────────────────
def icon_streak(m):
    d = ImageDraw.Draw(m)
    poly(d, [(284, 34), (334, 152), (376, 266), (344, 406), (238, 456),
             (142, 396), (136, 274), (204, 196), (244, 112)],
         radius=[14, 64, 92, 92, 92, 92, 62, 34, 30])
    poly(d, [(258, 250), (306, 342), (290, 406), (232, 418), (200, 360),
             (226, 300)], radius=[14, 46, 52, 52, 46, 34], v=0)  # язычок


def icon_lumen(m):
    d = ImageDraw.Draw(m)
    ring(d, C, C, 148, 36)
    pts = []
    for i in range(10):
        a = math.radians(90 + i * 36)
        r = 86 if i % 2 == 0 else 38
        pts.append((C + r * math.cos(a), C - r * math.sin(a)))
    poly(d, pts, radius=10)


def icon_freeze(m):
    d = ImageDraw.Draw(m)
    w = 30.0
    for k in range(6):
        a = math.radians(k * 60)
        ux, uy = math.cos(a), math.sin(a)
        tip = (C + ux * 176, C + uy * 176)
        line(d, [(C, C), tip], w)
        for frac, blen in ((0.52, 58.0), (0.80, 44.0)):
            bx, by = C + ux * 176 * frac, C + uy * 176 * frac
            for side in (+40, -40):
                b = math.radians(k * 60 + side)
                line(d, [(bx, by),
                         (bx + math.cos(b) * blen, by + math.sin(b) * blen)], w)


def icon_tab_courses(m):
    d = ImageDraw.Draw(m)
    # раскрытая книга: две страницы с прогибом к корешку
    left = [(62, 148), (232, 178), (232, 396), (62, 366)]
    right = [(450, 148), (280, 178), (280, 396), (450, 366)]
    poly(d, left, radius=26)
    poly(d, right, radius=26)
    rrect(d, [240, 168, 272, 402], 16)          # корешок


def icon_tab_profile(m):
    d = ImageDraw.Draw(m)
    ring(d, C, C, 148, 34)
    clipped(
        m,
        lambda di: (disc(di, C, 202, 56), rrect(di, [160, 288, 352, 470], 96)),
        lambda dc: disc(dc, C, C, 122),
    )


# ── приоритет 2 ────────────────────────────────────────────────────────
def icon_trophy(m):
    d = ImageDraw.Draw(m)
    poly(d, [(148, 96), (364, 96), (346, 244), (300, 300), (212, 300),
             (166, 244)], radius=26)
    arc(d, 148, 168, 56, -96, 96, 26)
    arc(d, 364, 168, 56, 84, 276, 26)
    rrect(d, [234, 292, 278, 366], 12)
    rrect(d, [180, 366, 332, 412], 20)


def icon_sunrise(m):
    d = ImageDraw.Draw(m)
    disc(d, C, 336, 104)
    d.rectangle(sbox([0, 336, CANVAS, CANVAS]), fill=0)     # полусолнце
    for a in (-150, -120, -90, -60, -30):
        ux, uy = math.cos(math.radians(a)), math.sin(math.radians(a))
        line(d, [(C + ux * 138, 336 + uy * 138),
                 (C + ux * 186, 336 + uy * 186)], 26)
    line(d, [(84, 372), (428, 372)], 32)
    line(d, [(158, 434), (354, 434)], 30)


def icon_journal(m):
    d = ImageDraw.Draw(m)
    rrect(d, [146, 66, 404, 446], 40, w=32)          # блок страниц
    for y in (124, 196, 268, 340, 412):              # пружина
        rrect(d, [110, y - 13, 186, y + 13], 13)
    line(d, [(226, 190), (352, 190)], 26)
    line(d, [(226, 272), (352, 272)], 26)


def icon_seal(m):
    d = ImageDraw.Draw(m)
    poly(d, [(C, 60), (402, 122), (402, 250), (C, 450), (110, 250),
             (110, 122)], radius=[34, 42, 42, 60, 42, 42])
    line(d, [(186, 252), (238, 306), (334, 196)], 36, v=0)


def icon_calendar(m):
    d = ImageDraw.Draw(m)
    rrect(d, [80, 108, 432, 442], 44, w=32)
    rrect(d, [80, 108, 432, 196], 44)
    d.rectangle(sbox([80, 168, 432, 196]), fill=255)
    rrect(d, [148, 56, 184, 140], 18)
    rrect(d, [328, 56, 364, 140], 18)
    for row in (268, 356):
        for col in (156, 256, 356):
            disc(d, col, row, 24)


def icon_shop(m):
    d = ImageDraw.Draw(m)
    rrect(d, [100, 166, 412, 440], 46, w=32)
    arc(d, C, 172, 78, 180, 360, 30)


def icon_stats(m):
    d = ImageDraw.Draw(m)
    rrect(d, [104, 268, 180, 424], 28)
    rrect(d, [218, 176, 294, 424], 28)
    rrect(d, [332, 88, 408, 424], 28)


def icon_settings(m):
    d = ImageDraw.Draw(m)
    for k in range(8):
        merged(m, lambda di: rrect(di, [C - 34, 62, C + 34, 178], 22),
               angle=k * 45)
    d = ImageDraw.Draw(m)
    disc(d, C, C, 156)
    disc(d, C, C, 68, v=0)


def icon_edit(m):
    def pencil(di):
        poly(di, [(C, 46), (218, 194), (294, 194)], radius=[7, 22, 22])
        rrect(di, [218, 188, 294, 448], 12)
        line(di, [(218, 194), (294, 194)], 12, v=0)     # срез заточки
        line(di, [(218, 392), (294, 392)], 14, v=0)     # ободок
    merged(m, pencil, angle=-45)


def icon_bell(m):
    d = ImageDraw.Draw(m)
    disc(d, C, 208, 104)
    rrect(d, [152, 208, 360, 336], 24)
    line(d, [(116, 348), (396, 348)], 34)
    disc(d, C, 404, 34)
    disc(d, C, 82, 26)


def icon_lock(m):
    d = ImageDraw.Draw(m)
    arc(d, C, 236, 88, 180, 360, 36)
    rrect(d, [112, 228, 400, 440], 48)
    disc(d, C, 312, 32, v=0)
    poly(d, [(C - 20, 312), (C + 20, 312), (C + 30, 386), (C - 30, 386)],
         radius=12, v=0)


# ── приоритет 3 ────────────────────────────────────────────────────────
def icon_glasses(m):
    d = ImageDraw.Draw(m)
    ring(d, 146, 274, 84, 32)
    ring(d, 366, 274, 84, 32)
    arc(d, C, 296, 42, 200, 340, 28)
    line(d, [(67, 245), (40, 176)], 30)      # заушники от края оправы
    line(d, [(445, 245), (472, 176)], 30)


def icon_crown(m):
    d = ImageDraw.Draw(m)
    poly(d, [(84, 396), (116, 162), (196, 258), (C, 116), (316, 258),
             (396, 162), (428, 396)], radius=20)
    for x, y in ((116, 158), (C, 112), (396, 158)):
        disc(d, x, y, 30)


def icon_selfhug(m):
    d = ImageDraw.Draw(m)
    poly(d, heart_pts(C, 254, 124))
    line(d, [(74, 160), (62, 296), (146, 376), (228, 396)], 36)
    line(d, [(438, 160), (450, 296), (366, 376), (284, 396)], 36)


def icon_target(m):
    d = ImageDraw.Draw(m)
    ring(d, C, C, 158, 34)
    ring(d, C, C, 92, 34)
    disc(d, C, C, 38)


def icon_plus(m):
    d = ImageDraw.Draw(m)
    ring(d, C, C, 158, 36)
    line(d, [(C, 166), (C, 346)], 36)
    line(d, [(166, C), (346, C)], 36)


def icon_hint(m):
    d = ImageDraw.Draw(m)
    disc(d, C, 212, 118)
    rrect(d, [198, 300, 314, 344], 14)
    rrect(d, [196, 356, 316, 390], 16)
    rrect(d, [212, 402, 300, 434], 15)


def icon_bolt(m):
    d = ImageDraw.Draw(m)
    poly(d, [(300, 54), (146, 288), (238, 288), (212, 458), (366, 224),
             (274, 224)], radius=14)


# ── приоритет 4 ────────────────────────────────────────────────────────
def icon_critic_voice(m):
    d = ImageDraw.Draw(m)
    rrect(d, [64, 74, 448, 334], 62)
    poly(d, [(160, 300), (150, 434), (262, 326)], radius=16)
    rrect(d, [238, 132, 274, 242], 18, v=0)
    disc(d, C, 282, 22, v=0)


def icon_clock(m):
    d = ImageDraw.Draw(m)
    ring(d, C, C, 158, 34)
    line(d, [(C, C), (C, 148)], 30)
    line(d, [(C, C), (338, 296)], 30)
    disc(d, C, C, 20)


def icon_heart_outline(m):
    d = ImageDraw.Draw(m)
    line(d, heart_pts(C, 272, 168, n=140), 36, closed=True)


def icon_anxiety(m):
    d = ImageDraw.Draw(m)
    ring(d, C, C, 158, 34)
    rrect(d, [238, 136, 274, 282], 18)
    disc(d, C, 330, 23)


def icon_question(m):
    d = ImageDraw.Draw(m)
    ring(d, C, C, 158, 34)
    arc(d, C, 196, 58, 180, 60, 30)
    line(d, [(C + 29, 246), (C, 288), (C, 306)], 30)
    disc(d, C, 352, 23)


def icon_book(m):
    d = ImageDraw.Draw(m)
    rrect(d, [112, 66, 400, 446], 40)
    rrect(d, [170, 66, 196, 446], 0, v=0)
    line(d, [(240, 176), (348, 176)], 24, v=0)
    line(d, [(240, 254), (348, 254)], 24, v=0)


def icon_headphones(m):
    d = ImageDraw.Draw(m)
    arc(d, C, 268, 152, 180, 360, 38)
    rrect(d, [82, 262, 166, 398], 42)
    rrect(d, [346, 262, 430, 398], 42)


def icon_tap(m):
    d = ImageDraw.Draw(m)
    rrect(d, [168, 250, 358, 444], 68)         # кулак
    rrect(d, [178, 118, 246, 300], 34)         # указательный палец
    rrect(d, [254, 226, 310, 300], 28)         # костяшки
    rrect(d, [306, 244, 356, 302], 25)
    arc(d, 212, 152, 82, 148, 252, 22)         # волны касания
    arc(d, 212, 152, 132, 156, 244, 22)


def icon_smile(m):
    d = ImageDraw.Draw(m)
    ring(d, C, C, 158, 34)
    disc(d, 206, 214, 23)
    disc(d, 306, 214, 23)
    arc(d, C, 244, 86, 32, 148, 30)


def icon_heart_fill(m):
    d = ImageDraw.Draw(m)
    poly(d, heart_pts(C, 272, 186))


# ── приоритет 5 ────────────────────────────────────────────────────────
def icon_friends(m):
    d = ImageDraw.Draw(m)
    disc(d, 322, 194, 60)
    rrect(d, [236, 274, 408, 424], 78)
    # передний человечек «вырезает» себя из заднего, чтобы был зазор
    for grow, v in ((16, 0), (0, 255)):
        disc(d, 188, 216, 68 + grow, v)
        rrect(d, [96 - grow, 306 - grow, 288 + grow, 448], 84 + grow, v=v)


def icon_letter(m):
    d = ImageDraw.Draw(m)
    rrect(d, [72, 128, 440, 384], 38, w=32)
    line(d, [(92, 150), (C, 288), (420, 150)], 32)


def icon_message(m):
    d = ImageDraw.Draw(m)
    rrect(d, [64, 82, 448, 340], 64)
    poly(d, [(152, 306), (142, 440), (254, 332)], radius=16)
    for x in (164, C, 348):
        disc(d, x, 212, 27, v=0)


def icon_call(m):
    def handset(di):
        arc(di, C, 150, 170, 35, 145, 70, caps=False)     # изгиб трубки
        for a in (35, 145):                               # динамик и микрофон
            disc(di, C + 170 * math.cos(math.radians(a)),
                 150 + 170 * math.sin(math.radians(a)), 58)
    merged(m, handset, angle=-32)


def icon_magic(m):
    def wand(di):
        poly(di, [(236, 148), (272, 148), (296, 442), (212, 442)], radius=16)
        line(di, [(240, 214), (292, 214)], 15, v=0)       # ободок у кончика
    merged(m, wand, angle=-32)
    d = ImageDraw.Draw(m)
    sparkle(d, 356, 112, 58)
    sparkle(d, 442, 202, 34)
    sparkle(d, 418, 322, 28)


def icon_quote(m):
    d = ImageDraw.Draw(m)
    for cx in (180, 348):
        disc(d, cx, 194, 64)
        poly(d, [(cx - 64, 190), (cx + 28, 242), (cx - 56, 340)],
             radius=[22, 48, 10])


def icon_ambience_silence(m):
    d = ImageDraw.Draw(m)
    disc(d, 240, C, 178)
    disc(d, 344, 168, 168, v=0)


def icon_ambience_rain(m):
    d = ImageDraw.Draw(m)
    disc(d, 190, 228, 78)
    disc(d, 296, 206, 96)
    disc(d, 364, 254, 62)
    rrect(d, [128, 246, 388, 312], 42)
    for x, y in ((176, 348), (256, 366), (336, 348)):
        line(d, [(x + 12, y), (x - 14, y + 62)], 28)


def icon_ambience_ocean(m):
    d = ImageDraw.Draw(m)
    for k, y in enumerate((160, 258, 356)):
        pts = []
        for i in range(41):
            x = 66 + (380 * i / 40)
            pts.append((x, y + 40 * math.sin(math.radians(
                i / 40 * 400 + k * 40))))
        line(d, pts, 32)


# ── реестр ─────────────────────────────────────────────────────────────
NEUTRAL = "#C9C2E6"

ICONS = {
    # приоритет 1
    "icon-streak":            (icon_streak, "#FF8A55", "Огонёк — серия дней"),
    "icon-lumen":             (icon_lumen, "#FFD166", "Люмены — валюта"),
    "icon-freeze":            (icon_freeze, "#8FC3FF", "Заморозка серии"),
    "icon-tab-courses":       (icon_tab_courses, "#C3B3FF", "Таб «Курсы»"),
    "icon-tab-profile":       (icon_tab_profile, "#C3B3FF", "Таб «Профиль»"),
    # приоритет 2
    "icon-trophy":            (icon_trophy, "#FFB020", "Достижение"),
    "icon-sunrise":           (icon_sunrise, NEUTRAL, "Ранняя пташка"),
    "icon-journal":           (icon_journal, NEUTRAL, "Дневник"),
    "icon-seal":              (icon_seal, NEUTRAL, "Курс пройден"),
    "icon-calendar":          (icon_calendar, NEUTRAL, "30 дней подряд"),
    "icon-shop":              (icon_shop, NEUTRAL, "Магазин"),
    "icon-stats":             (icon_stats, NEUTRAL, "Статистика"),
    "icon-settings":          (icon_settings, NEUTRAL, "Настройки"),
    "icon-edit":              (icon_edit, "#9C93C9", "Редактировать"),
    "icon-bell":              (icon_bell, "#9C93C9", "Уведомления"),
    "icon-lock":              (icon_lock, "#8A80B0", "Заблокировано"),
    # приоритет 3
    "icon-glasses":           (icon_glasses, "#5B9FFF", "Очки мечтателя"),
    "icon-crown":             (icon_crown, "#FF6EC7", "Звёздная корона"),
    "icon-selfhug":           (icon_selfhug, NEUTRAL, "Самообъятие"),
    "icon-target":            (icon_target, NEUTRAL, "Фокус на ценностях"),
    "icon-plus":              (icon_plus, NEUTRAL, "Доп. задание"),
    "icon-hint":              (icon_hint, "#8B6CF6", "Подсказка"),
    "icon-bolt":              (icon_bolt, NEUTRAL, "Бустеры"),
    # приоритет 4
    "icon-critic-voice":      (icon_critic_voice, NEUTRAL, "Критикую себя"),
    "icon-clock":             (icon_clock, NEUTRAL, "Границы"),
    "icon-heart-outline":     (icon_heart_outline, NEUTRAL, "Недостаточно хорош"),
    "icon-anxiety":           (icon_anxiety, NEUTRAL, "Тревожность"),
    "icon-question":          (icon_question, NEUTRAL, "Другое"),
    "icon-book":              (icon_book, NEUTRAL, "Формат «Чтение»"),
    "icon-headphones":        (icon_headphones, NEUTRAL, "Формат «Аудио»"),
    "icon-tap":               (icon_tap, NEUTRAL, "Формат «Интерактив»"),
    "icon-smile":             (icon_smile, NEUTRAL, "Меньше критики"),
    "icon-heart-fill":        (icon_heart_fill, "#EE606A", "Ценить себя"),
    # приоритет 5
    "icon-friends":           (icon_friends, NEUTRAL, "Что сказал бы друг"),
    "icon-letter":            (icon_letter, NEUTRAL, "Письмо поддержки"),
    "icon-message":           (icon_message, NEUTRAL, "Сообщение"),
    "icon-call":              (icon_call, NEUTRAL, "Позвонить"),
    "icon-magic":             (icon_magic, NEUTRAL, "Свой вариант"),
    "icon-quote":             (icon_quote, NEUTRAL, "Кавычка (аффирмация)"),
    "icon-ambience-silence":  (icon_ambience_silence, NEUTRAL, "Амбиенс: тишина"),
    "icon-ambience-rain":     (icon_ambience_rain, NEUTRAL, "Амбиенс: дождь"),
    "icon-ambience-ocean":    (icon_ambience_ocean, NEUTRAL, "Амбиенс: океан"),
}

PRIORITY = {
    1: ["icon-streak", "icon-lumen", "icon-freeze", "icon-tab-courses",
        "icon-tab-profile"],
    2: ["icon-trophy", "icon-sunrise", "icon-journal", "icon-seal",
        "icon-calendar", "icon-shop", "icon-stats", "icon-settings",
        "icon-edit", "icon-bell", "icon-lock"],
    3: ["icon-glasses", "icon-crown", "icon-selfhug", "icon-target",
        "icon-plus", "icon-hint", "icon-bolt"],
    4: ["icon-critic-voice", "icon-clock", "icon-heart-outline",
        "icon-anxiety", "icon-question", "icon-book", "icon-headphones",
        "icon-tap", "icon-smile", "icon-heart-fill"],
    5: ["icon-friends", "icon-letter", "icon-message", "icon-call",
        "icon-magic", "icon-quote", "icon-ambience-silence",
        "icon-ambience-rain", "icon-ambience-ocean"],
}


# ── рендер ─────────────────────────────────────────────────────────────
def icon_mask(name: str) -> Image.Image:
    """L-маска иконки в рабочем разрешении."""
    m = Image.new("L", (N, N), 0)
    ICONS[name][0](m)
    return m


def render_icon(name: str, size: int = 1024, color="#000000") -> Image.Image:
    mask = icon_mask(name).resize((size, size), Image.LANCZOS)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    img.paste(Image.new("RGBA", (size, size), color), (0, 0), mask)
    return img


def export(folder: str, size: int = 1024, colored: bool = False) -> None:
    os.makedirs(folder, exist_ok=True)
    for name, (_, color, _) in ICONS.items():
        img = render_icon(name, size, color if colored else "#000000")
        img.save(os.path.join(folder, f"{name}.png"))
        print(f"{folder}/{name}.png")


def contact_sheet(path: str = "icons.png", cell: int = 200) -> None:
    """Лист набора: иконки в своих цветах на тёмном фоне."""
    cols, pad, label = 6, 18, 34
    names = [n for p in sorted(PRIORITY) for n in PRIORITY[p]]
    rows = math.ceil(len(names) / cols)
    w = cols * (cell + pad) + pad
    h = rows * (cell + pad + label) + pad
    sheet = Image.new("RGB", (w, h), (18, 23, 42))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except OSError:
        font = ImageFont.load_default()

    for i, name in enumerate(names):
        cx = pad + (i % cols) * (cell + pad)
        cy = pad + (i // cols) * (cell + pad + label)
        sheet.paste(render_icon(name, cell, ICONS[name][1]), (cx, cy),
                    render_icon(name, cell, ICONS[name][1]))
        d.text((cx + cell / 2, cy + cell + 10), name.replace("icon-", ""),
               font=font, fill=(150, 158, 190), anchor="ma")

    sheet.save(path)
    print(f"{path}  ({w}x{h}, {len(names)} иконок)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Иконки в стиле Луми")
    ap.add_argument("--export", metavar="FOLDER", help="сохранить все PNG")
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--colored", action="store_true",
                    help="запечь цвет вместо чёрного силуэта")
    ap.add_argument("--one", help="одна иконка по имени")
    ap.add_argument("--out", default="icons.png")
    ap.add_argument("--sheet", action="store_true", help="только лист набора")
    args = ap.parse_args()

    if args.one:
        color = ICONS[args.one][1] if args.colored else "#000000"
        render_icon(args.one, args.size, color).save(args.out)
        print(args.out)
    elif args.export:
        export(args.export, args.size, args.colored)
        contact_sheet("icons.png")
    else:
        contact_sheet(args.out)


if __name__ == "__main__":
    main()
