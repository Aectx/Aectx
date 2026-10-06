#!/usr/bin/env python3
"""Isolate a portrait, boost local contrast, and composite it on white.

A flat or busy photo turns into a muddy ASCII blob. Three steps fix that:

1. Remove the background so only the subject remains.
2. CLAHE (local contrast) so facial highlights and shadows survive downsampling.
3. Composite onto pure white, then crop square around the subject. White maps
   to the blank end of the ASCII ramp, so the background prints as nothing.

    python scripts/prep_photo.py source-photo.jpg
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.jpg")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")


def main():
    cut = remove(Image.open(INP).convert("RGBA"))
    rgb = np.array(cut.convert("RGB"))
    alpha = np.array(cut.split()[-1])
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
    toned = clahe.apply(gray)

    subject = alpha > 128
    if subject.any():
        lo, hi = np.percentile(toned[subject], [2, 98])
        if hi > lo:
            toned = np.clip((toned.astype(np.float32) - lo) * (255.0 / (hi - lo)), 0, 255).astype(np.uint8)

    mask = cv2.GaussianBlur(alpha.astype(np.float32) / 255.0, (0, 0), 1.2)
    out = toned.astype(np.float32) * mask + 255.0 * (1.0 - mask)

    ys, xs = np.where(alpha > 20)
    if len(xs) == 0:
        raise SystemExit("no subject found after background removal")
    top, bottom = int(ys.min()), int(ys.max())
    height = bottom - top
    # the head is the upper part of the subject; ignore an outstretched arm
    head = alpha[top : top + max(1, int(height * 0.42)), :]
    hys, hxs = np.where(head > 20)
    head_left, head_right = int(hxs.min()), int(hxs.max())
    head_w = max(1, head_right - head_left)
    # Tight square on the head and shoulders. A full-body frame leaves the
    # face too small once it is downsampled to a character grid.
    margin = int(head_w * 0.08)
    content_top = max(0, top - margin)
    content_bottom = min(out.shape[0], bottom + margin)
    content_h = content_bottom - content_top
    side = content_h
    x0 = max(0, head_left - margin)
    if x0 + side > out.shape[1]:
        x0 = max(0, out.shape[1] - side)
    y0 = content_top
    side = min(side, out.shape[1] - x0, out.shape[0] - y0)
    canvas = np.full((side, side), 255, np.uint8)
    canvas[:, :] = out[y0 : y0 + side, x0 : x0 + side].astype(np.uint8)

    # A black suit below the collar turns into a solid block once it is
    # downsampled. Keep the frame on the head and shoulders instead.
    lower = canvas[int(canvas.shape[0] * 0.62) :]
    if lower.size and float(np.median(lower)) < 12:
        med = np.median(canvas, axis=1)
        lit = np.where(med > 40)[0]
        ink = np.where(canvas < 230)
        if len(lit) and len(ink[0]):
            top_i = max(0, int(ink[0].min()) - 6)
            bot_i = min(canvas.shape[0], int(lit.max()) + max(12, int(canvas.shape[0] * 0.06)))
            height = max(32, bot_i - top_i)
            cols = ink[1][(ink[0] >= top_i) & (ink[0] < top_i + height)]
            cx = int((cols.min() + cols.max()) / 2) if len(cols) else canvas.shape[1] // 2
            x_i = max(0, min(canvas.shape[1] - height, cx - height // 2))
            canvas = canvas[top_i : top_i + height, x_i : x_i + height]

    Image.fromarray(canvas, mode="L").save(OUT)
    print("wrote", OUT, canvas.shape)


if __name__ == "__main__":
    main()
