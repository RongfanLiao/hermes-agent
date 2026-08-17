#!/usr/bin/env python3
"""Generate ``skins/briefing.yaml`` — the Briefing Agent brand skin.

The skin carries two pieces of generated ASCII art plus the branded agent
name. Everything else inherits from the built-in ``mono`` palette, so the
fork keeps upstream's greyscale look and only the wordmark changes.

Why a generator instead of a hand-edited YAML: both artworks have
invariants that are easy to break by hand and silent when broken —

* the wordmark must use the same ANSI Shadow letterforms as upstream's
  ``ui-tui/src/banner.ts`` (verified here by rebuilding HERMES-AGENT and
  diffing against the real ``LOGO_ART``);
* the hero art must stay 15 rows, or the banner's two-column grid loses
  its height alignment;
* the hero's width feeds ``leftW = min(artWidth + 4, cols * 0.4)`` in
  ``ui-tui/src/components/branding.tsx``. Above 36 columns the art gets
  truncated on a 100-column terminal.

Usage::

    python scripts/build_briefing_skin.py            # write skins/briefing.yaml
    python scripts/build_briefing_skin.py --install  # also copy to ~/.hermes/skins/

After installing, activate with ``hermes skin use briefing``.
"""
from __future__ import annotations

import argparse
import math
import re
import shutil
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SKIN_NAME = "briefing"
AGENT_NAME = "Briefing Agent"
WORDMARK = "BRIEFING-AGENT"

# --------------------------------------------------------------------------
# Wordmark (banner_logo)
# --------------------------------------------------------------------------

# ANSI Shadow letterforms. Only the glyphs the wordmark needs, plus the ones
# required to reconstruct HERMES-AGENT for the self-check below.
GLYPHS: dict[str, list[str]] = {
    "A": [" █████╗ ", "██╔══██╗", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    "B": ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██████╔╝", "╚═════╝ "],
    "E": ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "███████╗", "╚══════╝"],
    "F": ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "██║     ", "╚═╝     "],
    "G": [" ██████╗ ", "██╔════╝ ", "██║  ███╗", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
    "H": ["██╗  ██╗", "██║  ██║", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    "I": ["██╗", "██║", "██║", "██║", "██║", "╚═╝"],
    "M": ["███╗   ███╗", "████╗ ████║", "██╔████╔██║", "██║╚██╔╝██║", "██║ ╚═╝ ██║", "╚═╝     ╚═╝"],
    "N": ["███╗   ██╗", "████╗  ██║", "██╔██╗ ██║", "██║╚██╗██║", "██║ ╚████║", "╚═╝  ╚═══╝"],
    "R": ["██████╗ ", "██╔══██╗", "██████╔╝", "██╔══██╗", "██║  ██║", "╚═╝  ╚═╝"],
    "S": ["███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝"],
    "T": ["████████╗", "╚══██╔══╝", "   ██║   ", "   ██║   ", "   ██║   ", "   ╚═╝   "],
    "-": ["      ", "      ", "█████╗", "╚════╝", "      ", "      "],
}


def render_wordmark(text: str) -> list[str]:
    rows = [""] * 6
    for ch in text.upper():
        glyph = GLYPHS[ch]
        for i in range(6):
            rows[i] += glyph[i]
    return rows


def assert_glyphs_match_upstream() -> None:
    """Rebuild HERMES-AGENT and diff it against ui-tui's real LOGO_ART.

    Catches drift if upstream ever redraws the wordmark: a mismatch means
    the letterforms here no longer belong to the same typeface.
    """
    banner = REPO / "ui-tui/src/banner.ts"
    if not banner.is_file():
        print(f"  skip glyph self-check ({banner} not found)", file=sys.stderr)
        return
    block = re.search(r"const LOGO_ART = \[(.*?)\n\]", banner.read_text("utf-8"), re.S)
    if not block:
        print("  skip glyph self-check (LOGO_ART not parseable)", file=sys.stderr)
        return
    upstream = re.findall(r"'([^']*)'", block.group(1))
    ours = render_wordmark("HERMES-AGENT")
    if upstream != ours:
        raise SystemExit(
            "glyph table no longer reproduces ui-tui/src/banner.ts LOGO_ART — "
            "upstream changed the typeface; update GLYPHS before regenerating."
        )


# --------------------------------------------------------------------------
# Hero mark (banner_hero): a circle crossed by a horizontal line
# --------------------------------------------------------------------------

# Braille cells are 2 dots wide x 4 tall and render at roughly 1:2, so a dot
# is square — a 60x60 dot canvas draws a true circle, not an ellipse.
DOT_BIT = {
    (0, 0): 0x01, (0, 1): 0x02, (0, 2): 0x04, (0, 3): 0x40,
    (1, 0): 0x08, (1, 1): 0x10, (1, 2): 0x20, (1, 3): 0x80,
}
BLANK = "⠀"

CANVAS_CELLS = 36          # working width; trimmed down after drawing
CANVAS_DOTS_H = 60
RADIUS = 27.0
LINE_OVERHANG = 8          # dots the rule extends past the circle, per side
MAX_ART_WIDTH = 36         # artWidth + 4 must stay under the cols*0.4 cap


def render_hero() -> list[str]:
    width = CANVAS_CELLS * 2
    cx, cy = (width - 1) / 2.0, (CANVAS_DOTS_H - 1) / 2.0
    dots = [[0] * width for _ in range(CANVAS_DOTS_H)]

    for y in range(CANVAS_DOTS_H):
        for x in range(width):
            if abs(math.hypot(x - cx, y - cy) - RADIUS) < 1.15:
                dots[y][x] = 1

    # The rule sits at the circle's lower quarter and passes through it.
    line_y = cy + RADIUS / 2
    half = math.sqrt(RADIUS**2 - (RADIUS / 2) ** 2) + LINE_OVERHANG
    for y in range(CANVAS_DOTS_H):
        if abs(y - line_y) < 1.05:
            for x in range(width):
                if abs(x - cx) <= half:
                    dots[y][x] = 1

    rows = [
        "".join(
            chr(0x2800 + sum(
                DOT_BIT[(dx, dy)]
                for dy in range(4) for dx in range(2)
                if dots[r * 4 + dy][c * 2 + dx]
            ))
            for c in range(width // 2)
        )
        for r in range(CANVAS_DOTS_H // 4)
    ]

    # Trim all-blank edge columns so artWidth reflects the real ink.
    while all(r[0] == BLANK for r in rows):
        rows = [r[1:] for r in rows]
    while all(r[-1] == BLANK for r in rows):
        rows = [r[:-1] for r in rows]
    return rows


# --------------------------------------------------------------------------

def colorize(rows: list[str], palette: list[str], gradient: list[int],
             *, bold: bool = False) -> str:
    """Wrap each row in the rich markup the skin loader parses.

    Built-in skins set ``bold`` on the wordmark but not on the hero mark —
    braille dots are already dense, and bolding them muddies the outline.
    """
    prefix = "bold " if bold else ""
    return "\n".join(
        f"[{prefix}{palette[gradient[i]]}]{row}[/]" for i, row in enumerate(rows)
    )


def build() -> dict:
    sys.path.insert(0, str(REPO))
    from hermes_cli.skin_engine import load_skin

    base = load_skin("mono")          # inherit upstream's greyscale palette
    palette = [
        base.get_color("banner_title", "#e6edf3"),
        base.get_color("banner_accent", "#aaaaaa"),
        base.get_color("banner_dim", "#606060"),
    ]

    assert_glyphs_match_upstream()

    logo_rows = render_wordmark(WORDMARK)
    if len({len(r) for r in logo_rows}) != 1:
        raise SystemExit("wordmark rows are ragged")

    hero_rows = render_hero()
    hero_w = len(hero_rows[0])
    if len(hero_rows) != 15:
        raise SystemExit(f"hero must be 15 rows (got {len(hero_rows)}) — the "
                         "banner grid aligns both columns on that height")
    if len({len(r) for r in hero_rows}) != 1:
        raise SystemExit("hero rows are ragged")
    if hero_w > MAX_ART_WIDTH:
        raise SystemExit(f"hero is {hero_w} cols; above {MAX_ART_WIDTH} the "
                         "leftW = min(artWidth + 4, cols * 0.4) clamp truncates "
                         "it on a 100-column terminal")

    print(f"  wordmark : 6 x {len(logo_rows[0])}")
    print(f"  hero     : 15 x {hero_w}  (leftW={hero_w + 4})")

    return {
        "name": SKIN_NAME,
        "description": "Briefing Agent — mono palette, custom wordmark and mark",
        "colors": dict(base.colors),
        "spinner": dict(base.spinner),
        "branding": dict(base.branding, agent_name=AGENT_NAME),
        "tool_prefix": base.tool_prefix,
        # Gradients mirror upstream's LOGO_GRADIENT / CADUC_GRADIENT shape:
        # brighter through the middle, dimmer at the edges.
        "banner_logo": colorize(logo_rows, palette, [0, 0, 1, 1, 2, 2], bold=True),
        "banner_hero": colorize(
            hero_rows, palette, [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2]
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--install", action="store_true",
                    help="also copy the result into ~/.hermes/skins/")
    args = ap.parse_args()

    skin = build()
    out = REPO / "skins" / f"{SKIN_NAME}.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        yaml.safe_dump(skin, allow_unicode=True, sort_keys=False, width=400),
        encoding="utf-8",
    )
    print(f"wrote {out.relative_to(REPO)}")

    if args.install:
        dest = Path.home() / ".hermes" / "skins" / f"{SKIN_NAME}.yaml"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(out, dest)
        print(f"installed {dest}  —  activate with: hermes skin use {SKIN_NAME}")


if __name__ == "__main__":
    main()
