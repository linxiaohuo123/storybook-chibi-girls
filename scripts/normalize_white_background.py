#!/usr/bin/env python3
"""Conservatively normalize only edge-connected neutral near-white backgrounds.

Never overwrite the source. Inspect the output: even flood-fill has edge cases.
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--min-channel", type=int, default=236)
    parser.add_argument("--max-channel-spread", type=int, default=12)
    args = parser.parse_args()
    if not 230 <= args.min_channel <= 254 or not 0 <= args.max_channel_spread <= 20:
        parser.error("min-channel must be 230..254 and max-channel-spread must be 0..20")
    if args.source.resolve() == args.output.resolve():
        parser.error("Source and output must be different paths")
    if args.output.suffix.lower() != ".png":
        parser.error("Output must be a PNG file")
    try:
        from PIL import Image, ImageChops, ImageDraw
    except ImportError:
        print(json.dumps({"status": "error", "reason": "Pillow required"}))
        return 2
    try:
        with Image.open(args.source) as input_image:
            if getattr(input_image, "n_frames", 1) != 1:
                raise ValueError("Multi-frame images are not supported")
            if "A" in input_image.getbands() and input_image.getchannel("A").getextrema() != (255, 255):
                raise ValueError("Source has transparency; background normalization refused")
            rgb = input_image.convert("RGB")
        r, g, b = rgb.split()
        low = ImageChops.darker(ImageChops.darker(r, g), b)
        high = ImageChops.lighter(ImageChops.lighter(r, g), b)
        spread = ImageChops.subtract(high, low)
        bright = low.point(lambda v: 255 if v >= args.min_channel else 0)
        neutral = spread.point(lambda v: 255 if v <= args.max_channel_spread else 0)
        mask = ImageChops.multiply(bright, neutral)
        w, h = rgb.size
        if min(w, h) < 32:
            raise ValueError("Image dimensions too small to analyze safely")
        corners = [(0, 0), (w-1, 0), (0, h-1), (w-1, h-1)]
        if sum(mask.getpixel(xy) == 255 for xy in corners) < 3:
            raise ValueError("Fewer than three corners are neutral near-white; refuse fill")
        for xy in corners:
            if mask.getpixel(xy) == 255:
                ImageDraw.floodfill(mask, xy, 128)
        connected_background = mask.point(lambda v: 255 if v == 128 else 0)
        filled_count = connected_background.histogram()[255]
        if filled_count < w * h * 0.12:
            raise ValueError("Connected background region is unexpectedly small; refuse fill")
        result = Image.composite(Image.new("RGB", (w, h), (255, 255, 255)), rgb, connected_background)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        result.save(args.output, format="PNG")
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": "created_needs_visual_review", "source": str(args.source),
                      "output": str(args.output), "size": [w,h], "edge_connected_pixels_normalized": filled_count,
                      "note": "Inspect result for changed clothing or edge artifacts. Enclosed background holes may remain slightly off-white."}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
