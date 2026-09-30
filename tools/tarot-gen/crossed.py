"""Crossed compositions for the Wands and Swords pip cards (handoff-pips-crossed-layout.md).

Swords : traced from the rough refs/sword_rough.png (handoff-swords-trace.md). Every sword is drawn
         from its pommel to its tip as listed in swords_traced.json; the sword asset is aligned by its
         measured blade axis, pommel and tip, never by the image center.
Wands  : diagonal lattice. floor(n/2) staffs at +20 deg and as many at -20 deg, spaced 0.30R;
         odd n adds one vertical staff. Rosettes sit on the crossings.

Coordinates are in pixels of the 1024x1536 canvas unless noted; lengths in R are relative to the
halo circle measured on the suit background (layout_config.json -> "circle").
All placement is deterministic (no randomness).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

ALPHA_THRESHOLD = 16

# --- swords (handoff-swords-trace.md) ---
TRACED_SWORDS = "swords_traced.json"   # next to this file
SWORD_AREA = 0.96           # swords may use the circle up to 0.96R (the rough goes close to the rim); no shrinking
WIDTH_REF_RANK = 4          # blades are widened to the blade width of the swords on the 4
MAX_BLADE_WIDEN = 1.00      # blade width/length ratio may grow by at most +100% (hilts are never deformed)
MAX_BLADE_TO_GUARD = 0.70   # warn when a widened blade is wider than 70% of its own guard
GUARD_WIDTH_RATIO = 2.5     # the guard starts at the first row wider than 2.5x the blade

# --- wands ---
WAND_ANGLE_DEG = 20.0
WAND_SPACING = 0.30
WAND_ROSETTE = 0.10

# --- common ---
AREA = 0.90                 # everything must stay inside the 0.90R circle
END_MARGIN = 0.05           # staffs end 0.05R inside the area circle


@dataclass
class Circle:
    cx: float
    cy: float
    r: float

    @classmethod
    def from_config(cls, cfg: dict) -> "Circle":
        c = cfg["circle"]
        return cls(float(c["cx"]), float(c["cy"]), float(c["r"]))


@dataclass
class Item:
    """One drawn element: RGBA image and top-left offset on the canvas."""
    image: Image.Image
    offset: tuple[int, int]
    kind: str               # "symbol" or "rosette"


def alpha_crop(im: Image.Image) -> Image.Image:
    rgba = im.convert("RGBA")
    arr = np.asarray(rgba).copy()
    arr[..., 3][arr[..., 3] < ALPHA_THRESHOLD] = 0
    out = Image.fromarray(arr, "RGBA")
    return out.crop(out.getchannel("A").getbbox())


def centered_item(im: Image.Image, x: float, y: float, kind: str) -> Item:
    return Item(im, (round(x - im.width / 2), round(y - im.height / 2)), kind)


def rosette_item(rosette: Image.Image, size_px: float, x: float, y: float) -> Item:
    rosette = alpha_crop(rosette)
    s = size_px / max(rosette.width, rosette.height)
    im = rosette.resize((max(1, round(rosette.width * s)), max(1, round(rosette.height * s))), Image.LANCZOS)
    return centered_item(im, x, y, "rosette")


# ---------------------------------------------------------------- swords

@dataclass
class SwordAxis:
    """Center line of the sword asset: x of the blade axis, tip row and pommel row (asset pixels)."""
    x: float
    tip: float
    pommel: float

    guard: float = 0.0      # top row of the guard (blade above, hilt from here down)
    blade_w: float = 0.0    # typical blade width (asset pixels)
    guard_w: float = 0.0    # widest row of the guard

    @classmethod
    def measure(cls, sword: Image.Image) -> "SwordAxis":
        a = np.asarray(sword.getchannel("A")) >= ALPHA_THRESHOLD
        ys = np.where(a.any(axis=1))[0]
        tip, pommel = int(ys.min()), int(ys.max())
        # Blade axis: median row center over the upper half (the blade), unaffected by the guard.
        centers = [np.where(a[y])[0].mean() for y in range(tip, tip + (pommel - tip) // 2) if a[y].any()]
        widths = np.array([np.ptp(np.where(r)[0]) + 1 if r.any() else 0 for r in a[tip:pommel + 1]])
        blade_w = np.median(widths[len(widths) // 5: len(widths) // 2])
        wide = widths > GUARD_WIDTH_RATIO * blade_w
        guard = tip + int(np.argmax(wide)) if wide.any() else pommel   # no guard: all blade
        return cls(float(np.median(centers)), float(tip), float(pommel), float(guard), float(blade_w),
                   float(widths.max()))


def widened_sword(sword: Image.Image, axis: SwordAxis, widen: float) -> tuple[Image.Image, SwordAxis]:
    """The asset with only the blade (tip .. guard top) widened by `widen` around the blade axis;
    the hilt (guard, grip, pommel) is kept pixel for pixel."""
    top, guard, bottom = int(axis.tip), int(axis.guard), int(axis.pommel) + 1
    blade = sword.crop((0, top, sword.width, guard))
    hilt = sword.crop((0, guard, sword.width, bottom))
    bw = max(1, round(sword.width * widen))
    bx = axis.x * widen                                        # blade axis in the widened blade
    left = max(bx, axis.x)
    width = math.ceil(left + max(bw - bx, sword.width - axis.x))
    out = Image.new("RGBA", (width, blade.height + hilt.height), (0, 0, 0, 0))
    out.alpha_composite(blade.resize((bw, blade.height), Image.LANCZOS), (round(left - bx), 0))
    out.alpha_composite(hilt, (round(left - axis.x), blade.height))
    return out, SwordAxis(left, 0.0, float(out.height - 1), float(blade.height), axis.blade_w * widen, axis.guard_w)


def place_sword(sword: Image.Image, axis: SwordAxis, length: float, angle: float,
                from_pommel: float, x: float, y: float, width_scale: float | None = None) -> Item:
    """Sword of `length` tilted by `angle` (degrees, clockwise from vertical: positive = tip leans right),
    rotated about the point `from_pommel` of its length above the pommel, which lands on (x, y).
    `width_scale` scales the asset horizontally (default: the same factor as the length)."""
    s = length / (axis.pommel - axis.tip)
    sx = s if width_scale is None else width_scale
    im = sword.resize((max(1, round(sword.width * sx)), max(1, round(sword.height * s))), Image.LANCZOS)
    rx = axis.x * sx
    ry = (axis.pommel - from_pommel * (axis.pommel - axis.tip)) * s
    # Pad so that the reference point is the exact center, then rotate about the center.
    half = math.ceil(math.hypot(max(rx, im.width - rx), max(ry, im.height - ry))) + 2
    canvas = Image.new("RGBA", (2 * half, 2 * half), (0, 0, 0, 0))
    canvas.paste(im, (round(half - rx), round(half - ry)))
    if angle:
        canvas = canvas.rotate(-angle, resample=Image.BICUBIC, center=(half, half))
    bbox = canvas.getchannel("A").getbbox()
    cropped = canvas.crop(bbox)
    return Item(cropped, (round(x - half + bbox[0]), round(y - half + bbox[1])), "symbol")


def sword_length(spec: dict) -> float:
    (hx, hy), (tx, ty) = spec["hilt"], spec["tip"]
    return math.hypot(tx - hx, ty - hy)


def traced_sword(sword: Image.Image, axis: SwordAxis, circle: Circle, spec: dict, blade_px: float
                 ) -> tuple[Item, float, float]:
    """Sword from its pommel (hilt) to its tip, both in R units around the circle center (y down).
    The sword is scaled uniformly to its length; then its blade alone is widened so that it is
    `blade_px` wide on the card (at most +MAX_BLADE_WIDEN). Returns the item, the requested widening
    and the blade/guard width ratio after widening."""
    R = circle.r
    (hx, hy), (tx, ty) = spec["hilt"], spec["tip"]
    length = sword_length(spec) * R
    s = length / (axis.pommel - axis.tip)
    widen = blade_px / (axis.blade_w * s)
    applied = min(max(widen, 1.0), 1.0 + MAX_BLADE_WIDEN)
    img, ax = widened_sword(sword, axis, applied)
    angle = math.degrees(math.atan2(tx - hx, -(ty - hy)))     # clockwise from vertical
    item = place_sword(img, ax, length, angle, 0.0, circle.cx + hx * R, circle.cy + hy * R)
    return item, widen, ax.blade_w / ax.guard_w


def swords_items(rank: int, circle: Circle, straight_sword: Image.Image, traced: dict,
                 size: tuple[int, int] = (1024, 1536), area_allow: dict | None = None
                 ) -> tuple[list[Item], list[str], float]:
    """Swords traced from the rough (swords_traced.json), drawn in the file's order.

    Overlaps between swords are intended. Nothing is shrunk: swords beyond SWORD_AREA produce a warning
    unless listed in `area_allow` ({"rank": [sword numbers]}, from layout_config.json)."""
    sword = alpha_crop(straight_sword)
    axis = SwordAxis.measure(sword)
    ref = traced.get(str(WIDTH_REF_RANK)) or traced.get(WIDTH_REF_RANK)
    blade_px = axis.blade_w * np.mean([sword_length(s) for s in ref]) * circle.r / (axis.pommel - axis.tip)
    warnings: list[str] = []
    items = []
    for i, spec in enumerate(traced.get(str(rank)) or traced.get(rank), 1):
        item, widen, to_guard = traced_sword(sword, axis, circle, spec, blade_px)
        items.append(item)
        if widen - 1 > MAX_BLADE_WIDEN:
            warnings.append(f"ソードの{rank}: 剣{i}の刃の太さ {widen - 1:+.0%} が上限 +{MAX_BLADE_WIDEN:.0%} を超えるため、上限で止めました")
        if to_guard > MAX_BLADE_TO_GUARD:
            warnings.append(f"ソードの{rank}: 剣{i}の刃の幅が鍔の {to_guard:.0%} で、{MAX_BLADE_TO_GUARD:.0%} を超えます")
    allowed = set((area_allow or {}).get(str(rank), []))
    warnings += outside_area(items, circle, size, SWORD_AREA, skip=allowed)
    return items, warnings, 1.0


def _mask(items: list[Item], size: tuple[int, int]) -> np.ndarray:
    m = np.zeros((size[1], size[0]), dtype=np.uint8)
    for it in items:
        a = (np.asarray(it.image.getchannel("A")) >= ALPHA_THRESHOLD).astype(np.uint8)
        x, y = it.offset
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + a.shape[1], size[0]), min(y + a.shape[0], size[1])
        if x1 > x0 and y1 > y0:
            m[y0:y1, x0:x1] |= a[y0 - y:y1 - y, x0 - x:x1 - x]
    return m


def min_gap(group_a: list[Item], group_b: list[Item], size: tuple[int, int] = (1024, 1536)) -> float:
    """Smallest pixel distance between the visible pixels of two groups of items (0 when touching)."""
    a, b = _mask(group_a, size), _mask(group_b, size)
    if not a.any() or not b.any():
        return float("inf")
    dist = cv2.distanceTransform((1 - b).astype(np.uint8), cv2.DIST_L2, 5)
    return float(dist[a > 0].min())


# ---------------------------------------------------------------- wands

def chord(px: float, py: float, ux: float, uy: float, radius: float) -> tuple[float, float] | None:
    """Parameters t1 < t2 where the line p + t*u (|u| = 1) crosses a circle at the origin."""
    b = px * ux + py * uy
    c = px * px + py * py - radius * radius
    disc = b * b - c
    if disc <= 0:
        return None
    root = math.sqrt(disc)
    return -b - root, -b + root


def wands_lines(rank: int, R: float) -> list[tuple[float, float, float]]:
    """(x at y=0, angle in degrees from vertical, positive = top leans right) for each staff."""
    k = rank // 2
    xs = [(j - (k - 1) / 2) * WAND_SPACING * R for j in range(k)]
    lines = [(x, WAND_ANGLE_DEG) for x in xs] + [(x, -WAND_ANGLE_DEG) for x in xs]
    if rank % 2:
        lines.append((0.0, 0.0))
    return lines


def wand_segment(x: float, angle: float, R: float) -> tuple[tuple[float, float], float, float]:
    """Center (local), length and angle of the longest staff on this line inside the area circle."""
    a = math.radians(angle)
    ux, uy = math.sin(a), -math.cos(a)                            # direction toward the top
    t = chord(x, 0.0, ux, uy, (AREA - END_MARGIN) * R)
    if t is None:
        raise ValueError("staff line misses the area circle")
    t1, t2 = t
    mid = (t1 + t2) / 2
    return (x + ux * mid, uy * mid), t2 - t1, angle


def crossing(l1: tuple[float, float], l2: tuple[float, float]) -> tuple[float, float] | None:
    (x1, a1), (x2, a2) = l1, l2
    t1, t2 = math.tan(math.radians(a1)), math.tan(math.radians(a2))
    if abs(t1 - t2) < 1e-9:
        return None
    # x = x0 - y * tan(a) with y pointing down (top leans right for positive a).
    y = (x1 - x2) / (t1 - t2)
    return x1 - y * t1, y


def wands_items(rank: int, circle: Circle, staff: Image.Image, rosette: Image.Image | None,
                rosette_mode: str = "all") -> tuple[list[Item], list[str]]:
    R = circle.r
    staff = alpha_crop(staff)
    items: list[Item] = []
    lines = wands_lines(rank, R)
    for x, angle in lines:
        (lx, ly), length, ang = wand_segment(x, angle, R)
        s = length / staff.height
        im = staff.resize((max(1, round(staff.width * s)), round(length)), Image.LANCZOS)
        # PIL rotates counter-clockwise; a positive angle (top leaning right) is a clockwise turn.
        im = im.rotate(-ang, resample=Image.BICUBIC, expand=True)
        items.append(centered_item(im, circle.cx + lx, circle.cy + ly, "symbol"))
    if rosette is not None:
        diag = [l for l in lines if l[1] != 0.0]
        right = [l for l in diag if l[1] > 0]
        left = [l for l in diag if l[1] < 0]
        for l1 in right:
            for l2 in left:
                p = crossing(l1, l2)
                if p is None or math.hypot(*p) > (AREA - WAND_ROSETTE / 2) * R:
                    continue
                if rosette_mode == "center" and abs(p[0]) > 1e-6:
                    continue
                items.append(rosette_item(rosette, WAND_ROSETTE * R, circle.cx + p[0], circle.cy + p[1]))
    return items, []


# ---------------------------------------------------------------- checks

def outside_area(items: list[Item], circle: Circle, size: tuple[int, int], area: float = AREA,
                 skip: set[int] | None = None) -> list[str]:
    """Items with visible pixels outside the `area` x R circle (0.90R unless given)."""
    h, w = size[1], size[0]
    ys, xs = np.mgrid[0:h, 0:w]
    inside = (xs - circle.cx) ** 2 + (ys - circle.cy) ** 2 <= (area * circle.r) ** 2
    msgs = []
    for i, it in enumerate(items, 1):
        if skip and i in skip:
            continue
        a = np.asarray(it.image.getchannel("A")) >= ALPHA_THRESHOLD
        x, y = it.offset
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + a.shape[1], w), min(y + a.shape[0], h)
        sub = a[y0 - y:y1 - y, x0 - x:x1 - x]
        clipped = a.sum() - sub.sum()
        out = int((sub & ~inside[y0:y1, x0:x1]).sum() + clipped)
        if out:
            label = "記号" if it.kind == "symbol" else "花飾り"
            msgs.append(f"{label}{i}の {out}px が配置可能領域（{area}R）の外にあります")
    return msgs
