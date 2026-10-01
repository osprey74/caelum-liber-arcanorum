"""Build the app's card assets from the selected artwork (handoff-app-implementation.md, phase 1).

For every card (ID 0-77) the artwork chosen in selected.json (out/raw/{id:02d}_{slug}_{v}.png) is
composited into the common frame, then written as WebP in three sizes. The chosen artwork is also
copied to final/ (tracked with Git LFS), so the assets can be rebuilt on a machine without out/raw:
sources are read from out/raw when present, otherwise from final/. The card back is the
point-symmetric refs/backimage_sym.png. Card names and glyphs are not drawn (the app overlays them).

    py -3.11 build_assets.py                 # quality 85
    py -3.11 build_assets.py --quality 90
    py -3.11 build_assets.py --full-quality 80   # full size only at quality 80 (medium/thumb keep --quality)

Outputs (relative to the repository root):
  src/assets/cards/{full,medium,thumb}/{id:02d}.webp and back.webp
  src/data/cards.json                       78 cards: metadata, glyph, image paths
  tools/tarot-gen/out/review/assets_report.json   source file, its mtime and output sizes per card
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from PIL import Image

import composite as c

ROOT = c.ROOT
REPO = ROOT.parent.parent
CARDS_OUT = REPO / "src" / "assets" / "cards"
MANIFEST = REPO / "src" / "data" / "cards.json"
REPORT = ROOT / "out" / "review" / "assets_report.json"
BACK = ROOT / "refs" / "backimage_sym.png"
FINAL_DIR = ROOT / "final"           # the 78 chosen artworks, kept in the repository (Git LFS)
SIZES = {"full": (1024, 1536), "medium": (512, 768), "thumb": (256, 384)}
JST = timezone(timedelta(hours=9))
# Generation-only fields that stay in tools/ (prompts and layout data).
DROP = {"subject", "symbols", "astro_accent", "method"}


def source_path(card: dict, variant: str) -> Path:
    """The chosen artwork: out/raw when it exists (working copy), else the archived copy in final/."""
    name = f"{card['id']:02d}_{card['slug']}_{variant}.png"
    raw = c.RAW_DIR / name
    return raw if raw.exists() else FINAL_DIR / name


def archive(sources: list[Path]) -> None:
    """Mirror the chosen artworks into final/: copy new or changed files, drop the ones no longer chosen."""
    FINAL_DIR.mkdir(exist_ok=True)
    keep = {p.name for p in sources}
    for src in sources:
        dst = FINAL_DIR / src.name
        if src.parent != FINAL_DIR and (not dst.exists() or dst.read_bytes() != src.read_bytes()):
            shutil.copy2(src, dst)
    for old in FINAL_DIR.glob("*.png"):
        if old.name not in keep:
            old.unlink()


def save_webp(img: Image.Image, stem: str, quality: int, full_quality: int | None = None) -> dict[str, int]:
    sizes = {}
    for name, size in SIZES.items():
        q = full_quality if (name == "full" and full_quality) else quality
        out = CARDS_OUT / name / f"{stem}.webp"
        out.parent.mkdir(parents=True, exist_ok=True)
        im = img if img.size == size else img.resize(size, Image.LANCZOS)
        im.save(out, "WEBP", quality=q, method=6)
        sizes[name] = out.stat().st_size
    return sizes


def manifest_entry(card: dict, stem: str) -> dict:
    entry = {k: v for k, v in card.items() if k not in DROP}
    entry["arcana"] = "minor" if "suit" in card else "major"
    entry["images"] = {name: f"cards/{name}/{stem}.webp" for name in SIZES}
    return entry


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--quality", type=int, default=85, help="WebP の品質（既定 85）")
    ap.add_argument("--full-quality", type=int, default=None, help="full サイズだけの品質（既定は --quality と同じ）")
    args = ap.parse_args()

    cards = c.load_cards()
    selected = json.loads(c.SELECTED_PATH.read_text(encoding="utf-8"))
    missing = [i for i in range(78) if i not in cards or str(i) not in selected]
    if missing:
        sys.exit(f"カード定義または採用案がありません: {missing}")

    frame = Image.open(c.FRAME_PATH).convert("RGB")
    mask = c.detect_window(frame)
    bbox = c.bbox_of(mask)
    c.check_bbox(bbox)

    report, manifest, total, sources = [], [], 0, []
    for cid in range(78):
        card, variant = cards[cid], selected[str(cid)]
        src = source_path(card, variant)
        if not src.exists():
            sys.exit(f"採用案の画像がありません: {src.name}")
        sources.append(src)
        with Image.open(src) as art:
            face = c.composite(frame, art, mask, bbox)
        stem = f"{cid:02d}"
        sizes = save_webp(face, stem, args.quality, args.full_quality)
        total += sum(sizes.values())
        manifest.append(manifest_entry(card, stem))
        report.append({"id": cid, "slug": card["slug"], "variant": variant, "source": src.name,
                       "source_mtime": datetime.fromtimestamp(src.stat().st_mtime, JST).isoformat(timespec="seconds"),
                       "bytes": sizes})
        print(f"[OK] {cid:02d} {card['slug']:<22} <- {src.name}", flush=True)

    with Image.open(BACK) as back:
        sizes = save_webp(back.convert("RGB"), "back", args.quality, args.full_quality)
    total += sum(sizes.values())
    report.append({"id": "back", "source": f"refs/{BACK.name}", "bytes": sizes})

    archive(sources)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"quality": args.quality, "full_quality": args.full_quality or args.quality,
                                  "total_bytes": total, "cards": report},
                                 ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    by_size = {n: sum(r["bytes"][n] for r in report) for n in SIZES}
    print(f"\n合計 {total / 1e6:.1f} MB（" + "、".join(f"{n} {b / 1e6:.1f} MB" for n, b in by_size.items()) + "）")
    print(f"マニフェスト: {MANIFEST.relative_to(REPO).as_posix()}（{len(manifest)} 件）")


if __name__ == "__main__":
    main()
