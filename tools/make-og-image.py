#!/usr/bin/env python3
"""Generate the 1200x630 social-preview (og-image) card for sphinx-doc.org.

Pillow-only, byte-reproducible. Run from the repo root:

    python3 tools/make-og-image.py

Writes doc/_static/og-image.png.
"""

from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
OUT = os.path.join('doc', '_static', 'og-image.png')
LOGO = os.path.join('doc', '_static', 'sphinx.png')

FONT_CANDIDATES = (
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
)

# Sphinx brand palette (from sphinx13 theme / sphinx-doc.org)
ACCENT = (0, 132, 150)  # teal
DARK = (32, 40, 48)  # near-black text
GROUND = (255, 255, 255)  # white ground
PILL_BG = (232, 245, 247)  # light teal pill
PILL_FG = (0, 100, 115)  # pill text
MUTED = (90, 100, 110)  # tagline grey


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def find_font() -> str:
    for cand in FONT_CANDIDATES:
        if os.path.exists(cand):
            return cand
    raise SystemExit(MSG_NO_FONT)


MSG_NO_FONT = 'no DejaVu font found'


def wrap(
    d: ImageDraw.ImageDraw,
    text: str,
    f: ImageFont.FreeTypeFont,
    max_w: int,
) -> list[str]:
    """Wrap *text* to fit *max_w* pixels using font *f*.

    Splits on whitespace and returns lines that each fit within ``max_w``
    when measured with ``d.textlength``.
    """
    words = text.split()
    lines: list[str] = []
    cur = ''
    for w_ in words:
        trial = (cur + ' ' + w_).strip()
        if d.textlength(trial, font=f) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def main() -> None:
    base = find_font()
    f_bold = font(base, 78)
    f_sub = font(base, 36)
    f_pill = font(base, 34)

    img = Image.new('RGB', (W, H), GROUND)
    d = ImageDraw.Draw(img)

    # Accent bar along the top
    d.rectangle([0, 0, W, 18], fill=ACCENT)

    # Wordmark / logo
    logo = Image.open(LOGO).convert('RGBA')
    logo_w = 520
    logo_h = int(logo.height * logo_w / logo.width)
    logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
    img.paste(logo, (80, 60), logo)

    # Domain chip (top-right, clear of logo and headline)
    chip = 'sphinx-doc.org'
    tw = d.textlength(chip, font=f_pill)
    pad = 24
    cx0, cy0 = W - 80 - tw - 2 * pad, 60
    d.rounded_rectangle(
        [cx0, cy0, cx0 + tw + 2 * pad, cy0 + 60], radius=30, fill=PILL_BG
    )
    d.text((cx0 + pad, cy0 + 12), chip, font=f_pill, fill=PILL_FG)

    # Headline (wrapped, two lines)
    head_lines = wrap(d, 'Documentation that works for your project', f_bold, W - 160)
    y = 250
    for ln in head_lines:
        d.text((80, y), ln, font=f_bold, fill=DARK)
        y += 96

    # Tagline (wrapped, two lines)
    tag = (
        'Sphinx is a tool that makes it easy to create intelligent and '
        'beautiful documentation for Python projects.'
    )
    tag_lines = wrap(d, tag, f_sub, W - 160)
    y = 500
    for ln in tag_lines:
        d.text((80, y), ln, font=f_sub, fill=MUTED)
        y += 48

    img.save(OUT)
    sys.stdout.write(f'wrote {OUT} ({img.size[0]}x{img.size[1]})\n')


if __name__ == '__main__':
    main()
