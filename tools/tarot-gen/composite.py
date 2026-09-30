"""Composite selected tarot artwork into the common frame.

Usage examples:
  python composite.py                   # composite cards listed in selected.json
  python composite.py --contact-sheet   # also build out/contact_sheet.png from all raw variants
  python composite.py --contact-sheet --no-composite
  python composite.py --contact-sheet --final --suit minor --no-composite   # final sheets per suit
  python composite.py --assets-sheet --no-composite                           # symbol/background variants
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
CARDS_PATH = ROOT / "cards.json"
CARDS_MINOR_PATH = ROOT / "cards_minor.json"
FRAME_PATH = ROOT / "refs" / "frame.png"
SELECTED_PATH = ROOT / "selected.json"
RAW_DIR = ROOT / "out" / "raw"
ASSETS_DIR = ROOT / "assets"
COMPOSITE_DIR = ROOT / "out" / "composite"
CONTACT_SHEET_PATH = ROOT / "out" / "contact_sheet.png"
ASSETS_SHEET_PATH = ROOT / "out" / "contact_sheet_assets.png"

CENTER = (512, 768)
COLOR_THRESHOLD = 30
DILATE_PX = 3
MASK_BLUR_RADIUS = 1
# Expected window bbox (x0, y0, x1, y1) measured on frame.png.
EXPECTED_BBOX = (150, 247, 872, 1234)
BBOX_TOLERANCE = 15

RAW_NAME = re.compile(r"^(\d{2})_(.+)_([a-z])\.png$")
ASSET_NAME = re.compile(r"^((?:symbol|bg)_[a-z_]+?|rosette)_([a-z])\.png$")
SUITS = ("major", "wands", "cups", "swords", "pentacles")


def detect_window(frame: Image.Image) -> np.ndarray:
    """Return a uint8 mask (255 = window) of the arch window in the frame."""
    a = np.asarray(frame.convert("RGB")).astype(np.int32)
    cx, cy = CENTER
    dist = np.sqrt(((a - a[cy, cx]) ** 2).sum(axis=-1))
    similar = (dist <= COLOR_THRESHOLD).astype(np.uint8)
    _, labels = cv2.connectedComponents(similar, connectivity=4)
    window = (labels == labels[cy, cx]).astype(np.uint8) * 255

    # Fill holes: flood the background from a corner; anything unreached is inside.
    h, w = window.shape
    flood = window.copy()
    cv2.floodFill(flood, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 255)
    window = window | cv2.bitwise_not(flood)

    k = 2 * DILATE_PX + 1
    return cv2.dilate(window, np.ones((k, k), np.uint8))


def bbox_of(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask > 0)
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def check_bbox(bbox: tuple[int, int, int, int]) -> None:
    diffs = [abs(a - b) for a, b in zip(bbox, EXPECTED_BBOX)]
    if max(diffs) > BBOX_TOLERANCE:
        print(f"警告: 窓の検出結果 {bbox} が想定 {EXPECTED_BBOX} と大きく異なります。", file=sys.stderr)


def fit_art(art: Image.Image, bbox: tuple[int, int, int, int]) -> Image.Image:
    """Scale to cover the bbox, center horizontally, align to the top, then crop."""
    x0, y0, x1, y1 = bbox
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    scale = max(bw / art.width, bh / art.height)
    resized = art.resize((round(art.width * scale), round(art.height * scale)), Image.LANCZOS)
    left = (resized.width - bw) // 2
    return resized.crop((left, 0, left + bw, bh))


def composite(frame: Image.Image, art: Image.Image, mask: np.ndarray,
              bbox: tuple[int, int, int, int]) -> Image.Image:
    layer = Image.new("RGB", frame.size)
    layer.paste(fit_art(art.convert("RGB"), bbox), (bbox[0], bbox[1]))
    soft = Image.fromarray(mask).filter(ImageFilter.GaussianBlur(MASK_BLUR_RADIUS))
    out = frame.convert("RGB").copy()
    out.paste(layer, (0, 0), soft)
    return out


def load_font(size: int) -> ImageFont.ImageFont:
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def load_cards() -> dict[int, dict]:
    """Major Arcana (cards.json) and, when present, Minor Arcana (cards_minor.json)."""
    cards = {}
    for path in (CARDS_PATH, CARDS_MINOR_PATH):
        if path.exists():
            cards.update({c["id"]: c for c in json.loads(path.read_text(encoding="utf-8"))})
    return cards


def card_label(card: dict | None, cid: int) -> str:
    if card is None:
        return f"{cid:02d}"
    return f"{card['roman']} {card['name_en']}" if "roman" in card else card["name_en"]


def suit_ids(cards: dict[int, dict], suit: str | None) -> set[int] | None:
    """IDs of one suit ("major" for the Major Arcana); None means every card."""
    if suit is None:
        return None
    return {cid for cid, c in cards.items() if c.get("suit", "major") == suit}


def save_sheet(sheet: Image.Image, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)
    return path


def build_contact_sheet(path: Path = CONTACT_SHEET_PATH, ids: set[int] | None = None,
                        thumb_w: int = 240) -> Path | None:
    """One row per card, every generated variant side by side (for selection)."""
    groups: dict[int, dict[str, Path]] = {}
    for p in sorted(RAW_DIR.glob("*.png")):
        m = RAW_NAME.match(p.name)
        if m and (ids is None or int(m.group(1)) in ids):
            groups.setdefault(int(m.group(1)), {})[m.group(3)] = p
    if not groups:
        print("生成案がありません。")
        return None

    cards = load_cards()
    cols = max(len(v) for v in groups.values())
    thumb_h = thumb_w * 3 // 2
    label_h, pad, head_w = 28, 12, 220
    row_h = thumb_h + label_h + pad
    sheet = Image.new("RGB", (head_w + cols * (thumb_w + pad) + pad, pad + len(groups) * row_h), (24, 28, 40))
    draw = ImageDraw.Draw(sheet)
    font, font_big = load_font(18), load_font(22)

    for r, cid in enumerate(sorted(groups)):
        y = pad + r * row_h
        draw.text((pad, y + thumb_h // 2), card_label(cards.get(cid), cid), fill=(230, 210, 160), font=font_big)
        for c, letter in enumerate(sorted(groups[cid])):
            x = head_w + pad + c * (thumb_w + pad)
            with Image.open(groups[cid][letter]) as im:
                sheet.paste(im.convert("RGB").resize((thumb_w, thumb_h), Image.LANCZOS), (x, y))
            draw.text((x + 4, y + thumb_h + 4), f"{cid:02d} {letter}", fill=(240, 240, 240), font=font)
    return save_sheet(sheet, path)


def build_final_sheet(selected: dict[str, str], path: Path = CONTACT_SHEET_PATH, ids: set[int] | None = None,
                      thumb_w: int = 240, cols: int = 6) -> Path | None:
    """Grid of the selected (final) artwork only, one cell per card."""
    cards = load_cards()
    items = []
    for key, letter in sorted(selected.items(), key=lambda kv: int(kv[0])):
        cid = int(key)
        if ids is not None and cid not in ids:
            continue
        card = cards.get(cid)
        src = RAW_DIR / f"{cid:02d}_{card['slug']}_{letter}.png" if card else None
        if src and src.exists():
            items.append((f"{card_label(card, cid)} ({letter})", src))
        else:
            print(f"[NG] 決定稿がありません: {key} {letter}")
    if not items:
        print("決定稿がありません。")
        return None

    thumb_h = thumb_w * 3 // 2
    label_h, pad = 30, 12
    rows = -(-len(items) // cols)
    sheet = Image.new("RGB", (pad + cols * (thumb_w + pad), pad + rows * (thumb_h + label_h + pad)), (24, 28, 40))
    draw = ImageDraw.Draw(sheet)
    font = load_font(17)
    for i, (label, src) in enumerate(items):
        x = pad + (i % cols) * (thumb_w + pad)
        y = pad + (i // cols) * (thumb_h + label_h + pad)
        with Image.open(src) as im:
            sheet.paste(im.convert("RGB").resize((thumb_w, thumb_h), Image.LANCZOS), (x, y))
        draw.text((x + 4, y + thumb_h + 6), label, fill=(230, 210, 160), font=font)
    return save_sheet(sheet, path)


def build_assets_sheet(path: Path = ASSETS_SHEET_PATH, thumb_w: int = 200) -> Path | None:
    """One row per asset (symbol/background per suit), variants side by side on the window color."""
    groups: dict[str, dict[str, Path]] = {}
    for p in sorted(ASSETS_DIR.glob("*.png")):
        m = ASSET_NAME.match(p.name)
        if m:
            groups.setdefault(m.group(1), {})[m.group(2)] = p
    if not groups:
        print("素材がありません。")
        return None

    order = [f"{k}_{s}" for s in SUITS[1:] for k in ("symbol", "bg")] + [
        "symbol_swords_curved", "symbol_wands_long", "rosette"]
    names = [n for n in order if n in groups] + sorted(n for n in groups if n not in order)
    cols = max(len(v) for v in groups.values())
    thumb_h = thumb_w * 3 // 2
    label_h, pad, head_w = 28, 12, 200
    row_h = thumb_h + label_h + pad
    sheet = Image.new("RGB", (head_w + cols * (thumb_w + pad) + pad, pad + len(names) * row_h), (24, 28, 40))
    draw = ImageDraw.Draw(sheet)
    font, font_big = load_font(18), load_font(22)
    backdrop = (17, 31, 47, 255)  # frame window color, to judge transparent symbols
    for r, name in enumerate(names):
        y = pad + r * row_h
        draw.text((pad, y + thumb_h // 2), name, fill=(230, 210, 160), font=font_big)
        for c, letter in enumerate(sorted(groups[name])):
            x = head_w + pad + c * (thumb_w + pad)
            with Image.open(groups[name][letter]) as im:
                # Letterbox instead of stretching: some symbols come back nearly square.
                s = min(thumb_w / im.width, thumb_h / im.height)
                fitted = im.convert("RGBA").resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
                tile = Image.new("RGBA", (thumb_w, thumb_h), backdrop)
                tile.alpha_composite(fitted, ((thumb_w - fitted.width) // 2, (thumb_h - fitted.height) // 2))
                sheet.paste(tile.convert("RGB"), (x, y))
            draw.text((x + 4, y + thumb_h + 4), f"{name} {letter}", fill=(240, 240, 240), font=font)
    return save_sheet(sheet, path)


def main() -> None:
    # Windows consoles default to cp932, which cannot print the prompt text.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Composite selected artwork into the tarot frame")
    ap.add_argument("--contact-sheet", action="store_true", help="生成案の一覧画像を出力する")
    ap.add_argument("--final", action="store_true",
                    help="--contact-sheet と併用：selected.json の決定稿だけで一覧画像を作る")
    ap.add_argument("--suit", choices=SUITS + ("minor", "all"),
                    help="--contact-sheet と併用：区分別に out/contact_sheet_{suit}.png を出力する"
                         "（minor＝小アルカナ4スート、all＝大アルカナを含む全5区分）")
    ap.add_argument("--assets-sheet", action="store_true", help="素材の一覧画像 out/contact_sheet_assets.png を出力する")
    ap.add_argument("--no-composite", action="store_true", help="合成を行わない（一覧画像のみ）")
    ap.add_argument("--selected", type=Path, default=SELECTED_PATH, help="採用案リストのパス")
    args = ap.parse_args()

    if args.assets_sheet:
        path = build_assets_sheet()
        if path:
            print(f"素材の一覧画像: {path.relative_to(ROOT).as_posix()}")
    if args.contact_sheet:
        cards = load_cards()
        selected = json.loads(args.selected.read_text(encoding="utf-8")) if args.final else None
        if args.suit is None:
            targets = [(None, CONTACT_SHEET_PATH)]
        else:
            suits = {"all": SUITS, "minor": SUITS[1:]}.get(args.suit, (args.suit,))
            targets = [(s, ROOT / "out" / f"contact_sheet_{s}.png") for s in suits]
        for suit, out_path in targets:
            ids = suit_ids(cards, suit)
            if selected is not None:
                cols = 7 if suit in SUITS[1:] else 6  # 14 cards per suit -> 7 x 2
                path = build_final_sheet(selected, out_path, ids, cols=cols)
            else:
                path = build_contact_sheet(out_path, ids)
            if path:
                print(f"一覧画像: {path.relative_to(ROOT).as_posix()}")
    if args.no_composite:
        return

    if not args.selected.exists():
        sys.exit("selected.json がありません。例: {\"0\": \"b\", \"17\": \"a\"}")
    selected: dict[str, str] = json.loads(args.selected.read_text(encoding="utf-8"))
    if not selected:
        print("selected.json に採用案が記入されていません。")
        return

    cards = load_cards()
    frame = Image.open(FRAME_PATH).convert("RGB")
    mask = detect_window(frame)
    bbox = bbox_of(mask)
    check_bbox(bbox)
    print(f"窓: x={bbox[0]}〜{bbox[2]}, y={bbox[1]}〜{bbox[3]}")

    COMPOSITE_DIR.mkdir(parents=True, exist_ok=True)
    for key, letter in sorted(selected.items(), key=lambda kv: int(kv[0])):
        cid = int(key)
        card = cards.get(cid)
        if card is None:
            print(f"[NG] 未知のカードID: {key}")
            continue
        src = RAW_DIR / f"{cid:02d}_{card['slug']}_{letter}.png"
        if not src.exists():
            print(f"[NG] 生成案がありません: {src.name}")
            continue
        with Image.open(src) as art:
            out = composite(frame, art, mask, bbox)
        dst = COMPOSITE_DIR / f"{cid:02d}_{card['slug']}.png"
        out.save(dst)
        print(f"[OK] {src.name} -> {dst.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
