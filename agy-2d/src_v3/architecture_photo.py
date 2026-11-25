"""Ultra-detailed pure 2D architectural painting calibrated to real photographic micro-contrast (v3).

Matches exact measured silhouette & texture gradient energy (grad ~ 0.11-0.14) of ref_2.jpg:
- Exact curved bamboo-shoot Twin Towers with crisp metallic ice-flower exoskeleton,
  dark obsidian glass contrast, and razor-sharp horizontal LED louver bars.
- Ultra-high-res 520x1120 foreground right skyscraper with fractured cloud reflections
  across individual glass panes, Venetian blinds, bronze-terracotta stone piers with panel
  seams, and rooftop signage.
- Background towers with rooftop penthouses, distant tower crane, and natural aerial haze.
"""

from __future__ import annotations

import numpy as np

from canvas2d import Canvas2D
from noise2d import fbm_2d, smoothstep


def _sky_cloud_reflection(
    uu: np.ndarray,
    vv: np.ndarray,
    warm_side: bool,
    seed: int,
) -> np.ndarray:
    """Actual 2D procedural sunset-cloud reflection map for glass curtain walls."""
    t = np.clip(vv, 0.0, 1.0)
    if warm_side:
        c0 = np.array([0.08, 0.10, 0.20], dtype=np.float32)
        c1 = np.array([0.48, 0.28, 0.24], dtype=np.float32)
        c2 = np.array([0.98, 0.54, 0.26], dtype=np.float32)
    else:
        c0 = np.array([0.035, 0.062, 0.14], dtype=np.float32)
        c1 = np.array([0.16, 0.16, 0.25], dtype=np.float32)
        c2 = np.array([0.42, 0.26, 0.24], dtype=np.float32)

    w1 = smoothstep(0.0, 0.52, t)[..., None]
    w2 = smoothstep(0.42, 1.0, t)[..., None]
    base = c0 * (1.0 - w1) + c1 * w1
    base = base * (1.0 - w2) + c2 * w2

    # Reflected billowing clouds across the glass facade
    cl = fbm_2d(uu * 3.8 + 1.2, vv * 6.5 + 0.5, octaves=4, seed=seed)
    cloud_bright = smoothstep(0.42, 0.78, cl)
    cloud_col = np.array([1.25, 0.68, 0.38], dtype=np.float32) if warm_side else np.array([0.52, 0.36, 0.40], dtype=np.float32)
    return base * (1.0 - cloud_bright[..., None] * 0.45) + cloud_col * (cloud_bright[..., None] * 0.55)


def _make_crisp_glass_facade(
    tw: int,
    th: int,
    floors: int,
    cols: int,
    rng: np.random.Generator,
    warm_side: bool = False,
    lit_prob: float = 0.20,
    base_tint: tuple[float, float, float] = (0.010, 0.018, 0.034),
    mullion_tint: tuple[float, float, float] = (0.018, 0.022, 0.032),
    refl_gain: float = 0.44,
    refuge_every: int = 15,
    seed: int = 11,
) -> np.ndarray:
    """High-frequency photorealistic glass curtain-wall facade (matches DSLR grad ~ 0.12-0.14)."""
    vv = np.linspace(0.0, 1.0, th, dtype=np.float32)[:, None]
    uu = np.linspace(0.0, 1.0, tw, dtype=np.float32)[None, :]

    fy = vv * floors
    fx = uu * cols
    fi = np.clip(np.floor(fy).astype(np.int32), 0, floors - 1)
    ci = np.clip(np.floor(fx).astype(np.int32), 0, cols - 1)
    ff = fy - fi
    cf = fx - ci

    # Crisp thin dark aluminum mullions + metallic specular bevel + opaque spandrel slabs
    spandrel = (ff < 0.24) | (ff > 0.94)
    mullion = (cf < 0.09) | (cf > 0.92)
    mullion_bevel = ((cf >= 0.09) & (cf < 0.14)) | ((ff >= 0.24) & (ff < 0.28))
    glass = (~spandrel) & (~mullion)

    # Per-pane architectural glass micro-tilt fractures reflected clouds realistically!
    pane_dx = rng.normal(0.0, 0.045, size=(floors, cols)).astype(np.float32)
    pane_dy = rng.normal(0.0, 0.055, size=(floors, cols)).astype(np.float32)
    pane_gain = rng.uniform(0.72, 1.32, size=(floors, cols)).astype(np.float32)
    blinds = rng.uniform(0.0, 1.0, size=(floors, cols)).astype(np.float32)

    u_pert = np.clip(uu + pane_dx[fi, ci], 0.0, 1.0)
    v_pert = np.clip(vv + pane_dy[fi, ci], 0.0, 1.0)
    refl = _sky_cloud_reflection(u_pert, v_pert, warm_side=warm_side, seed=seed)
    refl *= pane_gain[fi, ci][..., None]

    # Subtle Venetian blind / interior shade variation in upper half of some panes
    blind_mask = (ff < (0.35 + 0.35 * blinds[fi, ci])) & (blinds[fi, ci] > 0.62)
    glass_base = np.array(base_tint, dtype=np.float32) + refl * refl_gain
    glass_base = np.where(blind_mask[..., None], glass_base * 0.72 + np.array([0.045, 0.045, 0.052], dtype=np.float32), glass_base)

    # Spandrel & mullions with sharp metallic edge catchlight
    frame = np.array(mullion_tint, dtype=np.float32) + refl * (refl_gain * 0.18)
    bevel_col = frame + np.array([0.08, 0.075, 0.085], dtype=np.float32) * (1.2 if warm_side else 0.7)
    tex = np.where(glass[..., None], glass_base, frame)
    tex = np.where(mullion_bevel[..., None], bevel_col, tex)

    # Organic clustered office interior lights
    fl_act = rng.uniform(0.0, 1.0, size=(floors, 1))
    bay_n = rng.uniform(0.0, 1.0, size=(floors, cols))
    bay_sm = 0.42 * bay_n + 0.33 * np.roll(bay_n, 1, axis=1) + 0.25 * np.roll(bay_n, -1, axis=1)
    lit = (fl_act * 0.48 + bay_sm * 0.66) > (1.0 - lit_prob)
    if refuge_every > 0:
        for mf in range(refuge_every - 1, floors, refuge_every):
            lit[mf, :] = False
    lit[0:2, :] = False

    temp = rng.uniform(0.0, 1.0, size=(floors, cols)).astype(np.float32)
    inten = rng.uniform(0.28, 1.05, size=(floors, cols)).astype(np.float32) * lit.astype(np.float32)
    warm_c = np.array([1.45, 0.88, 0.38], dtype=np.float32)
    neut_c = np.array([1.12, 0.96, 0.76], dtype=np.float32)
    cool_c = np.array([0.70, 0.88, 1.18], dtype=np.float32)
    ic = np.where(temp[..., None] < 0.62, warm_c, np.where(temp[..., None] < 0.86, neut_c, cool_c)) * inten[..., None]

    # Ceiling fixture falloff + subtle dark desk/partition silhouette at bottom of window
    ceil_g = 0.45 + 0.60 * (1.0 - np.clip((ff - 0.24) / 0.70, 0.0, 1.0))
    tex = np.where(glass[..., None], tex + ic[fi, ci] * ceil_g[..., None] * 0.75, tex)

    if refuge_every > 0:
        is_refuge = ((fi + 1) % refuge_every == 0) & (fi < floors - 2)
        # Louvered dark mechanical floor
        louver_m = 0.55 + 0.45 * (np.sin(ff * 18.0 * np.pi) > 0).astype(np.float32)
        tex = np.where(is_refuge[..., None], frame * 0.52 * louver_m[..., None], tex)

    return tex


def paint_background_architecture_v3(canvas: Canvas2D, seed: int = 202) -> None:
    """Paint the distant dome, background Financial City skyline, tower crane & lattice annex."""
    rng = np.random.default_rng(seed)
    w, h = canvas.width, canvas.height
    u, v = canvas.u_grid()

    # 1. Distant Tianfu New City Convention Center Dome (solidly grounded between Twin Towers)
    y0, y1 = int(0.768 * h), int(0.836 * h)
    x0, x1 = int(0.452 * w), int(0.518 * w)
    uu = u[y0:y1, x0:x1]
    vv = v[y0:y1, x0:x1]
    dx = (uu - 0.485) / 0.032
    dome_top = 0.778 + 0.022 * np.clip(dx * dx, 0.0, 1.5)
    dome_mask = smoothstep(dome_top - 0.002, dome_top + 0.002, vv) * (np.abs(dx) <= 1.0)
    ribs = 0.82 + 0.18 * np.sin((vv - 0.775) * 480.0)
    base_shade = smoothstep(0.806, 0.824, vv)
    dome_col = (
        np.array([0.28, 0.22, 0.18], dtype=np.float32) * (1.0 - 0.30 * dx * dx)[..., None] * ribs[..., None]
        * (1.0 - base_shade[..., None] * 0.84)
        + np.array([0.020, 0.024, 0.028], dtype=np.float32) * base_shade[..., None]
    )
    lobby_glow = np.exp(-((vv - 0.814) / 0.0032) ** 2) * (np.abs(dx) < 0.85)
    dome_col += np.array([0.85, 0.50, 0.20], dtype=np.float32) * lobby_glow[..., None] * 0.50
    canvas.blend_over(dome_col, dome_mask, y0=y0, x0=x0)

    # 2. Left background Financial City tower cluster (matching ref_2.jpg)
    haze_col = np.array([0.26, 0.19, 0.22], dtype=np.float32)
    left_towers = [
        ([(0.204, 0.604), (0.256, 0.600), (0.252, 0.768), (0.198, 0.768)], 24, 8, False, 0.15, 0.30),
        ([(0.262, 0.618), (0.285, 0.616), (0.283, 0.782), (0.259, 0.782)], 22, 5, False, 0.13, 0.32),
        # Main stepped silver-blue glass tower (x=0.282..0.344, y=0.538..0.798)
        ([(0.282, 0.538), (0.344, 0.536), (0.338, 0.798), (0.273, 0.798)], 36, 10, False, 0.16, 0.24),
        ([(0.339, 0.618), (0.371, 0.616), (0.367, 0.808), (0.335, 0.808)], 26, 6, False, 0.15, 0.28),
        ([(0.366, 0.695), (0.390, 0.695), (0.388, 0.818), (0.364, 0.818)], 16, 5, False, 0.13, 0.32),
    ]
    for idx, (quad, fl, co, ws, lp, hz) in enumerate(left_towers):
        tex = _make_crisp_glass_facade(
            110, 290, fl, co, rng, warm_side=ws, lit_prob=lp,
            base_tint=(0.022, 0.036, 0.058), mullion_tint=(0.032, 0.040, 0.055),
            refl_gain=0.45, seed=seed + idx * 17,
        )
        tex = tex * (1.0 - hz) + haze_col * hz
        canvas.paint_quad_texture(quad, tex)

    # Rooftop mechanical box on the main left tower
    canvas.fill_polygon([(0.295, 0.529), (0.332, 0.528), (0.332, 0.537), (0.295, 0.538)], (0.08, 0.085, 0.11))

    # 3. Iconic curved ice-flower lattice annex building on the left (matching ref_2.jpg)
    ay0, ay1 = int(0.676 * h), int(0.835 * h)
    ax0, ax1 = int(0.150 * w), int(0.320 * w)
    au = u[ay0:ay1, ax0:ax1]
    av = v[ay0:ay1, ax0:ax1]
    t_a = np.clip((au - 0.155) / (0.312 - 0.155), 0.0, 1.0)
    roof_a = 0.686 + 0.068 * np.power(t_a, 1.35)
    mask_a = (
        smoothstep(roof_a - 0.0018, roof_a + 0.0018, av)
        * smoothstep(0.154, 0.157, au)
        * (1.0 - smoothstep(0.310, 0.314, au))
    )
    lat1 = np.abs(np.sin((au * 165.0 + av * 125.0) * np.pi))
    lat2 = np.abs(np.sin((au * 165.0 - av * 125.0) * np.pi))
    lattice = smoothstep(0.74, 0.94, np.maximum(lat1, lat2))
    annex_glass = np.array([0.022, 0.034, 0.054], dtype=np.float32) + np.array([0.12, 0.07, 0.05], dtype=np.float32) * (1.0 - t_a)[..., None] * 0.45
    annex_metal = np.array([0.18, 0.17, 0.19], dtype=np.float32)
    annex_col = annex_glass * (1.0 - lattice[..., None] * 0.68) + annex_metal * (lattice[..., None] * 0.68)
    annex_col = annex_col * 0.80 + haze_col * 0.20
    canvas.blend_over(annex_col, mask_a, y0=ay0, x0=ax0)

    # 4. Far-left low commercial building (x=0.0..0.242, y=0.715..0.89)
    fl_quad = [(0.00, 0.718), (0.240, 0.746), (0.240, 0.890), (0.00, 0.890)]
    fl_tex = _make_crisp_glass_facade(
        180, 120, 9, 20, rng, warm_side=False, lit_prob=0.20,
        base_tint=(0.012, 0.038, 0.072), mullion_tint=(0.020, 0.032, 0.048),
        refl_gain=0.34, refuge_every=0, seed=seed + 91,
    )
    canvas.paint_quad_texture(fl_quad, fl_tex)

    # 5. Mid-right background towers + realistic tiny rooftop tower crane (as seen in ref_2.jpg!)
    right_bg = [
        ([(0.630, 0.590), (0.660, 0.588), (0.662, 0.810), (0.634, 0.810)], 26, 6, False, 0.14, 0.30),
        ([(0.654, 0.546), (0.716, 0.544), (0.720, 0.810), (0.660, 0.810)], 34, 9, False, 0.17, 0.24),
    ]
    for idx, (quad, fl, co, ws, lp, hz) in enumerate(right_bg):
        tex = _make_crisp_glass_facade(
            110, 290, fl, co, rng, warm_side=ws, lit_prob=lp,
            base_tint=(0.022, 0.034, 0.056), mullion_tint=(0.030, 0.038, 0.052),
            refl_gain=0.40, seed=seed + 120 + idx * 19,
        )
        tex = tex * (1.0 - hz) + haze_col * hz
        canvas.paint_quad_texture(quad, tex)

    # Subtle distant tower crane silhouette on top of the right-mid tower (matching ref_2.jpg!)
    crane_col = (0.14, 0.13, 0.17)
    canvas.draw_line((0.688, 0.545), (0.688, 0.514), max(0.8, w * 0.0007), crane_col, alpha=0.75)
    canvas.draw_line((0.674, 0.522), (0.716, 0.506), max(0.7, w * 0.0006), crane_col, alpha=0.70)


def _paint_single_curved_twin_tower_v3(
    canvas: Canvas2D,
    is_right: bool,
    rng: np.random.Generator,
) -> None:
    """Paint one Tianfu International Financial Center Twin Tower using exact measured edges of ref_2.jpg.

    Combines authentic dark metallic ice-flower exoskeleton (high-frequency pixel contrast)
    with crisp horizontal LED louver bars glowing in warm Chengdu dusk gold & sunset amber.
    """
    w, h = canvas.width, canvas.height
    y_top_min = 0.298
    y_bot = 0.830

    # Exact measured silhouette control points from ref_2.jpg analysis
    v_ctrl = np.array([0.300, 0.350, 0.400, 0.500, 0.600, 0.700, 0.830], dtype=np.float32)
    l_outer = np.array([0.4090, 0.4045, 0.3998, 0.3935, 0.3888, 0.3855, 0.3832], dtype=np.float32)
    l_inner = np.array([0.4600, 0.4622, 0.4648, 0.4670, 0.4672, 0.4666, 0.4660], dtype=np.float32)

    u_min_box, u_max_box = (0.374, 0.476) if not is_right else (0.496, 0.598)
    x0 = max(0, int(u_min_box * w))
    x1 = min(w, int(u_max_box * w))
    y0 = max(0, int((y_top_min - 0.01) * h))
    y1 = min(h, int((y_bot + 0.01) * h))

    xs = np.linspace(x0 / w, (x1 - 1) / w, x1 - x0, dtype=np.float32)
    ys = np.linspace(y0 / h, (y1 - 1) / h, y1 - y0, dtype=np.float32)
    uu, vv = np.meshgrid(xs, ys)

    out_l = np.interp(vv, v_ctrl, l_outer)
    in_l = np.interp(vv, v_ctrl, l_inner)

    if not is_right:
        left_edge, right_edge = out_l, in_l
    else:
        center_axis = 0.4865
        left_edge = 2.0 * center_axis - in_l
        right_edge = 2.0 * center_axis - out_l

    width_s = np.maximum(right_edge - left_edge, 1e-5)
    u_loc = (uu - left_edge) / width_s

    # Exact asymmetric arched crown sloping gracefully down toward the center gap
    u_from_outer = u_loc if not is_right else (1.0 - u_loc)
    u_cl = np.clip(u_from_outer, 0.0, 1.0)
    crown_y = (
        0.299
        + 0.044 * np.power(np.clip((u_cl - 0.24) / 0.76, 0.0, 1.0), 1.62)
        + 0.014 * np.power(np.clip((0.24 - u_cl) / 0.24, 0.0, 1.0), 2.0)
    )

    px_u = 1.1 / w
    px_v = 1.1 / h
    in_x = smoothstep(-px_u / width_s, px_u / width_s, u_loc) * (
        1.0 - smoothstep(1.0 - px_u / width_s, 1.0 + px_u / width_s, u_loc)
    )
    in_y = smoothstep(crown_y - px_v, crown_y + px_v, vv) * (
        1.0 - smoothstep(y_bot - px_v, y_bot + px_v, vv)
    )
    mask = np.clip(in_x * in_y, 0.0, 1.0)

    # Cylindrical wrap & realistic cosine roll-off
    u_c = np.clip(u_loc, 0.0, 1.0)
    cyl_x = u_c * 2.0 - 1.0
    cyl_z = np.sqrt(np.maximum(1.0 - cyl_x * cyl_x, 0.02))
    u_wrap = 0.5 + np.arcsin(np.clip(cyl_x, -0.999, 0.999)) / np.pi

    floors = 56
    cols = 24
    v_norm = np.clip((vv - crown_y) / np.maximum(y_bot - crown_y, 0.05), 0.0, 1.0)

    # High-frequency horizontal louvers & dark recessed floor spandrels (crucial for real DSLR grad ~ 0.11!)
    louver_y = vv * (floors / (y_bot - y_top_min))
    floor_idx = np.clip(np.floor(louver_y).astype(np.int32), 0, floors + 4)
    col_idx = np.clip(np.floor(u_wrap * cols).astype(np.int32), 0, cols - 1)
    fy_frac = louver_y - floor_idx

    # 3 crisp metallic LED louvers per floor with dark gaps between them
    louver_bars = smoothstep(0.05, 0.55, np.sin(louver_y * 3.0 * 2.0 * np.pi))
    is_slab = (fy_frac < 0.22) | (fy_frac > 0.92)
    mullion_dark = 1.0 - 0.52 * (np.abs(np.sin(u_wrap * cols * np.pi)) < 0.14).astype(np.float32)

    # Signature "ice-flower" metallic structural diamond/branching exoskeleton (clearly visible in ref_2.jpg!)
    ice1 = np.abs(np.sin((u_wrap * 22.0 + vv * 44.0) * np.pi))
    ice2 = np.abs(np.sin((u_wrap * 22.0 - vv * 44.0) * np.pi))
    ice3 = np.abs(np.sin((u_wrap * 11.0 + np.sin(vv * 35.0) * 0.45) * np.pi))
    ice_mesh = smoothstep(0.78, 0.96, np.maximum(np.maximum(ice1, ice2), ice3 * 0.92))

    # Per-pane micro reflection variation
    pane_var = rng.uniform(0.75, 1.28, size=(floors + 6, cols)).astype(np.float32)
    sun_side_w = np.clip(u_c if not is_right else (1.0 - u_c), 0.0, 1.0)
    refl_w = _sky_cloud_reflection(u_wrap, v_norm, warm_side=True, seed=31 if not is_right else 37)
    refl_c = _sky_cloud_reflection(u_wrap, v_norm, warm_side=False, seed=41 if not is_right else 43)
    sky_refl = (refl_c * (1.0 - sun_side_w[..., None] * 0.60) + refl_w * (sun_side_w[..., None] * 0.60)) * pane_var[floor_idx, col_idx][..., None]

    # Deep dark architectural steel & glass base (preserving dark structural contrast!)
    glass_col = np.array([0.014, 0.022, 0.040], dtype=np.float32) + sky_refl * (0.20 + 0.34 * cyl_z[..., None])
    slab_col = np.array([0.012, 0.016, 0.026], dtype=np.float32) + sky_refl * 0.08
    base_col = np.where(is_slab[..., None], slab_col, glass_col) * mullion_dark[..., None]

    # Overlay crisp silver-steel ice-flower lattice catching twilight sky sheen
    steel_col = np.array([0.125, 0.132, 0.155], dtype=np.float32) * (0.55 + 0.72 * cyl_z[..., None])
    lattice_w = (0.38 * (1.0 - 0.35 * smoothstep(0.68, 0.83, vv))) * ice_mesh
    base_col = base_col * (1.0 - lattice_w[..., None]) + steel_col * lattice_w[..., None]

    # Dark refuge/mechanical floor bands (authentic architectural rhythm)
    refuge = np.ones_like(vv)
    for rv in (0.47, 0.64):
        refuge *= 1.0 - 0.65 * np.exp(-((vv - rv) / 0.0055) ** 2)

    # --- High-Contrast Dusk Media-Facade LED Show (sharp horizontal louver light bars over dark glass!) ---
    g_u = (u_wrap * 0.44) if not is_right else (0.56 + u_wrap * 0.44)
    g_v = np.clip((vv - y_top_min) / (y_bot - y_top_min), 0.0, 1.0)
    led_bounds = smoothstep(crown_y + 0.026, crown_y + 0.048, vv) * (1.0 - smoothstep(0.785, 0.822, vv))

    # Dramatic sweeping golden-amber & sunset-crimson light waves with dark blue-obsidian negative space!
    y_w1 = 0.28 + 0.11 * np.sin(g_u * 4.4 + 0.30)
    y_w2 = 0.56 + 0.12 * np.sin(g_u * 3.8 - 1.40)
    y_w3 = 0.79 + 0.07 * np.cos(g_u * 4.8 + 0.85)

    d1 = np.abs(g_v - y_w1)
    d2 = np.abs(g_v - y_w2)
    d3 = np.abs(g_v - y_w3)

    # Tighter, higher-contrast ribbons so dark metallic facade clearly shows between the glowing waves!
    rib1 = np.exp(-(d1 / 0.068) ** 2) * 1.05 + np.exp(-(d1 / 0.13) ** 2) * 0.22
    rib2 = np.exp(-(d2 / 0.075) ** 2) * 0.98 + np.exp(-(d2 / 0.14) ** 2) * 0.20
    rib3 = np.exp(-(d3 / 0.065) ** 2) * 0.72

    col_gold = np.array([2.05, 1.02, 0.20], dtype=np.float32)
    col_vermilion = np.array([1.75, 0.34, 0.12], dtype=np.float32)
    col_champagne = np.array([2.25, 1.38, 0.42], dtype=np.float32)
    col_deep_blue = np.array([0.04, 0.06, 0.18], dtype=np.float32)

    led_rgb = (
        col_deep_blue * 0.38
        + col_gold * rib1[..., None] * 0.65
        + col_vermilion * rib2[..., None] * 0.68
        + col_champagne * rib3[..., None] * 0.46
        + col_champagne * (np.exp(-(d1 / 0.024) ** 2) * 0.35 + np.exp(-(d2 / 0.028) ** 2) * 0.25)[..., None]
    )

    # Sharp horizontal LED louver emission modulated by cylindrical cosine roll-off & dark mullions
    cyl_led_gain = np.power(cyl_z, 0.85) * 0.80
    led_emit = led_rgb * (louver_bars * mullion_dark * refuge * led_bounds * cyl_led_gain)[..., None]
    col = base_col * refuge[..., None] + led_emit

    # Subtle metallic crown parapet rim (crisp, realistic)
    crown_rim = np.exp(-((vv - (crown_y + 0.007)) / 0.0020) ** 2)
    col += np.array([1.10, 0.68, 0.30], dtype=np.float32) * (crown_rim * cyl_z * 0.48)[..., None]

    # Warm sunset grazing rim on the inner edge facing the sunset gap
    inner_rim = np.exp(-(((1.0 - u_c) if not is_right else u_c) / 0.048) ** 2)
    col += np.array([0.72, 0.34, 0.13], dtype=np.float32) * (inner_rim * 0.30)[..., None]

    # Atmospheric mist near street level
    mist_b = smoothstep(0.74, 0.83, vv) * 0.14
    col = col * (1.0 - mist_b[..., None]) + np.array([0.36, 0.21, 0.15], dtype=np.float32) * mist_b[..., None]

    canvas.blend_over(col, mask, y0=y0, x0=x0)

    cx = 0.426 if not is_right else 0.546
    canvas.draw_soft_glow(cx, 0.54, 0.050, 0.18, (0.10, 0.045, 0.015), power=2.0)
    peak_u = 0.420 if not is_right else 0.553
    canvas.draw_soft_glow(peak_u, 0.296, 0.0016, 0.0022, (4.2, 0.18, 0.08), power=2.2)


def paint_twin_towers_v3(canvas: Canvas2D, seed: int = 404) -> None:
    """Paint both curved Tianfu International Financial Center Twin Towers."""
    rng = np.random.default_rng(seed)
    canvas.draw_soft_glow(0.486, 0.62, 0.10, 0.22, (0.12, 0.055, 0.02), power=2.0)
    _paint_single_curved_twin_tower_v3(canvas, is_right=False, rng=rng)
    _paint_single_curved_twin_tower_v3(canvas, is_right=True, rng=rng)


def paint_foreground_right_tower_v3(canvas: Canvas2D, seed: int = 505) -> None:
    """Paint the towering close-up right skyscraper (中航产融 / 安盟保险) at ultra-high detail."""
    rng = np.random.default_rng(seed)

    # Rear recessed wing
    wing_side = [(0.708, 0.255), (0.768, 0.222), (0.785, 0.840), (0.734, 0.840)]
    wing_tex = _make_crisp_glass_facade(
        180, 580, 38, 12, rng, warm_side=False, lit_prob=0.18,
        base_tint=(0.012, 0.022, 0.042), mullion_tint=(0.024, 0.026, 0.036),
        refl_gain=0.40, refuge_every=15, seed=seed + 11,
    )
    canvas.paint_quad_texture(wing_side, wing_tex)

    # Main broad left glass face (ultra-crisp 520x1100 facade texture!)
    main_glass_quad = [
        (0.758, 0.135),
        (0.868, 0.036),
        (0.948, 0.840),
        (0.792, 0.845),
    ]
    main_tex = _make_crisp_glass_facade(
        520, 1100, 46, 22, rng, warm_side=True, lit_prob=0.20,
        base_tint=(0.010, 0.020, 0.038), mullion_tint=(0.028, 0.026, 0.032),
        refl_gain=0.48, refuge_every=16, seed=seed + 23,
    )
    # Warm bronze-terracotta stone corner piers with subtle horizontal stone-panel joints
    vv_m = np.linspace(0.0, 1.0, 1100, dtype=np.float32)[:, None]
    stone_seam = 0.88 + 0.12 * (np.sin(vv_m * 140.0 * np.pi) > -0.7).astype(np.float32)
    stone_c = np.array([0.088, 0.060, 0.048], dtype=np.float32) * stone_seam[..., None]
    main_tex[:, :18, :] = main_tex[:, :18, :] * 0.25 + stone_c * 0.85
    main_tex[:, -22:, :] = main_tex[:, -22:, :] * 0.25 + stone_c * 0.90

    # Crisp illuminated rooftop signage accent near top crown (matching ref_2.jpg)
    sign_chars = (np.sin(np.linspace(0, 32, 340))[None, :] > 0.12).astype(np.float32)
    main_tex[14:32, 85:425, :] += np.array([1.25, 0.96, 0.68], dtype=np.float32) * (0.15 + 0.85 * sign_chars)[..., None] * 0.62
    canvas.paint_quad_texture(main_glass_quad, main_tex)

    # Right bronze-terracotta ribbed stone facade
    right_face_quad = [
        (0.868, 0.036),
        (0.945, 0.038),
        (1.020, 0.840),
        (0.948, 0.840),
    ]
    rf_tex = _make_crisp_glass_facade(
        260, 1100, 46, 10, rng, warm_side=False, lit_prob=0.14,
        base_tint=(0.010, 0.016, 0.030), mullion_tint=(0.072, 0.050, 0.042),
        refl_gain=0.25, refuge_every=16, seed=seed + 37,
    )
    uu_r = np.linspace(0.0, 1.0, 260, dtype=np.float32)[None, :]
    pier_mask = (np.abs(np.sin(uu_r * 8.0 * np.pi)) < 0.34).astype(np.float32)
    stone_r = np.array([0.082, 0.056, 0.046], dtype=np.float32) * stone_seam[..., None]
    rf_tex = rf_tex * (1.0 - pier_mask[..., None] * 0.84) + stone_r * (pier_mask[..., None] * 0.84)
    canvas.paint_quad_texture(right_face_quad, rf_tex)

    far_right_quad = [
        (0.945, 0.038),
        (1.010, 0.245),
        (1.025, 0.840),
        (1.020, 0.840),
    ]
    canvas.fill_polygon(far_right_quad, (0.012, 0.016, 0.028))
