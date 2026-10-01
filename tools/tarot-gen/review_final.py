"""Final check of the app card assets (handoff-app-implementation.md 1.4).

Reads the built WebP files (src/assets/cards/medium) and out/review/assets_report.json, and writes
  out/review/final_78.png               all 78 card faces + the back, one sheet
  out/review/final_{major,wands,cups,swords,pentacles}.png   the same, per group
Each tile is labelled with the card, the source file in out/raw and its date. Hand-made pips (h) are
marked in gold so mixed-in old versions are easy to spot.

Automatic checks (printed):
  - 78 cards x 3 sizes + back exist and are readable at the right size
  - every card's source matches selected.json
  - wands / swords pips 2-10 use the hand-made "h" designs, and each h file is newer than its design
  - cups / pentacles pips 2-10 use the layout.py output "a"
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone, timedelta

from PIL import Image, ImageDraw

import build_assets as b
import composite as c
import import_design

JST = timezone(timedelta(hours=9))
GROUPS = [("major", "大アルカナ", 6), ("wands", "ワンド", 7), ("cups", "カップ", 7),
          ("swords", "ソード", 7), ("pentacles", "ペンタクル", 7)]
TW, TH, PAD, LAB = 256, 384, 12, 46


def tile_sheet(items: list[tuple[str, str, str, bool]], cols: int) -> Image.Image:
    rows = -(-len(items) // cols)
    sheet = Image.new("RGB", (PAD + cols * (TW + PAD), PAD + rows * (TH + LAB + PAD)), (24, 28, 40))
    d = ImageDraw.Draw(sheet)
    f1, f2 = c.load_font(16), c.load_font(13)
    for i, (path, line1, line2, hand) in enumerate(items):
        x, y = PAD + (i % cols) * (TW + PAD), PAD + (i // cols) * (TH + LAB + PAD)
        with Image.open(path) as im:
            sheet.paste(im.convert("RGB").resize((TW, TH), Image.LANCZOS), (x, y))
        if hand:
            d.rectangle((x - 3, y - 3, x + TW + 2, y + TH + 2), outline=(230, 190, 90), width=3)
        d.text((x + 2, y + TH + 4), line1, fill=(230, 210, 160), font=f1)
        d.text((x + 2, y + TH + 24), line2, fill=(230, 190, 90) if hand else (170, 175, 190), font=f2)
    return sheet


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    report = json.loads(b.REPORT.read_text(encoding="utf-8"))
    by_id = {r["id"]: r for r in report["cards"]}
    cards = c.load_cards()
    selected = json.loads(c.SELECTED_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []

    # 1. files exist and have the right size
    for stem in [f"{i:02d}" for i in range(78)] + ["back"]:
        for name, size in b.SIZES.items():
            p = b.CARDS_OUT / name / f"{stem}.webp"
            if not p.exists():
                errors.append(f"{p.relative_to(b.REPO).as_posix()} がありません")
                continue
            with Image.open(p) as im:
                if im.size != size:
                    errors.append(f"{p.name} ({name}) のサイズが {im.size} です")
    # 2. sources match selected.json
    for i in range(78):
        exp = b.source_path(cards[i], selected[str(i)]).name
        if by_id[i]["source"] != exp:
            errors.append(f"{i:02d}: 生成元 {by_id[i]['source']} が selected.json の {exp} と違います")
    # 3. pip cards: hand-made wands/swords, layout cups/pentacles
    for i in range(78):
        card = cards[i]
        if card.get("type") != "pip":
            continue
        v = selected[str(i)]
        if card["suit"] in import_design.FILES:
            if v != import_design.VARIANT:
                errors.append(f"{i:02d} {card['slug']}: 手描き(h)ではなく {v} 案です")
                continue
            design = import_design.DESIGNS / import_design.FILES[card["suit"]].format(rank=card["rank"])
            src = b.source_path(card, v)
            if src.stat().st_mtime < design.stat().st_mtime:
                errors.append(f"{i:02d} {card['slug']}: {src.name} がデザイン {design.name} より古い（取り込み漏れ）")
        elif v != "a":
            errors.append(f"{i:02d} {card['slug']}: layout.py の出力(a)ではなく {v} 案です")

    # sheets
    all_items = []
    for key, label, cols in GROUPS:
        ids = [i for i in range(78) if cards[i].get("suit", "major") == key]
        items = []
        for i in ids:
            r = by_id[i]
            date = r["source_mtime"][5:16].replace("T", " ")
            hand = r["variant"] == import_design.VARIANT
            name = f"{cards[i].get('roman', '')} {cards[i]['name_ja']}".strip()
            items.append((b.CARDS_OUT / "medium" / f"{i:02d}.webp", f"{i:02d} {name}",
                          f"{r['source']}  {date}" + ("  手描き" if hand else ""), hand))
        tile_sheet(items, cols).save(c.ROOT / "out" / "review" / f"final_{key}.png")
        all_items += items
    all_items.append((b.CARDS_OUT / "medium" / "back.webp", "裏面", "refs/backimage_sym.png", False))
    tile_sheet(all_items, 13).save(c.ROOT / "out" / "review" / "final_78.png")

    total = report["total_bytes"]
    print(f"画像: 78枚 × 3サイズ + 裏面 3サイズ（full 品質 {report.get('full_quality', report['quality'])}、"
          f"medium・thumb 品質 {report['quality']}）、合計 {total / 1e6:.1f} MB")
    print("検査: " + ("すべて合格" if not errors else f"{len(errors)} 件の問題"))
    for e in errors:
        print("  - " + e)
    print("一覧: out/review/final_78.png, final_{major,wands,cups,swords,pentacles}.png")


if __name__ == "__main__":
    main()
