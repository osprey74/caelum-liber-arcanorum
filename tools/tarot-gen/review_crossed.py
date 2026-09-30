"""Build out/review/pips_crossed_preview.png: 2 rows x 4 cols (swords top, wands bottom), framed."""
import sys
from PIL import Image, ImageDraw
import composite as c

SRC = c.ROOT / "out" / "review" / "crossed"
ROWS = [["51_swords_02", "52_swords_03", "56_swords_07", "59_swords_10"],
        ["23_wands_02", "24_wands_03", "28_wands_07", "31_wands_10"]]
W, H, PAD, LAB = 400, 600, 16, 34

fr = Image.open(c.FRAME_PATH).convert("RGB")
m = c.detect_window(fr)
bb = c.bbox_of(m)
sheet = Image.new("RGB", (PAD + 4 * (W + PAD), PAD + 2 * (H + LAB + PAD)), (24, 28, 40))
d = ImageDraw.Draw(sheet)
font = c.load_font(20)
for r, row in enumerate(ROWS):
    for i, name in enumerate(row):
        x, y = PAD + i * (W + PAD), PAD + r * (H + LAB + PAD)
        card = c.composite(fr, Image.open(SRC / f"{name}_a.png"), m, bb).resize((W, H), Image.LANCZOS)
        sheet.paste(card, (x, y))
        d.text((x + 4, y + H + 6), name[3:], fill=(230, 210, 160), font=font)
out = c.ROOT / "out" / "review" / "pips_crossed_preview.png"
sheet.save(out)
print(out)
