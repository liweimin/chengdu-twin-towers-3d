"""Main rendering script for 《成都金融城双塔黄昏》 (Chengdu Financial City Twin Towers at Dusk).

Pure 2D procedural painting pipeline — zero 3D scenes, zero AI image models, zero photo assets.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from architecture import (
    paint_distant_skyline,
    paint_jiaozi_ring_and_waterfront,
    paint_midground_skyline,
    paint_twin_towers,
)
from canvas2d import Canvas2D
from sky_clouds import paint_dusk_sky
from water_foreground import paint_river_reflection_and_foreground


def render_scene(
    width: int = 1600,
    height: int = 1066,
    seed: int = 2026,
    out_path: str = "output/chengdu_twin_towers_dusk.png",
) -> None:
    t0 = time.perf_counter()
    horizon_v = 0.625
    waterline_v = 0.658

    canvas = Canvas2D(width=width, height=height)

    print(f"[1/6] Painting Chengdu twilight sky & sunset clouds ({width}x{height})...")
    paint_dusk_sky(canvas, horizon_v=horizon_v, sun_u=0.46, sun_v=horizon_v, seed=seed + 101)

    print("[2/6] Painting distant hazy skyline...")
    paint_distant_skyline(canvas, horizon_v=horizon_v, seed=seed + 201)

    print("[3/6] Painting Financial City midground skyscrapers...")
    paint_midground_skyline(canvas, horizon_v=horizon_v, seed=seed + 303)

    print("[4/6] Painting Tianfu International Financial Center Twin Towers...")
    paint_twin_towers(canvas, horizon_v=horizon_v, seed=seed + 404)

    print("[5/6] Painting Jiaozi Ring, waterfront promenade, trees, lamps & traffic trails...")
    paint_jiaozi_ring_and_waterfront(
        canvas, horizon_v=horizon_v, waterline_v=waterline_v, seed=seed + 505
    )

    print("[6/6] Painting river reflections, foreground bokeh & photographic optics...")
    paint_river_reflection_and_foreground(canvas, waterline_v=waterline_v, seed=seed + 606)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    canvas.save_png(
        out_path,
        exposure=0.96,
        bloom_strength=0.18,
        vignette_strength=0.30,
        grain_strength=0.011,
        ca_pixels=0.55,
        seed=seed + 999,
    )
    dt = time.perf_counter() - t0
    print(f"Done! Saved to {out_path} in {dt:.2f}s")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pure 2D procedural painting of Chengdu Financial City Twin Towers at Dusk"
    )
    parser.add_argument("--width", type=int, default=1600, help="Output image width in pixels")
    parser.add_argument("--height", type=int, default=1066, help="Output image height in pixels")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed for reproducibility")
    parser.add_argument(
        "--out",
        type=str,
        default="output/chengdu_twin_towers_dusk.png",
        help="Output PNG file path",
    )
    args = parser.parse_args()
    render_scene(width=args.width, height=args.height, seed=args.seed, out_path=args.out)


if __name__ == "__main__":
    main()
