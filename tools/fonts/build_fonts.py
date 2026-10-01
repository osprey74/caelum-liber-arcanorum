"""Subset the card-name fonts to the characters the app uses and write WOFF2 into src/assets/fonts/.

    py -3.11 build_fonts.py

Sources: the OFL-licensed TTFs in this folder (from https://github.com/google/fonts, ofl/<family>/).
Characters: every card name / roman numeral in src/data/cards.json plus EXTRA_TEXT. Add text to
EXTRA_TEXT when new strings are set in these fonts, then run this again.
"""
import json
import shutil
from pathlib import Path

from fontTools import subset

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
OUT = REPO / "src" / "assets" / "fonts"
# Card-name font, chosen 2026-10-01 (Shippori Mincho SemiBold) over Zen Old Mincho and Kaisei Tokumin.
FONTS = {  # source TTF -> output name
    "ShipporiMincho-SemiBold.ttf": "shippori-mincho-semibold",
}
LICENSES = {"ShipporiMincho": "shipporimincho_OFL.txt"}
EXTRA_TEXT = "0123456789IVXLCDM ・ー　正逆位置表裏面"


def charset() -> str:
    cards = json.loads((REPO / "src" / "data" / "cards.json").read_text(encoding="utf-8"))
    text = EXTRA_TEXT + "".join(c["name_ja"] + c.get("roman", "") + c["name_en"] for c in cards)
    return "".join(sorted(set(text)))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    chars = charset()
    for src, name in FONTS.items():
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["*"]
        font = subset.load_font(str(HERE / src), opts)
        s = subset.Subsetter(opts)
        s.populate(text=chars)
        s.subset(font)
        dst = OUT / f"{name}.woff2"
        subset.save_font(font, str(dst), opts)
        print(f"{dst.name}: {dst.stat().st_size / 1024:.0f} KB ({len(chars)} chars)")
    for family, lic in LICENSES.items():
        shutil.copyfile(HERE / lic, OUT / f"{family}-OFL.txt")


if __name__ == "__main__":
    main()
