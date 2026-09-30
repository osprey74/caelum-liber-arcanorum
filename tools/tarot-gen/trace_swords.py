"""Trace every sword of refs/sword_rough.png (handoff-swords-trace.md) into swords_traced.json.

The rough cards are registered onto raw 1024x1536 coordinates (see fit_rough.py) and the swords are
extracted as a mask. Each sword is then placed individually by its pommel (hilt) and tip points, and
the points are refined one sword at a time by coordinate descent on the IoU with the rough mask.
The starting points came from the X-unit table fitted earlier (out/review/sword_fit.json).

Usage:
  python trace_swords.py                  # automatic first pass (overwrites swords_traced.json)
  python trace_swords.py --overlay-only   # only redraw the overlay from the current swords_traced.json
  python trace_grid.py 6 t                # rough card 6 with a 0.1R grid and the traced lines, for
                                          # reading or correcting coordinates by hand

Note (2026-09-30): the automatic pass lined up only on cards 2 and 3. Cards 4-10 in swords_traced.json
were read by hand from the trace_grid.py images and verified on the overlay.

Outputs:
  swords_traced.json                     {"2": [{"hilt": [x, y], "tip": [x, y]}, ...], ...} in R, y down
  out/review/swords_trace_overlay.png    the rough with every traced sword drawn as a red line
"""
import json
import math
import sys

import numpy as np
from PIL import Image, ImageDraw

import composite as c
import crossed
import fit_rough
import layout
import review_rough as rr

SIZE = (1024, 1536)
TRACED_PATH = c.ROOT / "swords_traced.json"
STEPS = (0.04, 0.02, 0.01)


def initial_swords(spec: dict) -> list[dict]:
    """Hilt/tip of every sword implied by an X-unit spec (R units, y down)."""
    swords = []
    L, th = spec["length"], spec["angle"]
    f = 0.5  # the rough crosses mid-blade (handoff-swords-trace.md 1)
    for ux, uy in spec["units"]:
        for ang in (-th, th):
            dx, dy = math.sin(math.radians(ang)), -math.cos(math.radians(ang))
            swords.append({"hilt": [ux - f * L * dx, uy - f * L * dy],
                           "tip": [ux + (1 - f) * L * dx, uy + (1 - f) * L * dy]})
    if spec.get("vertical"):
        h = spec["vertical"] / 2
        swords.append({"hilt": [0.0, h], "tip": [0.0, -h]})
    return swords


def place(sword, axis, circle: crossed.Circle, s: dict, scale: float = 1.0) -> crossed.Item:
    R = circle.r * scale
    hx, hy = s["hilt"]
    tx, ty = s["tip"]
    length = math.hypot(tx - hx, ty - hy) * R
    angle = math.degrees(math.atan2(tx - hx, -(ty - hy)))   # clockwise from vertical
    return crossed.place_sword(sword, axis, length, angle, 0.0, circle.cx + hx * R, circle.cy + hy * R)


def mask_of(item: crossed.Item) -> np.ndarray:
    return crossed._mask([item], SIZE) > 0


def refine(swords: list[dict], target: np.ndarray, sword, axis, circle) -> tuple[list[dict], float]:
    masks = [mask_of(place(sword, axis, circle, s)) for s in swords]

    def score(ms):
        u = np.zeros_like(target)
        for m in ms:
            u |= m
        return (u & target).sum() / max((u | target).sum(), 1)

    best = score(masks)
    for step in STEPS:
        for _ in range(6):
            improved = False
            for i, s in enumerate(swords):
                for key in ("hilt", "tip"):
                    for axis_i in (0, 1):
                        for d in (step, -step):
                            cand = {"hilt": list(s["hilt"]), "tip": list(s["tip"])}
                            cand[key][axis_i] = round(cand[key][axis_i] + d, 3)
                            m = mask_of(place(sword, axis, circle, cand))
                            trial = masks[:i] + [m] + masks[i + 1:]
                            sc = score(trial)
                            if sc > best + 1e-4:
                                swords[i], masks, best, s, improved = cand, trial, sc, cand, True
                                break
            if not improved:
                break
    return swords, best


def overlay(traced: dict, circle: crossed.Circle) -> Image.Image:
    """Draw the traced swords on the rough itself (rough pixel coordinates)."""
    M = fit_rough.compose(fit_rough.ROUGH_TO_FRAMED, fit_rough.framed_to_raw())
    inv = np.linalg.inv(np.vstack([M, [0, 0, 1]]))[:2]           # raw -> rough card pixel
    W, H, PAD, LAB, SC = 390, 592, 12, 30, 2
    sheet = Image.new("RGB", (PAD + 9 * (W * SC + PAD), PAD + H * SC + LAB + PAD), (24, 28, 40))
    d = ImageDraw.Draw(sheet)
    font = c.load_font(22)
    for i, rank in enumerate(range(2, 11)):
        card = rr.rough_card(rank).resize((W * SC, H * SC), Image.LANCZOS)
        cd = ImageDraw.Draw(card)
        for s in traced[str(rank)]:
            pts = []
            for key in ("hilt", "tip"):
                x, y = s[key]
                raw = np.array([circle.cx + x * circle.r, circle.cy + y * circle.r, 1.0])
                px, py = inv @ raw
                pts.append((px * SC, py * SC))
            cd.line(pts, fill=(255, 40, 40), width=3)
            hx, hy = pts[0]
            cd.ellipse((hx - 6, hy - 6, hx + 6, hy + 6), outline=(255, 40, 40), width=3)
        x = PAD + i * (W * SC + PAD)
        sheet.paste(card, (x, PAD))
        d.text((x + 6, PAD + H * SC + 4), f"rough {rank} + trace", fill=(230, 210, 160), font=font)
    return sheet


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--overlay-only" in sys.argv:
        circle = crossed.Circle.from_config(layout.suit_config("swords", layout.load_config()))
        out = c.ROOT / "out" / "review" / "swords_trace_overlay.png"
        overlay(json.loads(TRACED_PATH.read_text(encoding="utf-8")), circle).save(out)
        print(out)
        return
    chosen = json.loads((c.ROOT / "selected_assets.json").read_text(encoding="utf-8"))
    circle = crossed.Circle.from_config(layout.suit_config("swords", layout.load_config()))
    bg_raw = np.asarray(Image.open(c.ASSETS_DIR / f"bg_swords_{chosen['bg_swords']}.png").convert("RGB").resize(SIZE))
    sword = crossed.alpha_crop(Image.open(c.ASSETS_DIR / f"symbol_swords_{chosen['symbol_swords']}.png"))
    axis = crossed.SwordAxis.measure(sword)
    fitted = json.loads((c.ROOT / "out" / "review" / "sword_fit.json").read_text(encoding="utf-8"))
    traced = {}
    for rank in range(2, 11):
        target = fit_rough.rough_mask(rank, bg_raw, circle)
        swords, score = refine(initial_swords(fitted[str(rank)]["after"]), target, sword, axis, circle)
        traced[str(rank)] = [{"hilt": [round(v, 3) for v in s["hilt"]], "tip": [round(v, 3) for v in s["tip"]]}
                             for s in swords]
        print(rank, f"IoU {score:.3f}", len(swords), "swords", flush=True)
    TRACED_PATH.write_text(json.dumps(traced, indent=1) + "\n", encoding="utf-8")
    out = c.ROOT / "out" / "review" / "swords_trace_overlay.png"
    overlay(traced, circle).save(out)
    print(out)


if __name__ == "__main__":
    main()
