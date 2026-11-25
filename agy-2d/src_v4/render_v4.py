"""Main rendering script for 《成都金融城双塔黄昏》 v4 (100% Pure 2D Brushstroke Edition).

Every single element — sky, sunset clouds, distant skyline, curved Twin Towers,
close-up foreground skyscraper, Jiaozi Avenue asphalt, dusk cars, streetlamps,
and fractal trees — is painted exclusively with physical 2D brushstrokes.

Preserves v1 (src/), v2 (src_v2/), and v3 (src_v3/) completely intact.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from architecture_brush import (
    paint_background_skyline_by_strokes,
    paint_foreground_right_tower_by_strokes,
    paint_twin_towers_by_strokes,
)
from brush_engine import BrushCanvas
from sky_brush import paint_sky_by_brushstrokes
from street_trees_brush import (
    paint_jiaozi_avenue_by_strokes,
    paint_trees_and_street_furniture_by_strokes,
)


def render_v4(
    width: int = 1600,
    height: int = 1200,
    seed: int = 2026,
    out_path: str = "output/chengdu_twin_towers_dusk_v4.png",
) -> None:
    t0 = time.perf_counter()
    bc = BrushCanvas(width=width, height=height, seed=seed)

    print(f"[1/5] Painting twilight sky & impasto clouds by brushstrokes ({width}x{height})...")
    paint_sky_by_brushstrokes(bc, horizon_v=0.825)

    print("[2/5] Painting distant dome, skyline, crane & curved annex by brushstrokes...")
    paint_background_skyline_by_strokes(bc)

    print("[3/5] Painting curved Twin Towers & luminous LED louvers by brushstrokes...")
    paint_twin_towers_by_strokes(bc)

    print("[4/5] Painting close-up foreground right skyscraper by brushstrokes...")
    paint_foreground_right_tower_by_strokes(bc)

    print("[5/5] Painting Jiaozi Avenue, painterly dusk cars & fractal botanical trees...")
    paint_jiaozi_avenue_by_strokes(bc)
    paint_trees_and_street_furniture_by_strokes(bc)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    bc.save_png(
        out_path,
        exposure=1.04,
        bloom_strength=0.14,
        vignette_strength=0.20,
        grain_strength=0.011,
        ca_pixels=0.35,
        sharpen_amount=0.18,
        seed=seed + 999,
    )
    dt = time.perf_counter() - t0
    print(f"Done! Painted {bc.total_strokes:,} physical 2D brushstrokes -> {out_path} in {dt:.2f}s")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="100% Pure 2D Brushstroke Painting of Chengdu Financial City Twin Towers at Dusk (v4)"
    )
    parser.add_argument("--width", type=int, default=1600, help="Output image width in pixels")
    parser.add_argument("--height", type=int, default=1200, help="Output image height in pixels")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed")
    parser.add_argument(
        "--out",
        type=str,
        default="output/chengdu_twin_towers_dusk_v4.png",
        help="Output PNG path",
    )
    args = parser.parse_args()
    render_v4(width=args.width, height=args.height, seed=args.seed, out_path=args.out)


if __name__ == "__main__":
    main()
