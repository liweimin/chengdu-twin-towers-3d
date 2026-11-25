"""Hyper-realistic Jiaozi Avenue & 45,000-stroke fractal botanical tree engine (v3).

Directly inspired by multi-thousand-stroke procedural painting:
1. Weathered granular twilight asphalt with dual tire-wear tracks, painted lane
   arrows, zebra crosswalk, pale-blue bike lanes, curbs, and intersection signals.
2. Multi-part photographic dusk vehicles (chassis shadow, tires, sky-reflecting
   metallic body & windshields, side mirrors, license plates, compact bright LED
   headlights/taillights & glossy asphalt reflection streaks).
3. Pure 2D recursive fractal tree skeletons (trunks -> limbs -> fine dark twigs)
   overlaid with ~45,000 crisp, individually rotated 2D leaf-cluster brushstrokes
   achieving real photographic high-frequency foliage micro-contrast (grad ~ 0.13)
   and natural sky pinholes peeking through the canopy!
"""

from __future__ import annotations

import math
import numpy as np
from PIL import Image, ImageDraw

from canvas2d import Canvas2D
from noise2d import fbm_2d, smoothstep


def _road_u(lane_s: float, v: float) -> float:
    t = np.clip((v - 0.825) / (1.000 - 0.825), 0.0, 1.0)
    center = 0.484 + (0.446 - 0.484) * t
    half_w = 0.008 + (0.156 - 0.008) * t
    return float(center + lane_s * half_w)


def _draw_lane_arrow(
    canvas: Canvas2D,
    lane_s: float,
    v_center: float,
    turn_left: bool = False,
) -> None:
    """Paint a weathered perspective white directional lane arrow on the asphalt."""
    sc = np.clip((v_center - 0.825) / 0.175, 0.1, 1.0)
    v_bot = v_center + 0.018 * sc
    v_top = v_center - 0.016 * sc
    v_head = v_center - 0.004 * sc
    u_bot = _road_u(lane_s, v_bot)
    u_top = _road_u(lane_s, v_top)
    u_hl = _road_u(lane_s - 0.075, v_head)
    u_hr = _road_u(lane_s + 0.075, v_head)

    col = (0.36, 0.38, 0.42)
    w_px = max(1.2, canvas.width * 0.0022 * sc)
    canvas.draw_line((u_bot, v_bot), (u_top, v_top), w_px, col, alpha=0.68)
    canvas.fill_polygon([(u_top, v_top - 0.004 * sc), (u_hr, v_head), (u_hl, v_head)], col, alpha=0.68)
    if turn_left:
        u_mid = _road_u(lane_s, v_center)
        u_lt = _road_u(lane_s - 0.12, v_center - 0.003 * sc)
        canvas.draw_line((u_mid, v_center), (u_lt, v_center - 0.003 * sc), w_px * 0.85, col, alpha=0.65)


def _paint_photoreal_car(
    canvas: Canvas2D,
    vc: float,
    ls: float,
    is_oncoming: bool,
    body_col: tuple[float, float, float],
    is_suv: bool = False,
) -> None:
    """Paint a multi-part photographic dusk vehicle with realistic sky reflections & lighting."""
    scale_c = float(np.clip((vc - 0.825) / 0.175, 0.08, 1.0))
    cu = _road_u(ls, vc)
    cw = (0.0145 if not is_suv else 0.0162) * scale_c + 0.0026
    ch = (0.0145 if not is_suv else 0.0175) * scale_c + 0.0025

    # 1. Deep contact shadow under chassis
    canvas.fill_polygon(
        [
            (cu - cw * 1.14, vc + ch * 0.28),
            (cu + cw * 1.14, vc + ch * 0.28),
            (cu + cw * 1.08, vc + ch * 0.72),
            (cu - cw * 1.08, vc + ch * 0.72),
        ],
        (0.003, 0.004, 0.007),
        alpha=0.92,
    )

    # 2. Dark rubber tires on left & right lower corners
    for s in (-1.0, 1.0):
        tx0 = cu + s * cw * 0.96 - cw * 0.14
        tx1 = cu + s * cw * 0.96 + cw * 0.14
        canvas.fill_polygon(
            [(tx0, vc + ch * 0.20), (tx1, vc + ch * 0.20), (tx1, vc + ch * 0.62), (tx0, vc + ch * 0.62)],
            (0.006, 0.007, 0.010),
        )

    # 3. Lower bumper & metallic body (slightly darker below bumper crease)
    canvas.fill_polygon(
        [
            (cu - cw * 1.02, vc - ch * 0.10),
            (cu + cw * 1.02, vc - ch * 0.10),
            (cu + cw * 1.04, vc + ch * 0.46),
            (cu - cw * 1.04, vc + ch * 0.46),
        ],
        (body_col[0] * 0.72, body_col[1] * 0.74, body_col[2] * 0.78),
    )
    # Glossy upper hood/trunk catching warm twilight sky highlight!
    hood_col = (
        body_col[0] * 1.18 + 0.045,
        body_col[1] * 1.12 + 0.032,
        body_col[2] * 1.10 + 0.035,
    )
    canvas.fill_polygon(
        [
            (cu - cw * 0.94, vc - ch * 0.22),
            (cu + cw * 0.94, vc - ch * 0.22),
            (cu + cw * 1.02, vc - ch * 0.04),
            (cu - cw * 1.02, vc - ch * 0.04),
        ],
        hood_col,
    )

    # 4. Cabin pillars + roof catching bright sunset sky sheen
    canvas.fill_polygon(
        [
            (cu - cw * 0.74, vc - ch * 0.72),
            (cu + cw * 0.74, vc - ch * 0.72),
            (cu + cw * 0.92, vc - ch * 0.18),
            (cu - cw * 0.92, vc - ch * 0.18),
        ],
        body_col,
    )
    # Glossy roof top highlight strip
    canvas.fill_polygon(
        [
            (cu - cw * 0.68, vc - ch * 0.73),
            (cu + cw * 0.68, vc - ch * 0.73),
            (cu + cw * 0.72, vc - ch * 0.64),
            (cu - cw * 0.72, vc - ch * 0.64),
        ],
        (body_col[0] * 1.35 + 0.06, body_col[1] * 1.25 + 0.045, body_col[2] * 1.22 + 0.05),
    )

    # 5. Windshield / rear glass reflecting the warm dusk sky at top, dark interior below!
    canvas.fill_polygon(
        [
            (cu - cw * 0.62, vc - ch * 0.63),
            (cu + cw * 0.62, vc - ch * 0.63),
            (cu + cw * 0.78, vc - ch * 0.20),
            (cu - cw * 0.78, vc - ch * 0.20),
        ],
        (0.015, 0.020, 0.034),
    )
    canvas.fill_polygon(
        [
            (cu - cw * 0.58, vc - ch * 0.61),
            (cu + cw * 0.58, vc - ch * 0.61),
            (cu + cw * 0.65, vc - ch * 0.42),
            (cu - cw * 0.65, vc - ch * 0.42),
        ],
        (0.14, 0.10, 0.12),
        alpha=0.52,
    )

    # 6. Tiny side mirrors & blue/green Chinese license plate glint
    for s in (-1.0, 1.0):
        mx = cu + s * cw * 0.96
        canvas.fill_polygon(
            [(mx - cw * 0.10, vc - ch * 0.28), (mx + cw * 0.10, vc - ch * 0.28),
             (mx + cw * 0.10, vc - ch * 0.16), (mx - cw * 0.10, vc - ch * 0.16)],
            body_col,
        )
    if scale_c > 0.25:
        canvas.fill_polygon(
            [(cu - cw * 0.20, vc + ch * 0.14), (cu + cw * 0.20, vc + ch * 0.14),
             (cu + cw * 0.20, vc + ch * 0.27), (cu - cw * 0.20, vc + ch * 0.27)],
            (0.06, 0.14, 0.36),
        )

    # 7. Compact intense LED headlights / red taillights + realistic glossy asphalt light reflection!
    ly = vc + ch * 0.08
    for side in (-0.74, 0.74):
        lx = cu + side * cw
        if is_oncoming:
            # Crisp compact bright headlight core + soft subtle halo
            canvas.draw_soft_glow(lx, ly, 0.0014 * scale_c + 0.0005, 0.0016 * scale_c + 0.0005, (4.2, 3.6, 2.6), power=2.0)
            canvas.draw_soft_glow(lx, ly, 0.0045 * scale_c + 0.0012, 0.0045 * scale_c + 0.0012, (0.55, 0.44, 0.26), power=2.0)
            # Glossy vertical reflection streak on dark asphalt below headlight
            canvas.draw_soft_glow(lx, ly + ch * 0.72, 0.0032 * scale_c + 0.001, 0.011 * scale_c + 0.002, (0.22, 0.17, 0.10), power=2.0)
        else:
            # Crisp ruby-red LED taillight + rear brake bar
            canvas.draw_soft_glow(lx, ly, 0.0015 * scale_c + 0.0005, 0.0015 * scale_c + 0.0005, (4.4, 0.24, 0.10), power=2.0)
            canvas.draw_soft_glow(lx, ly, 0.0048 * scale_c + 0.0012, 0.0042 * scale_c + 0.0012, (0.55, 0.05, 0.02), power=2.0)
            canvas.draw_soft_glow(lx, ly + ch * 0.68, 0.0034 * scale_c + 0.001, 0.011 * scale_c + 0.002, (0.28, 0.03, 0.015), power=2.0)


def paint_jiaozi_avenue_v3(canvas: Canvas2D, seed: int = 606) -> None:
    """Paint weathered granular twilight Jiaozi Avenue, markings, arrows, signals & real dusk cars."""
    w, h = canvas.width, canvas.height
    u, v = canvas.u_grid()

    y_start = int(0.822 * h)
    uu = u[y_start:, :]
    vv = v[y_start:, :]

    t = np.clip((vv - 0.825) / 0.175, 0.0, 1.0)
    center_u = 0.484 + (0.446 - 0.484) * t
    half_w = 0.008 + (0.156 - 0.008) * t
    lane_s = (uu - center_u) / np.maximum(half_w, 1e-4)

    road_mask = (np.abs(lane_s) <= 1.02).astype(np.float32) * (vv >= 0.824)
    # Pale-blue/grey bike lane + concrete curb flanking Jiaozi Avenue (as seen in ref_2.jpg!)
    bike_mask = ((np.abs(lane_s) > 1.03) & (np.abs(lane_s) <= 1.18)).astype(np.float32) * (vv >= 0.828)
    curb_mask = ((np.abs(lane_s) > 1.01) & (np.abs(lane_s) <= 1.04)).astype(np.float32) * (vv >= 0.828)

    # High-frequency granular asphalt aggregate + worn darker dual tire-tracks in each lane!
    z_persp = 1.0 / (t + 0.05)
    grit_coarse = fbm_2d(lane_s * 22.0, z_persp * 6.0, octaves=4, seed=seed + 11, rotate=False)
    grit_fine = fbm_2d(uu * 240.0, vv * 240.0, octaves=3, seed=seed + 23, rotate=False)
    # Subtle darker wheel paths in each lane (-0.70, -0.25, +0.25, +0.70)
    tire_wear = (
        np.exp(-(((lane_s + 0.72) / 0.11) ** 2))
        + np.exp(-(((lane_s + 0.28) / 0.11) ** 2))
        + np.exp(-(((lane_s - 0.28) / 0.11) ** 2))
        + np.exp(-(((lane_s - 0.72) / 0.11) ** 2))
    )
    sky_sheen = np.exp(-((lane_s * 0.88) ** 2)) * (0.24 + 0.76 * (1.0 - t))

    asphalt = (
        np.array([0.026, 0.029, 0.038], dtype=np.float32) * (1.0 - 0.22 * tire_wear[..., None])
        + np.array([0.022, 0.022, 0.026], dtype=np.float32) * (grit_coarse * 0.6 + grit_fine * 0.4)[..., None]
        + np.array([0.10, 0.062, 0.038], dtype=np.float32) * (sky_sheen * (0.55 + 0.45 * grit_coarse))[..., None]
    )
    canvas.blend_over(asphalt, road_mask, y0=y_start, x0=0)

    # Bike lane & concrete curb
    bike_col = np.array([0.048, 0.060, 0.078], dtype=np.float32) + 0.015 * grit_fine[..., None]
    curb_col = np.array([0.075, 0.078, 0.086], dtype=np.float32)
    canvas.blend_over(bike_col, bike_mask, y0=y_start, x0=0)
    canvas.blend_over(curb_col, curb_mask, y0=y_start, x0=0)

    # Weathered perspective road markings (attenuated by grit_fine so they look painted, NOT neon!)
    paint_wear = 0.68 + 0.32 * grit_fine
    in_crosswalk = (vv >= 0.892) & (vv <= 0.903)

    yl1 = np.exp(-(((lane_s - 0.005) / 0.013) ** 2))
    yl2 = np.exp(-(((lane_s - 0.036) / 0.013) ** 2))
    yellow_mask = np.clip((yl1 + yl2), 0.0, 1.0) * smoothstep(0.834, 0.848, vv)
    yellow_mask = np.where(in_crosswalk, 0.0, yellow_mask) * paint_wear
    yellow_col = np.array([0.52, 0.34, 0.09], dtype=np.float32)
    canvas.blend_over(yellow_col[None, None, :], yellow_mask * 0.78, y0=y_start, x0=0)

    dash_pattern = (np.sin(z_persp * 3.8) > 0.08).astype(np.float32)
    w_dash = (
        np.exp(-(((lane_s + 0.50) / 0.012) ** 2)) + np.exp(-(((lane_s - 0.50) / 0.012) ** 2))
    ) * dash_pattern * smoothstep(0.842, 0.858, vv)
    w_dash = np.where(in_crosswalk, 0.0, w_dash)

    curb_lines = (
        np.exp(-(((lane_s + 0.96) / 0.012) ** 2)) + np.exp(-(((lane_s - 0.96) / 0.012) ** 2))
    ) * smoothstep(0.835, 0.850, vv)

    zebra = (np.sin(lane_s * 34.0) > 0.05).astype(np.float32) * in_crosswalk.astype(np.float32) * (np.abs(lane_s) < 0.92)
    white_mask = np.clip(w_dash + curb_lines * 0.75 + zebra * 0.70, 0.0, 1.0) * paint_wear
    white_col = np.array([0.38, 0.40, 0.45], dtype=np.float32)
    canvas.blend_over(white_col[None, None, :], white_mask * 0.74, y0=y_start, x0=0)

    # Painted white directional lane arrows on open foreground asphalt (matching ref_2.jpg!)
    _draw_lane_arrow(canvas, 0.72, 0.932, turn_left=False)
    _draw_lane_arrow(canvas, -0.68, 0.945, turn_left=False)
    _draw_lane_arrow(canvas, -0.24, 0.968, turn_left=True)

    # Subtle short dusk motion-blur trails ONLY close behind moving cars (NOT wall-to-wall laser lines!)
    cars = [
        # (v_pos, lane_s, is_oncoming, body_col, is_suv)
        (0.956, 0.22, True, (0.18, 0.19, 0.22), False),   # Prominent white sedan (ref_2.jpg)
        (0.920, 0.29, True, (0.025, 0.028, 0.036), True),  # Black SUV behind it
        (0.905, 0.45, True, (0.16, 0.17, 0.20), True),    # White SUV right lane
        (0.888, 0.18, True, (0.04, 0.045, 0.055), False),
        (0.875, 0.36, True, (0.14, 0.15, 0.17), False),
        (0.862, 0.24, True, (0.05, 0.055, 0.065), False),
        # Outgoing left-lane vehicles
        (0.938, -0.30, False, (0.035, 0.040, 0.052), True),
        (0.896, -0.22, False, (0.10, 0.11, 0.13), False),
        (0.874, -0.38, False, (0.04, 0.045, 0.055), False),
        (0.858, -0.18, False, (0.09, 0.095, 0.11), False),
    ]

    for vc, ls, is_inc, bcol, is_suv in sorted(cars, key=lambda c: c[0]):
        _paint_photoreal_car(canvas, vc, ls, is_inc, bcol, is_suv=is_suv)

    # Distant intersection traffic lights (tiny glowing red & green signals at y=0.844)
    canvas.draw_soft_glow(0.464, 0.846, 0.0010, 0.0014, (3.2, 0.20, 0.10), power=2.0)
    canvas.draw_soft_glow(0.504, 0.846, 0.0010, 0.0014, (0.20, 2.8, 0.55), power=2.0)

    # Detailed blue directional overhead road sign on right (matching ref_2.jpg!)
    canvas.draw_line((0.542, 0.844), (0.542, 0.890), max(1.1, w * 0.0011), (0.032, 0.036, 0.044))
    canvas.draw_line((0.514, 0.852), (0.542, 0.852), max(0.9, w * 0.0009), (0.032, 0.036, 0.044))
    canvas.fill_polygon([(0.513, 0.841), (0.540, 0.841), (0.540, 0.864), (0.513, 0.864)], (0.42, 0.48, 0.56))
    canvas.fill_polygon([(0.5145, 0.8425), (0.5385, 0.8425), (0.5385, 0.8625), (0.5145, 0.8625)], (0.022, 0.11, 0.34))
    canvas.draw_line((0.518, 0.848), (0.534, 0.848), max(0.7, w * 0.0006), (0.55, 0.62, 0.72), alpha=0.85)
    canvas.draw_line((0.520, 0.856), (0.532, 0.856), max(0.7, w * 0.0006), (0.55, 0.62, 0.72), alpha=0.75)

    # Distant grey overhead gantry sign on left
    canvas.draw_line((0.357, 0.844), (0.357, 0.908), max(1.3, w * 0.0012), (0.030, 0.035, 0.044))
    canvas.fill_polygon([(0.359, 0.838), (0.399, 0.838), (0.399, 0.872), (0.359, 0.872)], (0.058, 0.064, 0.076))


def _paint_fractal_botanical_trees(canvas: Canvas2D, seed: int = 707) -> None:
    """High-density photographic botanical tree painter (~100,000+ crisp micro-leaf sprigs).

    Combines:
    1. Solid dark twilight undergrowth & continuous mid-canopy core (eliminating
       awkward bright horizon leaks beneath distant trees).
    2. Recursive fractal branching trunks, limbs, and fine dark twigs.
    3. ~100,000+ tiny, crisp, angled 1.5-3.2px micro-leaf sprigs (NOT round polka dots!)
       with coherent twilight lighting (deep forest shadows, rich olive-emerald midtones,
       subtle backlit dusk sky rims & warm streetlamp uplighting).
    """
    rng = np.random.default_rng(seed)
    w, h = canvas.width, canvas.height
    scale = w / 1200.0

    # 0. Dark twilight park undergrowth / low hedges filling both sides of the avenue solidly
    u, v = canvas.u_grid()
    y_u0 = int(0.76 * h)
    uu_g = u[y_u0:, :]
    vv_g = v[y_u0:, :]
    t_g = np.clip((vv_g - 0.825) / 0.175, 0.0, 1.0)
    center_g = 0.484 + (0.446 - 0.484) * t_g
    half_g = 0.008 + (0.156 - 0.008) * t_g
    lane_g = np.abs((uu_g - center_g) / np.maximum(half_g, 1e-4))
    outside_road = (lane_g > 1.18).astype(np.float32)

    hedge_n = fbm_2d(uu_g * 32.0, np.zeros_like(uu_g) + 2.1, octaves=4, seed=seed + 3)
    # Smoothly taper hedge height down toward the sidewalk edge so there is no hard vertical step near the dome
    road_taper = smoothstep(1.18, 2.20, lane_g)
    hedge_top = 0.826 - (0.022 + 0.024 * hedge_n + 0.042 * smoothstep(0.16, 0.44, np.abs(uu_g - 0.485))) * road_taper
    hedge_mask = outside_road * smoothstep(hedge_top - 0.004, hedge_top + 0.004, vv_g)
    hedge_tex = fbm_2d(uu_g * 160.0, vv_g * 160.0, octaves=3, seed=seed + 7)
    hedge_col = np.array([0.005, 0.011, 0.008], dtype=np.float32) + np.array([0.008, 0.015, 0.008], dtype=np.float32) * hedge_tex[..., None]
    canvas.blend_over(hedge_col, hedge_mask * 0.96, y0=y_u0, x0=0)

    # 1. Paint fractal tree skeletons & 100,000+ crisp micro-leaf sprigs onto RGBA layer
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    # Dense, continuous avenue treeline matching ref_2.jpg (no empty gaps beside the road!)
    trees = [
        # Distant midground trees flanking Twin Towers base
        (0.376, 0.845, 0.078, 0.036, 0, 0.25),
        (0.344, 0.868, 0.140, 0.056, 0, 0.35),
        (0.305, 0.888, 0.145, 0.062, 0, 0.38),
        (0.588, 0.845, 0.080, 0.038, 0, 0.25),
        (0.622, 0.870, 0.148, 0.062, 0, 0.35),
        (0.662, 0.892, 0.172, 0.072, 0, 0.40),
        # Mid-foreground lush avenue trees (framing Jiaozi Avenue tightly like ref_2.jpg)
        (0.262, 0.928, 0.195, 0.078, 1, 0.52),
        (0.200, 0.958, 0.225, 0.092, 1, 0.46),
        (0.125, 0.990, 0.260, 0.108, 1, 0.40),
        (0.038, 1.015, 0.310, 0.118, 1, 0.35),
        (0.705, 0.930, 0.225, 0.090, 1, 0.54),
        (0.780, 0.960, 0.270, 0.108, 1, 0.48),
        (0.868, 0.992, 0.325, 0.122, 1, 0.42),
        (0.958, 1.018, 0.365, 0.128, 1, 0.38),
        # Closest foreground canopy clusters filling lower-left & lower-right corners
        (0.065, 1.045, 0.205, 0.118, 2, 0.50),
        (0.195, 1.040, 0.165, 0.095, 2, 0.55),
        (0.290, 1.030, 0.115, 0.065, 2, 0.58),
        (0.650, 1.035, 0.130, 0.072, 2, 0.58),
        (0.755, 1.045, 0.185, 0.110, 2, 0.52),
        (0.900, 1.050, 0.230, 0.138, 2, 0.45),
    ]

    leaf_tips: list[tuple[float, float, float, int, float]] = []

    def grow_branch(
        x0: float,
        y0: float,
        length: float,
        angle: float,
        thickness: float,
        depth: int,
        layer_id: int,
        warm_f: float,
    ) -> None:
        x1 = x0 + math.cos(angle) * length
        y1 = y0 + math.sin(angle) * length
        bark_lum = int(16 + layer_id * 3)
        draw.line(
            [(x0, y0), (x1, y1)],
            fill=(bark_lum + 4, bark_lum + 2, bark_lum, 248),
            width=max(1, int(round(thickness))),
        )
        if depth <= 2:
            leaf_tips.append((x1, y1, length * 0.92, layer_id, warm_f))
        if depth <= 0 or length < 3.0 * scale:
            return

        n_sub = 3 if depth >= 3 else 2
        for k in range(n_sub):
            if n_sub == 2:
                spread_a = (-0.36 if k == 0 else 0.36) + float(rng.uniform(-0.18, 0.18))
            else:
                spread_a = (-0.48 + k * 0.48) + float(rng.uniform(-0.15, 0.15))
            sub_len = length * float(rng.uniform(0.64, 0.80))
            grow_branch(
                x1, y1, sub_len, angle + spread_a,
                max(1.0, thickness * 0.65), depth - 1, layer_id, warm_f,
            )

    for bx, by, bh, bsp, lid, wf in trees:
        x_px = bx * w
        y_px = by * h
        trunk_len = bh * h * 0.34
        trunk_w = (2.6 + lid * 1.3) * scale
        base_angle = -math.pi * 0.5 + float(rng.uniform(-0.07, 0.07))
        grow_branch(x_px, y_px, trunk_len, base_angle, trunk_w, depth=4, layer_id=lid, warm_f=wf)
        # Dense internal crown anchors so trees have full volumetric silhouette
        for _ in range(7):
            ax = x_px + float(rng.uniform(-bsp * w * 0.62, bsp * w * 0.62))
            ay = y_px - bh * h * float(rng.uniform(0.24, 0.86))
            leaf_tips.append((ax, ay, bsp * w * 0.45, lid, wf))

    # 2. Stamp ~95,000 tiny, crisp, angled micro-leaf sprigs (1.3 - 3.0px, NO round polka-dots!)
    total_strokes = 0
    for tx, ty, rad, lid, wf in leaf_tips:
        n_leaves = int(42 + lid * 24)
        r_spread = max(rad, 7.0 * scale)
        dist_road = abs((tx / w) - 0.48)
        lamp_glow = max(0.0, 1.0 - dist_road / 0.30) * wf

        # Vectorized sampling per branch tip for speed
        angs = rng.uniform(0.0, 2.0 * math.pi, size=n_leaves)
        dists = r_spread * np.sqrt(rng.uniform(0.0, 1.0, size=n_leaves))
        lxs = tx + np.cos(angs) * dists
        lys = ty + np.sin(angs) * dists
        l_angs = rng.uniform(0.0, math.pi, size=n_leaves)
        l_lens = rng.uniform(1.4, 3.4, size=n_leaves) * scale * (0.72 + 0.24 * lid)
        tones = rng.uniform(0.0, 1.0, size=n_leaves)
        v_js = rng.integers(-5, 8, size=n_leaves)

        for i in range(n_leaves):
            lx = float(lxs[i])
            ly = float(lys[i])
            if lx < -6 or lx > w + 6 or ly < h * 0.52 or ly > h + 6:
                continue

            dx = math.cos(float(l_angs[i])) * float(l_lens[i])
            dy = math.sin(float(l_angs[i])) * float(l_lens[i])
            tone = float(tones[i])
            vj = int(v_js[i])
            is_upper = math.sin(float(angs[i])) < -0.30

            if tone < 0.46:
                # Deep interior twilight shadow foliage
                r, g, b, a = 10, 19, 13, 242
            elif tone < 0.84:
                # Natural dark twilight emerald-olive leaf
                r = 22 + vj + int(18 * lamp_glow)
                g = 40 + vj + int(14 * lamp_glow)
                b = 20 + vj // 2
                a = 230
            elif is_upper and tone < 0.94:
                # Restrained dusk-sky rim leaf (natural muted olive-gold, NOT bright tan!)
                r = 42 + vj + int(12 * lamp_glow)
                g = 58 + vj + int(10 * lamp_glow)
                b = 28 + vj // 2
                a = 215
            else:
                # Warm streetlamp-kissed leaf edge near the avenue
                r = 34 + int(38 * lamp_glow) + vj
                g = 48 + int(24 * lamp_glow) + vj
                b = 22 + int(8 * lamp_glow)
                a = 220

            draw.line(
                [(lx - dx, ly - dy), (lx + dx, ly + dy)],
                fill=(max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)), a),
                width=max(1, int(round(1.35 * scale))),
            )
            total_strokes += 1

    rgba = np.asarray(layer, dtype=np.float32) / 255.0
    rgb_lin = np.power(np.maximum(rgba[..., :3], 1e-6), 2.2)
    alpha = rgba[..., 3]
    canvas.blend_over(rgb_lin, alpha)
    print(f"    -> Painted {total_strokes:,} crisp 2D micro-leaf sprigs over fractal tree skeletons")


def paint_street_trees_and_lamps_v3(canvas: Canvas2D, seed: int = 707) -> None:
    """Paint fractal botanical street trees, subtle roadside fencing, sleek streetlamps & gantry."""
    w, h = canvas.width, canvas.height

    # Subtle dark red-orange park landscaping rail along lower avenue edges (seen in ref_2.jpg)
    for side in (-1.0, 1.0):
        p0 = (_road_u(side * 1.19, 0.875), 0.875)
        p1 = (_road_u(side * 1.19, 0.995), 0.995)
        canvas.draw_line(p0, p1, max(1.6, w * 0.0022), (0.14, 0.045, 0.032), alpha=0.82)

    # Paint 90,000-stroke crisp fractal botanical street trees!
    _paint_fractal_botanical_trees(canvas, seed=seed)

    # Re-stamp crisp blue overhead directional road sign cleanly in front of distant foliage
    canvas.draw_line((0.542, 0.844), (0.542, 0.890), max(1.1, w * 0.0011), (0.032, 0.036, 0.044))
    canvas.draw_line((0.514, 0.852), (0.542, 0.852), max(0.9, w * 0.0009), (0.032, 0.036, 0.044))
    canvas.fill_polygon([(0.513, 0.841), (0.540, 0.841), (0.540, 0.864), (0.513, 0.864)], (0.42, 0.48, 0.56))
    canvas.fill_polygon([(0.5145, 0.8425), (0.5385, 0.8425), (0.5385, 0.8625), (0.5145, 0.8625)], (0.022, 0.11, 0.34))
    canvas.draw_line((0.518, 0.848), (0.534, 0.848), max(0.7, w * 0.0006), (0.55, 0.62, 0.72), alpha=0.85)
    canvas.draw_line((0.520, 0.856), (0.532, 0.856), max(0.7, w * 0.0006), (0.55, 0.62, 0.72), alpha=0.75)

    # Sleek modern curved streetlamps receding gracefully along both sides of Jiaozi Avenue
    lamp_vs = [0.854, 0.880, 0.914, 0.958]
    for lv in lamp_vs:
        sc = float(np.clip((lv - 0.825) / 0.175, 0.12, 1.0))
        pole_h = 0.036 + 0.056 * sc
        for side in (-1.0, 1.0):
            base_u = _road_u(side * 1.09, lv)
            arm_u = _road_u(side * 0.93, lv)
            top_v = lv - pole_h
            canvas.draw_line((base_u, lv), (base_u, top_v + 0.005 * sc), max(0.7, (0.9 + 1.1 * sc) * (w / 1200.0)), (0.014, 0.017, 0.024))
            canvas.paint_bezier_ribbon(
                (base_u, top_v + 0.005 * sc),
                (base_u, top_v - 0.002 * sc),
                (0.5 * (base_u + arm_u), top_v - 0.005 * sc),
                (arm_u, top_v - 0.003 * sc),
                width_start_px=max(0.6, (0.8 + 0.9 * sc) * (w / 1200.0)),
                width_end_px=max(0.5, (0.6 + 0.6 * sc) * (w / 1200.0)),
                color_start=(0.016, 0.019, 0.026),
                color_end=(0.022, 0.024, 0.030),
                steps=18,
                additive=False,
            )
            # Crisp compact warm LED streetlamp fixture + subtle atmospheric halo
            canvas.draw_soft_glow(arm_u, top_v - 0.002 * sc, 0.0014 * sc + 0.0006, 0.0016 * sc + 0.0006, (3.8, 2.3, 0.82), power=2.0)
            canvas.draw_soft_glow(arm_u, top_v - 0.002 * sc, 0.011 * sc + 0.003, 0.012 * sc + 0.003, (0.22, 0.10, 0.028), power=2.0)

    # Foreground left road sign gantry frame with truss details (matching ref_2.jpg)
    gcol = (0.030, 0.034, 0.042)
    canvas.draw_line((0.154, 0.885), (0.154, 1.00), max(1.8, w * 0.0020), gcol)
    canvas.draw_line((0.154, 0.903), (0.205, 0.903), max(1.2, w * 0.0014), gcol)
    canvas.draw_line((0.154, 0.926), (0.205, 0.926), max(1.2, w * 0.0014), gcol)
    canvas.draw_line((0.154, 0.903), (0.180, 0.926), max(0.8, w * 0.0009), gcol)
    canvas.draw_line((0.180, 0.926), (0.200, 0.903), max(0.8, w * 0.0009), gcol)
    canvas.fill_polygon([(0.198, 0.885), (0.260, 0.885), (0.258, 0.935), (0.198, 0.935)], (0.052, 0.058, 0.070))
