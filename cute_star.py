"""Рисуем милую жёлтую звёздочку-персонажа средствами Python (Pillow).

Всё считается в "логических" координатах холста 1240x1240, а рисуется
с суперсэмплингом (SS), после чего картинка уменьшается — так получаются
гладкие края без встроенного антиалиасинга.

Запуск:
    python3 cute_star.py [--out star.png] [--size 1240]
"""

from __future__ import annotations

import argparse
import math

from PIL import Image, ImageChops, ImageDraw, ImageFilter

# --- размеры и палитра -------------------------------------------------------

CANVAS = 1240          # логический размер холста
SS = 3                 # коэффициент суперсэмплинга

BG = (255, 255, 255)
BODY_TOP = (255, 214, 58)      # жёлтый у верхнего луча
BODY_BOTTOM = (248, 186, 8)    # жёлтый у нижних лучей
SHADOW = (203, 201, 223)
EYE = (32, 27, 28)
BROW = (150, 86, 18)
LIMB_SHADE = (198, 134, 4)     # тон, которым отделяются руки-ноги

# насколько руки-ноги отделяются от корпуса: (тон конечности, контактная тень)
LIMB_DEPTH = {"none": (0, 0), "soft": (70, 110),
              "medium": (110, 130), "strong": (170, 150)}
BLUSH = (246, 160, 74)
GLOSS = (255, 255, 255)
MOTION = (240, 178, 24)        # штрихи движения у машущей руки
HEART = (240, 122, 138)        # сердечки у «заботливой» эмоции
TEAR = (126, 186, 240)         # слеза

# центр звезды
CX, CY = 620.0, 566.0

# ножки-капсулы: полукруг — прямой участок — полукруг. Из-под корпуса должно
# торчать чуть меньше половины капсулы
FOOT_W, FOOT_H = 112.0, 132.0
FOOT_DX, FOOT_CY = 100.0, 834.0


def s(v: float) -> float:
    """Логическая координата -> координата рабочего холста."""
    return v * SS


def sbox(box):
    return [s(v) for v in box]


# --- геометрия ---------------------------------------------------------------


def polar(angle_deg: float, radius: float) -> tuple[float, float]:
    """Точка вокруг центра звезды; угол — против часовой, 90° = вверх."""
    a = math.radians(angle_deg)
    return CX + radius * math.cos(a), CY - radius * math.sin(a)


def star_vertices() -> list[tuple[float, float]]:
    """Вершины пятиконечной звезды: пропорции подогнаны под персонажа —
    широкие «бёдра» снизу и неглубокая выемка между ними."""
    outer = [
        polar(90, 312),    # верхний луч
        polar(17, 348),    # правая «рука»
        polar(-56, 358),   # правый нижний угол
        polar(236, 358),   # левый нижний угол
        polar(163, 348),   # левая «рука»
    ]
    inner = [
        polar(53, 200),
        polar(-24, 226),
        polar(-90, 240),   # выемка между ног — заметная, но не глубокая
        polar(204, 226),
        polar(127, 200),
    ]
    pts: list[tuple[float, float]] = []
    for i in range(5):
        pts.append(outer[i])
        pts.append(inner[i])
    return pts


def round_polygon(points, radii, steps: int = 26):
    """Скругляет углы многоугольника: для каждой вершины строит дугу,
    касающуюся обоих смежных рёбер."""
    n = len(points)
    out: list[tuple[float, float]] = []

    for i in range(n):
        prev = points[i - 1]
        cur = points[i]
        nxt = points[(i + 1) % n]

        v1 = (prev[0] - cur[0], prev[1] - cur[1])
        v2 = (nxt[0] - cur[0], nxt[1] - cur[1])
        l1 = math.hypot(*v1)
        l2 = math.hypot(*v2)
        if l1 < 1e-9 or l2 < 1e-9:
            out.append(cur)
            continue
        u1 = (v1[0] / l1, v1[1] / l1)
        u2 = (v2[0] / l2, v2[1] / l2)

        cos_a = max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1]))
        angle = math.acos(cos_a)
        if angle < 1e-6 or abs(angle - math.pi) < 1e-6:
            out.append(cur)
            continue

        half = angle / 2.0
        r = radii[i % len(radii)]
        t = r / math.tan(half)
        t = min(t, 0.5 * l1, 0.5 * l2)      # не «съедаем» соседние рёбра
        r_eff = t * math.tan(half)

        p1 = (cur[0] + u1[0] * t, cur[1] + u1[1] * t)
        p2 = (cur[0] + u2[0] * t, cur[1] + u2[1] * t)

        bis = (u1[0] + u2[0], u1[1] + u2[1])
        bl = math.hypot(*bis)
        if bl < 1e-9:
            out.extend([p1, p2])
            continue
        bis = (bis[0] / bl, bis[1] / bl)
        center = (cur[0] + bis[0] * r_eff / math.sin(half),
                  cur[1] + bis[1] * r_eff / math.sin(half))

        a1 = math.atan2(p1[1] - center[1], p1[0] - center[0])
        a2 = math.atan2(p2[1] - center[1], p2[0] - center[0])
        delta = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi   # кратчайший путь

        for k in range(steps + 1):
            a = a1 + delta * k / steps
            out.append((center[0] + r_eff * math.cos(a),
                        center[1] + r_eff * math.sin(a)))

    return out


def capsule(draw, cx, cy, w, h, fill):
    """Скруглённая «таблетка» — из неё сделаны ручки и ножки."""
    draw.rounded_rectangle(
        sbox([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2]),
        radius=s(min(w, h) / 2),
        fill=fill,
    )


def rotated_capsule(base: Image.Image, cx, cy, w, h, angle):
    """Повёрнутая таблетка, подмешанная в L-маску."""
    pad = int(s(max(w, h)))
    m = Image.new("L", (pad * 2, pad * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle(
        [pad - s(w) / 2, pad - s(h) / 2, pad + s(w) / 2, pad + s(h) / 2],
        radius=s(min(w, h) / 2),
        fill=255,
    )
    m = m.rotate(angle, resample=Image.BICUBIC)

    at = (int(s(cx)) - pad, int(s(cy)) - pad)
    patch = base.crop((at[0], at[1], at[0] + m.width, at[1] + m.height))
    base.paste(ImageChops.lighter(patch, m), at)


def soft_layer(size, color, alpha, painter, blur=0.0, mask=None) -> Image.Image:
    """Мягкое пятно заданного цвета: рисуем силуэт в маске, размываем её и
    только потом красим — так размытие не подмешивает чёрный."""
    m = Image.new("L", size, 0)
    painter(ImageDraw.Draw(m))
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    if alpha < 255:
        m = m.point(lambda v: v * alpha // 255)
    if mask is not None:
        m = Image.composite(m, Image.new("L", size, 0), mask)
    layer = Image.new("RGBA", size, color + (0,))
    layer.putalpha(m)
    return layer


# --- слои картинки -----------------------------------------------------------


def vertical_gradient(size, top_color, bottom_color) -> Image.Image:
    """Вертикальный градиент во всю ширину холста."""
    w, h = size
    grad = Image.new("RGB", (1, h))
    px = grad.load()
    for y in range(h):
        k = y / (h - 1)
        px[0, y] = tuple(
            round(top_color[c] + (bottom_color[c] - top_color[c]) * k) for c in range(3)
        )
    return grad.resize((w, h), Image.BILINEAR)


def draw_shadow(img: Image.Image) -> None:
    img.alpha_composite(soft_layer(
        img.size, SHADOW, 255,
        lambda d: d.ellipse(sbox([CX - 212, 888, CX + 212, 944]), fill=255),
        blur=s(10),
    ))


ARM_DOWN = (218, 706, 76, 150, 10)       # dx, cy, w, h, наклон наружу
ARM_UP = (259, 642, 76, 180, -50)        # та же «подмышка», что и у опущенной
                                         # руки, но капсула поднята вверх-вбок

# Пресеты рук: dx от центра, cy, ширина, высота, наклон наружу (для правой;
# левая зеркалит и знак наклона, и dx)
ARMS = {
    "down": ARM_DOWN,
    "up": ARM_UP,
    "hold": (150, 706, 74, 152, 58),     # вперёд-внутрь: держит предмет
    "point": (270, 646, 74, 176, -78),   # вбок, почти горизонтально
    "clap": (176, 676, 74, 150, 62),     # ладони сведены перед собой
    "hug": (186, 700, 74, 150, 54),      # обнимает — чуть ниже, чем hold
}

# Поза = (левая рука, правая рука, ноги). Ноги: stand — как обычно,
# sit — короче и разведены (персонаж сидит), none — не рисуются (лотос)
POSES = {
    "idle": ("down", "down", "stand"),
    "wave": ("down", "up", "stand"),
    "cheer": ("up", "up", "stand"),
    "hold": ("hold", "hold", "stand"),
    "point": ("down", "point", "stand"),
    "clap": ("clap", "clap", "stand"),
    "hug": ("hug", "hug", "stand"),
    "sit": ("down", "down", "sit"),
    "sit_hold": ("hug", "hug", "sit"),
    "lotus": ("hold", "hold", "none"),
}


def limb_mask(size, pose: str = "idle") -> Image.Image:
    """Ручки-культяпки по бокам и две ножки снизу — отдельной маской,
    которая потом сливается с телом в один силуэт."""
    left, right, legs = POSES.get(pose, POSES["idle"])
    m = Image.new("L", size, 0)

    if legs == "stand":
        capsule(ImageDraw.Draw(m), CX - FOOT_DX, FOOT_CY, FOOT_W, FOOT_H, 255)
        capsule(ImageDraw.Draw(m), CX + FOOT_DX, FOOT_CY, FOOT_W, FOOT_H, 255)
    elif legs == "sit":                  # ножки свисают короче и шире
        capsule(ImageDraw.Draw(m), CX - 128, FOOT_CY - 26, FOOT_W, 108, 255)
        capsule(ImageDraw.Draw(m), CX + 128, FOOT_CY - 26, FOOT_W, 108, 255)

    dx, cy, w, h, tilt = ARMS[left]
    rotated_capsule(m, CX - dx, cy, w, h, -tilt)
    dx, cy, w, h, tilt = ARMS[right]
    rotated_capsule(m, CX + dx, cy, w, h, tilt)
    return m


def star_mask(size) -> Image.Image:
    pts = star_vertices()
    radii = []
    for i in range(10):
        radii.append(52 if i % 2 == 0 else 56)   # внешние углы / внутренние
    radii[4] = radii[6] = 64                     # нижние углы — мягкие, но видны
    radii[5] = 52                                # выемка между ног — мягкая
    path = round_polygon(pts, radii)

    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon([(s(x), s(y)) for x, y in path], fill=255)
    return mask


def draw_body(img: Image.Image, mask: Image.Image) -> None:
    body = vertical_gradient(img.size, BODY_TOP, BODY_BOTTOM).convert("RGBA")

    # мягкая тень по нижнему краю, чтобы корпус выглядел объёмным
    body.alpha_composite(soft_layer(
        img.size, (226, 160, 6), 115,
        lambda d: d.ellipse(sbox([300, 700, 940, 1000]), fill=255),
        blur=s(40),
    ))

    body.putalpha(mask)
    img.alpha_composite(body)

    # глянцевый блик — узкая полоска вдоль левой грани верхнего луча
    pad = int(s(140))
    streak = Image.new("L", (pad * 2, pad * 2), 0)
    ImageDraw.Draw(streak).ellipse(
        [pad - s(44), pad - s(17), pad + s(44), pad + s(17)], fill=255
    )
    streak = streak.rotate(56, resample=Image.BICUBIC)

    def paint_streak(d, _streak=streak, _pad=pad):
        d.bitmap((int(s(592)) - _pad, int(s(342)) - _pad), _streak, fill=255)

    img.alpha_composite(soft_layer(
        img.size, GLOSS, 135, paint_streak, blur=s(12), mask=mask,
    ))


def tint(img: Image.Image, color, alpha: int, mask: Image.Image) -> None:
    """Подкрашивает область маски полупрозрачным цветом."""
    layer = Image.new("RGBA", img.size, tuple(color) + (0,))
    layer.putalpha(mask if alpha >= 255 else mask.point(lambda v: v * alpha // 255))
    img.alpha_composite(layer)


def draw_limb_depth(img: Image.Image, body: Image.Image, limbs: Image.Image,
                    tone: int = 30, contact: int = 60) -> None:
    """Отделяет руки-ноги от корпуса, не разрывая силуэт: видимая часть
    конечности делается чуть темнее, а вдоль края корпуса на неё ложится
    мягкая контактная тень."""
    visible = ImageChops.subtract(limbs, body)      # то, что торчит из-за тела

    if tone:
        tint(img, LIMB_SHADE, tone, visible)

    if contact:
        edge = body.filter(ImageFilter.GaussianBlur(s(16)))
        tint(img, LIMB_SHADE, contact, ImageChops.multiply(edge, visible))


EYE_X = (533, 722)          # центры глаз
EYE_CY = 598                # середина глаза по вертикали


def stroke_arc(d, box, start, end, color, width, caps=True):
    """Дуга с круглыми концами. PIL рисует толщину внутрь bbox, поэтому
    заглушки ставим по радиусу средней линии."""
    d.arc(sbox(box), start, end, fill=color + (255,), width=int(s(width)))
    if not caps:
        return
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    rx, ry = (box[2] - box[0]) / 2 - width / 2, (box[3] - box[1]) / 2 - width / 2
    r = width / 2
    for a in (start, end):
        x = cx + rx * math.cos(math.radians(a))
        y = cy + ry * math.sin(math.radians(a))
        d.ellipse(sbox([x - r, y - r, x + r, y + r]), fill=color + (255,))


def draw_eyes(d, kind: str) -> None:
    for i, ex in enumerate(EYE_X):
        closed = kind == "closed" or (kind == "wink" and i == 0)
        if closed:                                   # счастливый прищур ^^
            stroke_arc(d, [ex - 34, EYE_CY - 34, ex + 34, EYE_CY + 24],
                       200, 340, EYE, 13)
            continue
        if kind == "sleepy":                         # спокойно прикрытые глаза
            stroke_arc(d, [ex - 34, EYE_CY - 26, ex + 34, EYE_CY + 30],
                       20, 160, EYE, 13)
            continue

        w, h = (34, 50) if kind == "wide" else (29, 42)
        cy = EYE_CY
        if kind == "up":                             # взгляд наверх: зрачки выше
            w, h, cy = 29, 29, EYE_CY - 28
        d.rounded_rectangle(sbox([ex - w, cy - h, ex + w, cy + h]),
                            radius=s(w), fill=EYE + (255,))
        gx = ex + 6 if i == 0 else ex - 28           # блик смотрит к переносице
        gy = cy - h + 12
        d.ellipse(sbox([gx, gy, gx + 22, gy + 24]), fill=(255, 255, 255, 255))
        if kind == "sparkle":                        # второй блик — «горят глаза»
            d.ellipse(sbox([gx - 12, gy + 40, gx - 1, gy + 52]),
                      fill=(255, 255, 255, 255))


def draw_brows(d, kind: str) -> None:
    # «домиком» и «сердито» — прямые штрихи с наклоном: у sad внутренние
    # концы выше внешних, у angry — ниже
    if kind in ("sad", "angry"):
        lift = 24 if kind == "sad" else -24
        for i, (x0, x1) in enumerate(((486, 566), (678, 758))):
            inner_y, outer_y = 498 - lift, 498 + lift
            p0 = (x0, outer_y if i == 0 else inner_y)
            p1 = (x1, inner_y if i == 0 else outer_y)
            d.line(sbox([p0[0], p0[1], p1[0], p1[1]]),
                   fill=BROW + (255,), width=int(s(14)))
            for x, y in (p0, p1):
                d.ellipse(sbox([x - 7, y - 7, x + 7, y + 7]), fill=BROW + (255,))
        return

    dy = -26 if kind == "raised" else 0
    for i, (x0, x1) in enumerate(((480, 584), (660, 764))):
        box = [x0, 480 + dy, x1, 560 + dy]
        span = (205, 264) if i == 0 else (276, 335)
        stroke_arc(d, box, *span, BROW, 14)


def draw_mouth(d, kind: str) -> None:
    if kind == "open":                               # радостный открытый рот
        d.ellipse(sbox([586, 620, 670, 690]), fill=BROW + (255,))
        d.chord(sbox([600, 646, 656, 692]), 0, 180, fill=(232, 122, 132, 255))
        return
    if kind == "small":
        d.ellipse(sbox([608, 634, 640, 668]), fill=BROW + (255,))
        return
    if kind == "sad":
        stroke_arc(d, [592, 640, 664, 692], 205, 335, BROW, 12)
        return
    if kind == "think":                              # сжатые губы, сдвинуты вбок
        stroke_arc(d, [590, 632, 664, 674], 24, 156, BROW, 12)
        return
    box = [584, 612, 672, 678] if kind == "wide" else [592, 616, 664, 672]
    stroke_arc(d, box, 25, 155, BROW, 12)


def draw_face(img: Image.Image, mask: Image.Image, pose: str = "idle",
              eyes: str = "open", brows: str = "normal",
              mouth: str | None = None, blush: int = 175) -> None:
    # румянец — размытый, поэтому отдельным слоем; обрезаем по силуэту тела,
    # чтобы он не вылезал на фон
    def paint_blush(d):
        d.ellipse(sbox([448, 632, 528, 688]), fill=255)
        d.ellipse(sbox([718, 628, 798, 684]), fill=255)

    img.alpha_composite(
        soft_layer(img.size, BLUSH, blush, paint_blush, blur=s(11), mask=mask)
    )

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    draw_eyes(d, eyes)
    if brows != "none":
        draw_brows(d, brows)
    draw_mouth(d, mouth or ("wide" if pose == "wave" else "smile"))

    img.alpha_composite(layer)


def draw_heart(d, cx, cy, size, color) -> None:
    r = size / 2
    d.ellipse(sbox([cx - r, cy - r * 0.9, cx, cy + r * 0.2]), fill=color + (255,))
    d.ellipse(sbox([cx, cy - r * 0.9, cx + r, cy + r * 0.2]), fill=color + (255,))
    d.polygon([*sbox([cx - r * 0.96, cy - r * 0.1]),
               *sbox([cx + r * 0.96, cy - r * 0.1]),
               *sbox([cx, cy + r])], fill=color + (255,))


def draw_sparkle(d, cx, cy, size, color) -> None:
    """Четырёхлучевая искорка."""
    a, b = size, size * 0.22
    d.polygon([*sbox([cx, cy - a]), *sbox([cx + b, cy - b]),
               *sbox([cx + a, cy]), *sbox([cx + b, cy + b]),
               *sbox([cx, cy + a]), *sbox([cx - b, cy + b]),
               *sbox([cx - a, cy]), *sbox([cx - b, cy - b])], fill=color + (255,))


def draw_props(img: Image.Image, props) -> None:
    """Реквизит эмоций: искры, сердечки, zzz, слеза, вопрос."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    for prop in props:
        if prop == "sparkles":
            for cx, cy, size in ((352, 300, 40), (905, 250, 30), (975, 372, 22)):
                draw_sparkle(d, cx, cy, size, MOTION)
        elif prop == "hearts":
            for cx, cy, size in ((372, 424, 74), (880, 372, 58), (930, 520, 42)):
                draw_heart(d, cx, cy, size, HEART)
        elif prop == "zzz":
            x, y, size = 880, 380, 46
            for i in range(3):
                k = size * (1 - i * 0.22)
                zx, zy = x + i * 62, y - i * 78
                d.line(sbox([zx, zy, zx + k, zy, zx, zy + k, zx + k, zy + k]),
                       fill=MOTION + (255,), width=int(s(11)), joint="curve")
                size = k
        elif prop == "tear":
            for tx, ty, k in ((764, 682, 1.0), (486, 726, 0.72)):
                rx, ry = 22 * k, 31 * k
                d.ellipse(sbox([tx - rx, ty - ry, tx + rx, ty + ry]),
                          fill=TEAR + (235,))
                d.polygon([*sbox([tx - rx, ty]), *sbox([tx + rx, ty]),
                           *sbox([tx, ty - 52 * k])], fill=TEAR + (235,))
        elif prop == "question":
            stroke_arc(d, [846, 236, 946, 336], 175, 20, MOTION, 15)
            d.line(sbox([939, 303, 900, 352]), fill=MOTION + (255,),
                   width=int(s(15)))
            d.ellipse(sbox([888, 374, 914, 400]), fill=MOTION + (255,))

    img.alpha_composite(layer)


def draw_motion_lines(img: Image.Image) -> None:
    """Три коротких штриха у поднятой руки — чтобы читалось «машет»."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    hx, hy = 958, 576                      # примерно центр «ладони»
    for r in (58, 86):
        d.arc(sbox([hx - r, hy - r, hx + r, hy + r]), 292, 356,
              fill=MOTION + (255,), width=int(s(13)))
    img.alpha_composite(layer)


# --- эмоции ------------------------------------------------------------------
# Каждая эмоция — это набор: поза рук, форма глаз/бровей/рта и реквизит.
# title/desc используются на листе эмоций (make_emotions.py).

EMOTIONS = {
    "greeting": dict(
        pose="wave", eyes="open", brows="normal", mouth="wide",
        title="Приветствие",
        desc="Машет рукой и встречает\nтебя в начале дня."),
    "joy": dict(
        pose="cheer", eyes="closed", brows="none", mouth="open",
        props=("sparkles",),
        title="Радость",
        desc="Празднует твой прогресс\nи маленькие победы."),
    "care": dict(
        pose="idle", eyes="closed", brows="none", mouth="smile",
        props=("hearts",), blush=210,
        title="Забота",
        desc="Напоминает о любви к себе\nи бережности к чувствам."),
    "calm": dict(
        pose="idle", eyes="sleepy", brows="normal", mouth="smile",
        title="Спокойствие",
        desc="Помогает выдохнуть\nи вернуть равновесие."),
    "determined": dict(
        pose="cheer", eyes="open", brows="angry", mouth="wide",
        title="Решимость",
        desc="Поддерживает, когда нужно\nвыйти из зоны комфорта."),
    "curious": dict(
        pose="idle", eyes="wide", brows="raised", mouth="small",
        props=("question",),
        title="Любопытство",
        desc="Задаёт вопросы и помогает\nлучше узнать себя."),
    "excited": dict(
        pose="cheer", eyes="sparkle", brows="raised", mouth="open",
        props=("sparkles",),
        title="Восторг",
        desc="Заряжает энергией\nперед новым шагом."),
    "sleepy": dict(
        pose="idle", eyes="sleepy", brows="normal", mouth="small",
        props=("zzz",),
        title="Сон",
        desc="Провожает вечернюю практику\nи напоминает об отдыхе."),
    "sad": dict(
        pose="idle", eyes="open", brows="sad", mouth="sad",
        props=("tear",),
        title="Грусть",
        desc="Разделяет тяжёлый день —\nгрустить тоже нормально."),
    "wink": dict(
        pose="idle", eyes="wink", brows="normal", mouth="wide",
        title="Подмигивание",
        desc="Лёгкая похвала и мягкая\nподдержка без пафоса."),
}


def square_bbox(img: Image.Image, pad: float = 0.06) -> tuple[int, int, int, int]:
    """Квадрат вокруг непрозрачной части картинки с полем в долях стороны."""
    box = img.getbbox()
    if box is None:
        return (0, 0, img.width, img.height)
    x0, y0, x1, y1 = box
    side = max(x1 - x0, y1 - y0) * (1 + 2 * pad)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return (round(cx - side / 2), round(cy - side / 2),
            round(cx + side / 2), round(cy + side / 2))


def render(size: int = CANVAS, transparent: bool = False,
           shadow: bool = True, crop: bool = False,
           limb_tone: int = 110, limb_contact: int = 130,
           pose: str = "idle", emotion: str | None = None,
           face_override: dict | None = None, props: tuple = (),
           motion: bool | None = None, back=(), front=()) -> Image.Image:
    """back/front — функции рисования сцены: back вызывается до персонажа
    (фон, планета, звёзды), front — после (аксессуары, предметы в руках).
    Каждая получает холст в рабочем разрешении."""
    face = dict(eyes="open", brows="normal", mouth=None, blush=175)
    if emotion:
        cfg = EMOTIONS[emotion]
        pose = cfg.get("pose", pose)
        props = props or cfg.get("props", ())
        face.update({k: cfg[k] for k in ("eyes", "brows", "mouth", "blush")
                     if k in cfg})
    if face_override:
        face.update(face_override)

    work = (CANVAS * SS, CANVAS * SS)
    img = Image.new("RGBA", work, BG + (0,))    # рисуем на прозрачном холсте,
                                                # фон подкладываем в конце
    # тело, руки и ноги — один силуэт: заливаются общим градиентом, поэтому
    # руки не выглядят отдельной деталью под корпусом
    body, limbs = star_mask(work), limb_mask(work, pose)
    mask = ImageChops.lighter(body, limbs)
    if shadow:
        draw_shadow(img)
    for fn in back:
        fn(img)
    draw_body(img, mask)
    draw_limb_depth(img, body, limbs, limb_tone, limb_contact)
    draw_face(img, mask, pose, **face)
    if motion if motion is not None else pose == "wave":
        draw_motion_lines(img)
    if props:
        draw_props(img, props)
    for fn in front:
        fn(img)

    if crop:
        img = img.crop(square_bbox(img))

    img = img.resize((size, size), Image.LANCZOS)
    if transparent:
        return img

    sheet = Image.new("RGBA", img.size, BG + (255,))
    sheet.alpha_composite(img)
    return sheet.convert("RGB")


def main() -> None:
    ap = argparse.ArgumentParser(description="Нарисовать звёздочку-персонажа")
    ap.add_argument("--out", default="star.png", help="куда сохранить PNG")
    ap.add_argument("--size", default=str(CANVAS),
                    help="размер стороны в px; можно список через запятую "
                         "(например 1024,512,256) — тогда к имени файла "
                         "добавляется суффикс размера")
    ap.add_argument("--bg", choices=("white", "none"), default="white",
                    help="фон: белый или прозрачный (для иконок в приложении)")
    ap.add_argument("--crop", action="store_true",
                    help="обрезать по фигуре с небольшим полем")
    ap.add_argument("--no-shadow", dest="shadow", action="store_false",
                    help="без тени на полу")
    ap.add_argument("--limb-depth", choices=tuple(LIMB_DEPTH), default="medium",
                    help="насколько сильно руки-ноги отделяются от корпуса")
    ap.add_argument("--pose", choices=tuple(POSES), default="idle",
                    help="поза рук и ног")
    ap.add_argument("--emotion", choices=tuple(EMOTIONS), default=None,
                    help="готовая эмоция (задаёт позу, лицо и реквизит)")
    args = ap.parse_args()

    sizes = [int(v) for v in args.size.split(",") if v.strip()]
    stem, _, ext = args.out.rpartition(".")
    if not stem:                      # имя без расширения
        stem, ext = args.out, "png"

    for size in sizes:
        path = args.out if len(sizes) == 1 else f"{stem}_{size}.{ext}"
        tone, contact = LIMB_DEPTH[args.limb_depth]
        render(size, transparent=args.bg == "none", shadow=args.shadow,
               crop=args.crop, limb_tone=tone, limb_contact=contact,
               pose=args.pose, emotion=args.emotion).save(path)
        print(f"Готово: {path} ({size}x{size})")


if __name__ == "__main__":
    main()
