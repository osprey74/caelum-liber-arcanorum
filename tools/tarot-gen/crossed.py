"""Crossed compositions for the Wands and Swords pip cards (handoff-pips-crossed-layout.md).

Swords and wands share the skeleton traced from the rough refs/sword_rough.png (swords_traced.json,
handoff-swords-trace.md): every symbol runs from its bottom end (pommel / staff foot) to its top end.
The skeleton is enlarged about the halo center so the group matches the cups group of the same rank
(handoff-wands-swords-unify.md). Assets are aligned by their measured axis, never by the image center;
only the blade (swords) or shaft (wands) is widened, hilts and leaf ends are not deformed.

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

# --- traced layout (handoff-swords-trace.md, handoff-wands-swords-unify.md) ---
# Swords and wands share the skeleton traced from the rough: every symbol runs from its bottom end
# (sword pommel / staff foot) to its top end (sword tip / staff top), in R units around the halo center.
TRACED_SWORDS = "swords_traced.json"   # next to this file
WIDTH_REF_RANK = 4          # the widened part is made as wide as on the (enlarged) 4
MAX_WIDEN = 1.00            # the widened part may grow by at most +100% (ends/hilts are never deformed)
MAX_BLADE_TO_GUARD = 0.70   # swords: warn when a widened blade is wider than 70% of its own guard
GUARD_WIDTH_RATIO = 2.5     # swords: the guard starts at the first row wider than 2.5x the blade
LEAF_WIDTH_RATIO = 2.2      # wands: rows wider than 2.2x the shaft near the ends belong to the leaf ends
CUP_WIDTH_CAP = 1.15        # enlarged group width may be at most 1.15x the cups group width
WINDOW_MARGIN = 0.02        # everything stays 0.02R inside the visible arch window
SCALE_STEP = 0.98           # enlargement is lowered in 2% steps while a constraint is violated

# --- common ---


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


# ---------------------------------------------------------------- traced symbols

@dataclass
class LongAxis:
    """Center line of a long symbol asset (sword or staff), in asset pixels.

    tip / pommel: top and bottom rows. The rows seg_top .. seg_bottom (exclusive) form the part that may
    be widened (sword: the blade, tip .. guard top; staff: the shaft between the leaf ends).
    seg_w: typical width of that part; guard_w: widest row of the sword guard (0 for staffs)."""
    x: float
    tip: float
    pommel: float
    seg_top: float
    seg_bottom: float
    seg_w: float
    guard_w: float = 0.0

    @staticmethod
    def _rows(img: Image.Image) -> tuple[np.ndarray, int, int, np.ndarray]:
        a = np.asarray(img.getchannel("A")) >= ALPHA_THRESHOLD
        ys = np.where(a.any(axis=1))[0]
        tip, pommel = int(ys.min()), int(ys.max())
        widths = np.array([np.ptp(np.where(r)[0]) + 1 if r.any() else 0 for r in a[tip:pommel + 1]])
        return a, tip, pommel, widths

    @classmethod
    def sword(cls, sword: Image.Image) -> "LongAxis":
        a, tip, pommel, widths = cls._rows(sword)
        # Blade axis: median row center over the upper half (the blade), unaffected by the guard.
        centers = [np.where(a[y])[0].mean() for y in range(tip, tip + (pommel - tip) // 2) if a[y].any()]
        blade_w = float(np.median(widths[len(widths) // 5: len(widths) // 2]))
        wide = widths > GUARD_WIDTH_RATIO * blade_w
        guard = tip + int(np.argmax(wide)) if wide.any() else pommel   # no guard: all blade
        return cls(float(np.median(centers)), float(tip), float(pommel), float(tip), float(guard), blade_w,
                   float(widths.max()))

    @classmethod
    def staff(cls, staff: Image.Image) -> "LongAxis":
        a, tip, pommel, widths = cls._rows(staff)
        n = len(widths)
        shaft_w = float(np.median(widths[int(n * 0.3): int(n * 0.7)]))
        wide = widths > LEAF_WIDTH_RATIO * shaft_w
        head = np.where(wide[: int(n * 0.3)])[0]
        foot = np.where(wide[int(n * 0.7):])[0]
        top = tip + (int(head.max()) + 1 if head.size else 0)
        bottom = tip + (int(n * 0.7) + int(foot.min()) if foot.size else n)
        centers = [np.where(a[y])[0].mean() for y in range(top, bottom) if a[y].any()]
        return cls(float(np.median(centers)), float(tip), float(pommel), float(top), float(bottom), shaft_w)


def widened(img: Image.Image, axis: LongAxis, widen: float) -> tuple[Image.Image, LongAxis]:
    """The asset with only rows seg_top .. seg_bottom widened by `widen` around the axis; the rest
    (sword hilt, staff leaf ends) is kept pixel for pixel."""
    t, s0, s1, b = int(axis.tip), int(axis.seg_top), int(axis.seg_bottom), int(axis.pommel) + 1
    parts = [img.crop((0, t, img.width, s0)), img.crop((0, s0, img.width, s1)), img.crop((0, s1, img.width, b))]
    sw = max(1, round(img.width * widen))
    sx = axis.x * widen                                        # axis inside the widened part
    left = max(sx, axis.x)
    width = math.ceil(left + max(sw - sx, img.width - axis.x))
    out = Image.new("RGBA", (width, b - t), (0, 0, 0, 0))
    y = 0
    for k, part in enumerate(parts):
        if part.height:
            if k == 1:
                out.alpha_composite(part.resize((sw, part.height), Image.LANCZOS), (round(left - sx), y))
            else:
                out.alpha_composite(part, (round(left - axis.x), y))
        y += part.height
    return out, LongAxis(left, 0.0, float(out.height - 1), float(s0 - t), float(s1 - t), axis.seg_w * widen,
                         axis.guard_w)


def place_sword(sword: Image.Image, axis: LongAxis, length: float, angle: float,
                from_pommel: float, x: float, y: float) -> Item:
    """Symbol of `length` tilted by `angle` (degrees, clockwise from vertical: positive = top leans right),
    rotated about the point `from_pommel` of its length above the bottom end, which lands on (x, y)."""
    s = length / (axis.pommel - axis.tip)
    im = sword.resize((max(1, round(sword.width * s)), max(1, round(sword.height * s))), Image.LANCZOS)
    rx = axis.x * s
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


def traced_rank(traced: dict, rank: int) -> list[dict]:
    return traced.get(str(rank)) or traced.get(rank)


def traced_symbols(rank: int, circle: Circle, symbol: Image.Image, axis: LongAxis, traced: dict,
                   scale: float, ref_scale: float, label: str, dy: float = 0.0) -> tuple[list[Item], list[str]]:
    """Symbols of `rank` on the traced skeleton enlarged by `scale` about the halo center, then moved
    down by `dy` (in R; negative = up).

    Each symbol is scaled uniformly to its length; then only its widenable part is widened so that it is
    as wide as on the WIDTH_REF_RANK card enlarged by `ref_scale` (at most +MAX_WIDEN)."""
    R = circle.r * scale
    ref = traced_rank(traced, WIDTH_REF_RANK)
    target_px = axis.seg_w * np.mean([sword_length(s) for s in ref]) * circle.r * ref_scale / (axis.pommel - axis.tip)
    items, warnings = [], []
    for i, spec in enumerate(traced_rank(traced, rank), 1):
        (hx, hy), (tx, ty) = spec["hilt"], spec["tip"]
        length = sword_length(spec) * R
        s = length / (axis.pommel - axis.tip)
        widen = target_px / (axis.seg_w * s)
        applied = min(max(widen, 1.0), 1.0 + MAX_WIDEN)
        img, ax = widened(symbol, axis, applied)
        angle = math.degrees(math.atan2(tx - hx, -(ty - hy)))     # clockwise from vertical
        items.append(place_sword(img, ax, length, angle, 0.0, circle.cx + hx * R,
                                 circle.cy + dy * circle.r + hy * R))
        if widen - 1 > MAX_WIDEN:
            warnings.append(f"{label}の{rank}: {i}本目の太さ {widen - 1:+.0%} が上限 +{MAX_WIDEN:.0%} を超えるため、上限で止めました")
        if ax.guard_w and ax.seg_w / ax.guard_w > MAX_BLADE_TO_GUARD:
            warnings.append(f"{label}の{rank}: {i}本目の刃の幅が鍔の {ax.seg_w / ax.guard_w:.0%} で、"
                            f"{MAX_BLADE_TO_GUARD:.0%} を超えます")
    return items, warnings


def group_bbox(items: list[Item], size: tuple[int, int] = (1024, 1536)) -> tuple[int, int, int, int]:
    ys, xs = np.where(_mask(items, size) > 0)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def window_violations(items: list[Item], inner: np.ndarray, size: tuple[int, int] = (1024, 1536)) -> int:
    """Visible pixels of the items outside `inner` (the arch window shrunk by the margin)."""
    m = _mask(items, size) > 0
    return int((m & ~inner).sum())


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
