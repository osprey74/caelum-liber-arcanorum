"""Automated checks for layout.py: every pip card must show exactly `rank` symbols.

Run: python test_layout.py   (also works with pytest)

1. Synthetic shapes (rod, chalice, disc) are laid out for ranks 2-10 and the drawn symbols are
   counted independently via connected components of the rendered symbol mask.
2. When selected_assets.json and the real assets exist, each pip card is laid out with the real
   symbols and every symbol is checked to be drawn, unoccluded and non-overlapping.
"""

from __future__ import annotations

import json
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

import layout

BG = Image.new("RGB", layout.SIZE, (17, 31, 47))


def synthetic_symbol(kind: str) -> Image.Image:
    im = Image.new("RGBA", (400, 800), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if kind == "rod":        # tall and thin, like a wand or sword
        d.rectangle((170, 20, 230, 780), fill=(200, 160, 60, 255))
    elif kind == "chalice":  # wide top, narrow stem
        d.polygon([(40, 60), (360, 60), (230, 420), (170, 420)], fill=(210, 180, 70, 255))
        d.rectangle((185, 420, 215, 700), fill=(210, 180, 70, 255))
        d.rectangle((110, 700, 290, 760), fill=(210, 180, 70, 255))
    else:                    # disc, like a pentacle
        im = Image.new("RGBA", (600, 600), (0, 0, 0, 0))
        ImageDraw.Draw(im).ellipse((10, 10, 590, 590), fill=(220, 190, 80, 255))
    return im


SYNTHETIC = {"wands": "rod", "swords": "rod", "cups": "chalice", "pentacles": "disc"}


def union_mask(placements) -> np.ndarray:
    m = np.zeros((layout.SIZE[1], layout.SIZE[0]), dtype=bool)
    for p in placements:
        m |= p.mask()
    return m


def assert_no_overlap(placements, label: str) -> None:
    total = sum(int(p.mask().sum()) for p in placements)
    assert total == int(union_mask(placements).sum()), f"{label}: symbols overlap"


GRID_ONLY = {suit: {"layout": "grid"} for suit in SYNTHETIC}  # exercise the grid code for every shape


def test_synthetic_counts() -> None:
    for suit, kind in SYNTHETIC.items():
        symbol = synthetic_symbol(kind)
        for rank in range(2, 11):
            label = f"{suit} {rank}"
            _, placements, _, _ = layout.layout_card(BG, symbol, suit, rank, config=GRID_ONLY)
            assert len(placements) == rank, f"{label}: {len(placements)} placements"
            assert_no_overlap(placements, label)
            n, _ = cv2.connectedComponents(union_mask(placements).astype(np.uint8), connectivity=8)
            assert n - 1 == rank, f"{label}: counted {n - 1} symbols in the rendered mask"


def load_suit_assets(chosen: dict, suit: str, cfg: dict) -> tuple[Image.Image, Image.Image | None, dict] | None:
    names = {"bg": f"bg_{suit}"}
    if cfg["layout"] == "crossed":
        names.update(layout.CROSSED_ASSETS[suit])
    else:
        names["symbol"] = f"symbol_{suit}"
    paths = {}
    for role, name in names.items():
        if name not in chosen:
            return None
        paths[role] = layout.ASSETS_DIR / f"{name}_{chosen[name]}.png"
        if not paths[role].exists():
            return None
    images = {role: Image.open(p) for role, p in paths.items()}
    return images.pop("bg"), images.pop("symbol", None), images


def test_real_assets() -> None:
    if not layout.SELECTED_ASSETS_PATH.exists():
        print("  (selected_assets.json がないため、実素材のテストは省略)")
        return
    chosen = json.loads(layout.SELECTED_ASSETS_PATH.read_text(encoding="utf-8"))
    config = layout.load_config()
    visible = layout.visible_region()
    cards = [c for c in json.loads(layout.CARDS_MINOR_PATH.read_text(encoding="utf-8"))
             if c.get("method") == "layout"]
    tested = 0
    for card in cards:
        suit = card["suit"]
        cfg = layout.suit_config(suit, config)
        assets = load_suit_assets(chosen, suit, cfg)
        if assets is None:
            continue
        bg_img, symbol, extras = assets
        label = card["slug"]
        img, placements, _, warnings = layout.layout_card(bg_img, symbol, suit, card["rank"], visible, config, extras)
        assert len(placements) == card["rank"], f"{label}: {len(placements)} symbols"
        assert not warnings, f"{label}: {warnings}"
        bg = np.asarray(bg_img.convert("RGB").resize(layout.SIZE)).astype(int)
        out = np.asarray(img).astype(int)
        if cfg["layout"] == "grid":
            assert_no_overlap(placements, label)
            # Every symbol is actually drawn: its area differs from the plain background.
            for i, p in enumerate(placements, 1):
                m = p.mask()
                diff = np.abs(out[m] - bg[m]).mean()
                assert diff > 10, f"{label}: symbol {i} is not visible (mean diff {diff:.1f})"
        else:
            # Crossed symbols overlap by design; each one must still show a clear stretch of its own.
            covered = np.zeros(bg.shape[:2], dtype=np.int32)
            for p in placements:
                covered += p.mask()
            for i, p in enumerate(placements, 1):
                own = p.mask() & (covered == 1)
                assert own.sum() > 0.3 * p.mask().sum(), f"{label}: symbol {i} is mostly hidden"
        tested += 1
    print(f"  実素材で {tested} 枚を検証")


def test_crossed_geometry() -> None:
    """Symbol counts and area limits of the crossed layouts for every rank, with synthetic shapes."""
    import crossed
    circle = crossed.Circle(512, 600, 340)
    rod = synthetic_symbol("rod")
    for rank in range(2, 11):
        items, _ = crossed.wands_items(rank, circle, rod, rod)
        n = sum(i.kind == "symbol" for i in items)
        assert n == rank, f"wands {rank}: {n} staffs"
        assert not crossed.outside_area(items, circle, layout.SIZE), f"wands {rank}: outside the area"
        traced = json.loads((layout.ROOT / crossed.TRACED_SWORDS).read_text(encoding="utf-8"))
        items, _, _ = crossed.swords_items(rank, circle, rod, traced, layout.SIZE)
        n = sum(i.kind == "symbol" for i in items)
        assert n == rank, f"swords {rank}: {n} swords"
        # Traced swords are never shrunk; only count them here (the 0.96R limit is reported as a warning).


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    failed = 0
    for name, fn in [("synthetic_counts", test_synthetic_counts), ("crossed_geometry", test_crossed_geometry),
                     ("real_assets", test_real_assets)]:
        try:
            fn()
            print(f"[PASS] {name}")
        except AssertionError as e:
            failed += 1
            print(f"[FAIL] {name}: {e}")
    sys.exit(1 if failed else 0)
