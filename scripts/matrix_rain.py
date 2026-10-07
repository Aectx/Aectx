"""Falling character columns, the same kind of rain as a matrix background.

GitHub will play the SMIL motion when the SVG is shown with an <img> tag.
"""
import random

GLYPHS = "0123456789ABCDEF"


def matrix_rain(width, height, spacing=32, opacity=0.22, prefix="rain", static=False, length=None):
    rng = random.Random(prefix)
    cols = max(6, int(width / spacing))
    parts = [
        f'<clipPath id="{prefix}Clip"><rect width="{width}" height="{height}"/></clipPath>',
        f'<g clip-path="url(#{prefix}Clip)">',
    ]
    for i in range(cols):
        x = int(spacing * 0.35 + i * spacing)
        count = length or rng.randint(8, 14)
        glyphs = [rng.choice(GLYPHS) for _ in range(count)]
        line_h = 15
        column_h = count * line_h
        tspans = []
        for j, ch in enumerate(glyphs):
            if j == 0:
                fill, op = "#d8ffe8", min(0.9, opacity + 0.45)
            else:
                fill, op = "#1f9d55", opacity
            dy = 0 if j == 0 else line_h
            tspans.append(
                f'<tspan x="{x}" dy="{dy}" fill="{fill}" opacity="{op:.2f}">{ch}</tspan>'
            )
        text = (
            f'<text y="0" font-size="13" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">'
            f'{"".join(tspans)}</text>'
        )
        start = -column_h - rng.randint(0, int(height))
        dur = 8 + (i % 6) * 1.6
        begin = (i * 0.41) % dur
        if static:
            parked = rng.randint(-column_h, int(height))
            parts.append(f'<g transform="translate(0 {parked})">{text}</g>')
            continue
        parts.append(
            f"<g>{text}"
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="0 {start}" to="0 {int(height) + 8}" '
            f'begin="{begin:.2f}s" dur="{dur:.1f}s" repeatCount="indefinite"/>'
            f"</g>"
        )
    parts.append("</g>")
    return "".join(parts)
