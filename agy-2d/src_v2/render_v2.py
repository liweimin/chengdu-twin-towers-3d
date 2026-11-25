"""Main rendering script for 《成都金融城双塔黄昏》 v2 (Jiaozi Avenue Real-Perspective Edition).

Pure 2D procedural painting pipeline — zero 3D scenes, zero AI image models, zero photo assets.
All v1 files in src/ and output/chengdu_twin_towers_dusk.png are preserved intact.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from avenue_trees import paint_jiaozi_avenue_and_traffic, paint_street_trees_and_lamps
from canvas2d import Canvas2D
from city_v2 import (
    paint_background_architecture_v2,
    paint_foreground_right_tower_v2,
    paint_twin_towers_v2,
)
from sky_dusk import paint_dusk_sky_v2


def render_v2(
    width: int = 1600,
    height: int = 1200,
    seed: int = 2026,
    out_path: str = "output/chengdu_twin_towers_dusk_v2.png",
) -> None:
    t0 = time.perf_counter()
    horizon_v = 0.825

    canvas = Canvas2D(width=width, height=height)

    print(f"[1/5] Painting Chengdu golden-blue-hour sunset sky ({width}x{height})...")
    paint_dusk_sky_v2(canvas, horizon_v=horizon_v, sun_u=0.48, seed=seed + 101)

    print("[2/5] Painting distant convention dome & Financial City background skyline...")
    paint_background_architecture_v2(canvas, seed=seed + 202)

    print("[3/5] Painting curved Tianfu International Financial Center Twin Towers...")
    paint_twin_towers_v2(canvas, seed=seed + 404)

    print("[4/5] Painting foreground right skyscraper (2-point perspective)...")
    paint_foreground_right_tower_v2(canvas, seed=seed + 505)

    print("[5/5] Painting Jiaozi Avenue, twilight traffic, streetlamps & lush street trees...")
    paint_jiaozi_avenue_and_traffic(canvas, seed=seed + 606)
    paint_street_trees_and_lamps(canvas, seed=seed + 707)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    canvas.save_png(
        out_path,
        exposure=1.02,
        bloom_strength=0.16,
        vignette_strength=0.22,
        grain_strength=0.009,
        ca_pixels=0.45,
        seed=seed + 999,
    )
    dt = time.perf_counter() - t0
    print(f"Done! Saved v2 artwork to {out_path} in {dt:.2f}s")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pure 2D procedural painting of Chengdu Financial City Twin Towers at Dusk (v2)"
    )
    parser.add_argument("--width", type=int, default=1600, help="Output image width in pixels")
    parser.add_argument("--height", type=int, default=1200, help="Output image height in pixels")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed")
    parser.add_argument(
        "--out",
        type=str,
        default="output/chengdu_twin_towers_dusk_v2.png",
        help="Output PNG path",
    )
    args = parser.parse_args()
    render_v2(width=args.width, height=args.height, seed=args.seed, out_path=args.out)


if __name__ == "__main__":
    main()
