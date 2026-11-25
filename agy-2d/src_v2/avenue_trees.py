"""Pure 2D perspective painting of Jiaozi Avenue (交子大道), dusk traffic, streetlamps & lush trees (v2.2).

Fixes tree bounding-box transparency artifacts completely (pure organic feathery
leaf-cluster silhouettes!), anchors the ground/curbs cleanly, and refines
streetlamps and dusk traffic.
"""

from __future__ import annotations

import numpy as np

from canvas2d import Canvas2D
from noise2d import fbm_2d, smoothstep


def _road_u(lane_s: float, v: float) -> float:
    t = np.clip((v - 0.825) / (1.000 - 0.825), 0.0, 1.0)
    center = 0.484 + (0.446 - 0.484) * t
    half_w = 0.008 + (0.156 - 0.008) * t
    return float(center + lane_s * half_w)


def paint_jiaozi_avenue_and_traffic(canvas: Canvas2D, seed: int = 606) -> None:
    """Paint the converging twilight Jiaozi Avenue asphalt, markings, signs, and dusk cars."""
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
    sidewalk_mask = ((np.abs(lane_s) > 1.02) & (np.abs(lane_s) <= 1.24)).astype(np.float32) * (vv >= 0.828)

    asphalt_noise = fbm_2d(lane_s * 14.0, (1.0 / (t + 0.08)) * 4.5, octaves=4, seed=seed + 11, rotate=False)
    sky_sheen = np.exp(-((lane_s * 0.9) ** 2)) * (0.28 + 0.72 * (1.0 - t))
    asphalt = (
        np.array([0.020, 0.023, 0.034], dtype=np.float32)
        + np.array([0.016, 0.016, 0.022], dtype=np.float32) * asphalt_noise[..., None]
        + np.array([0.095, 0.052, 0.030], dtype=np.float32) * (sky_sheen * (0.65 + 0.35 * asphalt_noise))[..., None]
    )
    canvas.blend_over(asphalt, road_mask, y0=y_start, x0=0)

    sidewalk_col = np.array([0.038, 0.042, 0.054], dtype=np.float32) + 0.012 * asphalt_noise[..., None]
    canvas.blend_over(sidewalk_col, sidewalk_mask, y0=y_start, x0=0)

    # Crisp perspective road markings
    z_dist = 1.0 / (t + 0.045)
    in_crosswalk = (vv >= 0.891) & (vv <= 0.903)

    yl1 = np.exp(-(((lane_s - 0.005) / 0.014) ** 2))
    yl2 = np.exp(-(((lane_s - 0.038) / 0.014) ** 2))
    yellow_mask = np.clip((yl1 + yl2), 0.0, 1.0) * smoothstep(0.834, 0.846, vv)
    yellow_mask = np.where(in_crosswalk, 0.0, yellow_mask)
    yellow_col = np.array([0.65, 0.42, 0.09], dtype=np.float32)
    canvas.blend_over(yellow_col[None, None, :], yellow_mask * 0.86, y0=y_start, x0=0)

    dash_pattern = (np.sin(z_dist * 3.8) > 0.05).astype(np.float32)
    w_dash = (
        np.exp(-(((lane_s + 0.50) / 0.013) ** 2))
        + np.exp(-(((lane_s - 0.50) / 0.013) ** 2))
    ) * dash_pattern * smoothstep(0.840, 0.855, vv)
    w_dash = np.where(in_crosswalk, 0.0, w_dash)

    curb_lines = (
        np.exp(-(((lane_s + 0.95) / 0.014) ** 2)) + np.exp(-(((lane_s - 0.95) / 0.014) ** 2))
    ) * smoothstep(0.834, 0.848, vv)

    zebra = (np.sin(lane_s * 34.0) > 0.0).astype(np.float32) * in_crosswalk.astype(np.float32) * (np.abs(lane_s) < 0.92)
    white_mask = np.clip(w_dash + curb_lines * 0.82 + zebra * 0.74, 0.0, 1.0)
    white_col = np.array([0.48, 0.50, 0.56], dtype=np.float32)
    canvas.blend_over(white_col[None, None, :], white_mask * 0.80, y0=y_start, x0=0)

    # Subtle twilight traffic light trails
    for ls, is_inc in [(-0.28, False), (-0.65, False), (0.24, True), (0.58, True)]:
        p0 = (_road_u(ls, 0.846), 0.846)
        p1 = (_road_u(ls, 0.895), 0.895)
        p2 = (_road_u(ls, 0.945), 0.945)
        p3 = (_road_u(ls, 0.998), 0.998)
        if is_inc:
            canvas.paint_bezier_ribbon(
                p0, p1, p2, p3,
                width_start_px=max(0.45, w * 0.00038),
                width_end_px=max(1.3, w * 0.0011),
                color_start=(0.50, 0.38, 0.20),
                color_end=(0.88, 0.72, 0.44),
                steps=90,
                additive=True,
            )
        else:
            canvas.paint_bezier_ribbon(
                p0, p1, p2, p3,
                width_start_px=max(0.45, w * 0.00038),
                width_end_px=max(1.4, w * 0.0012),
                color_start=(0.72, 0.08, 0.04),
                color_end=(1.30, 0.13, 0.06),
                steps=90,
                additive=True,
            )

    cars = [
        (0.955, 0.22, True, (0.14, 0.15, 0.18)),
        (0.922, 0.28, True, (0.03, 0.035, 0.045)),
        (0.906, 0.42, True, (0.13, 0.14, 0.17)),
        (0.888, 0.18, True, (0.04, 0.045, 0.055)),
        (0.875, 0.36, True, (0.12, 0.12, 0.14)),
        (0.862, 0.24, True, (0.05, 0.05, 0.06)),
        (0.935, -0.30, False, (0.04, 0.045, 0.06)),
        (0.898, -0.22, False, (0.08, 0.085, 0.10)),
        (0.876, -0.38, False, (0.04, 0.04, 0.05)),
        (0.860, -0.18, False, (0.07, 0.07, 0.08)),
    ]

    for vc, ls, is_inc, bcol in sorted(cars, key=lambda c: c[0]):
        scale_c = np.clip((vc - 0.825) / 0.175, 0.08, 1.0)
        cu = _road_u(ls, vc)
        cw = 0.015 * scale_c + 0.003
        ch = 0.016 * scale_c + 0.003

        canvas.fill_polygon(
            [
                (cu - cw * 1.15, vc + ch * 0.25),
                (cu + cw * 1.15, vc + ch * 0.25),
                (cu + cw * 1.05, vc + ch * 0.65),
                (cu - cw * 1.05, vc + ch * 0.65),
            ],
            (0.004, 0.005, 0.008),
            alpha=0.85,
        )
        canvas.fill_polygon(
            [
                (cu - cw, vc - ch * 0.15),
                (cu + cw, vc - ch * 0.15),
                (cu + cw * 1.04, vc + ch * 0.45),
                (cu - cw * 1.04, vc + ch * 0.45),
            ],
            bcol,
        )
        canvas.fill_polygon(
            [
                (cu - cw * 0.72, vc - ch * 0.72),
                (cu + cw * 0.72, vc - ch * 0.72),
                (cu + cw * 0.92, vc - ch * 0.12),
                (cu - cw * 0.92, vc - ch * 0.12),
            ],
            (bcol[0] * 0.75, bcol[1] * 0.78, bcol[2] * 0.85),
        )
        canvas.fill_polygon(
            [
                (cu - cw * 0.60, vc - ch * 0.62),
                (cu + cw * 0.60, vc - ch * 0.62),
                (cu + cw * 0.76, vc - ch * 0.18),
                (cu - cw * 0.76, vc - ch * 0.18),
            ],
            (0.010, 0.014, 0.026),
        )

        ly = vc + ch * 0.12
        for side in (-0.72, 0.72):
            lx = cu + side * cw
            if is_inc:
                canvas.draw_soft_glow(lx, ly, 0.0020 * scale_c + 0.0007, 0.0024 * scale_c + 0.0007, (3.2, 2.6, 1.8), power=2.0)
                canvas.draw_soft_glow(lx, ly + ch * 0.55, 0.007 * scale_c + 0.002, 0.005 * scale_c + 0.001, (0.32, 0.25, 0.14), power=2.0)
            else:
                canvas.draw_soft_glow(lx, ly, 0.0020 * scale_c + 0.0007, 0.0022 * scale_c + 0.0007, (3.6, 0.26, 0.12), power=2.0)
                canvas.draw_soft_glow(lx, ly + ch * 0.50, 0.007 * scale_c + 0.002, 0.005 * scale_c + 0.001, (0.38, 0.04, 0.02), power=2.0)

    # Blue directional road sign on right (matching ref_2.jpg)
    canvas.draw_line((0.542, 0.846), (0.542, 0.888), max(1.1, w * 0.0011), (0.035, 0.040, 0.050))
    canvas.draw_line((0.514, 0.852), (0.542, 0.852), max(0.9, w * 0.0009), (0.035, 0.040, 0.050))
    canvas.fill_polygon(
        [(0.514, 0.842), (0.539, 0.842), (0.539, 0.863), (0.514, 0.863)],
        (0.025, 0.12, 0.36),
    )
    canvas.draw_line((0.518, 0.848), (0.534, 0.848), max(0.7, w * 0.0006), (0.50, 0.56, 0.66), alpha=0.8)
    canvas.draw_line((0.520, 0.855), (0.532, 0.855), max(0.7, w * 0.0006), (0.50, 0.56, 0.66), alpha=0.7)

    # Distant grey gantry sign on left
    canvas.draw_line((0.357, 0.845), (0.357, 0.905), max(1.3, w * 0.0012), (0.035, 0.040, 0.050))
    canvas.fill_polygon(
        [(0.359, 0.839), (0.399, 0.839), (0.399, 0.872), (0.359, 0.872)],
        (0.062, 0.068, 0.080),
    )


def _paint_tree_canopy_layer(
    canvas: Canvas2D,
    centers: list[tuple[float, float, float, float]],
    base_col: tuple[float, float, float],
    rim_col: tuple[float, float, float],
    warm_col: tuple[float, float, float],
    seed: int,
) -> None:
    """Paint organic multi-clustered twilight street trees with zero bounding-box artifacts."""
    rng = np.random.default_rng(seed)
    w, h = canvas.width, canvas.height
    u, v = canvas.u_grid()

    y_min = max(0, int((min(c[1] - c[3] * 1.4 for c in centers) - 0.03) * h))
    y_max = min(h, int((max(c[1] + c[3] * 1.4 for c in centers) + 0.03) * h))
    if y_max <= y_min:
        return

    uu = u[y_min:y_max, :]
    vv = v[y_min:y_max, :]
    dens = np.zeros_like(uu, dtype=np.float32)
    top_rim = np.zeros_like(uu, dtype=np.float32)

    leaf_macro = fbm_2d(uu * 46.0, vv * 38.0, octaves=4, seed=seed + 11)
    leaf_micro = fbm_2d(uu * 175.0, vv * 145.0, octaves=4, seed=seed + 29)
    leaf_tex = leaf_macro * 0.50 + leaf_micro * 0.50

    for cx, cy, rx, ry in centers:
        # 9 overlapping organic sub-crowns per tree for authentic feathery canopy silhouettes
        for _ in range(9):
            ox = cx + float(rng.uniform(-rx * 0.50, rx * 0.50))
            oy = cy + float(rng.uniform(-ry * 0.45, ry * 0.40))
            srx = rx * float(rng.uniform(0.38, 0.76))
            sry = ry * float(rng.uniform(0.38, 0.78))
            dx = (uu - ox) / max(srx, 1e-4)
            dy = (vv - oy) / max(sry, 1e-4)
            d2 = dx * dx + dy * dy
            blob = np.clip(1.0 - d2, 0.0, 1.0)
            dens = np.maximum(dens, blob)
            rim = np.clip(1.0 - d2, 0.0, 1.0) * smoothstep(0.15, -0.75, dy)
            top_rim = np.maximum(top_rim, rim)

    # Strictly zero outside tree crowns (dens == 0 -> alpha == 0!) with feathery leafy edges
    edge_mask = smoothstep(0.02, 0.24, dens)
    foliage_alpha = edge_mask * smoothstep(0.24, 0.58, dens * 0.76 + (leaf_tex - 0.30) * 0.52)

    # Rich dark twilight green foliage with internal leaf-cluster depth + warm streetlamp uplight
    crevice = 0.40 + 0.60 * leaf_micro
    col = (
        np.array(base_col, dtype=np.float32) * crevice[..., None]
        + np.array(rim_col, dtype=np.float32) * (top_rim * leaf_micro * 0.62)[..., None]
        + np.array(warm_col, dtype=np.float32) * (smoothstep(0.75, 0.96, vv) * leaf_macro * 0.42)[..., None]
    )
    canvas.blend_over(col, foliage_alpha * 0.98, y0=y_min, x0=0)


def paint_street_trees_and_lamps(canvas: Canvas2D, seed: int = 707) -> None:
    """Paint lush twilight ginkgo/camphor street trees and sleek streetlamps lining Jiaozi Avenue."""
    w, h = canvas.width, canvas.height

    # Tree trunks along left & right sidewalks
    trunks = [
        (0.06, 1.00, 0.06, 0.76, 3.2),
        (0.14, 1.00, 0.14, 0.78, 2.8),
        (0.22, 0.98, 0.22, 0.80, 2.2),
        (0.29, 0.95, 0.29, 0.81, 1.8),
        (0.35, 0.90, 0.35, 0.82, 1.4),
        (0.62, 0.92, 0.62, 0.79, 1.8),
        (0.70, 0.97, 0.70, 0.76, 2.4),
        (0.80, 1.00, 0.80, 0.73, 3.0),
        (0.91, 1.00, 0.91, 0.71, 3.4),
    ]
    for x0, y0, x1, y1, lw in trunks:
        canvas.draw_line((x0, y0), (x1, y1), max(1.2, lw * (w / 1200.0)), (0.010, 0.009, 0.010))

    # Layer 1: Distant midground trees framing the Twin Towers base (matching ref_2.jpg!)
    far_trees = [
        (0.378, 0.815, 0.028, 0.036),
        (0.342, 0.792, 0.038, 0.068),
        (0.305, 0.802, 0.044, 0.065),
        (0.588, 0.812, 0.032, 0.042),
        (0.628, 0.785, 0.046, 0.075),
        (0.675, 0.778, 0.055, 0.088),
    ]
    _paint_tree_canopy_layer(
        canvas, far_trees,
        base_col=(0.014, 0.032, 0.022),
        rim_col=(0.09, 0.07, 0.055),
        warm_col=(0.065, 0.038, 0.014),
        seed=seed + 10,
    )

    # Layer 2: Lush avenue treeline (left rising to ~0.70, right rising tall to ~0.63 matching ref_2.jpg!)
    mid_trees = [
        (0.258, 0.848, 0.058, 0.095),
        (0.192, 0.822, 0.068, 0.118),
        (0.118, 0.838, 0.078, 0.130),
        (0.038, 0.815, 0.088, 0.155),
        # Right dense lush treeline
        (0.668, 0.842, 0.068, 0.110),
        (0.748, 0.805, 0.082, 0.138),
        (0.840, 0.772, 0.095, 0.162),
        (0.945, 0.752, 0.105, 0.185),
    ]
    _paint_tree_canopy_layer(
        canvas, mid_trees,
        base_col=(0.010, 0.028, 0.018),
        rim_col=(0.075, 0.062, 0.048),
        warm_col=(0.095, 0.052, 0.018),
        seed=seed + 50,
    )

    # Layer 3: Closest lush foreground foliage filling bottom-left & bottom-right seamlessly
    near_trees = [
        (0.030, 0.945, 0.115, 0.120),
        (0.155, 0.960, 0.105, 0.100),
        (0.245, 0.965, 0.065, 0.075),
        (0.680, 0.950, 0.095, 0.095),
        (0.795, 0.935, 0.125, 0.120),
        (0.935, 0.915, 0.130, 0.145),
    ]
    _paint_tree_canopy_layer(
        canvas, near_trees,
        base_col=(0.007, 0.020, 0.014),
        rim_col=(0.052, 0.046, 0.036),
        warm_col=(0.085, 0.046, 0.016),
        seed=seed + 90,
    )

    # Sleek modern curved streetlamps receding gracefully along both sides of Jiaozi Avenue
    lamp_vs = [0.854, 0.880, 0.914, 0.958]
    for lv in lamp_vs:
        sc = np.clip((lv - 0.825) / 0.175, 0.12, 1.0)
        pole_h = 0.036 + 0.056 * sc
        for side in (-1.0, 1.0):
            base_u = _road_u(side * 1.09, lv)
            arm_u = _road_u(side * 0.93, lv)
            top_v = lv - pole_h
            # Slender dark pole + gently arched lamp arm
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
            # Crisp warm 2800K streetlamp glow + soft amber halo
            canvas.draw_soft_glow(arm_u, top_v - 0.002 * sc, 0.0016 * sc + 0.0007, 0.0020 * sc + 0.0007, (3.4, 1.95, 0.65), power=2.0)
            canvas.draw_soft_glow(arm_u, top_v - 0.002 * sc, 0.013 * sc + 0.004, 0.015 * sc + 0.004, (0.24, 0.11, 0.03), power=2.0)

    # Foreground left road sign gantry frame (matching ref_2.jpg)
    canvas.draw_line((0.154, 0.885), (0.154, 1.00), max(1.6, w * 0.0019), (0.026, 0.030, 0.038))
    canvas.draw_line((0.154, 0.905), (0.205, 0.905), max(1.2, w * 0.0014), (0.026, 0.030, 0.038))
    canvas.draw_line((0.154, 0.928), (0.205, 0.928), max(1.2, w * 0.0014), (0.026, 0.030, 0.038))
    canvas.fill_polygon(
        [(0.198, 0.885), (0.260, 0.885), (0.258, 0.935), (0.198, 0.935)],
        (0.048, 0.054, 0.066),
    )
