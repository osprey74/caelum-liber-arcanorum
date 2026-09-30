"""Tarot card artwork generator (Codex CLI built-in image_gen backend).

Generates the central artwork for each card by driving the official OpenAI
Codex CLI (`codex exec` + `$imagegen`) signed in with a ChatGPT account.
No OPENAI_API_KEY is used or read.

Usage examples:
  python generate.py --dry-run
  python generate.py --only 0,17 --variants 2
  python generate.py --variants 2 --max-images 20 --exclude 17
  python generate.py --cards cards_minor.json --variants 3     # aces and court cards (method "ai")
  python generate.py --assets --variants 3                     # suit symbols and backgrounds for pip cards
  python generate.py --assets --only wands,bg_cups
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
CARDS_PATH = ROOT / "cards.json"
STYLE_PATH = ROOT / "style.txt"
STYLE_ASSET_PATH = ROOT / "style_asset.txt"
STYLE_REF = ROOT / "refs" / "style_ref.png"
RAW_DIR = ROOT / "out" / "raw"
ASSETS_DIR = ROOT / "assets"
LOG_PATH = ROOT / "out" / "log.jsonl"
FAILURES_PATH = ROOT / "out" / "failures.json"

VARIANT_LETTERS = "abcdefghij"
EXPECTED_SIZE = (1024, 1536)
MAX_PARALLEL = 2
MAX_RETRIES = 3
CODEX_TIMEOUT_SEC = 600
# Measured on 2026-09-30 (ChatGPT Team, 10 images): ~0.9% of the 5-hour window and ~0.1% of the weekly window per image.
DEFAULT_QUOTA_PER_IMAGE = 0.9
JST = timezone(timedelta(hours=9))

# Patterns in Codex output that indicate the whole run should stop.
QUOTA_PATTERNS = re.compile(r"usage limit|rate limit reached|quota|try again (in|at)", re.I)
# Transient errors worth retrying.
TRANSIENT_PATTERNS = re.compile(r"\b(429|500|502|503|504)\b|timed out|timeout|connection|stream error", re.I)
# Codex fell back to the API-key CLI path instead of the built-in tool.
FALLBACK_PATTERNS = re.compile(r"OPENAI_API_KEY", re.I)
# Content moderation refusals: do not retry.
REFUSAL_PATTERNS = re.compile(r"safety|content polic|moderation|can(no|')t (help|create|generate)|refus", re.I)

STYLE_REF_PREAMBLE = """Use the attached image ONLY as a style reference (line, color, texture, level of detail).
Do not copy its composition or subject."""

CARD_PROMPT_TEMPLATE = STYLE_REF_PREAMBLE + """

{style}

[CARD]
Title (do not write it): {name_en}
Subject: {subject}
Key symbols: {symbols}
Astrological accent: {astro_accent}, woven subtly into the halo pattern as imagery, not as written symbols."""

SUITS = ("wands", "cups", "swords", "pentacles")
SUIT_SYMBOLS = {
    "wands": "sturdy, thick wooden staff with a bold silhouette, small sprouting leaves and gold fittings",
    "cups": "ornate golden chalice with Art Nouveau engraving",
    "swords": "straight double-edged sword with an ornate gold hilt, point up",
    "pentacles": "round golden disc engraved with a five-pointed star inside a circle, lily ornament on the rim",
}
# Extra transparent assets for the crossed wands/swords layouts (handoff-pips-crossed-layout.md).
EXTRA_SYMBOLS = {
    "symbol_swords_curved": "gently curved single-edged saber with a golden hilt, hilt at the bottom and point at the top, "
                            "the blade bowing in a smooth arc toward the right side",
    "symbol_wands_long": "long, slender, perfectly straight wooden staff, about twelve times as tall as it is wide, "
                         "with small sprouting leaves at both ends and gold fittings",
    "rosette": "small golden lily flower ornament, a compact round Art Nouveau rosette seen from the front",
}
SUIT_MOTIFS = {
    "wands": "sunflowers, flames and salamander-like curls",
    "cups": "water lilies and gentle waves",
    "swords": "clouds, feathers and butterflies",
    "pentacles": "grape vines, wheat and roses",
}

SYMBOL_PROMPT_TEMPLATE = STYLE_REF_PREAMBLE + """

{style}

[ASSET]
A single {symbol} drawn as an isolated ornamental object, centered, upright, vertical orientation,
occupying about 80% of the image height, on a plain transparent background.
No figure, no hand, no scenery, no halo, no shadow on the background."""

BACKGROUND_PROMPT_TEMPLATE = STYLE_REF_PREAMBLE + """

{style}

[ASSET]
Vertical 2:3 decorative background panel for the {suit_title} suit: large circular halo disc with fine geometric
and floral patterns, symmetrical botanical ornaments ({motif}), night sky in deep navy.
The central area must stay calm and uncluttered (symbols will be placed on top later).
Keep important ornaments away from the bottom 10% and from the upper-left and upper-right corners
(the image will be cropped into a rounded arch).
No figure, no objects in the center, no text."""

CODEX_WRAPPER_TEMPLATE = """$imagegen Use the BUILT-IN image_gen tool (default mode). Do NOT use the CLI fallback or scripts/image_gen.py; no OPENAI_API_KEY is available and none is needed.
The attached image (refs/style_ref.png) is a STYLE REFERENCE only.
Make exactly ONE image_gen call, portrait 2:3 (1024x1536){transparent}, with the image prompt below verbatim. Then copy the generated file from $CODEX_HOME/generated_images/... to {out} (relative to the current working directory; do not overwrite if it exists). Do not edit any other files. Reply only with the saved path and the image's pixel size.

--- IMAGE PROMPT (verbatim) ---
{image_prompt}
"""
TRANSPARENT_CLAUSE = ", with a genuinely TRANSPARENT background (preserve the alpha channel)"


@dataclass
class Job:
    path: Path
    image_prompt: str
    transparent: bool = False
    log_fields: dict = field(default_factory=dict)

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def rel(self) -> str:
        return self.path.relative_to(ROOT).as_posix()


def build_card_prompt(card: dict, style: str) -> str:
    # glyph is app-side metadata and must not be sent.
    return CARD_PROMPT_TEMPLATE.format(
        style=style,
        name_en=card["name_en"],
        subject=card["subject"],
        symbols=card["symbols"],
        astro_accent=card["astro_accent"],
    )


def build_codex_prompt(job: Job) -> str:
    return CODEX_WRAPPER_TEMPLATE.format(
        out=job.rel,
        transparent=TRANSPARENT_CLAUSE if job.transparent else "",
        image_prompt=job.image_prompt,
    )


def parse_list(value: str | None) -> set[str] | None:
    if not value:
        return None
    return {x.strip() for x in value.split(",") if x.strip()}


def plan_card_jobs(cards: list[dict], style: str, variants: int, only: set[str] | None,
                   exclude: set[str] | None) -> list[Job]:
    """Ordered variant-major: all 'a' first, then 'b', ..."""
    targets = [c for c in cards
               if c.get("method", "ai") == "ai"
               and (only is None or str(c["id"]) in only)
               and (exclude is None or str(c["id"]) not in exclude)]
    jobs = []
    for letter in VARIANT_LETTERS[:variants]:
        for card in targets:
            jobs.append(Job(
                path=RAW_DIR / f"{card['id']:02d}_{card['slug']}_{letter}.png",
                image_prompt=build_card_prompt(card, style),
                log_fields={"card_id": card["id"], "slug": card["slug"], "variant": letter},
            ))
    return jobs


def plan_asset_jobs(style_asset: str, variants: int, only: set[str] | None,
                    exclude: set[str] | None) -> list[Job]:
    """Suit symbols (transparent) and suit backgrounds for layout-based pip cards."""
    def wanted(name: str, suit: str) -> bool:
        if only is not None and name not in only and suit not in only:
            return False
        return exclude is None or (name not in exclude and suit not in exclude)

    jobs = []
    for letter in VARIANT_LETTERS[:variants]:
        for suit in SUITS:
            for kind in ("symbol", "bg"):
                name = f"{kind}_{suit}"
                if not wanted(name, suit):
                    continue
                if kind == "symbol":
                    prompt = SYMBOL_PROMPT_TEMPLATE.format(style=style_asset, symbol=SUIT_SYMBOLS[suit])
                else:
                    prompt = BACKGROUND_PROMPT_TEMPLATE.format(
                        style=style_asset, suit_title=suit.capitalize(), motif=SUIT_MOTIFS[suit])
                jobs.append(Job(
                    path=ASSETS_DIR / f"{name}_{letter}.png",
                    image_prompt=prompt,
                    transparent=kind == "symbol",
                    log_fields={"asset": name, "variant": letter},
                ))
    for letter in VARIANT_LETTERS[:variants]:
        for name, desc in EXTRA_SYMBOLS.items():
            if only is None or name not in only:
                continue  # extra assets are generated only when named explicitly
            if exclude is not None and name in exclude:
                continue
            jobs.append(Job(
                path=ASSETS_DIR / f"{name}_{letter}.png",
                image_prompt=SYMBOL_PROMPT_TEMPLATE.format(style=style_asset, symbol=desc),
                transparent=True,
                log_fields={"asset": name, "variant": letter},
            ))
    return jobs


_log_lock = threading.Lock()


def append_log(entry: dict) -> None:
    with _log_lock:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def find_codex() -> str:
    exe = shutil.which("codex.cmd") or shutil.which("codex")
    if not exe:
        sys.exit("codex CLI が見つかりません。`npm i -g @openai/codex` でインストールしてください。")
    return exe


def run_codex_once(codex: str, prompt: str, timeout: int) -> tuple[int, str, str]:
    """Run one `codex exec`. Returns (returncode, combined_output, last_message)."""
    with tempfile.TemporaryDirectory() as td:
        last_msg_path = Path(td) / "last.txt"
        cmd = [
            codex, "exec",
            "--skip-git-repo-check",
            "-s", "workspace-write",
            f"--image={STYLE_REF.relative_to(ROOT).as_posix()}",
            "-o", str(last_msg_path),
        ]
        # Prompt goes via stdin (no positional arg), since --image is greedy.
        proc = subprocess.run(
            cmd, input=prompt, cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
        last = last_msg_path.read_text(encoding="utf-8", errors="replace") if last_msg_path.exists() else ""
        return proc.returncode, (proc.stdout or "") + (proc.stderr or ""), last


def parse_tokens(output: str) -> int | None:
    m = re.search(r"tokens used\s*\n\s*([\d,]+)", output)
    return int(m.group(1).replace(",", "")) if m else None


def generate_one(job: Job, codex: str, timeout: int, stop_event: threading.Event) -> dict:
    prompt = build_codex_prompt(job)
    entry = {
        **job.log_fields,
        "backend": "codex-cli built-in image_gen",
        "model": "gpt-image-2 (codex built-in)",
        "quality": "default (built-in; not selectable)",
        "transparent": job.transparent,
        "prompt": prompt,
        "output": job.rel,
    }
    error = None
    for attempt in range(1, MAX_RETRIES + 1):
        if stop_event.is_set():
            error = "skipped: run stopped (quota)"
            break
        started = time.time()
        entry["attempt"] = attempt
        try:
            rc, output, last = run_codex_once(codex, prompt, timeout)
        except subprocess.TimeoutExpired:
            rc, output, last = -1, "timeout", ""
        elapsed = round(time.time() - started, 1)
        entry.update(elapsed_sec=elapsed, tokens_used=parse_tokens(output), codex_reply=last.strip()[:500])

        created = job.path.exists() and job.path.stat().st_mtime >= started - 1
        if created:
            with Image.open(job.path) as im:
                entry["size"] = f"{im.width}x{im.height}"
                warnings = []
                if im.size != EXPECTED_SIZE:
                    warnings.append(f"unexpected size {im.width}x{im.height}")
                if job.transparent and "A" not in im.getbands():
                    warnings.append("no alpha channel")
                if warnings:
                    entry["warning"] = "; ".join(warnings)
            error = None
            break

        # Only inspect the reply and the log tail: the head echoes skill docs.
        text = f"{last}\n{output[-2000:]}"
        if QUOTA_PATTERNS.search(text):
            stop_event.set()
            error = "quota exhausted"
            break
        if FALLBACK_PATTERNS.search(last):
            error = "codex chose CLI fallback (OPENAI_API_KEY) instead of built-in image_gen"
        elif REFUSAL_PATTERNS.search(last):
            error = f"refused: {last.strip()[:300]}"
            break  # moderation refusals are not retried
        elif rc != 0 and TRANSIENT_PATTERNS.search(text):
            error = f"transient error (rc={rc})"
        else:
            error = f"no output file (rc={rc}): {last.strip()[:300]}"
        if attempt < MAX_RETRIES:
            time.sleep(2 ** attempt * 5)  # 10s, 20s

    entry["timestamp"] = datetime.now(JST).isoformat(timespec="seconds")
    entry["success"] = error is None
    if error:
        entry["error"] = error
    append_log(entry)
    return entry


def main() -> None:
    # Windows consoles default to cp932, which cannot print the prompt text.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Generate tarot artwork via Codex CLI built-in image_gen")
    ap.add_argument("--dry-run", action="store_true", help="プロンプトと枠消費の目安を表示するだけ")
    ap.add_argument("--cards", type=Path, default=CARDS_PATH, help="カード定義ファイル（既定 cards.json）")
    ap.add_argument("--assets", action="store_true", help="数札用の素材（スート記号・背景）を生成する")
    ap.add_argument("--only", help="対象（カードID、または素材名・スート名。例：0,17 / wands,bg_cups）")
    ap.add_argument("--exclude", help="除外する対象（--only と同じ書式）")
    ap.add_argument("--variants", type=int, default=3, help="1点あたりの案数（既定3）")
    ap.add_argument("--max-images", type=int, default=None, help="この実行で生成する最大枚数")
    ap.add_argument("--parallel", type=int, default=1, help=f"並列数（1〜{MAX_PARALLEL}、既定1）")
    ap.add_argument("--force", action="store_true", help="既存の案を上書き再生成する")
    ap.add_argument("--yes", "-y", action="store_true", help="確認プロンプトを省略する")
    ap.add_argument("--quota-per-image", type=float, default=DEFAULT_QUOTA_PER_IMAGE,
                    help="5時間枠に対する1枚あたり消費%%の目安")
    ap.add_argument("--timeout", type=int, default=CODEX_TIMEOUT_SEC, help="1回の codex exec のタイムアウト秒")
    args = ap.parse_args()

    if not 1 <= args.variants <= len(VARIANT_LETTERS):
        sys.exit(f"--variants は 1〜{len(VARIANT_LETTERS)} で指定してください。")
    parallel = max(1, min(args.parallel, MAX_PARALLEL))
    only, exclude = parse_list(args.only), parse_list(args.exclude)

    if args.assets:
        required = (STYLE_ASSET_PATH, STYLE_REF)
    else:
        required = (args.cards, STYLE_PATH, STYLE_REF)
    for p in required:
        if not p.exists():
            sys.exit(f"必要なファイルがありません: {p}")

    if args.assets:
        style_asset = STYLE_ASSET_PATH.read_text(encoding="utf-8").strip()
        planned = plan_asset_jobs(style_asset, args.variants, only, exclude)
    else:
        style = STYLE_PATH.read_text(encoding="utf-8").strip()
        cards = json.loads(args.cards.read_text(encoding="utf-8"))
        planned = plan_card_jobs(cards, style, args.variants, only, exclude)

    skipped = [j for j in planned if j.path.exists() and not args.force]
    jobs = [j for j in planned if j not in skipped]
    if args.max_images is not None:
        jobs = jobs[: args.max_images]

    est = len(jobs) * args.quota_per_image
    print(f"生成予定: {len(jobs)} 枚（既存スキップ: {len(skipped)} 枚）")
    print(f"5時間枠消費の目安: 約 {est:.0f}%（1枚 {args.quota_per_image}% として。週枠は別途確認してください）")
    if jobs:
        print("対象: " + ", ".join(j.filename for j in jobs))

    if args.dry_run:
        shown = set()
        for job in jobs:
            if job.image_prompt in shown:  # variants share one prompt
                continue
            shown.add(job.image_prompt)
            print(f"\n===== {job.filename}{'（透過）' if job.transparent else ''} =====")
            print(job.image_prompt)
        return
    if not jobs:
        print("生成対象がありません。")
        return
    if not args.yes:
        if input("実行しますか？ [y/N] ").strip().lower() != "y":
            print("中止しました。")
            return

    codex = find_codex()
    for job in jobs:
        job.path.parent.mkdir(parents=True, exist_ok=True)
        if args.force:
            job.path.unlink(missing_ok=True)

    stop_event = threading.Event()
    results = []
    with ThreadPoolExecutor(max_workers=parallel) as pool:
        futures = {pool.submit(generate_one, j, codex, args.timeout, stop_event): j for j in jobs}
        for fut in as_completed(futures):
            job = futures[fut]
            try:
                r = fut.result()
            except Exception as e:  # keep going on unexpected errors
                r = {**job.log_fields, "output": job.rel, "success": False, "error": f"exception: {e!r}",
                     "timestamp": datetime.now(JST).isoformat(timespec="seconds")}
                append_log(r)
            results.append(r)
            mark = "OK " if r["success"] else "NG "
            detail = r.get("size", "") if r["success"] else r.get("error", "")
            if r.get("warning"):
                detail += f" 警告: {r['warning']}"
            print(f"[{mark}] {job.filename} {detail} ({r.get('elapsed_sec', '-')}s)", flush=True)

    keys = ("card_id", "slug", "asset", "variant", "output", "error", "timestamp")
    failures = [{k: r[k] for k in keys if k in r} for r in results if not r["success"]]
    FAILURES_PATH.write_text(json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(r["success"] for r in results)
    print(f"\n完了: 成功 {ok} / 失敗 {len(failures)}（{FAILURES_PATH.relative_to(ROOT).as_posix()}）")
    if stop_event.is_set():
        print("利用上限に達したため途中で停止しました。枠のリセット後に同じコマンドで再開できます。")


if __name__ == "__main__":
    main()
