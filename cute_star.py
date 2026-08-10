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

from PIL import Image, ImageDraw, ImageFilter

# --- размеры и палитра -------------------------------------------------------

CANVAS = 1240          # логический размер холста
SS = 3                 # коэффициент суперсэмплинга

BG = (255, 255, 255)
BODY_TOP = (255, 214, 58)      # жёлтый у верхнего луча
BODY_BOTTOM = (248, 186, 8)    # жёлтый у нижних лучей
LIMB = (245, 182, 10)          # руки-ноги чуть темнее корпуса
SHADOW = (203, 201, 223)
EYE = (32, 27, 28)
BROW = (150, 86, 18)
BLUSH = (246, 160, 74)
GLOSS = (255, 255, 255)

# центр звезды
CX, CY = 620.0, 566.0


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
    """Вершины пятиконечной звезды. Внутренние вершины лежат близко к центру,
    поэтому все пять лучей — включая два нижних — читаются как лучи."""
    outer = [
        polar(90, 330),    # верхний луч
        polar(18, 346),    # правый боковой луч
        polar(-47, 360),   # правый нижний луч
        polar(227, 360),   # левый нижний луч
        polar(162, 346),   # левый боковой луч
    ]
    inner = [
        polar(54, 152),
        polar(-19, 146),
        polar(-90, 150),   # выемка между нижними лучами
        polar(199, 146),
        polar(126, 152),
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


def rotated_capsule(base: Image.Image, cx, cy, w, h, fill, angle):
    """Та же таблетка, но повёрнутая. Крутим маску, а не цвет: у повёрнутого
    RGBA прозрачные пиксели чёрные и интерполяция пачкает края."""
    pad = int(s(max(w, h)))
    m = Image.new("L", (pad * 2, pad * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle(
        [pad - s(w) / 2, pad - s(h) / 2, pad + s(w) / 2, pad + s(h) / 2],
        radius=s(min(w, h) / 2),
        fill=255,
    )
    m = m.rotate(angle, resample=Image.BICUBIC)
    layer = Image.new("RGBA", m.size, tuple(fill[:3]) + (0,))
    layer.putalpha(m)
    base.alpha_composite(layer, (int(s(cx)) - pad, int(s(cy)) - pad))


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
        lambda d: d.ellipse(sbox([440, 856, 814, 910]), fill=255),
        blur=s(10),
    ))


def draw_limbs(img: Image.Image) -> None:
    """Ручки-культяпки по бокам и две ножки снизу (рисуются под корпусом)."""
    rotated_capsule(img, 428, 616, 66, 132, LIMB + (255,), -10)
    rotated_capsule(img, 812, 616, 66, 132, LIMB + (255,), 10)

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    capsule(d, 556, 790, 92, 150, LIMB + (255,))
    capsule(d, 684, 790, 92, 150, LIMB + (255,))
    img.alpha_composite(layer)


def star_mask(size) -> Image.Image:
    pts = star_vertices()
    radii = []
    for i in range(10):
        radii.append(48 if i % 2 == 0 else 40)   # кончики лучей / внутренние
    radii[4] = radii[6] = 36                     # нижние лучи — поострее
    radii[5] = 46                                # выемка между нижними лучами
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


def draw_face(img: Image.Image, mask: Image.Image) -> None:
    # румянец — размытый, поэтому отдельным слоем; обрезаем по силуэту тела,
    # чтобы он не вылезал на фон
    def paint_blush(d):
        d.ellipse(sbox([452, 628, 532, 684]), fill=255)
        d.ellipse(sbox([714, 624, 794, 680]), fill=255)

    img.alpha_composite(
        soft_layer(img.size, BLUSH, 175, paint_blush, blur=s(11), mask=mask)
    )

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # глаза
    for ex in (533, 722):
        d.rounded_rectangle(sbox([ex - 29, 556, ex + 29, 640]),
                            radius=s(29), fill=EYE + (255,))
    # блики в глазах смотрят к переносице
    d.ellipse(sbox([539, 566, 561, 590]), fill=(255, 255, 255, 255))
    d.ellipse(sbox([700, 564, 722, 588]), fill=(255, 255, 255, 255))

    # брови
    bw = int(s(14))
    d.arc(sbox([480, 480, 584, 560]), 205, 264, fill=BROW + (255,), width=bw)
    d.arc(sbox([660, 480, 764, 560]), 276, 335, fill=BROW + (255,), width=bw)
    # PIL рисует дугу толщиной внутрь bbox, поэтому закругления на концах
    # ставим по радиусу средней линии (rx - bw/2, ry - bw/2)
    for x, y in ((491.2, 506.1), (527.3, 487.2), (716.7, 487.2), (752.8, 506.1)):
        d.ellipse(sbox([x - 7, y - 7, x + 7, y + 7]), fill=BROW + (255,))

    # улыбка
    d.arc(sbox([592, 616, 664, 672]), 25, 155, fill=BROW + (255,), width=int(s(12)))
    for x, y in ((600.8, 653.3), (655.2, 653.3)):
        d.ellipse(sbox([x - 6, y - 6, x + 6, y + 6]), fill=BROW + (255,))

    img.alpha_composite(layer)


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
           shadow: bool = True, crop: bool = False) -> Image.Image:
    work = (CANVAS * SS, CANVAS * SS)
    img = Image.new("RGBA", work, BG + (0,))    # рисуем на прозрачном холсте,
                                                # фон подкладываем в конце
    mask = star_mask(work)
    if shadow:
        draw_shadow(img)
    draw_limbs(img)
    draw_body(img, mask)
    draw_face(img, mask)

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
    args = ap.parse_args()

    sizes = [int(v) for v in args.size.split(",") if v.strip()]
    stem, _, ext = args.out.rpartition(".")
    if not stem:                      # имя без расширения
        stem, ext = args.out, "png"

    for size in sizes:
        path = args.out if len(sizes) == 1 else f"{stem}_{size}.{ext}"
        render(size, transparent=args.bg == "none",
               shadow=args.shadow, crop=args.crop).save(path)
        print(f"Готово: {path} ({size}x{size})")


if __name__ == "__main__":
    main()
