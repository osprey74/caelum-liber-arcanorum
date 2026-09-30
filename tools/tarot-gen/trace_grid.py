"""Rough card (warped to raw coordinates) cropped to the halo circle with a 0.1R grid, for manual tracing."""
import json
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

import composite as c
import crossed
import fit_rough
import layout
import review_rough as rr

SIZE = (1024, 1536)
PX = 900   # output size of the -1R..+1R square


def grid_image(rank: int, traced: list | None = None) -> Image.Image:
    circle = crossed.Circle.from_config(layout.suit_config("swords", layout.load_config()))
    M = fit_rough.compose(fit_rough.ROUGH_TO_FRAMED, fit_rough.framed_to_raw())
    raw = cv2.warpAffine(np.asarray(rr.rough_card(rank)), M, SIZE, flags=cv2.INTER_CUBIC)
    R = circle.r
    box = (int(circle.cx - R), int(circle.cy - R), int(circle.cx + R), int(circle.cy + R))
    im = Image.fromarray(raw).crop(box).resize((PX, PX), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    font = c.load_font(14)
    to_px = lambda v: (v + 1) / 2 * PX
    for k in range(-10, 11):
        p = to_px(k / 10)
        col = (255, 255, 0) if k == 0 else ((0, 200, 255) if k % 5 == 0 else (90, 90, 90))
        d.line((p, 0, p, PX), fill=col, width=1)
        d.line((0, p, PX, p), fill=col, width=1)
        if k % 2 == 0:
            d.text((p + 2, 2), f"{k / 10:+.1f}", fill=(255, 255, 0), font=font)
            d.text((2, p + 2), f"{k / 10:+.1f}", fill=(255, 255, 0), font=font)
    for s in traced or []:
        (hx, hy), (tx, ty) = s["hilt"], s["tip"]
        d.line((to_px(hx), to_px(hy), to_px(tx), to_px(ty)), fill=(255, 40, 40), width=3)
        d.ellipse((to_px(hx) - 7, to_px(hy) - 7, to_px(hx) + 7, to_px(hy) + 7), outline=(255, 40, 40), width=3)
    return im


if __name__ == "__main__":
    rank = int(sys.argv[1])
    traced = None
    if len(sys.argv) > 2:
        traced = json.loads((c.ROOT / "swords_traced.json").read_text(encoding="utf-8")).get(str(rank))
    out = c.ROOT / "out" / "review" / f"trace_grid_{rank:02d}.png"
    grid_image(rank, traced).save(out)
    print(out)
