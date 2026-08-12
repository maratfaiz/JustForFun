"""Предметы магазина: item-*.png.

Третий набор ассетов, не путать с двумя другими:
  icon-*   — плоские однотонные силуэты для UI, красятся кодом;
  mascot-* — иллюстрации персонажа;
  item-*   — предмет магазина как отдельная вещь, без маскота (этот файл).

Полноцветные PNG: код их не перекрашивает. Объём делается одинаково у всех
девяти — диагональный градиент под свет сверху-слева плюс блик, поэтому
предметы выглядят одним набором, а не сборной солянкой.

    python3 items.py                        # -> items.png, контактный лист
    python3 items.py --export assets/items  # -> PNG по 1024 px
"""

from __future__ import annotations

import argparse
import math
import os

from PIL import Image, ImageDraw, ImageFilter

# --- сетка -------------------------------------------------------------------

SS = 4
BOX = 512.0                  # логический холст
N = int(BOX * SS)
C = BOX / 2
PAD = 52.0                   # ~10% поля: плитка магазина обрежет край рамкой
LIGHT = 45                   # угол света — сверху-слева, одинаковый у всех


def s(v: float) -> float:
    return v * SS


def sbox(box):
    return [s(v) for v in box]


# --- палитра -----------------------------------------------------------------

GOLD = (255, 214, 58)
GOLD_DK = (226, 152, 12)
PINK = (255, 110, 199)
PINK_DK = (214, 62, 158)
BLUE = (128, 186, 255)
BLUE_DK = (74, 132, 226)
VIOLET = (138, 122, 246)
VIOLET_DK = (86, 74, 178)
VIOLET_DEEP = (52, 44, 104)
NEBULA = (168, 96, 224)
PAPER = (253, 253, 255)
PAPER_DK = (206, 212, 234)
RED = (244, 104, 116)
RED_DK = (198, 54, 74)
ICE = (198, 232, 255)
ICE_DK = (108, 168, 232)
FLAME = (255, 178, 96)
FLAME_DK = (255, 108, 58)
METAL = (188, 196, 224)
METAL_DK = (118, 126, 164)
INK = (66, 72, 108)
LEATHER = (124, 108, 240)


# --- инструменты -------------------------------------------------------------


def mask():
    m = Image.new("L", (N, N), 0)
    return m, ImageDraw.Draw(m)


def _grad(c0, c1, angle):
    """Линейный градиент: c0 со стороны источника света, c1 в тени."""
    d = 512
    strip = Image.new("RGB", (1, d))
    for i in range(d):
        t = i / (d - 1)
        strip.putpixel((0, i), tuple(
            int(round(c0[k] + (c1[k] - c0[k]) * t)) for k in range(3)))
    g = strip.resize((d, d), Image.BILINEAR).rotate(
        angle, resample=Image.BICUBIC)
    off = int(d * 0.147)                      # вписанный квадрат без пустых углов
    return g.crop((off, off, d - off, d - off)).resize((N, N), Image.BICUBIC)


def shade(img, m, c0, c1, angle=LIGHT):
    """Кладёт градиент по маске m."""
    img.paste(_grad(c0, c1, angle).convert("RGBA"), (0, 0), m)


def _tinted(m, color, alpha):
    """RGBA-слой заданного цвета с прозрачностью по маске.

    Именно alpha_composite, а не paste: paste с полупрозрачным источником
    заменяет пиксели вместе с их альфой и пробивает дырки в предмете."""
    lay = Image.new("RGBA", (N, N), tuple(color) + (0,))
    lay.putalpha(m if alpha >= 255 else Image.eval(m, lambda v: v * alpha // 255))
    return lay


def flat(img, m, color, alpha=255):
    img.alpha_composite(_tinted(m, color, alpha))


def gloss(img, obj, spots, alpha=96, blur=10.0):
    """Мягкий блик сверху-слева, обрезанный по силуэту предмета.

    Блик рисуется в L-маске и только потом красится: размывать RGBA нельзя,
    у прозрачных пикселей чёрный RGB и он подмешивается в цвет."""
    g, d = mask()
    for cx, cy, rx, ry, rot in spots:
        e = Image.new("L", (int(s(rx * 2)) + 8, int(s(ry * 2)) + 8), 0)
        ImageDraw.Draw(e).ellipse([4, 4, s(rx * 2) + 4, s(ry * 2) + 4], fill=255)
        e = e.rotate(rot, resample=Image.BICUBIC, expand=True)
        g.paste(e, (int(s(cx) - e.width / 2), int(s(cy) - e.height / 2)), e)
    if blur:
        g = g.filter(ImageFilter.GaussianBlur(s(blur)))
    g = Image.composite(g, Image.new("L", (N, N), 0), obj)
    img.alpha_composite(_tinted(g, (255, 255, 255), alpha))


def _font(size_logical):
    from PIL import ImageFont
    return ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        int(s(size_logical)))


def spark(d, cx, cy, r, v=255):
    k = r * 0.24
    d.polygon([s(cx), s(cy - r), s(cx + k), s(cy - k), s(cx + r), s(cy),
               s(cx + k), s(cy + k), s(cx), s(cy + r), s(cx - k), s(cy + k),
               s(cx - r), s(cy), s(cx - k), s(cy - k)], fill=v)


def new_img():
    return Image.new("RGBA", (N, N), (0, 0, 0, 0))


def finish(img, size):
    return img.resize((size, size), Image.LANCZOS)


# --- аксессуары --------------------------------------------------------------


def item_glasses():
    """Очки мечтателя: круглые ретро-очки, в стекле звёздный блик."""
    img = new_img()
    # стёкла разведены: при r_out 96 и шаге 156 они пересекались и очки
    # читались как два слипшихся кружка
    lens_c = ((152, C - 6), (360, C - 6))
    r_out, r_in = 90.0, 70.0

    frame, fd = mask()
    for cx, cy in lens_c:
        fd.ellipse(sbox([cx - r_out, cy - r_out, cx + r_out, cy + r_out]),
                   fill=255)
    fd.arc(sbox([lens_c[0][0] + 46, C - 86, lens_c[1][0] - 46, C + 14]),
           186, 354, fill=255, width=int(s(22)))
    fd.line(sbox([62, C - 30, 96, C - 76]), fill=255, width=int(s(22)))
    fd.line(sbox([450, C - 30, 416, C - 76]), fill=255, width=int(s(22)))
    for cx, cy in lens_c:                      # вырезаем стёкла
        fd.ellipse(sbox([cx - r_in, cy - r_in, cx + r_in, cy + r_in]), fill=0)

    glass, gd = mask()
    for cx, cy in lens_c:
        gd.ellipse(sbox([cx - r_in - 4, cy - r_in - 4,
                         cx + r_in + 4, cy + r_in + 4]), fill=255)
    shade(img, glass, (176, 214, 255), VIOLET_DK)
    # оправа золотая: фиолетовая на фиолетовом стекле не читалась
    shade(img, frame, (255, 226, 128), GOLD_DK)

    st, sd = mask()                            # звёздочки в стекле
    spark(sd, 126, C - 34, 24)
    spark(sd, 176, C + 26, 14)
    spark(sd, 382, C - 26, 19)
    flat(img, st, (255, 255, 255), 240)
    gloss(img, glass, [(124, C - 40, 40, 18, 34)], alpha=130, blur=6)
    gloss(img, frame, [(124, C - 78, 50, 13, 26)], alpha=120, blur=6)
    return img


def item_headphones():
    """Галактические наушники: на чашках — туманность."""
    img = new_img()
    band, bd = mask()
    bd.arc(sbox([C - 168, 96, C + 168, 432]), 180, 360, fill=255,
           width=int(s(40)))
    bd.ellipse(sbox([C - 190, 236, C - 128, 300]), fill=255)
    bd.ellipse(sbox([C + 128, 236, C + 190, 300]), fill=255)
    shade(img, band, VIOLET, VIOLET_DK)

    cups, cd = mask()
    for cx in (C - 158, C + 158):
        cd.rounded_rectangle(sbox([cx - 74, 256, cx + 74, 448]), radius=s(66),
                             fill=255)
    shade(img, cups, VIOLET_DK, VIOLET_DEEP)

    inner, idr = mask()
    for cx in (C - 158, C + 158):
        idr.rounded_rectangle(sbox([cx - 54, 278, cx + 54, 426]),
                              radius=s(50), fill=255)
    shade(img, inner, VIOLET_DEEP, (30, 24, 62))

    for cx in (C - 158, C + 158):              # туманность и звёзды
        neb, nd = mask()
        nd.ellipse(sbox([cx - 40, 300, cx + 14, 358]), fill=255)
        nd.ellipse(sbox([cx - 10, 340, cx + 42, 396]), fill=255)
        neb = neb.filter(ImageFilter.GaussianBlur(s(14)))
        neb = Image.composite(neb, Image.new("L", (N, N), 0), inner)
        flat(img, neb, NEBULA, 150)
        st, sd = mask()
        spark(sd, cx - 18, 320, 15)
        spark(sd, cx + 22, 372, 11)
        sd.ellipse(sbox([cx + 14, 316, cx + 24, 326]), fill=255)
        sd.ellipse(sbox([cx - 30, 382, cx - 22, 390]), fill=255)
        flat(img, st, (255, 255, 255), 240)

    gloss(img, band, [(C - 104, 128, 78, 18, 32)], alpha=120, blur=8)
    gloss(img, cups, [(C - 200, 292, 26, 50, 16)], alpha=95, blur=9)
    return img


def item_crown():
    """Звёздная корона: зубцы-звёзды, золото → розовый."""
    img = new_img()
    body, bd = mask()
    bd.polygon([*sbox([88, 396]), *sbox([120, 176]), *sbox([206, 268]),
                *sbox([C, 138]), *sbox([306, 268]), *sbox([392, 176]),
                *sbox([424, 396])], fill=255)
    bd.rounded_rectangle(sbox([84, 356, 428, 434]), radius=s(28), fill=255)
    shade(img, body, GOLD, PINK)

    tips, td = mask()                          # пятиконечные звёзды на зубцах
    for cx, cy, r in ((120, 168, 46), (C, 128, 56), (392, 168, 46)):
        pts = []
        for i in range(10):
            a = math.radians(90 + i * 36)
            rr = r if i % 2 == 0 else r * 0.44
            pts += [s(cx + rr * math.cos(a)), s(cy - rr * math.sin(a))]
        td.polygon(pts, fill=255)
    shade(img, tips, (255, 246, 190), PINK)

    band, nd = mask()
    nd.rounded_rectangle(sbox([84, 372, 428, 418]), radius=s(20), fill=255)
    shade(img, band, PINK, PINK_DK)
    gem, gd = mask()
    for cx in (162, C, 350):
        gd.ellipse(sbox([cx - 20, 374, cx + 20, 414]), fill=255)
    shade(img, gem, (255, 250, 220), GOLD_DK)

    gloss(img, body, [(196, 236, 66, 18, 58)], alpha=110, blur=8)
    return img


# --- секретные техники -------------------------------------------------------


def _heart_mask(cx, cy, scale, n=140):
    m, d = mask()
    pts = []
    for i in range(n):
        t = i * 2 * math.pi / n
        x = 16 * math.sin(t) ** 3
        y = (13 * math.cos(t) - 5 * math.cos(2 * t)
             - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts += [s(cx + x * scale), s(cy - y * scale)]
    d.polygon(pts, fill=255)
    return m


def item_selfhug():
    """«Самообъятие»: руки скрещены на груди поверх сердца.

    Сердце не «держат снизу» — руки идут снизу-снаружи к противоположному
    плечу и перекрещиваются, как в настоящем самообъятии."""
    img = new_img()
    heart = _heart_mask(C, 232, 10.4)
    shade(img, heart, (255, 150, 168), RED_DK)
    gloss(img, heart, [(194, 182, 50, 26, 32)], alpha=125, blur=7)

    def arm(pts, w=46.0):
        """Рука обвивает сердце и заканчивается кистью.

        Прямые длинные диагонали здесь не годятся: они выходят далеко за
        силуэт и читаются как перечёркивание, а не объятие."""
        m, d = mask()
        d.line(sbox([v for p in pts for v in p]), fill=255,
               width=int(s(w)), joint="curve")
        d.ellipse(sbox([pts[0][0] - w / 2, pts[0][1] - w / 2,
                        pts[0][0] + w / 2, pts[0][1] + w / 2]), fill=255)
        hx, hy, hr = pts[-1][0], pts[-1][1], w * 0.62
        d.ellipse(sbox([hx - hr, hy - hr, hx + hr, hy + hr]), fill=255)
        return m

    # Руки лежат поперёк самой широкой части сердца, а не под его нижним
    # остриём: внизу они читаются как «держат снизу», а нужно объятие.
    back = arm([(438, 206), (398, 268), (330, 300), (250, 292)])
    front = arm([(74, 226), (114, 296), (192, 336), (282, 330)])
    shade(img, back, GOLD_DK, (184, 118, 4))

    sh = front.filter(ImageFilter.MaxFilter(9)).filter(
        ImageFilter.GaussianBlur(s(7)))
    sh = Image.composite(sh, Image.new("L", (N, N), 0), back)
    img.alpha_composite(_tinted(sh, (124, 78, 2), 135))

    shade(img, front, GOLD, GOLD_DK)
    gloss(img, front, [(126, 296, 14, 34, 10)], alpha=105, blur=6)
    return img


def item_journal():
    """Дневник эмоций: раскрытый блокнот, ручка и сердечко-пометка."""
    img = new_img()
    cover, cd = mask()
    cd.polygon([*sbox([56, 176]), *sbox([C, 214]), *sbox([456, 176]),
                *sbox([456, 414]), *sbox([C, 452]), *sbox([56, 414])],
               fill=255)
    shade(img, cover, LEATHER, VIOLET_DK)

    pages, pd = mask()
    pd.polygon([*sbox([74, 194]), *sbox([C - 6, 228]), *sbox([C - 6, 424]),
                *sbox([74, 392])], fill=255)
    pd.polygon([*sbox([438, 194]), *sbox([C + 6, 228]), *sbox([C + 6, 424]),
                *sbox([438, 392])], fill=255)
    shade(img, pages, PAPER, PAPER_DK)

    lines, ld = mask()
    for i in range(4):
        y = 262 + i * 38
        ld.rounded_rectangle(sbox([104, y - 7, 224, y + 7]), radius=s(7),
                             fill=255)
        ld.rounded_rectangle(sbox([292, y - 7, 412, y + 7]), radius=s(7),
                             fill=255)
    flat(img, lines, PAPER_DK)

    mark, md = mask()                          # сердечко-пометка
    pts = []
    for i in range(90):
        t = i * 2 * math.pi / 90
        x = 16 * math.sin(t) ** 3
        y = (13 * math.cos(t) - 5 * math.cos(2 * t)
             - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts += [s(150 + x * 1.9), s(238 - y * 1.9)]
    md.polygon(pts, fill=255)
    flat(img, mark, RED)

    pen, nd = mask()
    nd.line(sbox([318, 396, 424, 246]), fill=255, width=int(s(30)))
    shade(img, pen, GOLD, GOLD_DK)
    tip, td = mask()
    td.polygon([*sbox([308, 412]), *sbox([332, 388]), *sbox([348, 400])],
               fill=255)
    flat(img, tip, INK)

    gloss(img, cover, [(150, 200, 84, 16, 12)], alpha=100, blur=8)
    gloss(img, pen, [(400, 274, 12, 40, 34)], alpha=120, blur=5)
    return img


def item_target():
    """Фокус на ценностях: мишень со стрелой в центре."""
    img = new_img()
    rings = ((166, RED, RED_DK), (124, PAPER, PAPER_DK),
             (82, RED, RED_DK), (40, PAPER, PAPER_DK))
    for r, c0, c1 in rings:
        m, d = mask()
        d.ellipse(sbox([C - r, C - r, C + r, C + r]), fill=255)
        shade(img, m, c0, c1)

    # Стрела строится в осях самой стрелы: t — вдоль древка от наконечника
    # к хвосту, off — поперёк. Иначе наконечник, древко и оперение не
    # сходятся в одну линию и стрела выглядит приклеенной сверху.
    tip = (C - 4, C - 4)
    back = (0.784, -0.620)                     # от наконечника к хвосту
    perp = (-back[1], back[0])

    def P(t, off):
        return (tip[0] + back[0] * t + perp[0] * off,
                tip[1] + back[1] * t + perp[1] * off)

    hole, hd = mask()                          # входное отверстие в мишени
    hd.ellipse(sbox([C - 30, C - 30, C + 30, C + 30]), fill=255)
    hole = hole.filter(ImageFilter.GaussianBlur(s(9)))
    img.alpha_composite(_tinted(hole, (120, 28, 44), 120))

    shaft, sd = mask()
    a, b = P(46, 0), P(214, 0)
    sd.line(sbox([*a, *b]), fill=255, width=int(s(19)))
    shade(img, shaft, (228, 234, 250), METAL_DK)

    fl, fd = mask()                            # оперение у хвоста
    for sgn in (1, -1):
        fd.polygon([*sbox([*P(148, 9 * sgn)]), *sbox([*P(222, 9 * sgn)]),
                    *sbox([*P(206, 58 * sgn)])], fill=255)
    shade(img, fl, (255, 176, 138), FLAME_DK)
    nock, nd = mask()
    nd.ellipse(sbox([P(220, 0)[0] - 13, P(220, 0)[1] - 13,
                     P(220, 0)[0] + 13, P(220, 0)[1] + 13]), fill=255)
    shade(img, nock, METAL, METAL_DK)

    head, hhd = mask()                         # наконечник
    hhd.polygon([*sbox([*P(0, 0)]), *sbox([*P(62, 25)]), *sbox([*P(50, 0)]),
                 *sbox([*P(62, -25)])], fill=255)
    shade(img, head, (255, 238, 168), GOLD_DK)

    gloss(img, head, [(*P(30, -9), 22, 9, 38)], alpha=140, blur=4)
    gloss(img, shaft, [(*P(120, -5), 60, 5, -38)], alpha=120, blur=4)
    return img


# --- бустеры -----------------------------------------------------------------


def item_freeze():
    """Заморозка серии: объёмная снежинка-кристалл.

    Уют и защита, а не холод: светлая, почти белая, с тёплым сиреневым
    отливом в тени — не синева «морозилки»."""
    img = new_img()
    arm, w = 194.0, 30.0
    flake, d = mask()
    for k in range(6):
        a = math.radians(k * 60)
        ux, uy = math.cos(a), math.sin(a)
        d.line(sbox([C, C, C + ux * arm, C + uy * arm]), fill=255,
               width=int(s(w)))
        tx, ty = C + ux * arm, C + uy * arm     # ромбовидный наконечник
        px, py = -uy, ux
        d.polygon([*sbox([tx + ux * 30, ty + uy * 30]),
                   *sbox([tx + px * 26, ty + py * 26]),
                   *sbox([tx - ux * 26, ty - uy * 26]),
                   *sbox([tx - px * 26, ty - py * 26])], fill=255)
        for frac, blen, bw in ((0.44, 76.0, 26.0), (0.72, 56.0, 22.0)):
            bx, by = C + ux * arm * frac, C + uy * arm * frac
            for side in (+46, -46):
                t = math.radians(k * 60 + side)
                ex, ey = bx + math.cos(t) * blen, by + math.sin(t) * blen
                d.line(sbox([bx, by, ex, ey]), fill=255, width=int(s(bw)))
                d.ellipse(sbox([ex - bw / 2, ey - bw / 2,
                                ex + bw / 2, ey + bw / 2]), fill=255)

    hexes = [(C + 66 * math.cos(math.radians(k * 60 + 30)),
              C + 66 * math.sin(math.radians(k * 60 + 30))) for k in range(6)]
    d.polygon([v for p in hexes for v in sbox(list(p))], fill=255)
    shade(img, flake, (255, 255, 255), ICE_DK)

    core, cd = mask()                           # светлая сердцевина
    small = [(C + 40 * math.cos(math.radians(k * 60 + 30)),
              C + 40 * math.sin(math.radians(k * 60 + 30))) for k in range(6)]
    cd.polygon([v for p in small for v in sbox(list(p))], fill=255)
    shade(img, core, (255, 255, 255), (206, 230, 252))

    st, sd = mask()
    spark(sd, 96, 116, 28)
    spark(sd, 420, 140, 20)
    spark(sd, 404, 416, 24)
    flat(img, st, (226, 236, 255), 240)
    gloss(img, flake, [(178, 176, 70, 24, 42)], alpha=125, blur=8)
    return img


def item_plus():
    """Доп. задание дня: «+1» на билете."""
    img = new_img()
    ticket, td = mask()
    td.rounded_rectangle(sbox([64, 148, 448, 372]), radius=s(38), fill=255)
    for cy in (200, 260, 320):                  # вырезы по бокам
        td.ellipse(sbox([46, cy - 20, 86, cy + 20]), fill=0)
        td.ellipse(sbox([426, cy - 20, 466, cy + 20]), fill=0)
    shade(img, ticket, (255, 246, 214), GOLD_DK)

    band, bd = mask()
    bd.rounded_rectangle(sbox([64, 148, 448, 208]), radius=s(38), fill=255)
    bd.rectangle(sbox([64, 178, 448, 208]), fill=255)
    band = Image.composite(band, Image.new("L", (N, N), 0), ticket)
    shade(img, band, VIOLET, VIOLET_DK)

    perf, pd = mask()                           # линия отрыва
    for y in range(214, 366, 26):
        pd.rounded_rectangle(sbox([352, y, 362, y + 14]), radius=s(5), fill=255)
    flat(img, perf, GOLD_DK, 150)

    glyph, gd = mask()                          # «+1» шрифтом, а не палками
    gd.text((s(226), s(292)), "+1", font=_font(122), fill=255, anchor="mm")
    shade(img, glyph, (255, 154, 110), FLAME_DK)

    st, sd = mask()
    spark(sd, 398, 288, 30)
    spark(sd, 396, 226, 16)
    spark(sd, 104, 400, 22)
    flat(img, st, GOLD, 245)
    gloss(img, ticket, [(160, 200, 96, 18, 10)], alpha=110, blur=8)
    return img


def item_hint():
    """Подсказка в уроке: лампочка с искоркой."""
    img = new_img()
    glass, gd = mask()
    gd.ellipse(sbox([C - 116, 84, C + 116, 316]), fill=255)
    gd.polygon([*sbox([C - 68, 258]), *sbox([C + 68, 258]),
                *sbox([C + 46, 344]), *sbox([C - 46, 344])], fill=255)
    shade(img, glass, (255, 252, 214), GOLD)

    # нить накала: две ножки и зигзаг между ними — узнаваемее,
    # чем прежняя дуга с перекладиной, которая читалась как значок
    fil, fdw = mask()
    fdw.line(sbox([C - 30, 268, C - 30, 214]), fill=255, width=int(s(11)))
    fdw.line(sbox([C + 30, 268, C + 30, 214]), fill=255, width=int(s(11)))
    fdw.line(sbox([C - 30, 214, C - 14, 176, C, 214, C + 14, 176, C + 30, 214]),
             fill=255, width=int(s(11)), joint="curve")
    shade(img, fil, GOLD_DK, (182, 118, 4))

    cap, cd = mask()                            # цоколь с резьбой
    cd.polygon([*sbox([C - 48, 340]), *sbox([C + 48, 340]),
                *sbox([C + 42, 420]), *sbox([C - 42, 420])], fill=255)
    shade(img, cap, METAL, METAL_DK)
    ridge, rd = mask()
    for y in (360, 386):
        rd.rounded_rectangle(sbox([C - 47, y, C + 47, y + 9]), radius=s(4),
                             fill=255)
    ridge = Image.composite(ridge, Image.new("L", (N, N), 0), cap)
    flat(img, ridge, METAL_DK, 190)
    tipm, td = mask()
    td.rounded_rectangle(sbox([C - 26, 420, C + 26, 452]), radius=s(14),
                         fill=255)
    shade(img, tipm, METAL_DK, INK)

    st, sd = mask()
    spark(sd, 92, 140, 30)
    spark(sd, 428, 178, 24)
    spark(sd, 398, 76, 17)
    flat(img, st, (255, 236, 150), 245)
    gloss(img, glass, [(C - 54, 146, 38, 21, 38)], alpha=155, blur=6)
    gloss(img, cap, [(C - 36, 356, 12, 26, 4)], alpha=90, blur=4)
    return img


# --- набор -------------------------------------------------------------------

ITEMS = {
    "item-glasses": (item_glasses, "Очки мечтателя", "Редкий"),
    "item-headphones": (item_headphones, "Галакт. наушники", "Редкий"),
    "item-crown": (item_crown, "Звёздная корона", "Эпический"),
    "item-selfhug": (item_selfhug, "«Самообъятие»", "Техника"),
    "item-journal": (item_journal, "Дневник эмоций", "Техника"),
    "item-target": (item_target, "Фокус на ценностях", "Техника"),
    "item-freeze": (item_freeze, "Заморозка серии", "Бустер"),
    "item-plus": (item_plus, "Доп. задание дня", "Бустер"),
    "item-hint": (item_hint, "Подсказка в уроке", "Бустер"),
}


def render_item(name: str, size: int = 1024) -> Image.Image:
    return finish(ITEMS[name][0](), size)


def export(folder: str, size: int = 1024) -> None:
    os.makedirs(folder, exist_ok=True)
    for name in ITEMS:
        render_item(name, size).save(os.path.join(folder, f"{name}.png"))
    print(f"{folder}: {len(ITEMS)} PNG по {size}px")


def contact_sheet(path: str = "items.png", cell: int = 300) -> None:
    from PIL import ImageFont
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    mono = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15)
    names = list(ITEMS)
    cols, pad, label = 3, 26, 58
    rows = math.ceil(len(names) / cols)
    sheet = Image.new("RGB", (cols * (cell + pad) + pad,
                              rows * (cell + pad + label) + pad),
                      (22, 26, 46))
    d = ImageDraw.Draw(sheet)
    for i, name in enumerate(names):
        x = pad + (i % cols) * (cell + pad)
        y = pad + (i // cols) * (cell + pad + label)
        d.rounded_rectangle([x, y, x + cell, y + cell], radius=28,
                            fill=(32, 38, 62))
        art = render_item(name, cell)
        sheet.paste(art, (x, y), art)
        d.text((x + cell / 2, y + cell + 8), ITEMS[name][1], font=font,
               fill=(216, 222, 242), anchor="ma")
        d.text((x + cell / 2, y + cell + 32), name, font=mono,
               fill=(240, 196, 88), anchor="ma")
    sheet.save(path)
    print(f"{path} ({sheet.width}x{sheet.height})")


def main() -> None:
    ap = argparse.ArgumentParser(description="Предметы магазина")
    ap.add_argument("--export", metavar="DIR")
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--sheet", default="items.png")
    args = ap.parse_args()
    contact_sheet(args.sheet)
    if args.export:
        export(args.export, args.size)


if __name__ == "__main__":
    main()
