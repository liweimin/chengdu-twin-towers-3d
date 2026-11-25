"""
Main Reproducible Rendering Entrypoint for《成都金融城双塔黄昏》
(Chengdu Financial City Twin Towers at Dusk).

Usage:
  .venv/Scripts/python.exe render.py --preset draft
  .venv/Scripts/python.exe render.py --preset medium
  .venv/Scripts/python.exe render.py --preset final
"""

import os
import sys
import time
import argparse
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.sky_gen import generate_dusk_sky
from src.textures import generate_all_textures
from src.geometry import build_all_geometry
from src.scene import build_mitsuba_scene, render_with_aovs
from src.postprocess import postprocess_render


PRESETS = {
    "draft":  {"width": 1280, "height": 720,  "spp": 32,  "max_depth": 5, "denoise": 2, "sky_w": 3072, "sky_h": 1536},
    "medium": {"width": 1920, "height": 1080, "spp": 64,  "max_depth": 6, "denoise": 2, "sky_w": 4096, "sky_h": 2048},
    "final":  {"width": 3840, "height": 2160, "spp": 48,  "max_depth": 5, "denoise": 2, "sky_w": 4096, "sky_h": 2048},
}


def main():
    parser = argparse.ArgumentParser(description="Render Chengdu Financial City Twin Towers at Dusk")
    parser.add_argument("--preset", choices=["draft", "medium", "final"], default="draft")
    parser.add_argument("--rebuild-sky", action="store_true", help="Regenerate HDR dusk sky")
    parser.add_argument("--rebuild-textures", action="store_true", help="Regenerate procedural PBR textures")
    parser.add_argument("--rebuild-geo", action="store_true", help="Regenerate 3D PLY meshes")
    parser.add_argument("--out", default=None, help="Output PNG path")
    args = parser.parse_args()

    cfg = PRESETS[args.preset]
    os.makedirs("outputs", exist_ok=True)
    out_png = args.out or os.path.join("outputs", f"chengdu_twin_towers_dusk_{args.preset}.png")

    t_start = time.time()
    if args.rebuild_sky or not os.path.exists("assets/dusk_sky.npy"):
        generate_dusk_sky("assets", width=cfg["sky_w"], height=cfg["sky_h"])
    if args.rebuild_textures or not os.path.exists("assets/tower_led_north.png"):
        generate_all_textures("assets")
    if args.rebuild_geo or not os.path.exists("assets/meshes/tower_glass.ply"):
        build_all_geometry("assets/meshes")

    print(f"Loading Mitsuba 3 scene ({cfg['width']}x{cfg['height']} @ {cfg['spp']} spp)...")
    t0 = time.time()
    scene = build_mitsuba_scene(
        width=cfg["width"],
        height=cfg["height"],
        spp=cfg["spp"],
        max_depth=cfg["max_depth"],
    )
    print(f"Scene built & BVH ready in {time.time() - t0:.2f}s. Path tracing...")

    t1 = time.time()
    aovs = render_with_aovs(scene, spp=cfg["spp"])
    print(f"Path tracing completed in {time.time() - t1:.2f}s.")

    # Save raw linear beauty HDR array for archival / rapid re-grading
    raw_npy = out_png.replace(".png", "_raw.npy")
    np.save(raw_npy, aovs["beauty"])

    t2 = time.time()
    postprocess_render(
        aovs,
        out_png,
        exposure=1.08,
        denoise_iters=cfg["denoise"],
        mist_density=0.00042,
        bloom_strength=0.16,
        starburst_strength=0.14,
    )
    print(f"Post-processing done in {time.time() - t2:.2f}s. Total time: {time.time() - t_start:.2f}s")


if __name__ == "__main__":
    main()
