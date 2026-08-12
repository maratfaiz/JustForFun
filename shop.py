"""Картинки товаров магазина: секретные техники и бустеры.

Все шесть — мини-сцены с маскотом: тот же персонаж, что и в остальных
ассетах, поэтому стиль совпадает не «похоже», а буквально. Реквизит
собирается из тех же деталей, что и в scenes.py.

    python3 shop.py                        # -> shop.png, контактный лист
    python3 shop.py --export assets/shop   # -> PNG по 1024 px
"""

from __future__ import annotations

import argparse
import math
import os

from PIL import Image

import cute_star as cs
import scenes as sc
from cute_star import s, sbox

# --- палитра -----------------------------------------------------------------

ICE = (150, 205, 255)
ICE_LIGHT = (226, 243, 255)
VIOLET_SOFT = (168, 178, 250)
WARM_LIGHT = (255, 179, 122)      # #FFB37A — тёплый акцент из ТЗ
WARM_DARK = (255, 122, 77)        # #FF7A4D
BULB = (255, 214, 58)
BULB_DARK = (226, 158, 8)
GLASS = (255, 250, 226)           # стекло лампочки — светлее корпуса звезды
METAL = (150, 158, 190)
WOOD = (214, 176, 120)


def sparkle_at(d, spots, color, alpha=255):
    for cx, cy, r in spots:
        sc.star4(d, cx, cy, r, color, alpha)


def close_hearts(img):
    """Сердечки вплотную к фигуре — венок из scenes.hearts_around шире, и
    из-за него пришлось бы расширять общий кадр всех шести карточек."""
    lay, d = sc.layer(img)
    for x, y, size in ((300, 452, 76), (952, 424, 88), (274, 742, 58),
                       (964, 726, 64), (452, 300, 54), (836, 292, 62)):
        sc.heart(d, x, y, size, sc.RED)
    img.alpha_composite(lay)


# --- заморозка серии ---------------------------------------------------------


def ice_shield(img):
    """Снежинка-щит за фигурой: защита, а не клетка.

    Лучи расходятся наружу из-за спины и нигде не смыкаются в кольцо —
    замкнутый контур вокруг персонажа читался бы как «заперт»."""
    lay, d = sc.layer(img)
    cx, cy, arm = 620, 596, 466

    # Никакой подложки-круга: на тёмном фоне она читалась бы как плашка,
    # а ТЗ запрещает подложку. Лучи заметно длиннее силуэта звезды — если
    # они едва выглядывают, снежинка читается как шипы, а не как щит.
    # Кольцом лучи нигде не смыкаются: замкнутый контур = «заперт».
    for k in range(6):
        a = math.radians(k * 60)
        ux, uy = math.cos(a), math.sin(a)
        d.line(sbox([cx + ux * 120, cy + uy * 120,
                     cx + ux * arm, cy + uy * arm]),
               fill=ICE_LIGHT + (240,), width=int(s(42)))
        d.ellipse(sbox([cx + ux * arm - 21, cy + uy * arm - 21,
                        cx + ux * arm + 21, cy + uy * arm + 21]),
                  fill=ICE_LIGHT + (240,))
        for frac, blen in ((0.80, 92.0), (0.95, 64.0)):
            bx, by = cx + ux * arm * frac, cy + uy * arm * frac
            for side in (+44, -44):
                t = math.radians(k * 60 + side)
                d.line(sbox([bx, by, bx + math.cos(t) * blen,
                             by + math.sin(t) * blen]),
                       fill=ICE_LIGHT + (240,), width=int(s(30)))
    img.alpha_composite(lay)


def snow_bits(img):
    lay, d = sc.layer(img)
    sparkle_at(d, [(318, 232, 34), (930, 268, 28), (286, 962, 26),
                   (952, 934, 30)], VIOLET_SOFT)
    img.alpha_composite(lay)


# --- доп. задание дня --------------------------------------------------------


def checklist_card(img):
    """Список задач сбоку — «плавает» рядом, не заслоняя персонажа."""
    lay, d = sc.layer(img)
    x0, y0, x1, y1 = 146, 566, 424, 894
    d.rounded_rectangle(sbox([x0, y0, x1, y1]), radius=s(40),
                        fill=sc.PAPER + (255,))
    d.rounded_rectangle(sbox([x0, y0, x1, y0 + 88]), radius=s(40),
                        fill=sc.ACCENT + (255,))
    d.rectangle(sbox([x0, y0 + 48, x1, y0 + 88]), fill=sc.ACCENT + (255,))
    for i in range(3):
        y = y0 + 156 + i * 76
        done = i == 2                       # «лишняя» строка — выполненная
        box = sbox([x0 + 40, y - 24, x0 + 88, y + 24])
        d.rounded_rectangle(box, radius=s(13),
                            fill=(WARM_DARK if done else sc.PAPER_LINE) + (255,))
        d.rounded_rectangle(sbox([x0 + 114, y - 13, x1 - 40, y + 13]),
                            radius=s(13), fill=sc.PAPER_LINE + (255,))
        if done:
            d.line(sbox([x0 + 52, y, x0 + 62, y + 12, x0 + 78, y - 12]),
                   fill=sc.PAPER + (255,), width=int(s(12)), joint="curve")
    img.alpha_composite(lay)


def plus_one(img):
    """«+1» с искрой над списком."""
    lay, d = sc.layer(img)
    sparkle_at(d, [(178, 452, 42)], WARM_LIGHT)
    d.rounded_rectangle(sbox([254, 434, 280, 502]), radius=s(13),
                        fill=WARM_DARK + (255,))
    d.rounded_rectangle(sbox([233, 455, 301, 481]), radius=s(13),
                        fill=WARM_DARK + (255,))
    d.rounded_rectangle(sbox([346, 422, 372, 512]), radius=s(13),
                        fill=WARM_DARK + (255,))
    d.line(sbox([322, 450, 352, 426]), fill=WARM_DARK + (255,),
           width=int(s(24)))
    img.alpha_composite(lay)


# --- подсказка в уроке -------------------------------------------------------


def bulb_prop(img):
    """Лампочка в руках. Верхний край на 700 — ниже рта, чтобы не наезжала
    на лицо (та же граница, что у большого сердца)."""
    lay, d = sc.layer(img)
    cx, cy, r = 620, 812, 112
    # стекло почти белое: жёлтая лампочка на жёлтом теле сливалась бы
    d.ellipse(sbox([cx - r, cy - r, cx + r, cy + r]), fill=GLASS + (255,),
              outline=BULB_DARK + (255,), width=int(s(10)))
    d.polygon([*sbox([cx - 56, cy + 82]), *sbox([cx + 56, cy + 82]),
               *sbox([cx + 44, cy + 136]), *sbox([cx - 44, cy + 136])],
              fill=GLASS + (255,))
    d.arc(sbox([cx - 38, cy - 56, cx + 38, cy + 12]), 200, 340,
          fill=BULB_DARK + (255,), width=int(s(13)))
    d.line(sbox([cx, cy, cx, cy + 52]), fill=BULB_DARK + (255,),
           width=int(s(13)))
    d.rounded_rectangle(sbox([cx - 48, cy + 128, cx + 48, cy + 176]),
                        radius=s(18), fill=METAL + (255,))
    d.rounded_rectangle(sbox([cx - 36, cy + 186, cx + 36, cy + 226]),
                        radius=s(17), fill=METAL + (255,))
    img.alpha_composite(lay)


def hint_sparks(img):
    lay, d = sc.layer(img)
    sparkle_at(d, [(286, 838, 42), (964, 806, 36), (926, 592, 30)], BULB)
    img.alpha_composite(lay)


# --- дневник эмоций ----------------------------------------------------------


def doodle_face(d, cx, cy, r, kind):
    """Рожица-каракуля на странице дневника."""
    ex = r * 0.42
    if kind == "calm":
        for sgn in (-1, 1):
            d.arc(sbox([cx + sgn * ex - r * 0.26, cy - r * 0.34,
                        cx + sgn * ex + r * 0.26, cy + r * 0.12]),
                  20, 160, fill=sc.INK + (255,), width=int(s(r * 0.16)))
        d.line(sbox([cx - r * 0.3, cy + r * 0.42, cx + r * 0.3, cy + r * 0.42]),
               fill=sc.INK + (255,), width=int(s(r * 0.16)))
        return
    for sgn in (-1, 1):
        d.ellipse(sbox([cx + sgn * ex - r * 0.15, cy - r * 0.34,
                        cx + sgn * ex + r * 0.15, cy + r * 0.04]),
                  fill=sc.INK + (255,))
    if kind == "smile":
        d.arc(sbox([cx - r * 0.44, cy + r * 0.02, cx + r * 0.44, cy + r * 0.66]),
              20, 160, fill=sc.INK + (255,), width=int(s(r * 0.16)))
    else:                                   # задумчивая: рот сдвинут вбок
        d.line(sbox([cx - r * 0.28, cy + r * 0.46, cx + r * 0.12, cy + r * 0.4]),
               fill=sc.INK + (255,), width=int(s(r * 0.16)))


def open_diary(img):
    """Раскрытый дневник с рожицами на развороте."""
    lay, d = sc.layer(img)
    x0, y0, x1, y1 = 414, 684, 826, 914
    d.rounded_rectangle(sbox([x0, y0, x1, y1]), radius=s(24),
                        fill=sc.PAPER + (255,))
    d.line(sbox([620, y0 + 16, 620, y1 - 16]), fill=sc.PAPER_LINE + (255,),
           width=int(s(7)))
    doodle_face(d, 518, 772, 58, "smile")
    doodle_face(d, 722, 772, 58, "calm")
    for x in (518, 722):
        d.rounded_rectangle(sbox([x - 62, 856, x + 62, 872]), radius=s(8),
                            fill=sc.PAPER_LINE + (255,))
    img.alpha_composite(lay)


def pencil_prop(img):
    """Карандаш в правой руке — рисуется после рук, поэтому лежит в ладони."""
    lay, d = sc.layer(img)
    x0, x1 = 752, 792
    d.rounded_rectangle(sbox([x0, 632, x1, 754]), radius=s(10),
                        fill=sc.ACCENT + (255,))
    d.rectangle(sbox([x0, 754, x1, 784]), fill=WOOD + (255,))
    d.polygon([*sbox([x0, 784]), *sbox([x1, 784]), *sbox([(x0 + x1) / 2, 824])],
              fill=sc.INK + (255,))
    img.alpha_composite(lay)


# --- фокус на ценностях ------------------------------------------------------


def compass_prop(img):
    """Компас в руках: стрелка смотрит вперёд-вверх."""
    lay, d = sc.layer(img)
    cx, cy, r = 620, 816, 124
    d.ellipse(sbox([cx - r, cy - r, cx + r, cy + r]), fill=sc.ACCENT + (255,))
    d.ellipse(sbox([cx - r + 22, cy - r + 22, cx + r - 22, cy + r - 22]),
              fill=sc.PAPER + (255,))
    for k in range(4):                      # румбы
        a = math.radians(k * 90 + 90)
        ux, uy = math.cos(a), -math.sin(a)
        d.line(sbox([cx + ux * 78, cy + uy * 78, cx + ux * 92, cy + uy * 92]),
               fill=sc.PAPER_LINE + (255,), width=int(s(10)))

    u = (math.cos(math.radians(52)), -math.sin(math.radians(52)))
    p = (-u[1], u[0])
    tip = (cx + u[0] * 76, cy + u[1] * 76)
    tail = (cx - u[0] * 76, cy - u[1] * 76)
    s1 = (cx + p[0] * 22, cy + p[1] * 22)
    s2 = (cx - p[0] * 22, cy - p[1] * 22)
    d.polygon([*sbox([*tail]), *sbox([*s1]), *sbox([*s2])],
              fill=sc.PAPER_LINE + (255,))
    d.polygon([*sbox([*tip]), *sbox([*s1]), *sbox([*s2])],
              fill=WARM_DARK + (255,))
    d.ellipse(sbox([cx - 16, cy - 16, cx + 16, cy + 16]),
              fill=sc.ACCENT + (255,))
    img.alpha_composite(lay)


def compass_sparks(img):
    lay, d = sc.layer(img)
    sparkle_at(d, [(938, 610, 42), (986, 706, 26)], WARM_LIGHT)
    img.alpha_composite(lay)


# --- товары ------------------------------------------------------------------

ITEMS: dict[str, dict] = {
    "booster-streak-freeze": dict(
        pose="idle", face=sc.F(eyes="sleepy", mouth="smile"), blush=215,
        back=[ice_shield, snow_bits], title="Заморозка серии"),
    "booster-extra-task": dict(
        pose="wave", face=sc.F(eyes="sparkle", brows="raised", mouth="wide"),
        back=[checklist_card, plus_one], title="Доп. задание дня"),
    "booster-lesson-hint": dict(
        pose="hold", face=sc.F(eyes="sparkle", brows="raised", mouth="wide"),
        back=[hint_sparks], front=[bulb_prop, sc.hands_notepad],
        title="Подсказка в уроке"),
    "technique-self-embrace": dict(
        pose="hug", face=sc.F(eyes="closed", brows="none", mouth="smile"),
        blush=215, back=[close_hearts], title="«Самообъятие»"),
    "technique-emotion-diary": dict(
        pose="hold", face=sc.F(eyes="open", mouth="smile"),
        front=[open_diary, sc.hands_notepad, pencil_prop],
        title="Дневник эмоций"),
    "technique-values-focus": dict(
        pose="hold", face=sc.F(eyes="open", brows="normal", mouth="smile"),
        back=[compass_sparks], front=[compass_prop, sc.hands_notepad],
        title="Фокус на ценностях"),
}

# Одна рамка на все шесть карточек — доли от холста cute_star. Подобрана по
# объединённым габаритам сцен: если кадрировать каждую по содержимому,
# маскот будет прыгать по размеру от товара к товару.
CROP_CENTER = (0.500, 0.481)
CROP_SIDE = 0.850


def render_item(name: str, size: int = 1024) -> Image.Image:
    cfg = ITEMS[name]
    face = dict(cfg["face"])
    if "blush" in cfg:
        face["blush"] = cfg["blush"]
    art = cs.render(cs.CANVAS, transparent=True, shadow=False,
                    pose=cfg["pose"], face_override=face, motion=False,
                    back=cfg.get("back", ()), front=cfg.get("front", ()))
    n = art.size[0]
    half = int(n * CROP_SIDE / 2)
    cx, cy = int(n * CROP_CENTER[0]), int(n * CROP_CENTER[1])
    art = art.crop((cx - half, cy - half, cx + half, cy + half))
    return art.resize((size, size), Image.LANCZOS)


def export(folder: str, size: int = 1024) -> None:
    os.makedirs(folder, exist_ok=True)
    for name in ITEMS:
        render_item(name, size).save(os.path.join(folder, f"{name}.png"))
    print(f"{folder}: {len(ITEMS)} PNG по {size}px")


def contact_sheet(path: str = "shop.png", cell: int = 320) -> None:
    from PIL import ImageDraw, ImageFont
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    mono = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15)
    names = list(ITEMS)
    cols, pad, label = 3, 24, 58
    rows = math.ceil(len(names) / cols)
    sheet = Image.new("RGB", (cols * (cell + pad) + pad,
                              rows * (cell + pad + label) + pad),
                      (18, 23, 42))
    d = ImageDraw.Draw(sheet)
    for i, name in enumerate(names):
        x = pad + (i % cols) * (cell + pad)
        y = pad + (i // cols) * (cell + pad + label)
        art = render_item(name, cell)
        sheet.paste(art, (x, y), art)
        d.text((x + cell / 2, y + cell + 8), ITEMS[name]["title"], font=font,
               fill=(214, 220, 240), anchor="ma")
        d.text((x + cell / 2, y + cell + 32), name, font=mono,
               fill=(240, 196, 88), anchor="ma")
    sheet.save(path)
    print(f"{path} ({sheet.width}x{sheet.height})")


def main() -> None:
    ap = argparse.ArgumentParser(description="Картинки товаров магазина")
    ap.add_argument("--export", metavar="DIR")
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--sheet", default="shop.png")
    args = ap.parse_args()
    contact_sheet(args.sheet)
    if args.export:
        export(args.export, args.size)


if __name__ == "__main__":
    main()
