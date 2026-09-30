"""out/review/suits_size_compare.png: cups / swords / wands (rows) for ranks 2, 4, 7, 10 (columns), framed.
Also prints the enlargement of the traced skeleton per rank (handoff-wands-swords-unify.md 3)."""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import composite as c
import crossed
import layout

RANKS = [2, 4, 7, 10]
ROWS = [("cups", c.ROOT / "out" / "raw"), ("swords", None), ("wands", None)]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else c.ROOT / "out" / "review" / "unify"


def scale_table(ranks=range(2, 11)) -> dict:
    chosen = json.loads(layout.SELECTED_ASSETS_PATH.read_text(encoding="utf-8"))
    config = layout.load_config()
    visible = layout.visible_region()
    traced = json.loads((c.ROOT / crossed.TRACED_SWORDS).read_text(encoding="utf-8"))
    table = {}
    for suit, role, maker, label in (("swords", "symbol_swords", crossed.LongAxis.sword, "ソード"),
                                     ("wands", "symbol_wands_long", crossed.LongAxis.staff, "ワンド")):
        cfg = layout.suit_config(suit, config)
        circle = crossed.Circle.from_config(cfg)
        sym = layout.clean_symbol(Image.open(c.ASSETS_DIR / f"{role}_{chosen[role]}.png"))
        if cfg["brighten"]:
            sym = layout.brighten_symbol(sym)
        inner = layout.window_inner(circle, visible)
        for r in ranks:
            _, info = layout.crossed_scale(suit, r, sym, maker(sym), circle, traced, inner, label)
            table.setdefault(suit, {})[str(r)] = info
    return table


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    cards = {(x["suit"], x["rank"]): x for x in json.loads(layout.CARDS_MINOR_PATH.read_text(encoding="utf-8"))}
    fr = Image.open(c.FRAME_PATH).convert("RGB")
    m = c.detect_window(fr)
    bb = c.bbox_of(m)
    W, H, PAD, LAB = 390, 585, 12, 30
    sheet = Image.new("RGB", (PAD + 4 * (W + PAD), PAD + 3 * (H + LAB + PAD)), (24, 28, 40))
    d = ImageDraw.Draw(sheet)
    font = c.load_font(18)
    for r_i, (suit, src) in enumerate(ROWS):
        for c_i, rank in enumerate(RANKS):
            card = cards[(suit, rank)]
            path = (src or SRC) / f"{card['id']:02d}_{card['slug']}_a.png"
            x, y = PAD + c_i * (W + PAD), PAD + r_i * (H + LAB + PAD)
            sheet.paste(c.composite(fr, Image.open(path), m, bb).resize((W, H), Image.LANCZOS), (x, y))
            d.text((x + 4, y + H + 4), card["name_en"], fill=(230, 210, 160), font=font)
    out = c.ROOT / "out" / "review" / "suits_size_compare.png"
    sheet.save(out)
    print(out)
    print(json.dumps(scale_table(), ensure_ascii=False, indent=1))
