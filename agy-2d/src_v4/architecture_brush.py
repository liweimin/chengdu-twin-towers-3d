"""Pure Brushstroke Architecture: Skyline, Curved Twin Towers & Foreground Skyscraper (v4).

Zero homography texture warping, zero rigid CG grids!
Every building facade, window pane, glass cloud-reflection, steel mullion,
ice-flower lattice rib, LED louver dash, and terracotta stone pier is painted
individually by physical 2D brushstrokes in perspective!
"""

from __future__ import annotations

import math
import numpy as np

from brush_engine import BrushCanvas


def _bilinear_quad(
    quad: list[tuple[float, float]],
    su: float,
    sv: float,
) -> tuple[float, float]:
    """Map normalized facade coordinates (su in [0,1], sv in [0,1]) into 2D screen quad."""
    tl, tr, br, bl = quad
    top_x = tl[0] + (tr[0] - tl[0]) * su
    top_y = tl[1] + (tr[1] - tl[1]) * su
    bot_x = bl[0] + (br[0] - bl[0]) * su
    bot_y = bl[1] + (br[1] - bl[1]) * su
    return (top_x + (bot_x - top_x) * sv, top_y + (bot_y - top_y) * sv)


def _paint_brush_building_face(
    bc: BrushCanvas,
    quad: list[tuple[float, float]],
    floors: int,
    cols: int,
    warm_side: bool,
    lit_prob: float,
    haze: float = 0.0,
    stone_piers: bool = False,
    refuge_every: int = 15,
    is_foreground: bool = False,
) -> None:
    """Paint an entire skyscraper facade purely with directional brushstrokes & window dabs."""
    w, h = bc.width, bc.height
    sc = bc.scale
    rng = bc.rng

    # 1. Painterly vertical & horizontal underpainting wash inside the 2D perspective quad
    # Base glass silhouette built from overlapping vertical bristle strokes
    n_v_strokes = max(14, cols * 2)
    for i in range(n_v_strokes):
        su = 0.02 + (i + 0.5) / n_v_strokes * 0.96
        p_top = _bilinear_quad(quad, su, 0.0)
        p_bot = _bilinear_quad(quad, su, 1.0)
        p_next = _bilinear_quad(quad, min(0.99, su + 0.96 / n_v_strokes), 0.5)
        strip_w = max(2.0, abs(p_next[0] - p_top[0]) * w * 1.18)

        if warm_side:
            base_c = (0.16, 0.14, 0.20)
        else:
            base_c = (0.10, 0.14, 0.22)
        if haze > 0.0:
            base_c = (
                base_c[0] * (1.0 - haze) + 0.44 * haze,
                base_c[1] * (1.0 - haze) + 0.36 * haze,
                base_c[2] * (1.0 - haze) + 0.42 * haze,
            )
        bc.bristle_stroke(
            p_top[0] * w, p_top[1] * h, p_bot[0] * w, p_bot[1] * h,
            width_px=strip_w,
            color=base_c,
            alpha=0.96,
            bristles=2,
            jitter_col=0.015,
        )

    # 2. Individual hand-painted window-pane brushstrokes (sky-cloud reflections + lit offices!)
    # Precompute organic floor activity so lit offices cluster naturally
    floor_act = rng.uniform(0.0, 1.0, size=floors)

    for fl in range(floors):
        sv0 = (fl + 0.18) / floors
        sv1 = (fl + 0.86) / floors
        sv_mid = 0.5 * (sv0 + sv1)
        is_refuge = (refuge_every > 0) and ((fl + 1) % refuge_every == 0) and (fl < floors - 2)

        # Smooth sunset reflection gradient from roof (cool blue-slate) to lower floors (warm peach)
        if warm_side:
            refl_r = 0.26 + 0.52 * sv_mid
            refl_g = 0.24 + 0.34 * sv_mid
            refl_b = 0.34 + 0.16 * (1.0 - sv_mid)
        else:
            refl_r = 0.18 + 0.24 * sv_mid
            refl_g = 0.23 + 0.16 * sv_mid
            refl_b = 0.36 + 0.10 * (1.0 - sv_mid)

        # Horizontal dark floor spandrel brushstroke across the facade
        sp_l = _bilinear_quad(quad, 0.0, fl / floors)
        sp_r = _bilinear_quad(quad, 1.0, fl / floors)
        sp_h = max(1.0, abs(_bilinear_quad(quad, 0.5, (fl + 1) / floors)[1] - sp_l[1]) * h)
        sp_col = (0.08, 0.09, 0.13) if not is_refuge else (0.05, 0.06, 0.09)
        if haze > 0.0:
            sp_col = (
                sp_col[0] * (1.0 - haze) + 0.42 * haze,
                sp_col[1] * (1.0 - haze) + 0.35 * haze,
                sp_col[2] * (1.0 - haze) + 0.40 * haze,
            )
        bc.bristle_stroke(
            sp_l[0] * w, sp_l[1] * h, sp_r[0] * w, sp_r[1] * h,
            width_px=max(1.0, sp_h * (0.55 if is_refuge else 0.26)),
            color=sp_col,
            alpha=0.88,
            bristles=2 if is_foreground else 1,
            jitter_col=0.012,
        )

        if is_refuge or fl < 1:
            continue

        # Paint individual window panes as slightly organic horizontal brushstrokes
        for c_idx in range(cols):
            su0 = (c_idx + 0.12) / cols
            su1 = (c_idx + 0.88) / cols
            p0 = _bilinear_quad(quad, su0, sv_mid)
            p1 = _bilinear_quad(quad, su1, sv_mid)

            # Reflected cloud patch modulation + per-pane tilt variation
            cloud_mod = 0.5 + 0.5 * math.sin(su0 * 7.5 + sv_mid * 9.0) * math.cos(su0 * 4.2 - sv_mid * 6.5)
            tilt_var = float(rng.uniform(0.76, 1.24))

            # Is this office bay lit from inside?
            bay_p = floor_act[fl] * 0.48 + float(rng.uniform(0.0, 0.68))
            is_lit = bay_p > (1.0 - lit_prob)

            if is_lit:
                temp_r = float(rng.uniform(0.0, 1.0))
                brt = float(rng.uniform(0.65, 1.0))
                if temp_r < 0.62:
                    wcol = (0.96 * brt, 0.78 * brt, 0.52 * brt)  # Warm 3000K office
                elif temp_r < 0.86:
                    wcol = (0.90 * brt, 0.85 * brt, 0.74 * brt)  # Neutral office
                else:
                    wcol = (0.72 * brt, 0.82 * brt, 0.94 * brt)  # Cool fluorescent office
                w_alpha = 0.92
            else:
                # Sky-and-cloud reflection in dark glass pane
                gain = (0.55 + 0.50 * cloud_mod) * tilt_var
                wcol = (
                    min(0.95, refl_r * gain),
                    min(0.95, refl_g * gain),
                    min(0.95, refl_b * gain),
                )
                w_alpha = 0.72

            if haze > 0.0:
                wcol = (
                    wcol[0] * (1.0 - haze) + 0.45 * haze,
                    wcol[1] * (1.0 - haze) + 0.37 * haze,
                    wcol[2] * (1.0 - haze) + 0.42 * haze,
                )

            bc.bristle_stroke(
                p0[0] * w, p0[1] * h, p1[0] * w, p1[1] * h,
                width_px=max(1.0, sp_h * 0.62),
                color=wcol,
                alpha=w_alpha,
                bristles=2 if is_foreground else 1,
                jitter_col=0.022,
            )

    # 3. Vertical aluminum mullions or warm bronze-terracotta stone piers painted as vertical brushstrokes
    for c_idx in range(cols + 1):
        su = c_idx / cols
        p_t = _bilinear_quad(quad, su, 0.0)
        p_b = _bilinear_quad(quad, su, 1.0)
        if stone_piers:
            m_col = (0.32, 0.25, 0.22) if warm_side else (0.26, 0.21, 0.20)
            m_w = max(1.6, 3.6 * sc) if (c_idx % 1 == 0) else max(1.0, 1.8 * sc)
        else:
            m_col = (0.10, 0.12, 0.17)
            m_w = max(0.8, (1.4 if is_foreground else 0.9) * sc)
        if haze > 0.0:
            m_col = (
                m_col[0] * (1.0 - haze) + 0.42 * haze,
                m_col[1] * (1.0 - haze) + 0.35 * haze,
                m_col[2] * (1.0 - haze) + 0.40 * haze,
            )
        bc.bristle_stroke(
            p_t[0] * w, p_t[1] * h, p_b[0] * w, p_b[1] * h,
            width_px=m_w,
            color=m_col,
            alpha=0.86,
            bristles=2 if is_foreground else 1,
            jitter_col=0.015,
        )


def paint_background_skyline_by_strokes(bc: BrushCanvas) -> None:
    """Paint distant dome, Financial City towers, tower crane & curved lattice annex by brushstrokes."""
    w, h = bc.width, bc.height
    sc = bc.scale

    bc.begin_layer()
    # 1. Distant Tianfu New City Convention Center Dome (painted with curved horizontal arch strokes)
    for k in range(28):
        vf = 0.778 + (k / 27.0) * 0.052
        # Dome widens gracefully from top arch to base
        t = k / 27.0
        half_u = 0.031 * math.sqrt(min(1.0, t * 2.4 + 0.08))
        shade = 1.0 - 0.72 * max(0.0, (t - 0.48) / 0.52)
        rib = 0.88 + 0.12 * math.sin(k * 1.9)
        col = (0.56 * shade * rib, 0.46 * shade * rib, 0.40 * shade * rib)
        pts = []
        for s in range(7):
            sf = (s / 6.0) * 2.0 - 1.0
            pu = 0.485 + sf * half_u
            pv = vf + 0.008 * (sf * sf) * (1.0 - t * 0.6)
            pts.append((pu * w, pv * h))
        bc.curved_bristle_stroke(pts, width_px=max(1.5, 2.8 * sc), color=col, alpha=0.92, bristles=2)

    # Warm distant lobby glint at base of dome
    bc.bristle_stroke(0.462 * w, 0.815 * h, 0.508 * w, 0.815 * h, width_px=2.2 * sc, color=(0.88, 0.66, 0.40), alpha=0.65, bristles=2)

    # 2. Left & right distant Financial City towers (softly veiled in atmospheric haze)
    bg_towers = [
        ([(0.204, 0.604), (0.256, 0.600), (0.252, 0.768), (0.198, 0.768)], 22, 7, False, 0.15, 0.34),
        ([(0.262, 0.618), (0.285, 0.616), (0.283, 0.782), (0.259, 0.782)], 20, 4, False, 0.13, 0.36),
        ([(0.282, 0.538), (0.344, 0.536), (0.338, 0.798), (0.273, 0.798)], 32, 8, False, 0.17, 0.26),
        ([(0.339, 0.618), (0.371, 0.616), (0.367, 0.808), (0.335, 0.808)], 24, 5, False, 0.14, 0.30),
        ([(0.366, 0.695), (0.390, 0.695), (0.388, 0.818), (0.364, 0.818)], 14, 4, False, 0.12, 0.34),
        # Right background cluster
        ([(0.630, 0.590), (0.660, 0.588), (0.662, 0.810), (0.634, 0.810)], 24, 5, False, 0.14, 0.32),
        ([(0.654, 0.546), (0.716, 0.544), (0.720, 0.810), (0.660, 0.810)], 30, 8, False, 0.17, 0.25),
    ]
    for quad, fl, co, ws, lp, hz in bg_towers:
        _paint_brush_building_face(bc, quad, fl, co, ws, lp, haze=hz, refuge_every=14, is_foreground=False)

    # Rooftop penthouse & distant tower crane brushstrokes (matching ref_2.jpg)
    bc.bristle_stroke(0.296 * w, 0.533 * h, 0.331 * w, 0.532 * h, width_px=5.5 * sc, color=(0.24, 0.24, 0.30), alpha=0.90, bristles=2)
    bc.bristle_stroke(0.688 * w, 0.545 * h, 0.688 * w, 0.514 * h, width_px=1.3 * sc, color=(0.28, 0.26, 0.32), alpha=0.78, bristles=1)
    bc.bristle_stroke(0.674 * w, 0.522 * h, 0.716 * w, 0.506 * h, width_px=1.1 * sc, color=(0.28, 0.26, 0.32), alpha=0.72, bristles=1)

    # 3. Curved ice-flower lattice annex building on the left (painted with sweeping curve + diagonal strokes)
    for k in range(24):
        su = k / 23.0
        ux = 0.155 + su * (0.312 - 0.155)
        roof_y = 0.686 + 0.068 * (su ** 1.35)
        bc.bristle_stroke(ux * w, roof_y * h, ux * w, 0.830 * h, width_px=9.0 * sc, color=(0.15, 0.18, 0.24), alpha=0.92, bristles=2)
    # Cross-hatched metallic lattice brushstrokes over the curved annex
    for k in range(28):
        su = k / 27.0
        ux = 0.156 + su * 0.154
        ry = 0.688 + 0.066 * (su ** 1.35)
        bc.bristle_stroke(ux * w, ry * h, (ux + 0.035) * w, min(0.830, ry + 0.048) * h, width_px=1.2 * sc, color=(0.42, 0.40, 0.44), alpha=0.58, bristles=1)
        bc.bristle_stroke(ux * w, ry * h, max(0.155, ux - 0.035) * w, min(0.830, ry + 0.048) * h, width_px=1.2 * sc, color=(0.42, 0.40, 0.44), alpha=0.58, bristles=1)

    # 4. Far-left low commercial building
    _paint_brush_building_face(
        bc, [(0.00, 0.718), (0.240, 0.746), (0.240, 0.890), (0.00, 0.890)],
        floors=9, cols=16, warm_side=False, lit_prob=0.20, haze=0.12, refuge_every=0, is_foreground=False,
    )
    bc.commit_layer(blur_px=0.55)


def _twin_tower_bounds(vf: float, is_right: bool) -> tuple[float, float]:
    """Exact measured left & right u-edges of the curved bamboo-shoot Twin Towers from ref_2.jpg."""
    v_ctrl = [0.300, 0.350, 0.400, 0.500, 0.600, 0.700, 0.830]
    l_out = [0.4090, 0.4045, 0.3998, 0.3935, 0.3888, 0.3855, 0.3832]
    l_in = [0.4600, 0.4622, 0.4648, 0.4670, 0.4672, 0.4666, 0.4660]
    ol = float(np.interp(vf, v_ctrl, l_out))
    il = float(np.interp(vf, v_ctrl, l_in))
    if not is_right:
        return ol, il
    center_axis = 0.4865
    return 2.0 * center_axis - il, 2.0 * center_axis - ol


def _twin_crown_v(u_from_outer: float) -> float:
    u_cl = max(0.0, min(1.0, u_from_outer))
    return (
        0.299
        + 0.044 * (max(0.0, (u_cl - 0.24) / 0.76) ** 1.62)
        + 0.014 * (max(0.0, (0.24 - u_cl) / 0.24) ** 2.0)
    )


def paint_twin_towers_by_strokes(bc: BrushCanvas) -> None:
    """Paint the iconic curved Chengdu Twin Towers purely with ~30,000 layered brushstrokes."""
    w, h = bc.width, bc.height
    sc = bc.scale
    rng = bc.rng

    # Soft sunset backlight glow behind the Twin Towers gap
    bc.soft_glow_dab(0.486, 0.62, 0.10, 0.22, (0.14, 0.065, 0.025))

    # --- Pass 1: Cylindrical underpainting + metallic louvers + ice-flower brushwork ---
    bc.begin_layer()
    for is_right in (False, True):
        # A. Vertical cylindrical underpainting strokes (giving round architectural volume!)
        n_cols = 28
        for ci in range(n_cols):
            u_loc = (ci + 0.5) / n_cols
            u_from_outer = u_loc if not is_right else (1.0 - u_loc)
            top_v = _twin_crown_v(u_from_outer)
            cyl_x = u_loc * 2.0 - 1.0
            cyl_z = math.sqrt(max(0.04, 1.0 - cyl_x * cyl_x))
            # Warmer sunset sheen toward the inner edge facing the gap, cooler blue on outer curve
            sun_w = u_loc if not is_right else (1.0 - u_loc)

            # Build vertical column in 18 painterly segments so color grades smoothly down the shaft
            n_seg = 18
            for si in range(n_seg):
                v0 = top_v + (0.830 - top_v) * (si / n_seg)
                v1 = top_v + (0.830 - top_v) * ((si + 1.08) / n_seg)
                vm = 0.5 * (v0 + v1)
                l0, r0 = _twin_tower_bounds(v0, is_right)
                l1, r1 = _twin_tower_bounds(v1, is_right)
                x0 = (l0 + (r0 - l0) * u_loc) * w
                x1 = (l1 + (r1 - l1) * u_loc) * w

                v_grad = (vm - 0.30) / 0.53
                cr = (0.11 + 0.24 * v_grad + 0.14 * sun_w) * (0.45 + 0.60 * cyl_z)
                cg = (0.14 + 0.16 * v_grad + 0.08 * sun_w) * (0.45 + 0.60 * cyl_z)
                cb = (0.24 + 0.08 * (1.0 - v_grad)) * (0.45 + 0.60 * cyl_z)
                bc.bristle_stroke(
                    x0, v0 * h, x1, v1 * h,
                    width_px=max(2.5, (r0 - l0) * w / n_cols * 1.65),
                    color=(cr, cg, cb),
                    alpha=0.96,
                    bristles=2,
                    jitter_col=0.015,
                )

        # B. Diagonal metallic "ice-flower" lattice strokes wrapping the curved cylinder
        n_diag = 38
        for d in range(n_diag):
            v_start = 0.32 + (d / n_diag) * 0.49
            for sign in (-1, 1):
                pts = []
                for step in range(9):
                    vf = v_start + step * 0.0085
                    if vf > 0.828:
                        break
                    u_loc = 0.5 + sign * (-0.42 + step * 0.105)
                    if u_loc < 0.04 or u_loc > 0.96:
                        continue
                    u_fo = u_loc if not is_right else (1.0 - u_loc)
                    if vf < _twin_crown_v(u_fo) + 0.004:
                        continue
                    le, re = _twin_tower_bounds(vf, is_right)
                    pts.append(((le + (re - le) * u_loc) * w, vf * h))
                if len(pts) >= 2:
                    bc.curved_bristle_stroke(pts, width_px=max(0.8, 1.15 * sc), color=(0.38, 0.39, 0.44), alpha=0.34, bristles=1)

        # C. 56 floors of crisp dark structural floor ribs & fine metallic louver brushstrokes
        floors = 56
        for fl in range(floors):
            vf = 0.305 + (fl / floors) * 0.522
            le, re = _twin_tower_bounds(vf, is_right)
            # Determine valid u_loc span below the arched crown
            u_spans = []
            for k in range(12):
                ul = (k + 0.5) / 12.0
                ufo = ul if not is_right else (1.0 - ul)
                if vf >= _twin_crown_v(ufo) + 0.002:
                    u_spans.append(ul)
            if len(u_spans) < 2:
                continue
            ua, ub = u_spans[0] - 0.03, u_spans[-1] + 0.03
            is_refuge = fl in (18, 36)
            col_r = (0.06, 0.07, 0.10) if is_refuge else (0.09, 0.11, 0.16)
            bc.bristle_stroke(
                (le + (re - le) * max(0.0, ua)) * w, vf * h,
                (le + (re - le) * min(1.0, ub)) * w, vf * h,
                width_px=max(0.9, (3.2 if is_refuge else 1.2) * sc),
                color=col_r,
                alpha=0.82 if is_refuge else 0.65,
                bristles=2,
                jitter_col=0.01,
            )

        # D. Arched crown rim brushstroke
        crown_pts = []
        for k in range(15):
            ul = k / 14.0
            ufo = ul if not is_right else (1.0 - ul)
            cv = _twin_crown_v(ufo) + 0.006
            le, re = _twin_tower_bounds(cv, is_right)
            crown_pts.append(((le + (re - le) * ul) * w, cv * h))
        bc.curved_bristle_stroke(crown_pts, width_px=max(1.4, 2.0 * sc), color=(0.86, 0.68, 0.44), alpha=0.82, bristles=2)

    bc.commit_layer(blur_px=0.30)

    # --- Pass 2: Luminous Dusk LED Louver Dash Brushstrokes (additive HDR!) ---
    bc.begin_layer()
    for is_right in (False, True):
        n_rows = 112  # Fine horizontal LED louver rows
        n_dashes = 16
        for r_idx in range(n_rows):
            vf = 0.325 + (r_idx / n_rows) * 0.492
            g_v = (vf - 0.298) / 0.532
            # Skip dark refuge bands
            if abs(vf - 0.470) < 0.006 or abs(vf - 0.640) < 0.006:
                continue
            le, re = _twin_tower_bounds(vf, is_right)

            for d_idx in range(n_dashes):
                ul0 = (d_idx + 0.08) / n_dashes
                ul1 = (d_idx + 0.92) / n_dashes
                ul_mid = 0.5 * (ul0 + ul1)
                ufo = ul_mid if not is_right else (1.0 - ul_mid)
                if vf < _twin_crown_v(ufo) + 0.022:
                    continue

                cyl_x = ul_mid * 2.0 - 1.0
                cyl_z = math.sqrt(max(0.05, 1.0 - cyl_x * cyl_x))
                u_wrap = 0.5 + math.asin(max(-0.99, min(0.99, cyl_x))) / math.pi
                g_u = (u_wrap * 0.44) if not is_right else (0.56 + u_wrap * 0.44)

                # Sweeping golden-amber & sunset-crimson Chengdu silk waves across both curved towers!
                yw1 = 0.28 + 0.11 * math.sin(g_u * 4.4 + 0.30)
                yw2 = 0.56 + 0.12 * math.sin(g_u * 3.8 - 1.40)
                yw3 = 0.79 + 0.07 * math.cos(g_u * 4.8 + 0.85)
                d1, d2, d3 = abs(g_v - yw1), abs(g_v - yw2), abs(g_v - yw3)

                w1 = math.exp(-((d1 / 0.082) ** 2))
                w2 = math.exp(-((d2 / 0.088) ** 2))
                w3 = math.exp(-((d3 / 0.075) ** 2))
                strength = max(w1, w2 * 0.95, w3 * 0.80)
                if strength < 0.06:
                    continue

                # Mix champagne-gold, warm amber, and sunset vermilion organically
                c_r = min(1.0, (0.98 * w1 + 0.94 * w2 + 0.96 * w3) / max(0.4, w1 + w2 + w3) + 0.06)
                c_g = min(1.0, (0.76 * w1 + 0.42 * w2 + 0.80 * w3) / max(0.4, w1 + w2 + w3))
                c_b = min(1.0, (0.34 * w1 + 0.22 * w2 + 0.44 * w3) / max(0.4, w1 + w2 + w3))

                alpha_d = min(0.95, strength * (cyl_z ** 0.85) * float(rng.uniform(0.68, 0.98)))
                x0 = (le + (re - le) * ul0) * w
                x1 = (le + (re - le) * ul1) * w
                bc.bristle_stroke(
                    x0, vf * h, x1, vf * h,
                    width_px=max(0.8, 1.35 * sc),
                    color=(c_r, c_g, c_b),
                    alpha=alpha_d,
                    bristles=1,
                    jitter_col=0.03,
                )

    bc.commit_layer(blur_px=0.25, additive=True, hdr_gain=1.45)

    # Crisp glowing red aviation warning beacons on both arched peaks
    bc.soft_glow_dab(0.420, 0.296, 0.0018, 0.0024, (4.0, 0.18, 0.08))
    bc.soft_glow_dab(0.553, 0.296, 0.0018, 0.0024, (4.0, 0.18, 0.08))


def paint_foreground_right_tower_by_strokes(bc: BrushCanvas) -> None:
    """Paint the towering close-up right skyscraper (中航产融 / 安盟保险) purely with brushstrokes."""
    w, h = bc.width, bc.height
    sc = bc.scale

    bc.begin_layer()
    # 1. Rear recessed wing
    wing_quad = [(0.708, 0.255), (0.768, 0.222), (0.785, 0.840), (0.734, 0.840)]
    _paint_brush_building_face(
        bc, wing_quad, floors=36, cols=11, warm_side=False, lit_prob=0.18,
        haze=0.06, stone_piers=False, refuge_every=15, is_foreground=True,
    )

    # 2. Main broad left glass face (catching rich warm sunset cloud reflections!)
    main_quad = [(0.758, 0.135), (0.868, 0.036), (0.948, 0.840), (0.792, 0.845)]
    _paint_brush_building_face(
        bc, main_quad, floors=44, cols=20, warm_side=True, lit_prob=0.20,
        haze=0.02, stone_piers=False, refuge_every=16, is_foreground=True,
    )
    # Warm bronze-terracotta architectural corner piers cleanly aligned on edges
    bc.bristle_stroke(0.758 * w, 0.135 * h, 0.792 * w, 0.845 * h, width_px=5.0 * sc, color=(0.30, 0.23, 0.20), alpha=0.95, bristles=1)
    bc.bristle_stroke(0.868 * w, 0.036 * h, 0.948 * w, 0.840 * h, width_px=6.0 * sc, color=(0.33, 0.25, 0.21), alpha=0.95, bristles=1)

    # Subtle illuminated rooftop signage brushwork near top-left crown
    for k in range(11):
        su = 0.14 + k * 0.068
        p = _bilinear_quad(main_quad, su, 0.018)
        bc.dab(p[0] * w, p[1] * h, 2.8 * sc, 2.2 * sc, color=(0.95, 0.84, 0.66), alpha=0.82)

    # 3. Right bronze-terracotta stone-ribbed facade curving off right edge
    right_quad = [(0.868, 0.036), (0.945, 0.038), (1.020, 0.840), (0.948, 0.840)]
    _paint_brush_building_face(
        bc, right_quad, floors=44, cols=9, warm_side=False, lit_prob=0.14,
        haze=0.02, stone_piers=True, refuge_every=16, is_foreground=True,
    )

    # Far-right dark shadow edge (cleanly outside right_quad, not overlapping main face!)
    far_quad = [(0.945, 0.038), (1.015, 0.220), (1.025, 0.840), (1.020, 0.840)]
    for i in range(10):
        su = (i + 0.5) / 10.0
        pt = _bilinear_quad(far_quad, su, 0.0)
        pb = _bilinear_quad(far_quad, su, 1.0)
        bc.bristle_stroke(pt[0] * w, pt[1] * h, pb[0] * w, pb[1] * h, width_px=8.0 * sc, color=(0.08, 0.10, 0.15), alpha=0.98, bristles=1)

    bc.commit_layer(blur_px=0.25)
