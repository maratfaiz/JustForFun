"""Лист эмоций маскота: сетка поз с подписями. Результат — emotions.png.

    python3 make_emotions.py                 # -> emotions.png
    python3 make_emotions.py --export dir    # + отдельные прозрачные PNG
"""

from __future__ import annotations

import argparse
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import cute_star as cs

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

BG_TOP = (16, 21, 40)
BG_BOTTOM = (26, 32, 58)
CARD = (32, 40, 70)
BADGE = (124, 108, 240)
TITLE = (255, 255, 255)
TEXT = (176, 186, 214)
CODE = (240, 196, 88)

COLS, ROWS = 5, 2
CARD_W, CARD_H = 448, 648      # карточка эмоции
GAP = 26
MARGIN = 56
HEAD = 250


def background(size) -> Image.Image:
    """Тёмный вертикальный градиент."""
    w, h = size
    grad = Image.new("RGB", (1, h))
    px = grad.load()
    for y in range(h):
        k = y / (h - 1)
        px[0, y] = tuple(round(BG_TOP[c] + (BG_BOTTOM[c] - BG_TOP[c]) * k)
                         for c in range(3))
    return grad.resize((w, h), Image.BILINEAR)


def glow(size, box, color, alpha, blur) -> Image.Image:
    """Мягкое свечение под персонажем."""
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).ellipse(box, fill=alpha)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    layer = Image.new("RGBA", size, color + (0,))
    layer.putalpha(m)
    return layer


def export_pngs(folder: str, size: int = 512) -> None:
    """Отдельные прозрачные PNG — то, что кладётся в приложение."""
    os.makedirs(folder, exist_ok=True)
    for name in cs.EMOTIONS:
        path = os.path.join(folder, f"star_{name}.png")
        cs.render(size, transparent=True, shadow=False, emotion=name).save(path)
    print(f"Экспортировано в {folder}/: {len(cs.EMOTIONS)} PNG по {size}px")


def main() -> None:
    ap = argparse.ArgumentParser(description="Лист эмоций маскота")
    ap.add_argument("--export", metavar="DIR", default=None,
                    help="также сохранить каждую эмоцию отдельным PNG")
    ap.add_argument("--export-size", type=int, default=512)
    args = ap.parse_args()

    names = list(cs.EMOTIONS)
    W = MARGIN * 2 + COLS * CARD_W + (COLS - 1) * GAP
    H = HEAD + MARGIN + ROWS * CARD_H + (ROWS - 1) * GAP

    sheet = background((W, H)).convert("RGBA")
    d = ImageDraw.Draw(sheet)

    head = ImageFont.truetype(BOLD, 62)
    sub = ImageFont.truetype(FONT, 34)
    name_f = ImageFont.truetype(BOLD, 34)
    text_f = ImageFont.truetype(FONT, 25)
    code_f = ImageFont.truetype(MONO, 24)
    num_f = ImageFont.truetype(BOLD, 28)

    d.text((W // 2, 92), "ЭМОЦИИ МАСКОТА — ЗВЁЗДОЧКА", font=head,
           fill=TITLE, anchor="mm")
    d.text((W // 2, 158), "все позы рисуются кодом: cute_star.py --emotion ...",
           font=sub, fill=TEXT, anchor="mm")

    for i, name in enumerate(names):
        cfg = cs.EMOTIONS[name]
        col, row = i % COLS, i // COLS
        x = MARGIN + col * (CARD_W + GAP)
        y = HEAD + row * (CARD_H + GAP)

        d.rounded_rectangle([x, y, x + CARD_W, y + CARD_H], radius=28, fill=CARD)

        # crop=False — иначе у каждой эмоции свой масштаб и звёздочки
        # получаются разного размера
        art = cs.render(430, transparent=True, shadow=False, emotion=name)
        ax, ay = x + (CARD_W - 430) // 2, y - 4
        sheet.alpha_composite(
            glow(sheet.size, [ax + 120, ay + 290, ax + 310, ay + 350],
                 (250, 200, 60), 70, 40))
        sheet.alpha_composite(art, (ax, ay))

        # номер в кружке + название
        by = y + 420
        d.rounded_rectangle([x + 28, by, x + 74, by + 46], radius=14, fill=BADGE)
        d.text((x + 51, by + 23), str(i + 1), font=num_f, fill=TITLE, anchor="mm")
        d.text((x + 90, by + 23), cfg["title"], font=name_f, fill=TITLE,
               anchor="lm")

        d.multiline_text((x + 28, by + 76), cfg["desc"], font=text_f,
                         fill=TEXT, spacing=10)
        d.text((x + 28, y + CARD_H - 34), f"--emotion {name}", font=code_f,
               fill=CODE, anchor="lm")

    sheet.convert("RGB").save("emotions.png")
    print(f"Готово: emotions.png ({W}x{H}), эмоций: {len(names)}")

    if args.export:
        export_pngs(args.export, args.export_size)


if __name__ == "__main__":
    main()
