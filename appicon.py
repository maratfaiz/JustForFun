"""Иконка приложения: Луми на сплошном фоне.

Требования App Store, из-за которых иконка отличается от остальных ассетов:
  * 1024×1024, **без альфа-канала** — прозрачность приводит к отклонению;
  * без скруглённых углов — маску-суперэллипс накладывает система;
  * запас по краям: углы срезаются, к ним ничего важного не придвигаем.

    python3 appicon.py                       # -> appicon.png + превью
    python3 appicon.py --export assets       # -> appicon-<вариант>.png
"""

from __future__ import annotations

import argparse
import os

from PIL import Image, ImageDraw, ImageFilter

import cute_star as cs

# Доля стороны, которую занимает фигура. Больше 0.74 — упирается в углы,
# которые система срежет; меньше 0.62 — теряется на мелких размерах.
FIGURE = 0.70
CENTER_Y = 0.485          # оптический центр чуть выше геометрического

BACKGROUNDS = {
    "night": ((36, 42, 78), (14, 18, 38), "Тёмный космос"),
    "violet": ((146, 128, 250), (86, 68, 196), "Фиолетовый"),
    "cream": ((255, 246, 224), (255, 220, 156), "Тёплый светлый"),
}

FACE = dict(eyes="closed", brows="none", mouth="wide", blush=215)


def lumi(size: int) -> Image.Image:
    """Фигура, обрезанная по силуэту."""
    art = cs.render(cs.CANVAS, transparent=True, shadow=False, pose="idle",
                    face_override=dict(FACE))
    art = art.crop(art.getchannel("A").getbbox())
    side = max(art.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(art, ((side - art.width) // 2, (side - art.height) // 2))
    return square.resize((size, size), Image.LANCZOS)


def render(variant: str = "night", size: int = 1024) -> Image.Image:
    top, bottom, _ = BACKGROUNDS[variant]
    icon = cs.vertical_gradient((size, size), top, bottom).convert("RGBA")

    fig = lumi(int(size * FIGURE))
    x = (size - fig.width) // 2
    y = int(size * CENTER_Y) - fig.height // 2

    # мягкая тень со смещением вниз — это опора, а не ореол вокруг фигуры
    sh = Image.new("L", (size, size), 0)
    sh.paste(fig.getchannel("A"), (x, y + int(size * 0.022)))
    sh = sh.filter(ImageFilter.GaussianBlur(size * 0.028))
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow.putalpha(Image.eval(sh, lambda v: v * 58 // 255))
    icon.alpha_composite(shadow)

    icon.alpha_composite(fig, (x, y))
    return icon.convert("RGB")          # без альфы: требование App Store


def ios_preview(icon: Image.Image, size: int) -> Image.Image:
    """Как иконку покажет система: суперэллипс приближаем скруглением 22.37%."""
    im = icon.resize((size, size), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size * 4 - 1, size * 4 - 1],
                                        radius=int(size * 4 * 0.2237), fill=255)
    im.putalpha(m.resize((size, size), Image.LANCZOS))
    return im


def sheet(path: str = "appicon.png") -> None:
    from PIL import ImageFont
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 19)
    mono = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15)
    small = (180, 120, 80, 60, 40)
    big = 300
    row_h = big + 78
    sh = Image.new("RGB", (big + 60 + sum(small) + 24 * len(small),
                           row_h * len(BACKGROUNDS) + 24), (28, 30, 40))
    d = ImageDraw.Draw(sh)

    for r, (name, (_, _, title)) in enumerate(BACKGROUNDS.items()):
        icon = render(name, 1024)
        y = 24 + r * row_h
        sh.paste(ios_preview(icon, big), (24, y), ios_preview(icon, big))
        d.text((24, y + big + 12), title, font=font, fill=(226, 230, 245))
        d.text((24, y + big + 38), f"appicon-{name}", font=mono,
               fill=(240, 196, 88))
        x = 24 + big + 40
        for px in small:
            p = ios_preview(icon, px)
            sh.paste(p, (x, y + (big - px) // 2), p)
            d.text((x + px / 2, y + (big + px) // 2 + 10), f"{px}px",
                   font=mono, fill=(150, 158, 190), anchor="ma")
            x += px + 24
    sh.save(path)
    print(f"{path} ({sh.width}x{sh.height})")


def export(folder: str, size: int = 1024) -> None:
    os.makedirs(folder, exist_ok=True)
    for name in BACKGROUNDS:
        render(name, size).save(os.path.join(folder, f"appicon-{name}.png"))
    print(f"{folder}: {len(BACKGROUNDS)} PNG по {size}px, RGB без альфы")


def main() -> None:
    ap = argparse.ArgumentParser(description="Иконка приложения")
    ap.add_argument("--export", metavar="DIR")
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--sheet", default="appicon.png")
    args = ap.parse_args()
    sheet(args.sheet)
    if args.export:
        export(args.export, args.size)


if __name__ == "__main__":
    main()
