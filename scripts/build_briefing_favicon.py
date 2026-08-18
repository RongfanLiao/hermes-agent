#!/usr/bin/env python3
"""Generate the Briefing Agent favicon — a capital B on a dark rounded square.

Two artifacts, because two different pages need them:

  web/public/favicon.svg  the SPA declares this; crisp at any size
  web/public/favicon.ico  what browsers request by default, and what the
                          server-rendered login page gets (it declares no
                          icon, so the browser falls back to /favicon.ico)

The dark plate is deliberate. A bare light glyph on transparent vanishes
against a light tab bar, and a bare dark glyph vanishes against a dark one;
the plate makes the mark legible on both.

Usage:
    python scripts/build_briefing_favicon.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "web" / "public"

PLATE = (17, 20, 24, 255)      # near-black, reads as a plate on light tabs
GLYPH = (230, 237, 243, 255)   # the skin's banner_title tone
ICO_SIZES = [16, 32, 48, 64, 128, 256]
TARGET_INK = 0.62   # drawn height of the B as a fraction of the plate

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _font(px: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if Path(path).is_file():
            return ImageFont.truetype(path, px)
    raise SystemExit("no bold sans font found; install fonts-dejavu-core")


def render(size: int) -> Image.Image:
    """Draw one square icon at `size` px.

    Supersampled 4x then downscaled — at 16px the rounded corners and the
    glyph's bowls alias badly when drawn directly.
    """
    s = size * 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.22), fill=PLATE)

    # Size by measured ink, not by nominal em: a capital's cap-height is only
    # ~0.7 em, so asking for 0.74 em yields a glyph filling barely half the
    # plate. Converge on the point size whose drawn bbox hits TARGET_INK, then
    # centre on that same bbox (DejaVu's ascent/descent are asymmetric, so
    # centring on the em box leaves the B sitting high).
    px = int(s * TARGET_INK)
    for _ in range(4):
        font = _font(px)
        l, t, r, b = d.textbbox((0, 0), "B", font=font)
        h = b - t
        if h <= 0:
            break
        scaled = int(px * (s * TARGET_INK) / h)
        if scaled == px:
            break
        px = max(1, scaled)

    font = _font(px)
    l, t, r, b = d.textbbox((0, 0), "B", font=font)
    d.text(((s - (r - l)) / 2 - l, (s - (b - t)) / 2 - t), "B", font=font, fill=GLYPH)

    return img.resize((size, size), Image.LANCZOS)


SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#111418"/>
  <path fill="#e6edf3" d="M20 14h14.5c6.1 0 10 3.2 10 8.4 0 3.5-1.9 6-5 7.1v.3c4 .9 6.4 3.7
    6.4 7.9 0 5.9-4.3 9.3-11.4 9.3H20V14zm7.3 5.6v7.9h5.2c3 0 4.7-1.4 4.7-4 0-2.5-1.7-3.9-4.6-3.9h-5.3zm0
    13.1v8.7h6c3.3 0 5.1-1.5 5.1-4.4 0-2.8-1.9-4.3-5.3-4.3h-5.8z"/>
</svg>
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    frames = [render(n) for n in ICO_SIZES]
    ico = OUT / "favicon.ico"
    frames[-1].save(ico, format="ICO", sizes=[(n, n) for n in ICO_SIZES])
    print(f"wrote {ico.relative_to(REPO)}  ({', '.join(f'{n}x{n}' for n in ICO_SIZES)})")

    svg = OUT / "favicon.svg"
    svg.write_text(SVG, encoding="utf-8")
    print(f"wrote {svg.relative_to(REPO)}")

    png = OUT / "apple-touch-icon.png"
    render(180).save(png, format="PNG")
    print(f"wrote {png.relative_to(REPO)}  (180x180)")


if __name__ == "__main__":
    main()
