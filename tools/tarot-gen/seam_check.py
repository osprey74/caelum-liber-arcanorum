"""out/review/swords_seam_check.png: one sword of the 6 and of the 8 as drawn on the card (blade widened),
enlarged x5 around the blade/guard boundary, to check for steps or blur at the seam."""
import json
from PIL import Image, ImageDraw
import composite as c
import crossed
import layout

chosen = json.loads((c.ROOT / "selected_assets.json").read_text(encoding="utf-8"))
sword = crossed.alpha_crop(Image.open(c.ASSETS_DIR / f"symbol_swords_{chosen['symbol_swords']}.png"))
axis = crossed.SwordAxis.measure(sword)
circle = crossed.Circle.from_config(layout.suit_config("swords", layout.load_config()))
traced = json.loads((c.ROOT / crossed.TRACED_SWORDS).read_text(encoding="utf-8"))
ref = traced["4"]
blade_px = axis.blade_w * sum(map(crossed.sword_length, ref)) / len(ref) * circle.r / (axis.pommel - axis.tip)

ZOOM, HALF = 5, 40
sheet = Image.new("RGBA", (1300, 560), (17, 31, 47, 255))
d = ImageDraw.Draw(sheet)
font = c.load_font(18)
for i, rank in enumerate(("6", "8")):
    spec = traced[rank][0]
    s = crossed.sword_length(spec) * circle.r / (axis.pommel - axis.tip)
    widen = min(max(blade_px / (axis.blade_w * s), 1.0), 1.0 + crossed.MAX_BLADE_WIDEN)
    img, ax = crossed.widened_sword(sword, axis, widen)
    small = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)   # as on the card
    gy = round(ax.guard * s)
    crop = small.crop((0, max(0, gy - HALF), small.width, min(small.height, gy + HALF)))
    big = crop.resize((crop.width * ZOOM, crop.height * ZOOM), Image.NEAREST)
    x = 20 + i * 650
    sheet.alpha_composite(big, (x, 40))
    d.line((x, 40 + (gy - max(0, gy - HALF)) * ZOOM, x + big.width, 40 + (gy - max(0, gy - HALF)) * ZOOM),
           fill=(255, 60, 60, 120))
    d.text((x, 12), f"swords {rank}, sword 1: x{ZOOM} around the guard top (blade widened x{widen:.2f})",
           fill=(230, 210, 160, 255), font=font)
    sheet.alpha_composite(small, (x + 560, 40))
out = c.ROOT / "out" / "review" / "swords_seam_check.png"
sheet.convert("RGB").save(out)
print(out)
