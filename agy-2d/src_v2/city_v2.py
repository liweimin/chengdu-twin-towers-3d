"""Pure 2D architectural painting matching the real Chengdu Financial City Jiaozi Avenue view (v2.2).

Refinements over v2_draft1:
- Solidly anchored Convention Center dome between Twin Towers (no bright gap beneath).
- Finer, deeper, more photographic Twin Towers facade: rich dark obsidian-steel base,
  crisp dense horizontal louvers, subtle ice-flower mesh, and luxurious golden-amber /
  sunset-crimson flowing LED illumination (removing blocky window patches & thick crown band).
- Moodier twilight contrast on left background towers & curved ice-flower lattice annex.
- Richer dark reflective glass & warm bronze-stone ribs on foreground right skyscraper.
"""

from __future__ import annotations

import numpy as np

from canvas2d import Canvas2D
from noise2d import smoothstep


def _sky_refl_color(v_norm: np.ndarray, warm_side: bool = False) -> np.ndarray:
    t = np.clip(v_norm, 0.0, 1.0)
    if warm_side:
        c0 = np.array([0.09, 0.08, 0.16], dtype=np.float32)
        c1 = np.array([0.46, 0.21, 0.18], dtype=np.float32)
        c2 = np.array([0.92, 0.42, 0.18], dtype=np.float32)
    else:
        c0 = np.array([0.025, 0.048, 0.115], dtype=np.float32)
        c1 = np.array([0.11, 0.095, 0.175], dtype=np.float32)
        c2 = np.array([0.28, 0.16, 0.16], dtype=np.float32)
    w1 = smoothstep(0.0, 0.55, t)[..., None]
    w2 = smoothstep(0.45, 1.0, t)[..., None]
    col = c0 * (1.0 - w1) + c1 * w1
    return col * (1.0 - w2) + c2 * w2


def _make_glass_tower_tex(
    tw: int,
    th: int,
    floors: int,
    cols: int,
    rng: np.random.Generator,
    warm_side: bool = False,
    lit_prob: float = 0.20,
    base_tint: tuple[float, float, float] = (0.010, 0.018, 0.036),
    mullion_tint: tuple[float, float, float] = (0.007, 0.012, 0.024),
    refl_gain: float = 0.34,
    refuge_every: int = 14,
) -> np.ndarray:
    """High-detail procedural twilight glass curtain-wall facade texture."""
    vv = np.linspace(0.0, 1.0, th, dtype=np.float32)[:, None]
    uu = np.linspace(0.0, 1.0, tw, dtype=np.float32)[None, :]

    fy = vv * floors
    fx = uu * cols
    fi = np.clip(np.floor(fy).astype(np.int32), 0, floors - 1)
    ci = np.clip(np.floor(fx).astype(np.int32), 0, cols - 1)
    ff = fy - fi
    cf = fx - ci

    spandrel = (ff < 0.27) | (ff > 0.94)
    mullion = (cf < 0.11) | (cf > 0.91)
    glass = (~spandrel) & (~mullion)

    pane_tilt = rng.normal(0.0, 0.035, size=(floors, cols)).astype(np.float32)
    pane_var = rng.uniform(0.82, 1.20, size=(floors, cols)).astype(np.float32)
    v_pert = np.clip(vv + pane_tilt[fi, ci], 0.0, 1.0)

    refl = _sky_refl_color(v_pert, warm_side=warm_side)
    wave = 1.0 + 0.12 * np.sin(v_pert * 10.0 + uu * 3.0) + 0.07 * np.cos(v_pert * 22.0 - uu * 5.0)
    refl = refl * wave[..., None] * pane_var[fi, ci][..., None]

    tex = np.array(base_tint, dtype=np.float32) + refl * refl_gain
    frame = np.array(mullion_tint, dtype=np.float32) + refl * (refl_gain * 0.20)
    tex = np.where(glass[..., None], tex, frame)

    # Organic clustered office interior lighting
    fl_act = rng.uniform(0.0, 1.0, size=(floors, 1))
    bay_n = rng.uniform(0.0, 1.0, size=(floors, cols))
    bay_sm = 0.4 * bay_n + 0.35 * np.roll(bay_n, 1, axis=1) + 0.25 * np.roll(bay_n, -1, axis=1)
    lit = (fl_act * 0.50 + bay_sm * 0.65) > (1.0 - lit_prob)
    if refuge_every > 0:
        for mf in range(refuge_every - 1, floors, refuge_every):
            lit[mf, :] = False
    lit[0:2, :] = False

    temp = rng.uniform(0.0, 1.0, size=(floors, cols)).astype(np.float32)
    inten = rng.uniform(0.24, 0.95, size=(floors, cols)).astype(np.float32) * lit.astype(np.float32)
    warm_c = np.array([1.35, 0.80, 0.34], dtype=np.float32)
    neut_c = np.array([1.05, 0.90, 0.70], dtype=np.float32)
    cool_c = np.array([0.65, 0.84, 1.15], dtype=np.float32)
    ic = np.where(temp[..., None] < 0.66, warm_c, np.where(temp[..., None] < 0.88, neut_c, cool_c)) * inten[..., None]

    ceil_g = 0.55 + 0.45 * (1.0 - np.clip((ff - 0.27) / 0.67, 0.0, 1.0))
    tex = np.where(glass[..., None], tex + ic[fi, ci] * ceil_g[..., None] * 0.78, tex)

    if refuge_every > 0:
        is_refuge = ((fi + 1) % refuge_every == 0) & (fi < floors - 2)
        tex = np.where(is_refuge[..., None], frame * 0.60, tex)

    return tex


def paint_background_architecture_v2(canvas: Canvas2D, seed: int = 202) -> None:
    """Paint the distant dome and surrounding Financial City towers matching ref_2.jpg."""
    rng = np.random.default_rng(seed)
    w, h = canvas.width, canvas.height
    u, v = canvas.u_grid()

    # 1. Distant Tianfu New City Convention Center Dome peeking between Twin Towers
    # Solidly grounded down to v = 0.832 with dark twilight plaza/trees at its base!
    y0, y1 = int(0.768 * h), int(0.836 * h)
    x0, x1 = int(0.452 * w), int(0.518 * w)
    uu = u[y0:y1, x0:x1]
    vv = v[y0:y1, x0:x1]
    dx = (uu - 0.485) / 0.032
    # Upper dome arch + solid lower drum down to y=0.832
    dome_top = 0.778 + 0.022 * np.clip(dx * dx, 0.0, 1.5)
    dome_mask = smoothstep(dome_top - 0.002, dome_top + 0.002, vv) * (np.abs(dx) <= 1.0)
    ribs = 0.86 + 0.14 * np.sin((vv - 0.775) * 460.0)
    # Warm golden-lit ribbed roof transitioning to dark twilight base & trees
    base_shade = smoothstep(0.806, 0.824, vv)
    dome_col = (
        np.array([0.30, 0.22, 0.18], dtype=np.float32) * (1.0 - 0.30 * dx * dx)[..., None] * ribs[..., None]
        * (1.0 - base_shade[..., None] * 0.82)
        + np.array([0.025, 0.028, 0.032], dtype=np.float32) * base_shade[..., None]
    )
    # Subtle warm lobby glow strip at bottom of dome
    lobby_glow = np.exp(-((vv - 0.814) / 0.0035) ** 2) * (np.abs(dx) < 0.85)
    dome_col += np.array([0.85, 0.48, 0.18], dtype=np.float32) * lobby_glow[..., None] * 0.55
    canvas.blend_over(dome_col, dome_mask, y0=y0, x0=x0)

    # 2. Left background Financial City tower cluster (matching ref_2.jpg x=0.20..0.388)
    haze_col = np.array([0.24, 0.15, 0.19], dtype=np.float32)

    left_towers = [
        ([(0.204, 0.604), (0.256, 0.600), (0.252, 0.768), (0.198, 0.768)], 24, 7, False, 0.16, 0.28),
        ([(0.262, 0.618), (0.285, 0.616), (0.283, 0.782), (0.259, 0.782)], 22, 4, False, 0.14, 0.30),
        ([(0.282, 0.538), (0.344, 0.536), (0.338, 0.798), (0.273, 0.798)], 34, 8, False, 0.18, 0.22),
        ([(0.339, 0.618), (0.371, 0.616), (0.367, 0.808), (0.335, 0.808)], 26, 5, False, 0.16, 0.26),
        ([(0.366, 0.695), (0.390, 0.695), (0.388, 0.818), (0.364, 0.818)], 16, 4, False, 0.14, 0.30),
    ]
    for quad, fl, co, ws, lp, hz in left_towers:
        tex = _make_glass_tower_tex(
            76, 230, fl, co, rng, warm_side=ws, lit_prob=lp,
            base_tint=(0.016, 0.026, 0.048), refl_gain=0.38,
        )
        tex = tex * (1.0 - hz) + haze_col * hz
        canvas.paint_quad_texture(quad, tex)

    # 3. Curved ice-flower lattice annex building on the left (moody twilight glass + subtle metallic mesh)
    ay0, ay1 = int(0.676 * h), int(0.830 * h)
    ax0, ax1 = int(0.150 * w), int(0.320 * w)
    au = u[ay0:ay1, ax0:ax1]
    av = v[ay0:ay1, ax0:ax1]
    t_a = np.clip((au - 0.155) / (0.312 - 0.155), 0.0, 1.0)
    roof_a = 0.686 + 0.068 * np.power(t_a, 1.35)
    mask_a = (
        smoothstep(roof_a - 0.002, roof_a + 0.002, av)
        * smoothstep(0.154, 0.157, au)
        * (1.0 - smoothstep(0.310, 0.314, au))
    )
    lat1 = np.abs(np.sin((au * 150.0 + av * 115.0) * np.pi))
    lat2 = np.abs(np.sin((au * 150.0 - av * 115.0) * np.pi))
    lattice = smoothstep(0.78, 0.95, np.maximum(lat1, lat2))
    annex_glass = np.array([0.020, 0.032, 0.056], dtype=np.float32) + np.array([0.14, 0.075, 0.05], dtype=np.float32) * (1.0 - t_a)[..., None] * 0.45
    annex_metal = np.array([0.14, 0.13, 0.16], dtype=np.float32)
    annex_col = annex_glass * (1.0 - lattice[..., None] * 0.60) + annex_metal * (lattice[..., None] * 0.60)
    annex_col = annex_col * 0.82 + haze_col * 0.18
    canvas.blend_over(annex_col, mask_a, y0=ay0, x0=ax0)

    # 4. Far-left low blue-glass commercial building (x=0.0..0.242, y=0.715..0.88)
    fl_quad = [(0.00, 0.718), (0.240, 0.746), (0.240, 0.880), (0.00, 0.880)]
    fl_tex = _make_glass_tower_tex(
        140, 96, 9, 18, rng, warm_side=False, lit_prob=0.22,
        base_tint=(0.010, 0.034, 0.068), refl_gain=0.30, refuge_every=0,
    )
    canvas.paint_quad_texture(fl_quad, fl_tex)

    # 5. Mid-right background towers between Right Twin Tower & foreground right skyscraper
    right_bg = [
        ([(0.630, 0.590), (0.660, 0.588), (0.662, 0.805), (0.634, 0.805)], 26, 5, False, 0.15, 0.28),
        ([(0.654, 0.546), (0.716, 0.544), (0.720, 0.805), (0.660, 0.805)], 32, 8, False, 0.19, 0.22),
    ]
    for quad, fl, co, ws, lp, hz in right_bg:
        tex = _make_glass_tower_tex(
            84, 230, fl, co, rng, warm_side=ws, lit_prob=lp,
            base_tint=(0.016, 0.026, 0.048), refl_gain=0.36,
        )
        tex = tex * (1.0 - hz) + haze_col * hz
        canvas.paint_quad_texture(quad, tex)


def _paint_single_curved_twin_tower(
    canvas: Canvas2D,
    is_right: bool,
    rng: np.random.Generator,
) -> None:
    """Paint one curved bamboo-shoot Tianfu International Financial Center Twin Tower (v2.2)."""
    w, h = canvas.width, canvas.height
    y_top_min = 0.298
    y_bot = 0.828

    if not is_right:
        u_min_box, u_max_box = 0.376, 0.476
    else:
        u_min_box, u_max_box = 0.496, 0.596

    x0 = max(0, int(u_min_box * w))
    x1 = min(w, int(u_max_box * w))
    y0 = max(0, int((y_top_min - 0.01) * h))
    y1 = min(h, int((y_bot + 0.01) * h))

    xs = np.linspace(x0 / w, (x1 - 1) / w, x1 - x0, dtype=np.float32)
    ys = np.linspace(y0 / h, (y1 - 1) / h, y1 - y0, dtype=np.float32)
    uu, vv = np.meshgrid(xs, ys)

    s = np.clip((y_bot - vv) / (y_bot - y_top_min), 0.0, 1.0)

    outer_x_l = 0.384 + 0.022 * np.power(s, 1.65) - 0.005 * np.sin(s * np.pi)
    inner_x_l = 0.468 - 0.007 * np.power(s, 1.85) + 0.004 * np.sin(s * np.pi)

    if not is_right:
        left_edge = outer_x_l
        right_edge = inner_x_l
    else:
        center_axis = 0.486
        left_edge = 2.0 * center_axis - inner_x_l
        right_edge = 2.0 * center_axis - outer_x_l

    width_s = np.maximum(right_edge - left_edge, 1e-5)
    u_loc = (uu - left_edge) / width_s

    # Iconic asymmetric arched crown matching ref_2.jpg
    u_from_outer = u_loc if not is_right else (1.0 - u_loc)
    u_clamped = np.clip(u_from_outer, 0.0, 1.0)
    crown_y = (
        0.299
        + 0.044 * np.power(np.clip((u_clamped - 0.24) / 0.76, 0.0, 1.0), 1.65)
        + 0.015 * np.power(np.clip((0.24 - u_clamped) / 0.24, 0.0, 1.0), 2.0)
    )

    px_u = 1.2 / w
    px_v = 1.2 / h
    in_x = smoothstep(-px_u / width_s, px_u / width_s, u_loc) * (
        1.0 - smoothstep(1.0 - px_u / width_s, 1.0 + px_u / width_s, u_loc)
    )
    in_y = smoothstep(crown_y - px_v, crown_y + px_v, vv) * (
        1.0 - smoothstep(y_bot - px_v, y_bot + px_v, vv)
    )
    mask = np.clip(in_x * in_y, 0.0, 1.0)

    # Cylindrical surface wrap & roll-off
    u_c = np.clip(u_loc, 0.0, 1.0)
    cyl_x = u_c * 2.0 - 1.0
    cyl_z = np.sqrt(np.maximum(1.0 - cyl_x * cyl_x, 0.02))
    u_wrap = 0.5 + np.arcsin(np.clip(cyl_x, -0.999, 0.999)) / np.pi

    floors = 54
    v_norm = np.clip((vv - crown_y) / np.maximum(y_bot - crown_y, 0.05), 0.0, 1.0)

    # Fine dense horizontal louvers + subtle vertical structural mullions
    louver_y = vv * (floors / (y_bot - y_top_min))
    louver_bars = smoothstep(-0.12, 0.58, np.sin(louver_y * 3.0 * 2.0 * np.pi))
    floor_slabs = 1.0 - 0.42 * (np.abs(np.sin(louver_y * np.pi)) < 0.14).astype(np.float32)

    cols = 22
    mullions = 1.0 - 0.34 * (np.abs(np.sin(u_wrap * cols * np.pi)) < 0.12).astype(np.float32)

    # Signature subtle "ice-flower" metallic structural lattice (from ref_2.jpg)
    ice_lat = 0.5 + 0.5 * np.sin(u_wrap * 32.0 * np.pi + vv * 60.0) * np.cos(u_wrap * 28.0 * np.pi - vv * 52.0)
    ice_mesh = smoothstep(0.65, 0.93, ice_lat)

    # Deep obsidian-blue cylindrical glass base reflecting sunset sky
    sun_side_w = np.clip(u_c if not is_right else (1.0 - u_c), 0.0, 1.0)
    refl_warm = _sky_refl_color(v_norm, warm_side=True)
    refl_cool = _sky_refl_color(v_norm, warm_side=False)
    sky_refl = refl_cool * (1.0 - sun_side_w[..., None] * 0.62) + refl_warm * (sun_side_w[..., None] * 0.62)

    base_col = (
        np.array([0.010, 0.016, 0.032], dtype=np.float32)
        + sky_refl * (0.16 + 0.28 * cyl_z[..., None])
        + np.array([0.045, 0.050, 0.068], dtype=np.float32) * (ice_mesh * 0.26 * cyl_z)[..., None]
    ) * (floor_slabs * mullions)[..., None]

    # --- Iconic Cylindrical Dusk Media-Facade LED Show (rich, moody, NOT washed-out white!) ---
    g_u = (u_wrap * 0.44) if not is_right else (0.56 + u_wrap * 0.44)
    g_v = np.clip((vv - y_top_min) / (y_bot - y_top_min), 0.0, 1.0)

    # Dark crown glass cap above LED screen (just like real Twin Towers!)
    led_bounds = smoothstep(crown_y + 0.022, crown_y + 0.045, vv) * (1.0 - smoothstep(0.778, 0.818, vv))

    # Sweeping golden-amber & sunset-vermilion silk waves across both curved towers
    y_w1 = 0.30 + 0.11 * np.sin(g_u * 4.4 + 0.35)
    y_w2 = 0.56 + 0.12 * np.sin(g_u * 3.9 - 1.45)
    y_w3 = 0.78 + 0.07 * np.cos(g_u * 4.8 + 0.85)

    d1 = np.abs(g_v - y_w1)
    d2 = np.abs(g_v - y_w2)
    d3 = np.abs(g_v - y_w3)

    rib1 = np.exp(-(d1 / 0.088) ** 2) * 0.92 + np.exp(-(d1 / 0.17) ** 2) * 0.26
    rib2 = np.exp(-(d2 / 0.095) ** 2) * 0.88 + np.exp(-(d2 / 0.18) ** 2) * 0.24
    rib3 = np.exp(-(d3 / 0.080) ** 2) * 0.65 + np.exp(-(d3 / 0.15) ** 2) * 0.20

    # Deep blue-indigo & burgundy-crimson LED backdrop so the golden silk pops with true HDR depth!
    bg_led = (
        np.array([0.055, 0.055, 0.20], dtype=np.float32) * (1.0 - g_v[..., None])
        + np.array([0.28, 0.055, 0.11], dtype=np.float32) * g_v[..., None]
    )
    col_gold = np.array([1.95, 0.92, 0.16], dtype=np.float32)
    col_vermilion = np.array([1.68, 0.30, 0.10], dtype=np.float32)
    col_champagne = np.array([2.15, 1.25, 0.34], dtype=np.float32)

    led_rgb = (
        bg_led * 0.44
        + col_gold * rib1[..., None] * 0.62
        + col_vermilion * rib2[..., None] * 0.68
        + col_champagne * rib3[..., None] * 0.45
        + col_champagne * (np.exp(-(d1 / 0.032) ** 2) * 0.32 + np.exp(-(d2 / 0.036) ** 2) * 0.24)[..., None]
    )

    # Strong cylindrical viewing-angle shading makes the roundness unmistakable!
    cyl_led_gain = np.power(cyl_z, 0.78) * 0.82
    col = base_col + led_rgb * (louver_bars * mullions * led_bounds * cyl_led_gain)[..., None]

    # Subtle refined architectural crown rim (thin, realistic, NOT a thick white headband)
    crown_rim = np.exp(-((vv - (crown_y + 0.008)) / 0.0024) ** 2)
    col += np.array([1.35, 0.78, 0.32], dtype=np.float32) * (crown_rim * cyl_z * 0.55)[..., None]

    # Warm sunset grazing rim on the inner edge facing the gap
    inner_rim = np.exp(-(((1.0 - u_c) if not is_right else u_c) / 0.055) ** 2)
    col += np.array([0.75, 0.32, 0.11], dtype=np.float32) * (inner_rim * 0.32)[..., None]

    # Gentle atmospheric mist near street level
    mist_b = smoothstep(0.73, 0.83, vv) * 0.14
    col = col * (1.0 - mist_b[..., None]) + np.array([0.36, 0.19, 0.13], dtype=np.float32) * mist_b[..., None]

    canvas.blend_over(col, mask, y0=y0, x0=x0)

    cx = 0.426 if not is_right else 0.546
    canvas.draw_soft_glow(cx, 0.54, 0.052, 0.19, (0.12, 0.05, 0.015), power=2.0)
    peak_u = 0.420 if not is_right else 0.552
    canvas.draw_soft_glow(peak_u, 0.295, 0.0018, 0.0025, (4.4, 0.20, 0.09), power=2.2)


def paint_twin_towers_v2(canvas: Canvas2D, seed: int = 404) -> None:
    """Paint both curved Tianfu International Financial Center Twin Towers."""
    rng = np.random.default_rng(seed)
    canvas.draw_soft_glow(0.486, 0.62, 0.11, 0.24, (0.14, 0.06, 0.02), power=2.0)
    _paint_single_curved_twin_tower(canvas, is_right=False, rng=rng)
    _paint_single_curved_twin_tower(canvas, is_right=True, rng=rng)


def paint_foreground_right_tower_v2(canvas: Canvas2D, seed: int = 505) -> None:
    """Paint the towering close-up right skyscraper (中航产融 / 安盟保险) matching ref_2.jpg."""
    rng = np.random.default_rng(seed)

    # Rear recessed wing
    wing_side = [(0.708, 0.255), (0.768, 0.222), (0.785, 0.840), (0.734, 0.840)]
    wing_tex = _make_glass_tower_tex(
        110, 380, 38, 12, rng, warm_side=False, lit_prob=0.20,
        base_tint=(0.010, 0.018, 0.036), mullion_tint=(0.018, 0.016, 0.022),
        refl_gain=0.34, refuge_every=15,
    )
    canvas.paint_quad_texture(wing_side, wing_tex)

    # Main broad left glass face (facing Jiaozi Avenue & sunset!)
    main_glass_quad = [
        (0.758, 0.135),
        (0.868, 0.036),
        (0.948, 0.840),
        (0.792, 0.845),
    ]
    main_tex = _make_glass_tower_tex(
        280, 620, 46, 22, rng, warm_side=True, lit_prob=0.22,
        base_tint=(0.008, 0.016, 0.034), mullion_tint=(0.022, 0.018, 0.022),
        refl_gain=0.40, refuge_every=16,
    )
    main_tex[:, :10, :] = main_tex[:, :10, :] * 0.35 + np.array([0.07, 0.044, 0.034], dtype=np.float32)
    main_tex[:, -12:, :] = main_tex[:, -12:, :] * 0.35 + np.array([0.08, 0.050, 0.038], dtype=np.float32)
    # Subtle illuminated rooftop signage strip near top-left crown
    main_tex[8:18, 42:220, :] += np.array([1.15, 0.85, 0.52], dtype=np.float32) * (
        0.20 + 0.80 * (np.sin(np.linspace(0, 28, 178))[None, :] > 0.15)
    )[..., None] * 0.58
    canvas.paint_quad_texture(main_glass_quad, main_tex)

    # Right bronze-stone ribbed facade
    right_face_quad = [
        (0.868, 0.036),
        (0.945, 0.038),
        (1.020, 0.840),
        (0.948, 0.840),
    ]
    rf_tex = _make_glass_tower_tex(
        160, 620, 46, 10, rng, warm_side=False, lit_prob=0.16,
        base_tint=(0.009, 0.014, 0.026), mullion_tint=(0.070, 0.045, 0.038),
        refl_gain=0.22, refuge_every=16,
    )
    uu_r = np.linspace(0.0, 1.0, 160, dtype=np.float32)[None, :]
    pier_mask = (np.abs(np.sin(uu_r * 8.0 * np.pi)) < 0.34).astype(np.float32)
    stone_col = np.array([0.075, 0.048, 0.040], dtype=np.float32)
    rf_tex = rf_tex * (1.0 - pier_mask[..., None] * 0.82) + stone_col * (pier_mask[..., None] * 0.82)
    canvas.paint_quad_texture(right_face_quad, rf_tex)

    far_right_quad = [
        (0.945, 0.038),
        (1.010, 0.245),
        (1.025, 0.840),
        (1.020, 0.840),
    ]
    canvas.fill_polygon(far_right_quad, (0.010, 0.014, 0.026))
