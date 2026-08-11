#!/usr/bin/env python3
"""Доводка набора Phosphor: две составные иконки + цветная копия.

    node tools/phosphor_render.js package/assets out/raw 1024
    python3 tools/phosphor_finish.py out/raw assets/icons-phosphor

Составные иконки:
  * icon-lumen        — кольцо + звезда внутри (валюты со звездой в наборе нет)
  * icon-critic-voice — пузырь + восклицательный знак (в наборе только знак
                        внутри рамки, поэтому знак дорисовывается вручную
                        той же толщиной линии)
"""

import os
import shutil
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from icons import ICONS  # noqa: E402  — только ради таблицы цветов

STROKE_RATIO = 24 / 256      # толщина линии Phosphor bold относительно стороны


def place(base: Image.Image, part: Image.Image, frac_h, cx, cy):
    """Вписывает part по высоте frac_h и ставит центром в (cx, cy) — доли."""
    n = base.size[0]
    part = part.crop(part.getchannel("A").getbbox())
    h = int(n * frac_h)
    w = max(1, int(part.size[0] * h / part.size[1]))
    part = part.resize((w, h), Image.LANCZOS)
    base.paste(part, (int(n * cx - w / 2), int(n * cy - h / 2)), part)
    return base


def compose_lumen(raw: str) -> Image.Image:
    coin = Image.open(os.path.join(raw, "part-circle.png")).convert("RGBA")
    star = Image.open(os.path.join(raw, "part-star.png")).convert("RGBA")
    return place(coin, star, 0.40, 0.5, 0.5)


def compose_critic_voice(raw: str) -> Image.Image:
    bub = Image.open(os.path.join(raw, "part-chat-teardrop.png")).convert("RGBA")
    n = bub.size[0]
    stroke = n * STROKE_RATIO
    ss = 4
    m = Image.new("L", (n * ss, n * ss), 0)
    d = ImageDraw.Draw(m)
    cx, r = 0.556 * n * ss, stroke * ss / 2
    top, bot, dot = 0.305 * n * ss, 0.502 * n * ss, 0.594 * n * ss
    d.rounded_rectangle([cx - r, top, cx + r, bot], radius=r, fill=255)
    d.ellipse([cx - r, dot - r, cx + r, dot + r], fill=255)
    bub.paste(Image.new("RGBA", (n, n), "#000000"), (0, 0),
              m.resize((n, n), Image.LANCZOS))
    return bub


def main() -> None:
    raw, out = sys.argv[1], sys.argv[2]
    colored = out + "-colored"
    os.makedirs(out, exist_ok=True)
    os.makedirs(colored, exist_ok=True)

    for name in ICONS:
        src = os.path.join(raw, f"{name}.png")
        if name == "icon-lumen":
            img = compose_lumen(raw)
        elif name == "icon-critic-voice":
            img = compose_critic_voice(raw)
        else:
            img = Image.open(src).convert("RGBA")
        img.save(os.path.join(out, f"{name}.png"))

        flat = Image.new("RGBA", img.size, ICONS[name][1])
        tinted = Image.new("RGBA", img.size, (0, 0, 0, 0))
        tinted.paste(flat, (0, 0), img.getchannel("A"))
        tinted.save(os.path.join(colored, f"{name}.png"))

    here = os.path.dirname(os.path.abspath(__file__))
    for folder in (out, colored):
        shutil.copy(os.path.join(here, "PHOSPHOR-LICENSE.txt"),
                    os.path.join(folder, "LICENSE.txt"))
    print(f"{out}: {len(ICONS)} иконок, цветная копия в {colored}")


if __name__ == "__main__":
    main()
