#!/usr/bin/env python3
"""Neofetch-style info card. Edit scripts/profile.json, then rerun this.

Lines fade and slide in once, then hold. STATIC=1 writes a frozen frame.
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
OUT = os.path.join(ROOT, "info-card.svg")

with open(os.path.join(HERE, "profile.json")) as f:
    PROFILE = json.load(f)

STATIC = bool(os.environ.get("STATIC"))

W, H = 980, 880
BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
TEXT = "#e6edf3"
ACCENT = "#22d3ee"
GREEN = "#3fb950"
KEY = "#79c0ff"

COLORS = ["#ff5f56", "#ffbd2e", "#27c93f", "#22d3ee", "#a371f7", "#f778ba", "#39d353", "#f2cc60"]


def main():
    lines = PROFILE["lines"]
    prompt = PROFILE["prompt"]
    name = PROFILE["name"]
    login = PROFILE["login"]
    tagline = PROFILE.get("tagline", "")

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        "<defs>"
        f'<linearGradient id="ibg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/>'
        f"</linearGradient></defs>",
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#ibg)"/>',
        f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="30" x2="{W}" y2="30" stroke="{FRAME}"/>',
    ]
    for i, dot in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{22 + i * 16}" cy="15" r="5" fill="{dot}"/>')
    parts.append(
        f'<text x="{W / 2}" y="19" fill="{MUTED}" font-size="13" text-anchor="middle">'
        f'{html.escape(prompt)}: ~$ neofetch</text>'
    )

    y = 150
    header = [
        (f"{html.escape(name)}", TEXT, 28, "700"),
        (f"@{html.escape(login)}", ACCENT, 16, "400"),
    ]
    if tagline:
        header.append((html.escape(tagline), MUTED, 15, "400"))

    def row(content, delay, size=18):
        if STATIC:
            return content
        return (
            f'<g opacity="0">{content}'
            f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur="0.35s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" from="-14 0" to="0 0" '
            f'begin="{delay:.2f}s" dur="0.35s" fill="freeze"/>'
            f"</g>"
        )

    delay = 0.15
    for text, fill, size, weight in header:
        parts.append(
            row(
                f'<text x="48" y="{y}" fill="{fill}" font-size="{size}" font-weight="{weight}">{text}</text>',
                delay,
                size,
            )
        )
        y += size + 22
        delay += 0.18

    y += 18
    rule = f'<line x1="48" y1="{y}" x2="{48 + 320}" y2="{y}" stroke="{FRAME}"/>'
    parts.append(rule if STATIC else row(rule, delay))
    y += 72
    delay += 0.12

    key_w = 110
    for key, value in lines:
        content = (
            f'<text x="48" y="{y}" fill="{KEY}" font-size="18">{html.escape(key)}</text>'
            f'<text x="{48 + key_w}" y="{y}" fill="{TEXT}" font-size="18">{html.escape(value)}</text>'
        )
        parts.append(content if STATIC else row(content, delay))
        y += 64
        delay += 0.16

    y += 80
    swatch = []
    x = 48
    for color in COLORS:
        swatch.append(f'<rect x="{x}" y="{y}" width="28" height="18" rx="3" fill="{color}"/>')
        x += 34
    block = "".join(swatch)
    parts.append(block if STATIC else row(block, delay))

    y += 70
    foot = (
        f'<text x="48" y="{y}" fill="{MUTED}" font-size="14">'
        f'{html.escape(prompt)}:~$ <tspan fill="{GREEN}">echo $USER</tspan></text>'
    )
    parts.append(foot if STATIC else row(foot, delay + 0.2))
    cursor_x = 48 + len(f"{prompt}:~$ echo $USER ") * 14 * 0.62
    parts.append(
        f'<rect x="{cursor_x:.0f}" y="{y - 14}" width="9" height="16" fill="{GREEN}">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
        f'dur="1.1s" repeatCount="indefinite"/></rect>'
    )
    parts.append("</svg>")

    with open(OUT, "w") as f:
        f.write("".join(parts))
    print("wrote", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
