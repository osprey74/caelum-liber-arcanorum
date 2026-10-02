"""Subset the card-name fonts to the characters the app uses and write WOFF2 into src/assets/fonts/.

    py -3.11 build_fonts.py

Sources: the OFL-licensed TTFs in this folder (from https://github.com/google/fonts, ofl/<family>/).
Characters: every card name / roman numeral in src/data/cards.json, every spread name and position label in
src/data/spreads.json, printable ASCII, EXTRA_TEXT and DISPLAY_TEXT. Add text to DISPLAY_TEXT when a new fixed
string is set in `font-display` (titles, headings, buttons), then run this again. Text that is not known in
advance (AI interpretations, card meanings) uses the OS Mincho instead (tailwind.config.js `font-mincho`).
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
# Fixed strings shown in `font-display` (src/components/*). Keep in step with the components.
DISPLAY_TEXT = [
    "LIBER ARCANORUM", "秘儀の書", "CAELUM SERIES",
    "心に浮かぶ問いを、ひとつ思い描いてください。", "スプレッド", "山札をシャッフルする",
    "全体の読み解き", "カードごとの読み解き", "これからのヒント", "先にお伝えしたいこと",
    "占いの履歴", "AIによる解釈の設定", "使い方", "ご利用にあたって", "ライセンス", "：（）・", "、。「」",
]


def charset() -> str:
    cards = json.loads((REPO / "src" / "data" / "cards.json").read_text(encoding="utf-8"))
    spreads = json.loads((REPO / "src" / "data" / "spreads.json").read_text(encoding="utf-8"))
    text = EXTRA_TEXT + "".join(DISPLAY_TEXT) + "".join(chr(i) for i in range(0x20, 0x7F))
    text += "".join(c["name_ja"] + c.get("roman", "") + c["name_en"] for c in cards)
    text += "".join(s["name"] + "".join(p["label"] for p in s["positions"]) for s in spreads)
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
