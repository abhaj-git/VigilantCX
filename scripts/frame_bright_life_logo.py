#!/usr/bin/env python3
"""Add a soft, rounded champagne-gold frame around the logo PNG. Requires Pillow."""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SRC = ROOT / "assets" / "bright-life-astrology-logo-unframed.png"


def frame_logo(
    src: Path,
    dst: Path,
    *,
    border: int = 34,
) -> None:
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    b = border
    cw, ch = w + 2 * b, h + 2 * b

    # Corner radius: soft, proportional to canvas
    r_outer = min(58, max(38, min(cw, ch) // 14))
    r_inner = max(22, r_outer - 16)

    # Layered soft golds (outer cushion → main ring)
    pale = (244, 238, 228, 255)  # whisper of warmth at the very edge
    champagne = (232, 216, 194, 255)  # main soft frame
    blush = (248, 240, 228, 255)  # inner highlight on the gold ring
    warm_white = (255, 252, 249, 255)  # window behind logo

    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # Slight outer halo (softer than a hard rectangle)
    draw.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=r_outer, fill=pale)
    draw.rounded_rectangle([2, 2, cw - 3, ch - 3], radius=max(4, r_outer - 2), fill=champagne)

    # Thin luminous inner edge on the gold band
    inset = 5
    draw.rounded_rectangle(
        [inset, inset, cw - 1 - inset, ch - 1 - inset],
        radius=max(8, r_outer - inset),
        outline=blush,
        width=2,
    )

    # Inner “mat” — warm white with rounded corners
    draw.rounded_rectangle(
        [b, b, cw - b - 1, ch - b - 1],
        radius=r_inner,
        fill=warm_white,
    )

    canvas.paste(im, (b, b), im)
    canvas.save(dst, "PNG")


def main() -> None:
    p = argparse.ArgumentParser(description="Soft rounded champagne frame for Bright Life logo")
    p.add_argument("--src", type=Path, default=DEFAULT_SRC)
    p.add_argument("--out", type=Path, default=ROOT / "assets" / "bright-life-astrology-logo.png")
    p.add_argument("--border", type=int, default=34, help="Frame thickness in pixels")
    args = p.parse_args()
    frame_logo(args.src, args.out, border=args.border)


if __name__ == "__main__":
    main()
