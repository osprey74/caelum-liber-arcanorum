"""Lay out suit symbols on suit backgrounds for the pip cards (2-10) of the Minor Arcana.

Inputs : assets/bg_{suit}_{v}.png, assets/symbol_{suit}_{v}.png (variants chosen in selected_assets.json),
         cards_minor.json (cards with method "layout")
Outputs: out/raw/{id:02d}_{slug}_a.png (1024x1536), registered in selected.json as variant "a"

Usage examples:
  python layout.py
  python layout.py --only wands
  python layout.py --only 23,51
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

import composite
import crossed

ROOT = Path(__file__).resolve().parent
CARDS_MINOR_PATH = ROOT / "cards_minor.json"
ASSETS_DIR = ROOT / "assets"
SELECTED_ASSETS_PATH = ROOT / "selected_assets.json"
SELECTED_PATH = ROOT / "selected.json"
RAW_DIR = ROOT / "out" / "raw"

SIZE = (1024, 1536)
LAYOUT_VARIANT = "a"
ALPHA_THRESHOLD = 16      # alpha below this is treated as fully transparent
GAP_PX = 6                # minimum spacing between symbols
SHRINK_STEP = 0.95
MAX_SHRINK_STEPS = 30
TILT_DEG = 12
TILTED_SUITS = {"wands", "swords"}
SHADOW_OPACITY = 0.18     # must stay at or below 0.20
SHADOW_BLUR = 8
SHADOW_OFFSET = (0, 10)
BOTTOM_LIMIT = 0.89       # symbols must end above this (the composite crops ~8.9% at the bottom)
LAYOUT_CONFIG_PATH = ROOT / "layout_config.json"
# Per-suit tuning (handoff-pips-layout-fix.md). Values can be overridden by layout_config.json or --config.
#   scale    : multiplier on the base symbol height. Shrunk 5% at a time while symbols overlap,
#              cross BOTTOM_LIMIT or are hidden by the frame.
#   glow     : ivory glow behind the symbol (drawn above the dark halo, below the drop shadow).
#   y_offset : added to the normalized y positions (wands: clear the sun ornament at the top).
#   y_offset_mode : "uniform" adds y_offset to every row; "taper" adds the full y_offset to the top row,
#              nothing to the bottom row and a proportional amount in between, so the bottom never moves.
#   brighten : brightness +15% / saturation +10% on the symbol, in memory only.
#   layout   : "grid" (addendum 3.1 positions) or "crossed" (the traced skeleton of swords_traced.json,
#              handoff-wands-swords-unify.md; needs "circle" from layout_config.json). The crossed layout
#              ignores scale/glow/y_offset and the dark halo.
SUIT_CONFIG = {
    "wands":     {"layout": "crossed", "brighten": True},
    "swords":    {"layout": "crossed", "brighten": False},
    "cups":      {"layout": "grid", "scale": 1.00, "glow": False, "y_offset": 0.00, "brighten": False},
    "pentacles": {"layout": "grid", "scale": 1.00, "glow": False, "y_offset": 0.00, "brighten": False},
}
# Crossed layouts: a thin navy outline around every symbol and rosette.
OUTLINE_COLOR = (15, 30, 58)   # #0F1E3A
OUTLINE_PX = 2
OUTLINE_OPACITY = 0.60
# Extra assets used by the crossed layouts, per suit: role -> asset name in selected_assets.json.
CROSSED_ASSETS = {
    "wands": {"staff": "symbol_wands_long"},
    "swords": {"straight": "symbol_swords"},
}
GLOW_COLOR = (243, 233, 210)   # ivory, #F3E9D2
GLOW_GROW = 5                  # dilation of the alpha mask before blurring
GLOW_BLUR = 12
GLOW_OPACITY = 0.35            # adjustable within 0.30-0.40
BRIGHTNESS = 1.15
SATURATION = 1.10
# Dark halo (all suits): the background is softly darkened around the symbols so they read on ornate panels.
HALO_STRENGTH = 0.85
HALO_GROW = 61
HALO_BLUR = 30
HALO_COLOR = (10, 18, 30)

# Symbol centers in normalized image coordinates (x, y).
_FOUR = [(.32, .28), (.68, .28), (.32, .68), (.68, .68)]
_SIX = [(x, y) for y in (.22, .48, .74) for x in (.32, .68)]
_EIGHT = [(x, y) for y in (.18, .39, .60, .81) for x in (.32, .68)]
POSITIONS = {
    2: [(.50, .30), (.50, .68)],
    3: [(.50, .24), (.30, .64), (.70, .64)],
    4: _FOUR,
    5: _FOUR + [(.50, .48)],
    6: _SIX,
    7: _SIX + [(.50, .35)],
    8: _EIGHT,
    9: _EIGHT + [(.50, .50)],
    10: _EIGHT + [(.50, .28), (.50, .71)],
}


def symbol_height_ratio(rank: int) -> float:
    if rank <= 3:
        return 0.26
    if rank <= 6:
        return 0.20
    return 0.15


@dataclass
class Placement:
    center: tuple[float, float]
    angle: float
    image: Image.Image        # rotated RGBA symbol
    offset: tuple[int, int]   # top-left position on the canvas

    def mask(self) -> np.ndarray:
        """Boolean mask of the symbol on the full canvas."""
        full = np.zeros((SIZE[1], SIZE[0]), dtype=bool)
        a = np.asarray(self.image.getchannel("A")) >= ALPHA_THRESHOLD
        x, y = self.offset
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + a.shape[1], SIZE[0]), min(y + a.shape[0], SIZE[1])
        if x1 > x0 and y1 > y0:
            full[y0:y1, x0:x1] = a[y0 - y:y1 - y, x0 - x:x1 - x]
        return full


def clean_symbol(symbol: Image.Image) -> Image.Image:
    """Drop near-invisible alpha noise and crop to the visible extent."""
    rgba = symbol.convert("RGBA")
    arr = np.asarray(rgba).copy()
    arr[..., 3][arr[..., 3] < ALPHA_THRESHOLD] = 0
    cleaned = Image.fromarray(arr, "RGBA")
    bbox = cleaned.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("symbol image is fully transparent")
    return cleaned.crop(bbox)


def tilt_for(suit: str, x: float) -> float:
    if suit not in TILTED_SUITS or abs(x - 0.5) < 1e-6:
        return 0.0
    # PIL rotates counter-clockwise; lean the tops of both columns toward the center.
    return -TILT_DEG if x < 0.5 else TILT_DEG


def load_config(path: Path | None = None) -> dict[str, dict]:
    """SUIT_CONFIG merged with layout_config.json (or the given file); keys are merged per suit."""
    config = {suit: dict(values) for suit, values in SUIT_CONFIG.items()}
    path = path or LAYOUT_CONFIG_PATH
    if path.exists():
        for suit, values in json.loads(path.read_text(encoding="utf-8")).items():
            config.setdefault(suit, {}).update(values)
    return config


def suit_config(suit: str, config: dict[str, dict] | None) -> dict:
    defaults = {"layout": "grid", "scale": 1.0, "glow": False, "y_offset": 0.0, "y_offset_mode": "uniform",
                "brighten": False}
    return {**defaults, **(config or SUIT_CONFIG).get(suit, {})}


def brighten_symbol(symbol: Image.Image) -> Image.Image:
    alpha = symbol.getchannel("A")
    rgb = ImageEnhance.Brightness(symbol.convert("RGB")).enhance(BRIGHTNESS)
    rgb = ImageEnhance.Color(rgb).enhance(SATURATION)
    rgb.putalpha(alpha)
    return rgb


def shifted_positions(rank: int, y_offset: float, mode: str = "uniform") -> list[tuple[float, float]]:
    positions = POSITIONS[rank]
    if mode == "uniform" or not y_offset:
        return [(x, y + y_offset) for x, y in positions]
    if mode != "taper":
        raise ValueError(f"unknown y_offset_mode: {mode}")
    top = min(y for _, y in positions)
    bottom = max(y for _, y in positions)
    return [(x, y + y_offset * (bottom - y) / (bottom - top)) for x, y in positions]


def place(symbol: Image.Image, suit: str, rank: int, scale: float, y_offset: float = 0.0,
          y_offset_mode: str = "uniform") -> list[Placement]:
    target_h = max(1, round(symbol_height_ratio(rank) * SIZE[1] * scale))
    target_w = max(1, round(symbol.width * target_h / symbol.height))
    base = symbol.resize((target_w, target_h), Image.LANCZOS)
    placements = []
    for cx, cy in shifted_positions(rank, y_offset, y_offset_mode):
        angle = tilt_for(suit, cx)
        img = base.rotate(angle, resample=Image.BICUBIC, expand=True) if angle else base
        offset = (round(cx * SIZE[0] - img.width / 2), round(cy * SIZE[1] - img.height / 2))
        placements.append(Placement((cx, cy), angle, img, offset))
    return placements


def overlaps(placements: list[Placement]) -> bool:
    count = np.zeros((SIZE[1], SIZE[0]), dtype=np.uint8)
    # Grow each mask by half the gap so that neighbors closer than GAP_PX count as overlapping.
    kernel = np.ones((GAP_PX + 1, GAP_PX + 1), np.uint8)
    for p in placements:
        count += cv2.dilate(p.mask().astype(np.uint8), kernel) > 0
    return bool((count > 1).any())


def fit_placements(symbol: Image.Image, suit: str, rank: int, visible: np.ndarray | None = None,
                   cfg: dict | None = None) -> tuple[list[Placement], float]:
    cfg = cfg or suit_config(suit, None)
    scale = cfg["scale"]
    for _ in range(MAX_SHRINK_STEPS):
        placements = place(symbol, suit, rank, scale, cfg["y_offset"], cfg["y_offset_mode"])
        if overlaps(placements) or check_placements(placements, visible):
            scale *= SHRINK_STEP
        else:
            return placements, scale
    raise RuntimeError(f"{suit} {rank}: symbols still overlap or leave the visible area "
                       f"after {MAX_SHRINK_STEPS} shrink steps")


def visible_region() -> np.ndarray:
    """Pixels of the raw 1024x1536 image that remain visible after composite.py places it in the frame."""
    frame = Image.open(composite.FRAME_PATH).convert("RGB")
    window = composite.detect_window(frame)
    x0, y0, x1, y1 = composite.bbox_of(window)
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    s = max(bw / SIZE[0], bh / SIZE[1])
    left = (round(SIZE[0] * s) - bw) // 2
    # Map each raw pixel to its frame position (same transform as composite.fit_art).
    ys, xs = np.mgrid[0:SIZE[1], 0:SIZE[0]]
    fx = np.round(xs * s - left + x0).astype(int)
    fy = np.round(ys * s + y0).astype(int)
    inside = (fx >= x0) & (fx <= x1) & (fy >= y0) & (fy <= y1)
    vis = np.zeros_like(inside)
    vis[inside] = window[fy[inside], fx[inside]] > 0
    return vis


def render(bg: Image.Image, placements: list[Placement], glow: bool = False,
           glow_opacity: float = GLOW_OPACITY) -> Image.Image:
    """Draw order: background -> dark halo -> ivory glow (optional) -> drop shadow -> symbols."""
    base = bg.convert("RGB").resize(SIZE, Image.LANCZOS)
    union = np.zeros((SIZE[1], SIZE[0]), dtype=np.uint8)
    for p in placements:
        union |= p.mask().astype(np.uint8)
    halo = (Image.fromarray(union * 255).filter(ImageFilter.MaxFilter(HALO_GROW))
            .filter(ImageFilter.GaussianBlur(HALO_BLUR)).point(lambda v: round(v * HALO_STRENGTH)))
    canvas = Image.composite(Image.new("RGB", SIZE, HALO_COLOR), base, halo)
    if glow:
        k = 2 * GLOW_GROW + 1
        light = (Image.fromarray(cv2.dilate(union * 255, np.ones((k, k), np.uint8)))
                 .filter(ImageFilter.GaussianBlur(GLOW_BLUR)).point(lambda v: round(v * glow_opacity)))
        canvas = Image.composite(Image.new("RGB", SIZE, GLOW_COLOR), canvas, light)
    canvas = canvas.convert("RGBA")
    for p in placements:
        alpha = p.image.getchannel("A").point(lambda v: round(v * SHADOW_OPACITY))
        shadow = Image.new("RGBA", p.image.size, (0, 0, 0, 0))
        shadow.putalpha(alpha)
        pad = SHADOW_BLUR * 3
        padded = Image.new("RGBA", (shadow.width + pad * 2, shadow.height + pad * 2), (0, 0, 0, 0))
        padded.paste(shadow, (pad, pad))
        padded = padded.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))
        canvas.alpha_composite(padded, (p.offset[0] - pad + SHADOW_OFFSET[0], p.offset[1] - pad + SHADOW_OFFSET[1]))
    for p in placements:
        layer = Image.new("RGBA", SIZE, (0, 0, 0, 0))
        layer.paste(p.image, p.offset, p.image)
        canvas.alpha_composite(layer)
    return canvas.convert("RGB")


def check_placements(placements: list[Placement], visible: np.ndarray | None) -> list[str]:
    warnings = []
    limit = BOTTOM_LIMIT * SIZE[1]
    for i, p in enumerate(placements, 1):
        m = p.mask()
        ys = np.where(m.any(axis=1))[0]
        if ys.size and ys.max() > limit:
            warnings.append(f"記号{i}の下端 y={ys.max() / SIZE[1]:.3f} が {BOTTOM_LIMIT} を超えています")
        if visible is not None:
            hidden = (m & ~visible).sum() / max(m.sum(), 1)
            if hidden > 0.01:
                warnings.append(f"記号{i}の {hidden:.0%} がフレームに隠れます")
    return warnings


def render_crossed(bg: Image.Image, items: list[crossed.Item]) -> Image.Image:
    """Draw order: background -> drop shadows -> symbols (back to front, each outlined) -> rosettes."""
    canvas = bg.convert("RGBA").resize(SIZE, Image.LANCZOS)
    pad = SHADOW_BLUR * 3
    for it in items:
        a = Image.new("L", (it.image.width + pad * 2, it.image.height + pad * 2), 0)
        a.paste(it.image.getchannel("A").point(lambda v: round(v * SHADOW_OPACITY)), (pad, pad))
        shadow = Image.new("RGBA", a.size, (0, 0, 0, 0))
        shadow.putalpha(a.filter(ImageFilter.GaussianBlur(SHADOW_BLUR)))
        canvas.alpha_composite(shadow, (it.offset[0] - pad + SHADOW_OFFSET[0], it.offset[1] - pad + SHADOW_OFFSET[1]))
    k = 2 * OUTLINE_PX + 1
    opad = OUTLINE_PX + 1
    for it in sorted(items, key=lambda i: i.kind == "rosette"):   # stable sort: symbols keep their order
        grown = cv2.dilate(np.pad(np.asarray(it.image.getchannel("A")), opad), np.ones((k, k), np.uint8))
        outline = Image.new("RGBA", (grown.shape[1], grown.shape[0]), OUTLINE_COLOR + (0,))
        outline.putalpha(Image.fromarray(grown).point(lambda v: round(v * OUTLINE_OPACITY)))
        layer = Image.new("RGBA", SIZE, (0, 0, 0, 0))
        layer.paste(outline, (it.offset[0] - opad, it.offset[1] - opad), outline)
        canvas.alpha_composite(layer)
        layer = Image.new("RGBA", SIZE, (0, 0, 0, 0))
        layer.paste(it.image, it.offset, it.image)
        canvas.alpha_composite(layer)
    return canvas.convert("RGB")


_CUPS_BBOX: dict[int, tuple[int, int, int, int]] = {}
_SCALES: dict[tuple[str, int], float] = {}


def cups_bbox(rank: int) -> tuple[int, int, int, int]:
    """Bounding box (x0, y0, x1, y1) of the cups symbols of `rank`: the size reference for crossed suits."""
    if rank not in _CUPS_BBOX:
        chosen = json.loads(SELECTED_ASSETS_PATH.read_text(encoding="utf-8"))
        bg = Image.open(ASSETS_DIR / f"bg_cups_{chosen['bg_cups']}.png")
        sym = Image.open(ASSETS_DIR / f"symbol_cups_{chosen['symbol_cups']}.png")
        _, placements, _, _ = layout_card(bg, sym, "cups", rank, None, load_config())
        union = np.zeros((SIZE[1], SIZE[0]), dtype=bool)
        for p in placements:
            union |= p.mask()
        ys, xs = np.where(union)
        _CUPS_BBOX[rank] = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    return _CUPS_BBOX[rank]


def window_inner(circle: crossed.Circle, visible: np.ndarray | None) -> np.ndarray:
    """Visible arch window shrunk by WINDOW_MARGIN, with the bottom crop line applied."""
    vis = visible if visible is not None else visible_region()
    k = 2 * math.ceil(crossed.WINDOW_MARGIN * circle.r) + 1
    inner = cv2.erode(vis.astype(np.uint8), np.ones((k, k), np.uint8)) > 0
    inner[int(BOTTOM_LIMIT * SIZE[1]) + 1:, :] = False
    return inner


def crossed_scale(suit: str, rank: int, symbol: Image.Image, axis: crossed.LongAxis, circle: crossed.Circle,
                  traced: dict, inner: np.ndarray, label: str) -> tuple[float, dict]:
    """Enlargement of the traced skeleton (handoff-wands-swords-unify.md 3), with the steps taken."""
    key = (suit, rank)
    ref_scale = None if rank == crossed.WIDTH_REF_RANK else _SCALES.get((suit, crossed.WIDTH_REF_RANK))
    if ref_scale is None and rank != crossed.WIDTH_REF_RANK:
        ref_scale, _ = crossed_scale(suit, crossed.WIDTH_REF_RANK, symbol, axis, circle, traced, inner, label)

    def build(k):
        return crossed.traced_symbols(rank, circle, symbol, axis, traced, k,
                                      k if rank == crossed.WIDTH_REF_RANK else ref_scale, label)[0]

    cx0, cy0, cx1, cy1 = cups_bbox(rank)
    cup_h, cup_w = cy1 - cy0 + 1, cx1 - cx0 + 1
    k = 1.0
    for _ in range(4):                                      # height match (the bbox is ~linear in k)
        x0, y0, x1, y1 = crossed.group_bbox(build(k))
        k *= cup_h / (y1 - y0 + 1)
    by_height = k
    for _ in range(4):                                      # width cap
        x0, y0, x1, y1 = crossed.group_bbox(build(k))
        if x1 - x0 + 1 <= crossed.CUP_WIDTH_CAP * cup_w + 0.5:
            break
        k *= crossed.CUP_WIDTH_CAP * cup_w / (x1 - x0 + 1)
    by_width = k
    steps = 0
    while crossed.window_violations(build(k), inner) and steps < 60:
        k *= crossed.SCALE_STEP
        steps += 1
    _SCALES[key] = k
    return k, {"by_height": round(by_height, 3), "by_width_cap": round(by_width, 3), "final": round(k, 3),
               "window_steps": steps}


def crossed_setup(suit: str, extras: dict[str, Image.Image], cfg: dict):
    """Cleaned (and brightened) symbol, its measured axis and the message label for a crossed suit."""
    if suit == "swords":
        symbol, label = clean_symbol(extras["straight"]), "ソード"
        maker = crossed.LongAxis.sword
    elif suit == "wands":
        symbol, label = clean_symbol(extras["staff"]), "ワンド"
        maker = crossed.LongAxis.staff
    else:
        raise ValueError(f"crossed layout is not defined for {suit}")
    if cfg["brighten"]:
        symbol = brighten_symbol(symbol)
    return symbol, maker(symbol), label


def hand_size(cfg: dict, rank: int) -> tuple[float, float] | None:
    """(scale, dy) chosen by hand in size_tuner.html (layout_config.json -> suit.size), if any."""
    entry = (cfg.get("size") or {}).get(str(rank))
    return (float(entry["scale"]), float(entry.get("dy", 0.0))) if entry else None


def crossed_constraints(items: list[crossed.Item], circle: crossed.Circle, visible: np.ndarray | None
                        ) -> tuple[int, int]:
    """(px outside the arch window minus the 0.02R margin, px below the bottom crop line y=0.89)."""
    vis = visible if visible is not None else visible_region()
    k = 2 * math.ceil(crossed.WINDOW_MARGIN * circle.r) + 1
    inner = cv2.erode(vis.astype(np.uint8), np.ones((k, k), np.uint8)) > 0
    m = crossed._mask(items, SIZE) > 0
    below = m.copy()
    below[: int(BOTTOM_LIMIT * SIZE[1]) + 1, :] = False
    return int((m & ~inner).sum()), int(below.sum())


def crossed_card(bg: Image.Image, suit: str, rank: int, extras: dict[str, Image.Image], cfg: dict,
                 visible: np.ndarray | None, scale: float, dy: float, ref_scale: float
                 ) -> tuple[Image.Image, list[crossed.Item], list[str], tuple[int, int]]:
    """Render one crossed card with an explicit enlargement, offset and rank-4 reference scale."""
    circle = crossed.Circle.from_config(cfg)
    traced = json.loads((ROOT / crossed.TRACED_SWORDS).read_text(encoding="utf-8"))
    symbol, axis, label = crossed_setup(suit, extras, cfg)
    items, warnings = crossed.traced_symbols(rank, circle, symbol, axis, traced, scale, ref_scale, label, dy)
    window_px, bottom_px = crossed_constraints(items, circle, visible)
    if window_px:
        warnings.append(f"{label}の{rank}: {window_px}px がアーチ窓の余白（{crossed.WINDOW_MARGIN}R）の外にあります")
    if bottom_px:
        warnings.append(f"{label}の{rank}: {bottom_px}px が下端 y={BOTTOM_LIMIT} より下にあります")
    return render_crossed(bg, items), items, warnings, (window_px, bottom_px)


def layout_crossed(bg: Image.Image, suit: str, rank: int, extras: dict[str, Image.Image], cfg: dict,
                   visible: np.ndarray | None) -> tuple[Image.Image, list[Placement], float, list[str]]:
    """Sizes come from layout_config.json (suit.size, set with size_tuner.html); ranks without an entry
    fall back to the automatic rule of handoff-wands-swords-unify.md 3."""
    circle = crossed.Circle.from_config(cfg)
    traced = json.loads((ROOT / crossed.TRACED_SWORDS).read_text(encoding="utf-8"))
    symbol, axis, label = crossed_setup(suit, extras, cfg)

    def size_of(r: int) -> tuple[float, float]:
        chosen = hand_size(cfg, r)
        if chosen:
            return chosen
        k, _ = crossed_scale(suit, r, symbol, axis, circle, traced, window_inner(circle, visible), label)
        return k, 0.0

    scale, dy = size_of(rank)
    ref_scale = scale if rank == crossed.WIDTH_REF_RANK else size_of(crossed.WIDTH_REF_RANK)[0]
    img, items, warnings, _ = crossed_card(bg, suit, rank, extras, cfg, visible, scale, dy, ref_scale)
    symbols = [Placement((0.0, 0.0), 0.0, i.image, i.offset) for i in items]
    warnings += check_placements(symbols, visible)
    return img, symbols, scale, warnings


def layout_card(bg: Image.Image, symbol: Image.Image | None, suit: str, rank: int,
                visible: np.ndarray | None = None, config: dict[str, dict] | None = None,
                extras: dict[str, Image.Image] | None = None,
                ) -> tuple[Image.Image, list[Placement], float, list[str]]:
    cfg = suit_config(suit, config)
    if cfg["layout"] == "crossed":
        return layout_crossed(bg, suit, rank, extras or {}, cfg, visible)
    sym = clean_symbol(symbol)
    if cfg["brighten"]:
        sym = brighten_symbol(sym)
    placements, scale = fit_placements(sym, suit, rank, visible, cfg)
    img = render(bg, placements, cfg["glow"], cfg.get("glow_opacity", GLOW_OPACITY))
    return img, placements, scale, check_placements(placements, visible)


def main() -> None:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Lay out suit symbols for the Minor Arcana pip cards")
    ap.add_argument("--only", help="対象（カードIDまたはスート名。例：23,51 / wands）")
    ap.add_argument("--config", type=Path, help="スート別設定の上書きファイル（既定 layout_config.json）")
    ap.add_argument("--set", action="append", default=[], metavar="SUIT.KEY=VALUE",
                    help="スート別設定を1項目だけ上書きする（例：wands.y_offset=0.05、繰り返し可）")
    ap.add_argument("--out-dir", type=Path, default=RAW_DIR, help="出力先（既定 out/raw）")
    args = ap.parse_args()
    only = {x.strip() for x in args.only.split(",")} if args.only else None
    config = load_config(args.config)
    for item in args.set:
        key, _, value = item.partition("=")
        suit, _, field = key.partition(".")
        config.setdefault(suit, {})[field] = json.loads(value)
    out_dir = args.out_dir

    if not SELECTED_ASSETS_PATH.exists():
        sys.exit('selected_assets.json がありません。例: {"symbol_wands": "a", "bg_wands": "b", ...}')
    chosen = json.loads(SELECTED_ASSETS_PATH.read_text(encoding="utf-8"))
    cards = [c for c in json.loads(CARDS_MINOR_PATH.read_text(encoding="utf-8")) if c.get("method") == "layout"]
    if only:
        cards = [c for c in cards if str(c["id"]) in only or c["suit"] in only]

    selected = json.loads(SELECTED_PATH.read_text(encoding="utf-8")) if SELECTED_PATH.exists() else {}
    visible = visible_region()
    out_dir.mkdir(parents=True, exist_ok=True)
    loaded: dict[str, Image.Image] = {}
    ok = 0
    for card in cards:
        suit = card["suit"]
        cfg = suit_config(suit, config)
        names = {"bg": f"bg_{suit}"}
        if cfg["layout"] == "crossed":
            names.update(CROSSED_ASSETS[suit])
        else:
            names["symbol"] = f"symbol_{suit}"
        try:
            paths = {role: ASSETS_DIR / f"{name}_{chosen[name]}.png" for role, name in names.items()}
        except KeyError as e:
            print(f"[NG] {card['slug']}: selected_assets.json に {e.args[0]} がありません")
            continue
        missing = [p.name for p in paths.values() if not p.exists()]
        if missing:
            print(f"[NG] {card['slug']}: 素材がありません {missing}")
            continue
        for p in paths.values():
            loaded.setdefault(str(p), Image.open(p).copy())
        images = {role: loaded[str(p)] for role, p in paths.items()}
        bg = images.pop("bg")
        img, placements, scale, warnings = layout_card(
            bg, images.pop("symbol", None), suit, card["rank"], visible, config, images)
        dst = out_dir / f"{card['id']:02d}_{card['slug']}_{LAYOUT_VARIANT}.png"
        img.save(dst)
        if out_dir == RAW_DIR:
            selected.setdefault(str(card["id"]), LAYOUT_VARIANT)
        ok += 1
        note = f"（倍率 {scale:.2f}）" if scale != (cfg["scale"] if cfg["layout"] == "grid" else 1.0) else ""
        print(f"[OK] {dst.name} 記号 {len(placements)} 個{note}")
        for w in warnings:
            print(f"     警告: {w}")

    selected = dict(sorted(selected.items(), key=lambda kv: int(kv[0])))
    SELECTED_PATH.write_text(json.dumps(selected, indent=2) + "\n", encoding="utf-8")
    print(f"\n完了: {ok} / {len(cards)} 枚")


if __name__ == "__main__":
    main()
