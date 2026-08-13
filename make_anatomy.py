"""Служебный скрипт: рисует схему персонажа с подписями параметров.

Нужен, чтобы объяснить (человеку или другой модели), где в `cute_star.py`
лежит какая часть звёздочки. Результат — anatomy.png.

    python3 make_anatomy.py
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

import cute_star as cs

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
INK = (40, 44, 58)
ACCENT = (208, 60, 90)
GRID = (200, 205, 220)

W = 1240            # ширина одной колонки = логический холст cute_star
PAD_X = 430         # поля справа/слева под подписи


def label(d, xy, target, text, code, font, mono, anchor="lm"):
    """Подпись со стрелкой к точке target."""
    x, y = xy
    d.line([xy, target], fill=ACCENT, width=3)
    d.ellipse([target[0] - 7, target[1] - 7, target[0] + 7, target[1] + 7],
              fill=ACCENT)
    dx = 14 if anchor == "lm" else -14
    d.text((x + dx, y - 20), text, font=font, fill=INK,
           anchor="lm" if anchor == "lm" else "rm")
    d.text((x + dx, y + 14), code, font=mono, fill=ACCENT,
           anchor="lm" if anchor == "lm" else "rm")


def panel(pose: str, notes) -> Image.Image:
    """Одна колонка: рендер позы + подписи вокруг."""
    art = cs.render(W, pose=pose)
    sheet = Image.new("RGB", (W + PAD_X * 2, W + 150), "white")
    sheet.paste(art, (PAD_X, 120))
    d = ImageDraw.Draw(sheet)

    font = ImageFont.truetype(FONT, 27)
    mono = ImageFont.truetype(MONO, 24)
    head = ImageFont.truetype(FONT, 40)

    d.text((PAD_X, 46), f"--pose {pose}", font=head, fill=INK)

    # оси координат: центр звезды
    cx, cy = PAD_X + cs.CX, 120 + cs.CY
    d.line([(cx, 120), (cx, 120 + W)], fill=GRID, width=2)
    d.line([(PAD_X, cy), (PAD_X + W, cy)], fill=GRID, width=2)
    d.text((PAD_X + 20, 120 + W - 30), "CX, CY = 620, 566", font=mono, fill=GRID)

    for (lx, ly), (tx, ty), text, code, anchor in notes:
        label(d, (PAD_X + lx, 120 + ly), (PAD_X + tx, 120 + ty),
              text, code, font, mono, anchor)
    return sheet


IDLE_NOTES = [
    ((-420, 300), (300, 254), "кончик луча: угол и радиус",
     "polar(163, 348)", "lm"),
    ((-420, 470), (455, 400), "толщина луча у основания",
     "polar(127, 200)", "lm"),
    ((-420, 700), (395, 700), "рука (dx, cy, w, h, наклон)",
     "ARM_DOWN", "lm"),
    ((-420, 880), (420, 850), "нижний угол тела",
     "polar(236, 358)", "lm"),
    ((1330, 300), (940, 254), "скругление кончиков",
     "star_mask(): radii[0,2,8]", "rm"),
    ((1330, 500), (826, 658), "боковой вырез (талия)",
     "polar(-24, 226)", "rm"),
    ((1330, 700), (845, 700), "правая рука — зеркало левой",
     "ARM_DOWN, tilt +10", "rm"),
    ((1330, 860), (620, 806), "вырез между ножками",
     "polar(-90, 240)", "rm"),
    ((1330, 980), (720, 880), "ножка-капсула",
     "FOOT_W/H/DX/CY", "rm"),
]

WAVE_NOTES = [
    ((1330, 180), (1024, 512), "штрихи движения у кисти",
     "draw_motion_lines()", "rm"),
    ((1330, 470), (905, 640), "поднятая рука: то же плечо,",
     "ARM_UP = (259, 642, 76, 180, -50)", "rm"),
    ((-420, 620), (600, 650), "улыбка шире, чем в idle",
     "draw_face(pose='wave')", "lm"),
    ((-420, 790), (395, 700), "вторая рука не меняется",
     "ARM_DOWN", "lm"),
]


def main() -> None:
    left = panel("idle", IDLE_NOTES)
    right = panel("wave", WAVE_NOTES)
    out = Image.new("RGB", (left.width + right.width, left.height), "white")
    out.paste(left, (0, 0))
    out.paste(right, (left.width, 0))
    out = out.resize((out.width // 2, out.height // 2), Image.LANCZOS)
    out.save("anatomy.png")
    print(f"Готово: anatomy.png ({out.width}x{out.height})")


if __name__ == "__main__":
    main()
