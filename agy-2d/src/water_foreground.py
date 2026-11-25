"""Pure 2D reflective water surface (Jinjiang River / Jiaozi Park Lake) and subtle bokeh foreground (v3).

Enhanced silky horizontal ripple breakup in the foreground water and ultra-soft
35mm f/4 optical bokeh framing at the very bottom corners.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates

from canvas2d import Canvas2D
from noise2d import fbm_2d, smoothstep


def paint_river_reflection_and_foreground(
    canvas: Canvas2D,
    waterline_v: float = 0.658,
    seed: int = 606,
) -> None:
    """Paint the twilight reflective lake/river surface and subtle foreground framing."""
    h, w = canvas.height, canvas.width
    wy0 = int(round(waterline_v * h))
    wh = h - wy0
    if wh <= 0:
        return

    u = np.linspace(0.0, 1.0, w, dtype=np.float32)
    t = np.linspace(0.0, 1.0, wh, dtype=np.float32)
    uu, tt = np.meshgrid(u, t)

    # 1. Perspective-foreshortened 2D water ripple field
    depth = 0.032 + tt * 0.968
    wx = (uu - 0.5) * 9.5 / np.power(depth, 0.36)
    wy = 4.2 / np.power(depth, 0.80)

    wave_swell = fbm_2d(wx * 0.65, wy * 1.90, octaves=4, lacunarity=2.1, gain=0.50, seed=seed + 11, rotate=False)
    wave_ripple = fbm_2d(wx * 2.10 + 7.3, wy * 6.80 + 3.1, octaves=3, lacunarity=2.2, gain=0.48, seed=seed + 29, rotate=False)
    wave = (wave_swell - 0.5) * 0.62 + (wave_ripple - 0.5) * 0.38

    dw_dy = np.gradient(wave, axis=0)
    dw_dx = np.gradient(wave, axis=1)

    # 2. Sample mirrored upper scene with perspective ripple displacement
    src_y_base = wy0 - (tt * wh * 1.12)
    src_x_base = uu * (w - 1)

    amp_scale = (0.16 + 0.84 * np.power(tt, 0.55)) * (w / 1600.0)
    disp_x = dw_dx * 30.0 * amp_scale + (wave_swell - 0.5) * 14.0 * amp_scale
    disp_y = dw_dy * 56.0 * amp_scale + (wave_ripple - 0.5) * 20.0 * amp_scale

    sample_y = np.clip(src_y_base + disp_y, 0.0, wy0 - 1.0)
    sample_x = np.clip(src_x_base + disp_x, 0.0, w - 1.0)

    upper = canvas.img[:wy0, :, :]
    sigma_v = max(1.0, 2.2 * (h / 1066.0))
    sigma_h = max(0.5, 0.8 * (w / 1600.0))
    upper_soft = np.stack(
        [gaussian_filter(upper[..., c], sigma=(sigma_v, sigma_h)) for c in range(3)],
        axis=-1,
    )

    coords = np.array([sample_y, sample_x], dtype=np.float32)
    refl = np.empty((wh, w, 3), dtype=np.float32)
    for c in range(3):
        refl[..., c] = map_coordinates(upper_soft[..., c], coords, order=1, mode="nearest")

    # Vertically stretched specular shimmer columns under bright city lights & Twin Towers LEDs
    upper_luma = 0.2126 * upper[..., 0] + 0.7152 * upper[..., 1] + 0.0722 * upper[..., 2]
    upper_bright = upper * np.clip((upper_luma - 0.42) / 1.0, 0.0, 3.5)[..., None]
    upper_streak = np.stack(
        [
            gaussian_filter(
                upper_bright[..., c],
                sigma=(max(5.0, 19.0 * (h / 1066.0)), max(0.7, 1.3 * (w / 1600.0))),
            )
            for c in range(3)
        ],
        axis=-1,
    )
    shimmer_y = np.clip(src_y_base + disp_y * 1.5, 0.0, wy0 - 1.0)
    shimmer_x = np.clip(src_x_base + disp_x * 1.9, 0.0, w - 1.0)
    shimmer_coords = np.array([shimmer_y, shimmer_x], dtype=np.float32)
    shimmer = np.empty((wh, w, 3), dtype=np.float32)
    for c in range(3):
        shimmer[..., c] = map_coordinates(upper_streak[..., c], shimmer_coords, order=1, mode="nearest")

    crest_glint = smoothstep(0.015, 0.24, np.abs(dw_dy) * 6.0 + np.maximum(wave_ripple - 0.50, 0.0))
    refl += shimmer * (0.28 + 0.95 * crest_glint)[..., None] * 0.36

    # 3. Realistic twilight water absorption & Fresnel curve
    fresnel = 0.68 * np.exp(-tt * 0.92) + 0.16
    water_deep = np.array([0.005, 0.013, 0.028], dtype=np.float32)
    water_rgb = water_deep * (1.0 - fresnel[..., None]) + refl * (fresnel[..., None] * 0.75)

    trough_dark = 1.0 - 0.30 * smoothstep(-0.08, 0.14, -dw_dy * 3.8) * (0.35 + 0.65 * tt)
    water_rgb *= trough_dark[..., None]

    shore_ao = 1.0 - 0.72 * np.exp(-tt / 0.022)
    water_rgb *= shore_ao[..., None]

    facet_glint = np.clip(dw_dy * 4.2, 0.0, 1.0) * (0.25 + 0.75 * (1.0 - tt))
    water_rgb += np.array([0.10, 0.05, 0.035], dtype=np.float32) * (facet_glint * 0.18)[..., None]

    canvas.img[wy0:, :, :] = water_rgb

    # 4. Ultra-subtle out-of-focus foreground lakeside grasses at the extreme bottom corners
    _paint_soft_foreground_framing(canvas, seed=seed + 99)


def _paint_soft_foreground_framing(canvas: Canvas2D, seed: int = 707) -> None:
    """Paint very subtle, softly defocused foreground lakeside grasses at extreme bottom corners."""
    rng = np.random.default_rng(seed)
    w, h = canvas.width, canvas.height
    temp = Canvas2D(w, h)

    clusters = [
        (0.00, 0.075, 10),
        (0.925, 1.00, 10),
    ]
    for x_min, x_max, count in clusters:
        for _ in range(count):
            bx = float(rng.uniform(x_min, x_max))
            edge_dist = min(bx, 1.0 - bx)
            blade_h = float(rng.uniform(0.03, 0.085)) * (1.0 - smoothstep(0.01, 0.08, edge_dist) * 0.75)
            lean = float(rng.uniform(-0.018, 0.018)) + (0.010 if bx < 0.5 else -0.010)
            p0 = (bx, 1.02)
            p1 = (bx + lean * 0.35, 1.02 - blade_h * 0.45)
            p2 = (bx + lean * 0.85, 1.02 - blade_h * 0.85)
            p3 = (bx + lean, 1.02 - blade_h)
            width_px = max(0.7, w * float(rng.uniform(0.0006, 0.0012)))
            temp.paint_bezier_ribbon(
                p0, p1, p2, p3,
                width_px=width_px,
                color_start=(1.0, 1.0, 1.0),
                color_end=(0.65, 0.65, 0.65),
                steps=36,
                additive=True,
            )

    reed_mask = np.clip(temp.img[..., 0], 0.0, 1.0)
    blur_sigma = max(2.8, w / 360.0)
    reed_mask = np.clip(gaussian_filter(reed_mask, sigma=blur_sigma) * 0.72, 0.0, 0.78)
    reed_col = np.array([0.004, 0.006, 0.011], dtype=np.float32)[None, None, :]
    canvas.img = canvas.img * (1.0 - reed_mask[..., None]) + reed_col * reed_mask[..., None]
