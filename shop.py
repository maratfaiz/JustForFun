"""Картинки товаров магазина: секретные техники и бустеры.

Техники — мини-сцены с маскотом (собираются из тех же деталей, что и
scenes.py). Бустеры — предметы: снежинка, карточка задания, лампочка.

    python3 shop.py                        # -> shop.png, контактный лист
    python3 shop.py --export assets/shop   # -> PNG по 512 px
"""

from __future__ import annotations

import argparse
import math
import os

from PIL import Image, ImageDraw

import cute_star as cs
import scenes as sc
from cute_star import s, sbox

# --- палитра предметов -------------------------------------------------------

ICE = (150, 205, 255)
ICE_DARK = (86, 152, 228)
ICE_LIGHT = (222, 241, 255)
BULB = (255, 214, 58)
BULB_DARK = (240, 172, 10)
METAL = (150, 158, 190)
METAL_DARK = (110, 118, 152)
GREEN = (86, 200, 150)
GREEN_DARK = (54, 166, 118)


# --- реквизит для техник -----------------------------------------------------


def journal_pad(img):
    """Блокнот с улыбающейся рожицей — дневник эмоций."""
    lay, d = sc.layer(img)
    d.rounded_rectangle(sbox([478, 678, 762, 886]), radius=s(24),
                        fill=sc.PAPER + (255,))
    d.rounded_rectangle(sbox([478, 678, 528, 886]), radius=s(24),
                        fill=sc.ACCENT + (255,))
    # рожица на странице
    cx, cy = 656, 756
    d.ellipse(sbox([cx - 36, cy - 18, cx - 20, cy + 4]), fill=sc.INK + (255,))
    d.ellipse(sbox([cx + 20, cy - 18, cx + 36, cy + 4]), fill=sc.INK + (255,))
    d.arc(sbox([cx - 42, cy + 2, cx + 42, cy + 60]), 20, 160,
          fill=sc.INK + (255,), width=int(s(12)))
    for i, w in enumerate((150, 106)):
        d.rounded_rectangle(sbox([560, 830 + i * 32, 560 + w, 848 + i * 32]),
                            radius=s(9), fill=sc.PAPER_LINE + (255,))
    img.alpha_composite(lay)


def target_disc(img):
    """Мишень в руках — фокус на ценностях."""
    lay, d = sc.layer(img)
    # верхний край на 700 — там же, где у большого сердца: ниже рта, иначе
    # предмет наезжает на лицо
    cx, cy = 620, 834
    for r, color in ((134, sc.PAPER), (96, sc.RED), (58, sc.PAPER),
                     (24, sc.RED)):
        d.ellipse(sbox([cx - r, cy - r, cx + r, cy + r]), fill=color + (255,))
    img.alpha_composite(lay)


def small_hearts(img):
    """Пара сердечек вокруг — теплее, чем полный венок из ex6."""
    lay, d = sc.layer(img)
    for x, y, size in ((286, 470, 68), (960, 428, 84), (352, 830, 54),
                       (912, 806, 62)):
        sc.heart(d, x, y, size, sc.RED)
    img.alpha_composite(lay)


TECHNIQUES = {
    "technique-selfhug": dict(
        pose="hug", face=sc.F(eyes="closed", brows="none", mouth="smile"),
        blush=215, back=[small_hearts], title="«Самообъятие»"),
    "technique-journal": dict(
        pose="hold", face=sc.F(eyes="open", mouth="smile"),
        front=[journal_pad, sc.hands_notepad], title="Дневник эмоций"),
    "technique-values": dict(
        pose="hold", face=sc.F(eyes="sparkle", brows="raised", mouth="wide"),
        front=[target_disc, sc.hands_notepad], title="Фокус на ценностях"),
}

# Общая рамка для всех трёх карточек — доли от холста cute_star. Кадр один
# на все техники, иначе в списке маскот будет прыгать по размеру. Подобран
# по объединённым габаритам трёх сцен (x 0.20–0.81, y 0.23–0.79) с полями.
CROP_CENTER = (0.505, 0.505)
CROP_SIDE = 0.720


def render_technique(name: str, size: int = 512) -> Image.Image:
    cfg = TECHNIQUES[name]
    face = dict(cfg["face"])
    if "blush" in cfg:
        face["blush"] = cfg["blush"]
    art = cs.render(cs.CANVAS, transparent=True, shadow=False,
                    pose=cfg["pose"], face_override=face,
                    back=cfg.get("back", ()), front=cfg.get("front", ()))
    n = art.size[0]
    half = int(n * CROP_SIDE / 2)
    cx, cy = int(n * CROP_CENTER[0]), int(n * CROP_CENTER[1])
    art = art.crop((cx - half, cy - half, cx + half, cy + half))
    return art.resize((size, size), Image.LANCZOS)


# --- бустеры -----------------------------------------------------------------
# Рисуются в своей сетке 512 с суперсэмплингом: это предметы, а не сцены.

BS = 4                       # суперсэмплинг бустеров
BOX = 512.0                  # логический холст
BN = int(BOX * BS)
BC = BOX / 2


def b(v: float) -> float:
    return v * BS


def bbox_(box):
    return [b(v) for v in box]


def shaded(mask: Image.Image, top, bottom) -> Image.Image:
    """Заливает L-маску вертикальным градиентом — предмет получает объём."""
    grad = cs.vertical_gradient(mask.size, top, bottom)
    out = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    out.paste(grad, (0, 0), mask)
    return out


def bmask() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    m = Image.new("L", (BN, BN), 0)
    return m, ImageDraw.Draw(m)


def sparkles(d, spots):
    for cx, cy, r in spots:
        k = r * 0.26
        d.polygon([b(cx), b(cy - r), b(cx + k), b(cy - k), b(cx + r), b(cy),
                   b(cx + k), b(cy + k), b(cx), b(cy + r), b(cx - k), b(cy + k),
                   b(cx - r), b(cy), b(cx - k), b(cy - k)], fill=255)


def booster_freeze() -> Image.Image:
    """Снежинка — заморозка серии."""
    m, d = bmask()
    w = 34.0
    for k in range(6):
        a = math.radians(k * 60)
        ux, uy = math.cos(a), math.sin(a)
        d.line([b(BC), b(BC), b(BC + ux * 190), b(BC + uy * 190)],
               fill=255, width=int(b(w)))
        for frac, blen in ((0.50, 66.0), (0.78, 50.0)):
            bx, by = BC + ux * 190 * frac, BC + uy * 190 * frac
            for side in (+42, -42):
                t = math.radians(k * 60 + side)
                d.line([b(bx), b(by), b(bx + math.cos(t) * blen),
                        b(by + math.sin(t) * blen)], fill=255, width=int(b(w)))
        # утолщение на конце луча
        d.ellipse(bbox_([BC + ux * 190 - 24, BC + uy * 190 - 24,
                         BC + ux * 190 + 24, BC + uy * 190 + 24]), fill=255)
    d.ellipse(bbox_([BC - 46, BC - 46, BC + 46, BC + 46]), fill=255)

    img = shaded(m, ICE_LIGHT, ICE_DARK)
    core, dc = bmask()
    dc.ellipse(bbox_([BC - 26, BC - 26, BC + 26, BC + 26]), fill=255)
    img.paste(Image.new("RGBA", (BN, BN), ICE_LIGHT + (255,)), (0, 0), core)

    spark, ds = bmask()
    sparkles(ds, [(96, 118, 30), (424, 150, 22), (398, 402, 26)])
    img.paste(Image.new("RGBA", (BN, BN), ICE + (255,)), (0, 0), spark)
    return img.resize((int(BOX), int(BOX)), Image.LANCZOS)


def booster_task() -> Image.Image:
    """Карточка задания с галочкой и плюсом — доп. задание дня."""
    m, d = bmask()
    d.rounded_rectangle(bbox_([96, 62, 400, 442]), radius=b(40), fill=255)
    img = shaded(m, sc.PAPER, (222, 226, 242))

    lay = Image.new("RGBA", (BN, BN), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.rounded_rectangle(bbox_([96, 62, 400, 148]), radius=b(40),
                         fill=sc.ACCENT + (255,))
    dl.rectangle(bbox_([96, 108, 400, 148]), fill=sc.ACCENT + (255,))
    for i in range(3):
        y = 200 + i * 74
        done = i == 0
        color = GREEN if done else sc.PAPER_LINE
        dl.rounded_rectangle(bbox_([136, y - 22, 180, y + 22]), radius=b(12),
                             fill=color + (255,))
        dl.rounded_rectangle(bbox_([204, y - 12, 204 + (128 - i * 18), y + 12]),
                             radius=b(12), fill=sc.PAPER_LINE + (255,))
    dl.line([b(146), b(200), b(156), b(211), b(172), b(190)],
            fill=sc.PAPER + (255,), width=int(b(11)), joint="curve")
    img.alpha_composite(lay)

    # значок «+» в углу
    badge, db = bmask()
    db.ellipse(bbox_([326, 306, 470, 450]), fill=255)
    img.paste(shaded(badge, (168, 152, 255), sc.ACCENT), (0, 0), badge)
    plus, dp = bmask()
    dp.rounded_rectangle(bbox_([386, 340, 410, 416]), radius=b(12), fill=255)
    dp.rounded_rectangle(bbox_([360, 366, 436, 390]), radius=b(12), fill=255)
    img.paste(Image.new("RGBA", (BN, BN), sc.PAPER + (255,)), (0, 0), plus)
    return img.resize((int(BOX), int(BOX)), Image.LANCZOS)


def booster_hint() -> Image.Image:
    """Лампочка — подсказка в уроке."""
    m, d = bmask()
    d.ellipse(bbox_([146, 62, 366, 282]), fill=255)
    d.polygon([b(196), b(250), b(316), b(250), b(300), b(338), b(212), b(338)],
              fill=255)
    img = shaded(m, (255, 232, 140), BULB_DARK)

    lay = Image.new("RGBA", (BN, BN), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    dl.arc(bbox_([222, 118, 290, 200]), 200, 340, fill=BULB_DARK + (255,),
           width=int(b(13)))
    dl.line([b(256), b(186), b(256), b(238)], fill=BULB_DARK + (255,),
            width=int(b(13)))
    img.alpha_composite(lay)

    cap, dc = bmask()
    dc.rounded_rectangle(bbox_([210, 340, 302, 386]), radius=b(18), fill=255)
    dc.rounded_rectangle(bbox_([222, 396, 290, 438]), radius=b(20), fill=255)
    img.paste(shaded(cap, METAL, METAL_DARK), (0, 0), cap)

    spark, ds = bmask()
    sparkles(ds, [(94, 128, 30), (420, 168, 24), (108, 300, 20)])
    img.paste(Image.new("RGBA", (BN, BN), BULB + (255,)), (0, 0), spark)
    return img.resize((int(BOX), int(BOX)), Image.LANCZOS)


BOOSTERS = {
    "booster-freeze": (booster_freeze, "Заморозка серии"),
    "booster-extra-task": (booster_task, "Доп. задание дня"),
    "booster-hint": (booster_hint, "Подсказка в уроке"),
}


# --- сборка ------------------------------------------------------------------


def render_item(name: str, size: int = 512) -> Image.Image:
    if name in TECHNIQUES:
        return render_technique(name, size)
    img = BOOSTERS[name][0]()
    return img if size == int(BOX) else img.resize((size, size), Image.LANCZOS)


def titles() -> dict[str, str]:
    out = {k: v["title"] for k, v in TECHNIQUES.items()}
    out.update({k: v[1] for k, v in BOOSTERS.items()})
    return out


def export(folder: str, size: int = 512) -> None:
    os.makedirs(folder, exist_ok=True)
    for name in titles():
        render_item(name, size).save(os.path.join(folder, f"{name}.png"))
    print(f"{folder}: {len(titles())} PNG по {size}px")


def contact_sheet(path: str = "shop.png", cell: int = 320) -> None:
    from PIL import ImageFont
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    mono = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)
    names = list(titles())
    cols = 3
    rows = math.ceil(len(names) / cols)
    pad, label = 24, 58
    sheet = Image.new("RGB", (cols * (cell + pad) + pad,
                              rows * (cell + pad + label) + pad),
                      (18, 23, 42))
    d = ImageDraw.Draw(sheet)
    for i, name in enumerate(names):
        x = pad + (i % cols) * (cell + pad)
        y = pad + (i // cols) * (cell + pad + label)
        art = render_item(name, cell)
        sheet.paste(art, (x, y), art)
        d.text((x + cell / 2, y + cell + 8), titles()[name], font=font,
               fill=(214, 220, 240), anchor="ma")
        d.text((x + cell / 2, y + cell + 32), name, font=mono,
               fill=(240, 196, 88), anchor="ma")
    sheet.save(path)
    print(f"{path} ({sheet.width}x{sheet.height})")


def main() -> None:
    ap = argparse.ArgumentParser(description="Картинки товаров магазина")
    ap.add_argument("--export", metavar="DIR")
    ap.add_argument("--size", type=int, default=512)
    ap.add_argument("--sheet", default="shop.png")
    args = ap.parse_args()
    contact_sheet(args.sheet)
    if args.export:
        export(args.export, args.size)


if __name__ == "__main__":
    main()
