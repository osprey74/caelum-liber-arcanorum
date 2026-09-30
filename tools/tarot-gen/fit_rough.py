"""Register refs/sword_rough.png onto raw 1024x1536 card coordinates and extract the sword mask.

Used by trace_swords.py. (Its earlier role, fitting the X-unit table of handoff-swords-from-rough.md,
was dropped when handoff-swords-trace.md replaced the table with traced coordinates.)
"""
import json
import sys

import cv2
import numpy as np
from PIL import Image

import composite as c
import crossed
import layout
import review_rough as rr

# rough card pixel -> framed card pixel (measured with ORB + RANSAC on cards 2 and 10)
ROUGH_TO_FRAMED = np.float32([[2.562, 0.0, 12.8], [0.0, 2.562, 10.3]])
SIZE = (1024, 1536)


def framed_to_raw() -> np.ndarray:
    fr = Image.open(c.FRAME_PATH).convert("RGB")
    x0, y0, x1, y1 = c.bbox_of(c.detect_window(fr))
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    s = max(bw / SIZE[0], bh / SIZE[1])
    left = (round(SIZE[0] * s) - bw) // 2
    # framed = raw * s + (x0 - left, y0)  ->  raw = (framed - t) / s
    return np.float32([[1 / s, 0, -(x0 - left) / s], [0, 1 / s, -y0 / s]])


def compose(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Affine b after a."""
    A = np.vstack([a, [0, 0, 1]])
    B = np.vstack([b, [0, 0, 1]])
    return (B @ A)[:2].astype(np.float32)


def rough_mask(rank: int, bg_raw: np.ndarray, circle: crossed.Circle) -> np.ndarray:
    M = compose(ROUGH_TO_FRAMED, framed_to_raw())
    card = cv2.warpAffine(np.asarray(rr.rough_card(rank)), M, SIZE, flags=cv2.INTER_LINEAR)
    diff = np.abs(card.astype(int) - bg_raw.astype(int)).sum(axis=-1) > 90
    ys, xs = np.mgrid[0:SIZE[1], 0:SIZE[0]]
    inside = (xs - circle.cx) ** 2 + (ys - circle.cy) ** 2 <= (0.93 * circle.r) ** 2
    m = (diff & inside).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))   # drop stars / noise
    return cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
