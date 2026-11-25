"""Main rendering script for 《成都金融城双塔黄昏》 v3 (Photorealistic Multi-Stroke Edition).

Pure 2D procedural painting pipeline — zero 3D scenes, zero AI image models, zero photo assets.
Preserves v1 (src/) and v2 (src_v2/) intact.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from architecture_photo import (
    paint_background_architecture_v3,
    paint_foreground_right_tower_v3,
    paint_twin_towers_v3,
)
from canvas2d import Canvas2D
from sky_photo import paint_dusk_sky_v3
from street_botanical_photo import paint_jiaozi_avenue_v3, paint_street_trees_and_lamps_v3


def render_v3(
    width: int = 1600,
    height: int = 1200,
    seed: int = 2026,
    out_path: str = "output/chengdu_twin_towers_dusk_v3.png",
) -> None:
    t0 = time.perf_counter()
    horizon_v = 0.825

    canvas = Canvas2D(width=width, height=height)

    print(f"[1/5] Painting DSLR-calibrated Chengdu dusk sky ({width}x{height})...")
    paint_dusk_sky_v3(canvas, horizon_v=horizon_v, sun_u=0.475, seed=seed + 101)

    print("[2/5] Painting distant dome, Financial City skyline, tower crane & lattice annex...")
    paint_background_architecture_v3(canvas, seed=seed + 202)

    print("[3/5] Painting curved Twin Towers (ice-flower exoskeleton + sharp LED louvers)...")
    paint_twin_towers_v3(canvas, seed=seed + 404)

    print("[4/5] Painting ultra-high-res foreground right skyscraper...")
    paint_foreground_right_tower_v3(canvas, seed=seed + 505)

    print("[5/5] Painting weathered Jiaozi Avenue, dusk cars & 45,000-stroke fractal trees...")
    paint_jiaozi_avenue_v3(canvas, seed=seed + 606)
    paint_street_trees_and_lamps_v3(canvas, seed=seed + 707)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    canvas.save_png(
        out_path,
        exposure=1.02,
        bloom_strength=0.13,
        vignette_strength=0.20,
        grain_strength=0.011,
        ca_pixels=0.40,
        sharpen_amount=0.24,
        seed=seed + 999,
    )
    dt = time.perf_counter() - t0
    print(f"Done! Saved v3 photorealistic artwork to {out_path} in {dt:.2f}s")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pure 2D photorealistic procedural painting of Chengdu Twin Towers at Dusk (v3)"
    )
    parser.add_argument("--width", type=int, default=1600, help="Output image width in pixels")
    parser.add_argument("--height", type=int, default=1200, help="Output image height in pixels")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed")
    parser.add_argument(
        "--out",
        type=str,
        default="output/chengdu_twin_towers_dusk_v3.png",
        help="Output PNG path",
    )
    args = parser.parse_args()
    render_v3(width=args.width, height=args.height, seed=args.seed, out_path=args.out)


if __name__ == "__main__":
    main()
