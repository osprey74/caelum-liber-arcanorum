"""swords_rough_compare.png: the rough (refs/sword_rough.png, cards 2-10) above the framed output.

Also provides sword masks for measuring: the difference between a card and the same card without swords.
"""
import json
import numpy as np
from PIL import Image, ImageDraw
import composite as c

ROUGH = c.ROOT / "refs" / "sword_rough.png"
SRC = c.ROOT / "out" / "review" / "rough"
# Card boxes in the rough (5 x 2 grid, cards 1-10), measured from the flat navy margins.
COLS = [(57, 446), (506, 895), (955, 1344), (1404, 1793), (1853, 2242)]
ROWS = [(29, 620), (677, 1268)]
NAMES = {r: f"{50 + r - 1:02d}_swords_{r:02d}" for r in range(2, 11)}


def rough_card(rank: int) -> Image.Image:
    i = rank - 1
    (x0, x1), (y0, y1) = COLS[i % 5], ROWS[i // 5]
    return Image.open(ROUGH).convert("RGB").crop((x0, y0, x1 + 1, y1 + 1))


def framed(raw: Image.Image) -> Image.Image:
    fr = Image.open(c.FRAME_PATH).convert("RGB")
    m = c.detect_window(fr)
    return c.composite(fr, raw, m, c.bbox_of(m))


def plain_card() -> Image.Image:
    chosen = json.loads((c.ROOT / "selected_assets.json").read_text(encoding="utf-8"))
    return framed(Image.open(c.ASSETS_DIR / f"bg_swords_{chosen['bg_swords']}.png").convert("RGB").resize((1024, 1536)))


def sword_mask(card: Image.Image, plain: Image.Image, thresh: int = 60) -> np.ndarray:
    a = np.asarray(card.convert("RGB")).astype(int)
    b = np.asarray(plain.resize(card.size, Image.LANCZOS)).astype(int)
    return np.abs(a - b).sum(axis=-1) > thresh


if __name__ == "__main__":
    W, H, PAD, LAB = 390, 592, 12, 30
    sheet = Image.new("RGB", (PAD + 9 * (W + PAD), PAD + 2 * (H + LAB + PAD)), (24, 28, 40))
    d = ImageDraw.Draw(sheet)
    font = c.load_font(18)
    for i, rank in enumerate(range(2, 11)):
        x = PAD + i * (W + PAD)
        sheet.paste(rough_card(rank).resize((W, H), Image.LANCZOS), (x, PAD))
        d.text((x + 4, PAD + H + 4), f"rough {rank}", fill=(230, 210, 160), font=font)
        out = framed(Image.open(SRC / f"{NAMES[rank]}_a.png")).resize((W, H), Image.LANCZOS)
        sheet.paste(out, (x, PAD + H + LAB + PAD))
        d.text((x + 4, PAD + 2 * H + LAB + PAD + 4), f"output {rank}", fill=(230, 210, 160), font=font)
    path = c.ROOT / "out" / "review" / "swords_rough_compare.png"
    sheet.save(path)
    print(path)
