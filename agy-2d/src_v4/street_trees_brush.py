"""Pure Brushstroke Jiaozi Avenue, Painterly Dusk Cars & 100,000-Stroke Botanical Trees (v4).

Replaces rigid polygon cars and sterile vector road stripes with layered
impressionistic-to-photorealistic physical brushstrokes:
- Converging perspective asphalt brushstrokes, worn tire tracks, broken hand-painted
  yellow/white lane markings, curbs & bike lanes.
- Organic multi-brushstroke twilight cars (40-60 dabs/strokes per car: soft shadow,
  curved glossy roof & hood sky-reflection strokes, dark glass, compact bright LED
  lights & painterly shimmering vertical reflections on the asphalt!).
- Recursive fractal tree branches & ~95,000 crisp individual micro-leaf brushstrokes.
"""

from __future__ import annotations

import math
import numpy as np

from brush_engine import BrushCanvas


def _road_u(lane_s: float, v: float) -> float:
    t = max(0.0, min(1.0, (v - 0.825) / 0.175))
    center = 0.484 + (0.446 - 0.484) * t
    half_w = 0.008 + (0.156 - 0.008) * t
    return float(center + lane_s * half_w)


def _paint_painterly_dusk_car(
    bc: BrushCanvas,
    vc: float,
    ls: float,
    is_oncoming: bool,
    body_srgb: tuple[float, float, float],
    is_suv: bool = False,
) -> None:
    """Paint a realistic twilight car purely with layered soft & crisp brushstrokes (no cartoon polygons!)."""
    w, h = bc.width, bc.height
    sc = bc.scale
    scale_c = max(0.10, min(1.0, (vc - 0.825) / 0.175))
    cu = _road_u(ls, vc) * w
    cy = vc * h
    cw = ((0.0145 if not is_suv else 0.0165) * scale_c + 0.0024) * w
    ch = ((0.0142 if not is_suv else 0.0172) * scale_c + 0.0022) * h

    # 1. Soft dark underbody contact shadow dabs on the asphalt
    bc.dab(cu, cy + ch * 0.44, cw * 1.18, ch * 0.34, color=(0.03, 0.04, 0.06), alpha=0.88)
    bc.dab(cu, cy + ch * 0.50, cw * 1.05, ch * 0.24, color=(0.02, 0.02, 0.04), alpha=0.92)

    # 2. Dark wheel/tire dabs
    for s in (-1.0, 1.0):
        bc.dab(cu + s * cw * 0.82, cy + ch * 0.42, cw * 0.22, ch * 0.22, color=(0.04, 0.05, 0.07), alpha=0.95)

    # 3. Lower body & bumper brushstrokes (slightly darker, textured)
    bc.bristle_stroke(
        cu - cw * 0.96, cy + ch * 0.16, cu + cw * 0.96, cy + ch * 0.16,
        width_px=max(2.0, ch * 0.52),
        color=(body_srgb[0] * 0.72, body_srgb[1] * 0.74, body_srgb[2] * 0.78),
        alpha=0.96,
        bristles=3,
        jitter_col=0.02,
    )
    # Glossy curved hood / trunk top catching warm apricot sunset sheen!
    bc.curved_bristle_stroke(
        [(cu - cw * 0.88, cy - ch * 0.08), (cu, cy - ch * 0.14), (cu + cw * 0.88, cy - ch * 0.08)],
        width_px=max(1.5, ch * 0.26),
        color=(min(1.0, body_srgb[0] * 1.18 + 0.14), min(1.0, body_srgb[1] * 1.10 + 0.10), min(1.0, body_srgb[2] * 1.05 + 0.08)),
        alpha=0.90,
        bristles=2,
        jitter_col=0.018,
    )

    # 4. Cabin silhouette & curved roof brushstroke catching twilight sky
    bc.dab(cu, cy - ch * 0.36, cw * 0.78, ch * 0.34, color=body_srgb, alpha=0.95)
    bc.curved_bristle_stroke(
        [(cu - cw * 0.62, cy - ch * 0.64), (cu, cy - ch * 0.68), (cu + cw * 0.62, cy - ch * 0.64)],
        width_px=max(1.2, ch * 0.18),
        color=(min(1.0, body_srgb[0] * 1.25 + 0.18), min(1.0, body_srgb[1] * 1.18 + 0.14), min(1.0, body_srgb[2] * 1.15 + 0.14)),
        alpha=0.88,
        bristles=2,
    )

    # 5. Dark glass windshield / rear window with soft dusk sky reflection dab
    bc.dab(cu, cy - ch * 0.38, cw * 0.64, ch * 0.22, color=(0.08, 0.10, 0.16), alpha=0.92)
    bc.bristle_stroke(
        cu - cw * 0.48, cy - ch * 0.48, cu + cw * 0.48, cy - ch * 0.48,
        width_px=max(1.0, ch * 0.14),
        color=(0.38, 0.32, 0.36),
        alpha=0.58,
        bristles=2,
    )

    # 6. Tiny side mirror dabs & license plate glint
    for s in (-1.0, 1.0):
        bc.dab(cu + s * cw * 0.90, cy - ch * 0.20, cw * 0.12, ch * 0.09, color=body_srgb, alpha=0.90)
    if scale_c > 0.26:
        bc.bristle_stroke(cu - cw * 0.16, cy + ch * 0.20, cu + cw * 0.16, cy + ch * 0.20, width_px=max(1.0, ch * 0.14), color=(0.18, 0.34, 0.65), alpha=0.85, bristles=1)

    # 7. Compact intense LED headlights / red taillights + painterly vertical asphalt reflection strokes!
    ly_u = (cy + ch * 0.08) / h
    for side in (-0.72, 0.72):
        lx_u = (cu + side * cw) / w
        if is_oncoming:
            bc.soft_glow_dab(lx_u, ly_u, 0.0014 * scale_c + 0.0005, 0.0015 * scale_c + 0.0005, (3.8, 3.3, 2.4))
            bc.soft_glow_dab(lx_u, ly_u, 0.0046 * scale_c + 0.0012, 0.0042 * scale_c + 0.0012, (0.48, 0.38, 0.22))
            bc.soft_glow_dab(lx_u, ly_u + (ch * 0.75) / h, 0.0032 * scale_c + 0.001, 0.011 * scale_c + 0.002, (0.20, 0.15, 0.09))
        else:
            bc.soft_glow_dab(lx_u, ly_u, 0.0015 * scale_c + 0.0005, 0.0014 * scale_c + 0.0005, (4.0, 0.22, 0.09))
            bc.soft_glow_dab(lx_u, ly_u, 0.0048 * scale_c + 0.0012, 0.0040 * scale_c + 0.0012, (0.48, 0.045, 0.02))
            bc.soft_glow_dab(lx_u, ly_u + (ch * 0.70) / h, 0.0034 * scale_c + 0.001, 0.011 * scale_c + 0.002, (0.24, 0.025, 0.012))


def paint_jiaozi_avenue_by_strokes(bc: BrushCanvas) -> None:
    """Paint converging Jiaozi Avenue asphalt, markings, signs & painterly dusk cars by brushstrokes."""
    w, h = bc.width, bc.height
    sc = bc.scale
    rng = bc.rng

    bc.begin_layer()
    # 1. Perspective asphalt & bike-lane brushstrokes converging toward the Twin Towers vanishing point!
    n_strips = 42
    for i in range(n_strips):
        ls = -1.18 + (i + 0.5) / n_strips * 2.36
        is_bike = abs(ls) > 1.02
        # Darken dual tire-wear paths slightly
        in_track = min(abs(ls + 0.72), abs(ls + 0.28), abs(ls - 0.28), abs(ls - 0.72)) < 0.12
        # Center lanes catch subtle warm sunset & Twin Towers reflection sheen
        sheen = math.exp(-((ls * 0.9) ** 2))

        n_segs = 18
        for s in range(n_segs):
            v0 = 0.824 + (s / n_segs) * 0.178
            v1 = 0.824 + ((s + 1.15) / n_segs) * 0.178
            vm = 0.5 * (v0 + v1)
            t = (vm - 0.825) / 0.175
            u0, u1 = _road_u(ls, v0), _road_u(ls, v1)
            seg_w = max(2.0, (0.009 + 0.16 * t) * 2.4 * w / n_strips * 1.45)

            if is_bike:
                col = (0.24, 0.27, 0.32)
            else:
                base = 0.15 if in_track else 0.19
                # Subtle warm sky reflection strongest near distant center
                warm_s = sheen * (0.35 + 0.65 * (1.0 - t)) * 0.16
                col = (base + warm_s * 1.15, base + 0.01 + warm_s * 0.75, base + 0.04 + warm_s * 0.40)

            bc.bristle_stroke(
                u0 * w, v0 * h, u1 * w, v1 * h,
                width_px=seg_w,
                color=col,
                alpha=0.95,
                bristles=3,
                jitter_col=0.022,
            )

    # 2. Painterly weathered road markings (double yellow center line, white dashes, crosswalk & arrows)
    # Double yellow center line
    for y_ls in (0.006, 0.036):
        for s in range(20):
            v0 = 0.836 + (s / 20.0) * 0.164
            v1 = 0.836 + ((s + 0.92) / 20.0) * 0.164
            if 0.890 <= v0 <= 0.903:
                continue
            t = (v0 - 0.825) / 0.175
            bc.bristle_stroke(
                _road_u(y_ls, v0) * w, v0 * h, _road_u(y_ls, v1) * w, v1 * h,
                width_px=max(0.8, (0.7 + 2.4 * t) * sc),
                color=(0.72, 0.56, 0.24),
                alpha=float(rng.uniform(0.68, 0.86)),
                bristles=2,
                jitter_col=0.025,
            )

    # White dashed lane dividers & curb lines
    for ls_d in (-0.50, 0.50):
        for s in range(0, 16, 2):
            v0 = 0.844 + (s / 16.0) * 0.154
            v1 = 0.844 + ((s + 1.05) / 16.0) * 0.154
            if 0.889 <= v0 <= 0.904:
                continue
            t = (v0 - 0.825) / 0.175
            bc.bristle_stroke(
                _road_u(ls_d, v0) * w, v0 * h, _road_u(ls_d, v1) * w, v1 * h,
                width_px=max(0.7, (0.6 + 2.2 * t) * sc),
                color=(0.60, 0.62, 0.66),
                alpha=float(rng.uniform(0.62, 0.82)),
                bristles=2,
            )

    for ls_c in (-0.96, 0.96):
        bc.bristle_stroke(
            _road_u(ls_c, 0.835) * w, 0.835 * h, _road_u(ls_c, 1.00) * w, 1.00 * h,
            width_px=max(1.2, 2.2 * sc),
            color=(0.56, 0.58, 0.62),
            alpha=0.72,
            bristles=2,
        )

    # Weathered zebra crosswalk stripes at v = 0.892..0.903
    for k in range(11):
        ls_z = -0.85 + (k / 10.0) * 1.70
        bc.bristle_stroke(
            _road_u(ls_z, 0.892) * w, 0.892 * h, _road_u(ls_z, 0.903) * w, 0.903 * h,
            width_px=max(1.8, 3.8 * sc),
            color=(0.58, 0.60, 0.64),
            alpha=0.72,
            bristles=2,
        )

    # Painted white directional arrows on open foreground asphalt
    for a_ls, a_v in [(0.72, 0.932), (-0.68, 0.945), (-0.24, 0.966)]:
        t = (a_v - 0.825) / 0.175
        bc.bristle_stroke(
            _road_u(a_ls, a_v + 0.016 * t) * w, (a_v + 0.016 * t) * h,
            _road_u(a_ls, a_v - 0.014 * t) * w, (a_v - 0.014 * t) * h,
            width_px=max(1.5, 3.0 * t * sc),
            color=(0.56, 0.58, 0.62),
            alpha=0.66,
            bristles=2,
        )
        bc.dab(_road_u(a_ls, a_v - 0.012 * t) * w, (a_v - 0.012 * t) * h, 4.5 * t * sc, 3.2 * t * sc, color=(0.56, 0.58, 0.62), alpha=0.62)

    bc.commit_layer(blur_px=0.35)

    # 3. Paint all dusk cars purely with layered brushstrokes (back-to-front!)
    bc.begin_layer()
    cars = [
        (0.956, 0.22, True, (0.48, 0.49, 0.52), False),
        (0.920, 0.29, True, (0.14, 0.16, 0.19), True),
        (0.905, 0.45, True, (0.44, 0.45, 0.48), True),
        (0.888, 0.18, True, (0.18, 0.19, 0.22), False),
        (0.875, 0.36, True, (0.40, 0.41, 0.44), False),
        (0.862, 0.24, True, (0.20, 0.22, 0.25), False),
        (0.938, -0.30, False, (0.16, 0.18, 0.22), True),
        (0.896, -0.22, False, (0.34, 0.36, 0.40), False),
        (0.874, -0.38, False, (0.18, 0.19, 0.22), False),
        (0.858, -0.18, False, (0.32, 0.34, 0.38), False),
    ]
    for vc, ls, is_inc, bcol, is_suv in sorted(cars, key=lambda c: c[0]):
        _paint_painterly_dusk_car(bc, vc, ls, is_inc, bcol, is_suv=is_suv)
    bc.commit_layer(blur_px=0.20)

    # Tiny crisp intersection traffic signals
    bc.soft_glow_dab(0.464, 0.846, 0.0010, 0.0014, (3.2, 0.20, 0.10))
    bc.soft_glow_dab(0.504, 0.846, 0.0010, 0.0014, (0.20, 2.8, 0.55))


def paint_trees_and_street_furniture_by_strokes(bc: BrushCanvas) -> None:
    """Paint dark park undergrowth, fractal branching trees, ~95,000 crisp leaf strokes & lamps."""
    w, h = bc.width, bc.height
    sc = bc.scale
    rng = bc.rng

    bc.begin_layer()
    # 1. Dark twilight park undergrowth / low hedges painted with broad soft foliage strokes
    for side in (-1.0, 1.0):
        # Red-orange roadside park fencing stroke
        bc.bristle_stroke(
            _road_u(side * 1.19, 0.875) * w, 0.875 * h,
            _road_u(side * 1.19, 0.995) * w, 0.995 * h,
            width_px=max(1.8, 2.8 * sc),
            color=(0.38, 0.19, 0.14),
            alpha=0.82,
            bristles=2,
        )
        # Continuous dark twilight park ground & low hedge brushstrokes (no bright horizon gaps or sticks!)
        for k in range(36):
            f = k / 35.0
            vf = 0.830 + f * 0.175
            u_inner = _road_u(side * 1.22, vf)
            u_outer = 0.0 if side < 0 else 1.0
            bc.bristle_stroke(
                u_inner * w, vf * h, u_outer * w, vf * h,
                width_px=max(5.0, 9.5 * sc),
                color=(0.045, 0.075, 0.055),
                alpha=0.96,
                bristles=2,
                jitter_col=0.012,
            )
            # Soft dark micro-foliage texture strokes along the roadside hedge top
            for m in range(14):
                mf = (m + float(rng.uniform(0.05, 0.95))) / 14.0
                uu = u_inner + (u_outer - u_inner) * mf
                vv = vf - 0.008 * mf + float(rng.uniform(-0.005, 0.005))
                ang = float(rng.uniform(0.0, math.pi))
                ln = float(rng.uniform(1.8, 3.8)) * sc
                bc._draw.line(
                    [(uu * w - math.cos(ang) * ln, vv * h - math.sin(ang) * ln),
                     (uu * w + math.cos(ang) * ln, vv * h + math.sin(ang) * ln)],
                    fill=(14, 26, 18, 225),
                    width=max(1, int(round(1.6 * sc))),
                )
                bc.total_strokes += 1

    # 2. Recursive fractal tree skeletons + ~95,000 crisp angled micro-leaf brushstrokes!
    trees = [
        (0.376, 0.845, 0.078, 0.036, 0, 0.25),
        (0.344, 0.868, 0.140, 0.056, 0, 0.35),
        (0.305, 0.888, 0.145, 0.062, 0, 0.38),
        (0.588, 0.845, 0.080, 0.038, 0, 0.25),
        (0.622, 0.870, 0.148, 0.062, 0, 0.35),
        (0.662, 0.892, 0.172, 0.072, 0, 0.40),
        (0.262, 0.928, 0.195, 0.078, 1, 0.52),
        (0.200, 0.958, 0.225, 0.092, 1, 0.46),
        (0.125, 0.990, 0.260, 0.108, 1, 0.40),
        (0.038, 1.015, 0.310, 0.118, 1, 0.35),
        (0.705, 0.930, 0.225, 0.090, 1, 0.54),
        (0.780, 0.960, 0.270, 0.108, 1, 0.48),
        (0.868, 0.992, 0.325, 0.122, 1, 0.42),
        (0.958, 1.018, 0.365, 0.128, 1, 0.38),
        (0.065, 1.045, 0.205, 0.118, 2, 0.50),
        (0.195, 1.040, 0.165, 0.095, 2, 0.55),
        (0.290, 1.030, 0.115, 0.065, 2, 0.58),
        (0.650, 1.035, 0.130, 0.072, 2, 0.58),
        (0.755, 1.045, 0.185, 0.110, 2, 0.52),
        (0.900, 1.050, 0.230, 0.138, 2, 0.45),
    ]

    leaf_tips: list[tuple[float, float, float, int, float]] = []

    def grow_branch(x0: float, y0: float, length: float, angle: float, thick: float, depth: int, lid: int, wf: float) -> None:
        x1 = x0 + math.cos(angle) * length
        y1 = y0 + math.sin(angle) * length
        b_lum = 0.065 + lid * 0.012
        bc.bristle_stroke(x0, y0, x1, y1, width_px=max(1.0, thick), color=(b_lum + 0.015, b_lum + 0.008, b_lum), alpha=0.96, bristles=1, jitter_col=0.01)
        if depth <= 2:
            leaf_tips.append((x1, y1, length * 0.92, lid, wf))
        if depth <= 0 or length < 3.0 * sc:
            return
        n_sub = 3 if depth >= 3 else 2
        for k in range(n_sub):
            sp = (-0.36 if k == 0 else 0.36) if n_sub == 2 else (-0.48 + k * 0.48)
            sp += float(rng.uniform(-0.17, 0.17))
            grow_branch(x1, y1, length * float(rng.uniform(0.64, 0.80)), angle + sp, max(1.0, thick * 0.65), depth - 1, lid, wf)

    for bx, by, bh, bsp, lid, wf in trees:
        x_px, y_px = bx * w, by * h
        grow_branch(x_px, y_px, bh * h * 0.34, -math.pi * 0.5 + float(rng.uniform(-0.07, 0.07)), (2.6 + lid * 1.3) * sc, 4, lid, wf)
        for _ in range(7):
            leaf_tips.append((
                x_px + float(rng.uniform(-bsp * w * 0.62, bsp * w * 0.62)),
                y_px - bh * h * float(rng.uniform(0.24, 0.86)),
                bsp * w * 0.45, lid, wf,
            ))

    draw = bc._draw
    for tx, ty, rad, lid, wf in leaf_tips:
        n_leaves = int(42 + lid * 24)
        r_spread = max(rad, 7.0 * sc)
        lamp_glow = max(0.0, 1.0 - abs((tx / w) - 0.48) / 0.30) * wf

        angs = rng.uniform(0.0, 2.0 * math.pi, size=n_leaves)
        dists = r_spread * np.sqrt(rng.uniform(0.0, 1.0, size=n_leaves))
        lxs = tx + np.cos(angs) * dists
        lys = ty + np.sin(angs) * dists
        l_angs = rng.uniform(0.0, math.pi, size=n_leaves)
        l_lens = rng.uniform(1.4, 3.4, size=n_leaves) * sc * (0.72 + 0.24 * lid)
        tones = rng.uniform(0.0, 1.0, size=n_leaves)
        v_js = rng.integers(-5, 8, size=n_leaves)
        w_leaf = max(1, int(round(1.35 * sc)))

        for i in range(n_leaves):
            lx, ly = float(lxs[i]), float(lys[i])
            if lx < -6 or lx > w + 6 or ly < h * 0.52 or ly > h + 6:
                continue
            dx = math.cos(float(l_angs[i])) * float(l_lens[i])
            dy = math.sin(float(l_angs[i])) * float(l_lens[i])
            tone, vj = float(tones[i]), int(v_js[i])
            is_upper = math.sin(float(angs[i])) < -0.30

            if tone < 0.46:
                r, g, b, a = 10, 19, 13, 242
            elif tone < 0.84:
                r = 22 + vj + int(18 * lamp_glow)
                g = 40 + vj + int(14 * lamp_glow)
                b = 20 + vj // 2
                a = 230
            elif is_upper and tone < 0.94:
                r = 42 + vj + int(12 * lamp_glow)
                g = 58 + vj + int(10 * lamp_glow)
                b = 28 + vj // 2
                a = 215
            else:
                r = 34 + int(38 * lamp_glow) + vj
                g = 48 + int(24 * lamp_glow) + vj
                b = 22 + int(8 * lamp_glow)
                a = 220

            draw.line(
                [(lx - dx, ly - dy), (lx + dx, ly + dy)],
                fill=(max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)), a),
                width=w_leaf,
            )
            bc.total_strokes += 1

    # 3. Crisp blue directional road sign & grey overhead gantry painted with solid single-pass strokes
    bc.bristle_stroke(0.542 * w, 0.844 * h, 0.542 * w, 0.890 * h, width_px=1.6 * sc, color=(0.14, 0.16, 0.20), alpha=0.95, bristles=1)
    bc.bristle_stroke(0.514 * w, 0.852 * h, 0.542 * w, 0.852 * h, width_px=1.4 * sc, color=(0.14, 0.16, 0.20), alpha=0.95, bristles=1)
    bc.bristle_stroke(0.514 * w, 0.852 * h, 0.539 * w, 0.852 * h, width_px=18.0 * sc, color=(0.12, 0.28, 0.58), alpha=0.98, bristles=1)
    bc.bristle_stroke(0.517 * w, 0.848 * h, 0.535 * w, 0.848 * h, width_px=1.2 * sc, color=(0.76, 0.82, 0.88), alpha=0.85, bristles=1)
    bc.bristle_stroke(0.519 * w, 0.855 * h, 0.533 * w, 0.855 * h, width_px=1.2 * sc, color=(0.76, 0.82, 0.88), alpha=0.78, bristles=1)

    bc.bristle_stroke(0.357 * w, 0.844 * h, 0.357 * w, 0.908 * h, width_px=1.6 * sc, color=(0.14, 0.16, 0.20), alpha=0.95, bristles=1)
    bc.bristle_stroke(0.359 * w, 0.855 * h, 0.399 * w, 0.855 * h, width_px=26.0 * sc, color=(0.24, 0.26, 0.30), alpha=0.96, bristles=1)

    bc.bristle_stroke(0.154 * w, 0.885 * h, 0.154 * w, 1.00 * h, width_px=2.4 * sc, color=(0.14, 0.16, 0.20), alpha=0.96, bristles=1)
    bc.bristle_stroke(0.154 * w, 0.903 * h, 0.205 * w, 0.903 * h, width_px=1.6 * sc, color=(0.14, 0.16, 0.20), alpha=0.95, bristles=1)
    bc.bristle_stroke(0.154 * w, 0.926 * h, 0.205 * w, 0.926 * h, width_px=1.6 * sc, color=(0.14, 0.16, 0.20), alpha=0.95, bristles=1)
    bc.bristle_stroke(0.198 * w, 0.910 * h, 0.259 * w, 0.910 * h, width_px=40.0 * sc, color=(0.22, 0.24, 0.28), alpha=0.96, bristles=1)

    # 4. Sleek curved modern streetlamps receding along both sides of Jiaozi Avenue
    lamp_vs = [0.854, 0.880, 0.914, 0.958]
    for lv in lamp_vs:
        t_l = max(0.12, min(1.0, (lv - 0.825) / 0.175))
        pole_h = 0.036 + 0.056 * t_l
        for side in (-1.0, 1.0):
            base_u = _road_u(side * 1.09, lv)
            arm_u = _road_u(side * 0.93, lv)
            top_v = lv - pole_h
            bc.bristle_stroke(base_u * w, lv * h, base_u * w, (top_v + 0.005 * t_l) * h, width_px=max(0.8, (0.9 + 1.1 * t_l) * sc), color=(0.10, 0.12, 0.16), alpha=0.95, bristles=1)
            bc.curved_bristle_stroke(
                [(base_u * w, (top_v + 0.005 * t_l) * h), (base_u * w, (top_v - 0.002 * t_l) * h), (arm_u * w, (top_v - 0.003 * t_l) * h)],
                width_px=max(0.7, (0.8 + 0.8 * t_l) * sc),
                color=(0.12, 0.14, 0.18),
                alpha=0.95,
                bristles=1,
            )
            bc.soft_glow_dab(arm_u, top_v - 0.002 * t_l, 0.0014 * t_l + 0.0006, 0.0016 * t_l + 0.0006, (3.6, 2.2, 0.78))
            bc.soft_glow_dab(arm_u, top_v - 0.002 * t_l, 0.011 * t_l + 0.003, 0.012 * t_l + 0.003, (0.20, 0.095, 0.025))

    bc.commit_layer(blur_px=0.0)
