"""Import the hand-made Wands / Swords pip designs (designs/) into the card pipeline.

Each design is a transparent 1024x1536 PNG in raw (background) coordinates, holding only the symbols:
  designs/Sword_design{2..10}.png, designs/wand_design{2..10}.png   (originals, kept in the repository)

For every card the symbols get the same dark halo and soft drop shadow as the cups / pentacles pips
(layout.py: HALO_* and SHADOW_*), are composited onto the selected suit background
(assets/bg_{suit}_{v}.png from selected_assets.json) and saved as out/raw/{id:02d}_{slug}_h.png ("h" = hand-made).
selected.json is pointed at "h" for these cards; `python composite.py` then builds the framed cards.
layout.py writes variant "a" only, so re-running it never overwrites the hand-made designs.

    python import_design.py            # import, check and update selected.json
    python import_design.py --check    # only check (arch window, bottom line y=0.89), write nothing
"""
from __future__ import annotations

import argparse
import json
import sys

import numpy as np
from PIL import Image, ImageFilter

import layout

ROOT = layout.ROOT
DESIGNS = ROOT / "designs"
VARIANT = "h"
FILES = {"swords": "Sword_design{rank}.png", "wands": "wand_design{rank}.png"}


def with_shadow(bg: Image.Image, design: Image.Image) -> Image.Image:
    """Same treatment as the cups / pentacles pips in layout.py:
    background -> dark halo around the symbols -> soft drop shadow -> design."""
    alpha = design.getchannel("A")
    solid = alpha.point(lambda v: 255 if v >= layout.ALPHA_THRESHOLD else 0)
    halo = (solid.filter(ImageFilter.MaxFilter(layout.HALO_GROW)).filter(ImageFilter.GaussianBlur(layout.HALO_BLUR))
            .point(lambda v: round(v * layout.HALO_STRENGTH)))
    base = Image.composite(Image.new("RGB", layout.SIZE, layout.HALO_COLOR), bg.convert("RGB"), halo)
    shadow_a = alpha.point(lambda v: round(v * layout.SHADOW_OPACITY)).filter(
        ImageFilter.GaussianBlur(layout.SHADOW_BLUR))
    shadow = Image.new("RGBA", design.size, (0, 0, 0, 0))
    shadow.putalpha(shadow_a)
    out = base.convert("RGBA")
    dx, dy = layout.SHADOW_OFFSET
    out.alpha_composite(shadow, (dx, dy))
    out.alpha_composite(design)
    return out.convert("RGB")


def check(design: Image.Image, visible: np.ndarray) -> list[str]:
    a = np.asarray(design.getchannel("A")) >= layout.ALPHA_THRESHOLD
    msgs = []
    hidden = int((a & ~visible).sum())
    if hidden:
        msgs.append(f"{hidden}px がフレームに隠れます")
    ys = np.where(a.any(axis=1))[0]
    if ys.size and ys.max() > layout.BOTTOM_LIMIT * layout.SIZE[1]:
        msgs.append(f"下端 y={ys.max() / layout.SIZE[1]:.3f} が {layout.BOTTOM_LIMIT} を超えています")
    return msgs


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="検証だけを行い、何も書き出さない")
    args = ap.parse_args()

    cards = {(c["suit"], c["rank"]): c for c in json.loads(layout.CARDS_MINOR_PATH.read_text(encoding="utf-8"))}
    visible = layout.visible_region()
    selected = json.loads(layout.SELECTED_PATH.read_text(encoding="utf-8"))
    chosen = json.loads(layout.SELECTED_ASSETS_PATH.read_text(encoding="utf-8"))
    problems = 0
    for suit, pattern in FILES.items():
        bg = Image.open(layout.ASSETS_DIR / f"bg_{suit}_{chosen['bg_' + suit]}.png").convert("RGB").resize(layout.SIZE)
        for rank in range(2, 11):
            card = cards[(suit, rank)]
            src = DESIGNS / pattern.format(rank=rank)
            if not src.exists():
                print(f"[NG] {src.name} がありません")
                problems += 1
                continue
            design = Image.open(src).convert("RGBA")
            if design.size != layout.SIZE:
                print(f"[NG] {src.name}: サイズ {design.size} が {layout.SIZE} と異なります")
                problems += 1
                continue
            msgs = check(design, visible)
            problems += bool(msgs)
            dst = layout.RAW_DIR / f"{card['id']:02d}_{card['slug']}_{VARIANT}.png"
            if not args.check:
                with_shadow(bg, design).save(dst)
                selected[str(card["id"])] = VARIANT
            print(f"[{'NG' if msgs else 'OK'}] {src.name} -> {dst.name}" + "".join(f"\n     警告: {m}" for m in msgs))
    if not args.check:
        selected = dict(sorted(selected.items(), key=lambda kv: int(kv[0])))
        layout.SELECTED_PATH.write_text(json.dumps(selected, indent=2) + "\n", encoding="utf-8")
    print(f"\n完了（警告のあるファイル: {problems}）")


if __name__ == "__main__":
    main()
