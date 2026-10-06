#!/usr/bin/env python3
"""Corrupt-alert warning panel plus the SYSTEM OVERRIDE banner.

Edit scripts/profile.json, then rerun. STATIC=1 writes a frozen frame.
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "info-card.svg")
BANNER = os.path.join(ROOT, "override.svg")

with open(os.path.join(HERE, "profile.json")) as f:
    PROFILE = json.load(f)

STATIC = bool(os.environ.get("STATIC"))

W, H = 980, 880
BG = "#050203"
FRAME = "#e10600"
MUTED = "#a34a4a"
TEXT = "#f2f2f2"
RED = "#ff1a1a"
DIM = "#7a181c"


def glitch_text(x, y, text, size, dx, delay, anchor="start", clip_id="gslice"):
    """Green SYSTEM OVERRIDE title: offset copies plus a fast sliced band."""
    green = "#39ff14"
    dim = "#0b3d12"
    hot = "#b6ff9a"
    body = (
        f'<text x="{x + dx}" y="{y}" fill="{dim}" font-size="{size}" font-weight="700" text-anchor="{anchor}">{text}</text>'
        f'<text x="{x - dx}" y="{y}" fill="{hot}" font-size="{size}" font-weight="700" opacity="0.8" text-anchor="{anchor}">{text}</text>'
        f'<text x="{x}" y="{y}" fill="{green}" font-size="{size}" font-weight="700" text-anchor="{anchor}">{text}</text>'
    )
    band_y = y - size * 0.72
    band_h = size * 0.28
    sliced = (
        f'<clipPath id="{clip_id}"><rect x="0" y="{band_y:.1f}" width="100%" height="{band_h:.1f}">'
        f'<animate attributeName="y" values="{band_y:.1f};{band_y + size * 0.45:.1f};{band_y + size * 0.15:.1f};{band_y:.1f}" '
        f'dur="0.7s" repeatCount="indefinite"/></rect></clipPath>'
        f'<g clip-path="url(#{clip_id})">'
        f'<text x="{x}" y="{y}" fill="{green}" font-size="{size}" font-weight="700" text-anchor="{anchor}">{text}</text>'
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="0 0; {dx * 2} 0; {-dx * 2} 0; {dx} 0; 0 0" dur="0.45s" repeatCount="indefinite"/>'
        f"</g>"
    )
    if STATIC:
        return f'<g transform="translate({dx // 2} 0)">{body}</g>'
    return (
        f"<g>{body}{sliced}"
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="0 0; {dx} 0; {-dx // 2} 0; 0 0" '
        f'begin="{delay:.2f}s" dur="1.4s" repeatCount="indefinite"/>'
        f"</g>"
    )


def row(content, delay):
    if STATIC:
        return content
    return (
        f'<g opacity="0">{content}'
        f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur="0.28s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" from="-18 0" to="0 0" '
        f'begin="{delay:.2f}s" dur="0.28s" fill="freeze"/>'
        f"</g>"
    )


def write_banner():
    title = html.escape(PROFILE.get("tagline") or "SYSTEM OVERRIDE")
    bw, bh = 1200, 108
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{bw}" height="{bh}" viewBox="0 0 {bw} {bh}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f'<rect width="{bw}" height="{bh}" fill="{BG}"/>',
        f'<rect x="1" y="1" width="{bw - 2}" height="{bh - 2}" fill="none" stroke="{FRAME}" stroke-width="2"/>',
        glitch_text(bw / 2, 68, title, 42, 8, 0.2, anchor="middle", clip_id="bannerSlice"),
        "</svg>",
    ]
    with open(BANNER, "w") as f:
        f.write("".join(parts))
    print("wrote", BANNER, os.path.getsize(BANNER), "bytes")


def main():
    write_banner()
    lines = PROFILE["lines"]
    name = html.escape(PROFILE["name"])
    login = html.escape(PROFILE["login"])

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f'<rect width="{W}" height="{H}" fill="{BG}"/>',
        f'<rect x="2" y="2" width="{W - 4}" height="{H - 4}" fill="none" stroke="{FRAME}" stroke-width="2"/>',
        f'<rect x="10" y="10" width="{W - 20}" height="{H - 20}" fill="none" stroke="{FRAME}" stroke-opacity="0.35"/>',
    ]
    parts.append(glitch_text(48, 150, "SYSTEM OVERRIDE", 34, 7, 0.4, clip_id="cardSlice"))
    parts.append(
        f'<text x="48" y="196" fill="{MUTED}" font-size="16">root@{login} // signal unstable</text>'
    )
    parts.append(f'<line x1="48" y1="230" x2="460" y2="230" stroke="{FRAME}" stroke-opacity="0.7"/>')

    y = 310
    delay = 0.3
    alert = {"TRACE", "FIREWALL"}
    for key, value in lines:
        value_fill = RED if key in alert else TEXT
        content = (
            f'<text x="48" y="{y}" fill="{MUTED}" font-size="22">{html.escape(key)}</text>'
            f'<text x="280" y="{y}" fill="{value_fill}" font-size="22" font-weight="700">{html.escape(value)}</text>'
        )
        parts.append(row(content, delay))
        y += 88
        delay += 0.22

    parts.append(
        f'<text x="48" y="760" fill="{RED}" font-size="16">IDENTITY LOCKED // {name}</text>'
    )
    parts.append(
        f'<rect x="48" y="778" width="14" height="18" fill="{RED}">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
        f'dur="1s" repeatCount="indefinite"/></rect>'
    )
    parts.append("</svg>")

    with open(OUT, "w") as f:
        f.write("".join(parts))
    print("wrote", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
