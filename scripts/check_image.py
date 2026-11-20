#!/usr/bin/env python3
"""Read-only format/background screening. This is not a visual quality verdict."""

import argparse
import json
import math
import sys
import warnings
from pathlib import Path


VISUAL_CHECKS = [
    "single_complete_girl_and_positive_expression",
    "flat_hair_without_highlights_or_shading",
    "clean_structural_lines_and_correct_anatomy",
    "coherent_palette_and_readable_theme",
    "no_shadows_white_outline_text_or_background_objects",
    "white_background_across_the_whole_image",
]


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--white-tolerance", type=int, default=8,
                        help="Near-white means every RGB channel >= 255 minus this value (default 8).")
    parser.add_argument("--min-white-border", type=float, default=0.95,
                        help="Heuristic minimum near-white border fraction (default 0.95).")
    parser.add_argument("--require-exact-white-border", action="store_true",
                        help="Also require >=99.5%% of the outer border band pixels to be exactly RGB 255,255,255.")
    args = parser.parse_args()
    if not 0 <= args.white_tolerance <= 32 or not 0 <= args.min_white_border <= 1:
        parser.error("white-tolerance must be 0..32; min-white-border must be 0..1")

    base = {"schema_version": 1, "image": str(args.image),
            "visual_review_required": VISUAL_CHECKS}
    try:
        from PIL import Image, ImageChops
    except ImportError:
        emit({**base, "status": "error", "format_checks_passed": False,
              "error": "Missing dependency: Pillow. Install Pillow in the active Python environment."})
        return 2

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(args.image) as original:
                original.load()
                width, height = original.size
                frame_count = getattr(original, "n_frames", 1)
                rgba = original.convert("RGBA")
                opaque = rgba.getchannel("A").getextrema() == (255, 255)
                rgb = rgba.convert("RGB")
                diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, "white"))
                red, green, blue = diff.split()
                max_diff = ImageChops.lighter(ImageChops.lighter(red, green), blue)
                mask = max_diff.point(lambda v: 255 if v > args.white_tolerance else 0)
                bbox = mask.getbbox()
                band = max(1, math.ceil(min(width, height) * 0.025))
                pixels = mask.load()
                border_count = nonwhite_border = exact_white_border = 0
                for y in range(height):
                    xs = range(width) if y < band or y >= height - band else (
                        list(range(min(band, width))) + list(range(max(band, width - band), width)))
                    for x in xs:
                        border_count += 1
                        nonwhite_border += bool(pixels[x, y])
                        exact_white_border += rgb.getpixel((x, y)) == (255, 255, 255)
                white_fraction = 1 - nonwhite_border / border_count
                exact_white_fraction = exact_white_border / border_count
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        emit({**base, "status": "error", "format_checks_passed": False,
              "error": f"Cannot inspect image: {type(exc).__name__}: {exc}"})
        return 2

    issues = []
    notes = ["Thresholds screen file geometry and sampled border color only; they do not prove visual quality or a pure-white background away from the border."]
    if width != height:
        issues.append("not_square")
    if not opaque:
        issues.append("transparent_pixels_present")
    if frame_count != 1:
        issues.append("multiple_frames")
    if bbox is None:
        issues.append("no_nonwhite_content_detected")
    if white_fraction < args.min_white_border:
        issues.append("border_not_sufficiently_near_white")
    if args.require_exact_white_border and exact_white_fraction < 0.995:
        issues.append("border_not_exact_white")
    margins = None
    if bbox:
        margins = {"left": bbox[0], "top": bbox[1],
                   "right": width - bbox[2], "bottom": height - bbox[3]}
        if min(margins.values()) < math.ceil(min(width, height) * 0.04):
            notes.append("Content is close to an edge; inspect the complete hair, accessories, hands and feet.")
    emit({**base, "status": "failed" if issues else "needs_visual_review",
          "format_checks_passed": not issues, "width": width, "height": height,
          "square": width == height, "fully_opaque": opaque, "frame_count": frame_count,
          "white_tolerance": args.white_tolerance, "border_band_px": band,
          "minimum_white_border_fraction": args.min_white_border,
          "border_near_white_fraction": round(white_fraction, 6),
          "border_exact_white_fraction": round(exact_white_fraction, 6),
          "exact_white_border_enforced": args.require_exact_white_border,
          "foreground_bbox_xyxy": list(bbox) if bbox else None,
          "foreground_margins_px": margins, "issues": issues, "notes": notes})
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
