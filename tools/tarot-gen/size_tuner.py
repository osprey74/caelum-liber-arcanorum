"""Local server for size_tuner.html: pick the size and height of the Wands / Swords pip layouts by eye.

    python size_tuner.py            # then open http://127.0.0.1:8765/
    python size_tuner.py --port 9000

The previews are rendered by layout.py itself (same code path as the final output), so what you see is
what `python layout.py` produces. "Save" writes the values to layout_config.json -> {suit}.size and keeps
a backup of the previous file in out/review/layout_config.backup.json.

Endpoints (127.0.0.1 only):
  GET  /                                  size_tuner.html
  GET  /api/state                         saved sizes {"swords": {"2": {"scale": s, "dy": d}, ...}, "wands": ...}
  GET  /api/render?suit=&rank=&scale=&dy=&ref=   framed card (base64 PNG) + constraint warnings
  GET  /api/cups?rank=                    framed cups card of the same rank (base64 PNG)
  POST /api/save                          body: same shape as /api/state
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import shutil
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

try:
    import cv2  # noqa: F401  (needed by composite / layout)
    import numpy  # noqa: F401
    from PIL import Image
except ModuleNotFoundError as e:
    sys.exit(f"{e.name} が見つかりません（実行中の Python: {sys.executable}）。\n"
             "Pillow・numpy・opencv-python の入った Python で起動してください。例: py -3.11 size_tuner.py\n"
             "または、この Python に入れる場合: python -m pip install pillow numpy opencv-python")

import composite
import layout

ROOT = layout.ROOT
HTML = ROOT / "size_tuner.html"
BACKUP = ROOT / "out" / "review" / "layout_config.backup.json"
PREVIEW = (512, 768)          # size of the framed preview sent to the page
SUITS = ("swords", "wands")
DEFAULT = {"scale": 1.0, "dy": 0.0}

_lock = threading.Lock()      # PIL / numpy work is done one request at a time
_cache: dict = {}


def resources() -> dict:
    if not _cache:
        chosen = json.loads(layout.SELECTED_ASSETS_PATH.read_text(encoding="utf-8"))
        frame = Image.open(composite.FRAME_PATH).convert("RGB")
        mask = composite.detect_window(frame)
        _cache.update(frame=frame, mask=mask, bbox=composite.bbox_of(mask), visible=layout.visible_region())
        for suit in SUITS:
            names = {"bg": f"bg_{suit}", **layout.CROSSED_ASSETS[suit]}
            imgs = {role: Image.open(layout.ASSETS_DIR / f"{n}_{chosen[n]}.png").copy() for role, n in names.items()}
            _cache[suit] = (imgs.pop("bg"), imgs)
        _cache["cards"] = {(c["suit"], c["rank"]): c
                           for c in json.loads(layout.CARDS_MINOR_PATH.read_text(encoding="utf-8"))}
    return _cache


def framed_png(raw: Image.Image) -> str:
    r = resources()
    card = composite.composite(r["frame"], raw, r["mask"], r["bbox"]).resize(PREVIEW, Image.LANCZOS)
    buf = io.BytesIO()
    card.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def render(suit: str, rank: int, scale: float, dy: float, ref: float) -> dict:
    r = resources()
    cfg = layout.suit_config(suit, layout.load_config())
    bg, extras = r[suit]
    img, _, warnings, (window_px, bottom_px) = layout.crossed_card(
        bg, suit, rank, extras, cfg, r["visible"], scale, dy, ref)
    return {"image": framed_png(img), "warnings": warnings, "window_px": window_px, "bottom_px": bottom_px}


def cups(rank: int) -> dict:
    card = resources()["cards"][("cups", rank)]
    raw = Image.open(layout.RAW_DIR / f"{card['id']:02d}_{card['slug']}_{layout.LAYOUT_VARIANT}.png")
    return {"image": framed_png(raw)}


def state() -> dict:
    config = layout.load_config()
    out = {}
    for suit in SUITS:
        sizes = config.get(suit, {}).get("size") or {}
        out[suit] = {str(r): {**DEFAULT, **sizes.get(str(r), {})} for r in range(2, 11)}
    return out


def save(data: dict) -> dict:
    path = layout.LAYOUT_CONFIG_PATH
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, BACKUP)
    config = json.loads(path.read_text(encoding="utf-8"))
    for suit in SUITS:
        sizes = {}
        for r in range(2, 11):
            v = data[suit][str(r)]
            sizes[str(r)] = {"scale": round(float(v["scale"]), 3), "dy": round(float(v["dy"]), 3)}
        config.setdefault(suit, {})["size"] = sizes
        config[suit]["size_note"] = ("scale: 光背の円の中心を基準とする拡大率、dy: 上下位置（R 単位、下向きが正）。"
                                     "size_tuner.html で総司が目視で決定")
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"saved": str(path.relative_to(ROOT)), "backup": str(BACKUP.relative_to(ROOT))}


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if url.path in ("/", "/size_tuner.html"):
                body = HTML.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif url.path == "/api/state":
                self._json(state())
            elif url.path == "/api/render":
                with _lock:
                    self._json(render(q["suit"], int(q["rank"]), float(q["scale"]), float(q["dy"]),
                                      float(q["ref"])))
            elif url.path == "/api/cups":
                with _lock:
                    self._json(cups(int(q["rank"])))
            else:
                self._json({"error": "not found"}, 404)
        except Exception as e:  # report to the page instead of dropping the connection
            self._json({"error": repr(e)}, 500)

    def do_POST(self):
        if urlparse(self.path).path != "/api/save":
            return self._json({"error": "not found"}, 404)
        try:
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8"))
            with _lock:
                self._json(save(data))
        except Exception as e:
            self._json({"error": repr(e)}, 500)

    def log_message(self, fmt, *args):  # keep the console quiet
        pass


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args()
    print("素材を読み込んでいます…", flush=True)
    resources()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"ブラウザで http://127.0.0.1:{args.port}/ を開いてください（終了は Ctrl+C）", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
