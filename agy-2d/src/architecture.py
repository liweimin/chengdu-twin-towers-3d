"""Pure 2D architectural painting for Chengdu Financial City Twin Towers at dusk (v3).

Refinements for true photographic realism:
- Consistent backlit sunset physics: ALL camera-facing broad facades stay in
  moody cool twilight shadow while narrow angled side faces catch warm golden
  grazing sunset reflections (fixing left/right consistency).
- Luxurious, painterly flowing golden-amber & sunset-crimson LED silk waves on
  the Twin Towers (no harsh thin laser curves), darker obsidian glass base,
  and refined multi-bay glass podium.
- Proper depth layering of Jiaozi Ring (交子之环): back arc behind trees, front
  illuminated vermilion-orange ring cleanly in front of trees with dark
  structural soffit & warm pedestrian glow.
- Refined embankment, organic dark lakeside trees, and delicate non-blocky
  waterfront lamps & silky traffic trails.
"""

from __future__ import annotations

import numpy as np

from canvas2d import Canvas2D
from noise2d import fbm_2d, smoothstep


def _sample_sky_reflection(
    v_norm: np.ndarray,
    is_sun_side: bool,
    sun_proximity: float = 0.6,
) -> np.ndarray:
    """Rich sunset sky reflection for dark architectural glass."""
    t = np.clip(v_norm, 0.0, 1.0)
    if is_sun_side:
        top_col = np.array([0.11, 0.085, 0.17], dtype=np.float32)
        mid_col = np.array([0.58, 0.23, 0.15], dtype=np.float32)
        bot_col = np.array([1.15, 0.45, 0.15], dtype=np.float32)
    else:
        top_col = np.array([0.022, 0.042, 0.105], dtype=np.float32)
        mid_col = np.array([0.090, 0.078, 0.155], dtype=np.float32)
        bot_col = np.array([0.24, 0.125, 0.105], dtype=np.float32)

    w1 = smoothstep(0.0, 0.52, t)[..., None]
    w2 = smoothstep(0.44, 1.0, t)[..., None]
    col = top_col * (1.0 - w1) + mid_col * w1
    col = col * (1.0 - w2) + bot_col * w2
    return col * (0.74 + 0.40 * sun_proximity)


def _generate_office_facade_texture(
    tw: int,
    th: int,
    floors: int,
    cols: int,
    is_sun_side: bool,
    rng: np.random.Generator,
    lit_prob: float = 0.18,
    crown_color: tuple[float, float, float] | None = None,
    vertical_accent: tuple[float, float, float] | None = None,
    sun_proximity: float = 0.5,
    style: str = "curtain",
) -> np.ndarray:
    """Generate a photorealistic dark twilight skyscraper facade texture (linear HDR)."""
    vv = np.linspace(0.0, 1.0, th, dtype=np.float32)[:, None]
    uu = np.linspace(0.0, 1.0, tw, dtype=np.float32)[None, :]

    fy = vv * floors
    fx = uu * cols
    floor_idx = np.clip(np.floor(fy).astype(np.int32), 0, floors - 1)
    col_idx = np.clip(np.floor(fx).astype(np.int32), 0, cols - 1)
    fy_frac = fy - floor_idx
    fx_frac = fx - col_idx

    if style == "horizontal_band":
        is_spandrel = (fy_frac < 0.36) | (fy_frac > 0.94)
        is_mullion = (fx_frac < 0.06) | (fx_frac > 0.95)
    elif style == "vertical_fin":
        is_spandrel = (fy_frac < 0.22) | (fy_frac > 0.94)
        is_mullion = (fx_frac < 0.16) | (fx_frac > 0.86)
    else:
        is_spandrel = (fy_frac < 0.28) | (fy_frac > 0.95)
        is_mullion = (fx_frac < 0.10) | (fx_frac > 0.92)

    glass_mask = (~is_spandrel) & (~is_mullion)

    pane_tilt = rng.normal(0.0, 0.04, size=(floors, cols)).astype(np.float32)
    pane_gain = rng.uniform(0.80, 1.22, size=(floors, cols)).astype(np.float32)
    v_pert = np.clip(vv + pane_tilt[floor_idx, col_idx], 0.0, 1.0)

    refl = _sample_sky_reflection(v_pert, is_sun_side=is_sun_side, sun_proximity=sun_proximity)
    cloud_band = np.sin(v_pert * 11.0 + uu * 2.0) * 0.10 + np.sin(v_pert * 25.0 - uu * 3.5) * 0.06
    refl = refl * (1.0 + cloud_band[..., None]) * pane_gain[floor_idx, col_idx][..., None]

    base_glass = np.array([0.008, 0.014, 0.028], dtype=np.float32)
    refl_strength = 0.42 if is_sun_side else 0.24
    tex = base_glass + refl * refl_strength

    frame_col = np.array([0.006, 0.009, 0.017], dtype=np.float32) + refl * (0.08 if is_sun_side else 0.04)
    tex = np.where(glass_mask[..., None], tex, frame_col)

    # Contiguous lit office suites on scattered floors
    floor_on = rng.uniform(0.0, 1.0, size=(floors, 1))
    bay_raw = rng.uniform(0.0, 1.0, size=(floors, cols))
    bay_run = 0.4 * bay_raw + 0.35 * np.roll(bay_raw, 1, axis=1) + 0.25 * np.roll(bay_raw, -1, axis=1)
    lit_grid = (floor_on * 0.50 + bay_run * 0.65) > (1.0 - lit_prob)

    for mf in range(13, floors, 15):
        lit_grid[mf, :] = False
    lit_grid[0:2, :] = False

    temp_pick = rng.uniform(0.0, 1.0, size=(floors, cols)).astype(np.float32)
    intensity = rng.uniform(0.22, 0.92, size=(floors, cols)).astype(np.float32) * lit_grid.astype(np.float32)

    warm_c = np.array([1.35, 0.78, 0.30], dtype=np.float32)
    neut_c = np.array([1.05, 0.88, 0.65], dtype=np.float32)
    cool_c = np.array([0.62, 0.80, 1.12], dtype=np.float32)

    int_col = np.where(
        temp_pick[..., None] < 0.68,
        warm_c,
        np.where(temp_pick[..., None] < 0.90, neut_c, cool_c),
    ) * intensity[..., None]

    win_grad = 0.55 + 0.50 * (1.0 - np.clip((fy_frac - 0.24) / 0.70, 0.0, 1.0))
    interior_rgb = int_col[floor_idx, col_idx] * win_grad[..., None]
    tex = np.where(glass_mask[..., None], tex + interior_rgb * 0.76, tex)

    parapet = vv < 0.022
    tex = np.where(parapet[..., None], np.array([0.008, 0.011, 0.020], dtype=np.float32), tex)

    if crown_color is not None:
        crown_band = np.exp(-((vv - 0.024) / 0.0065) ** 2)
        tex += np.array(crown_color, dtype=np.float32)[None, None, :] * crown_band[..., None]

    if vertical_accent is not None:
        edge_mask = np.exp(-((uu - 0.025) / 0.010) ** 2) + np.exp(-((uu - 0.975) / 0.010) ** 2)
        vert_fade = smoothstep(0.02, 0.10, vv) * (1.0 - smoothstep(0.85, 0.98, vv))
        tex += np.array(vertical_accent, dtype=np.float32)[None, None, :] * (edge_mask * vert_fade)[..., None]

    return tex


def _generate_twin_tower_facade(
    tw: int,
    th: int,
    tower_index: int,
    is_side_face: bool,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate the signature Tianfu International Financial Center Twin Tower facade (v3).

    Dark obsidian-navy glass curtain wall + crisp horizontal LED louver bars
    rendering a lush, sweeping golden-amber, sunset-crimson, and deep-indigo
    architectural light show seamlessly spanning both towers.
    """
    floors = 54
    cols = 14 if not is_side_face else 6

    tex = _generate_office_facade_texture(
        tw=tw,
        th=th,
        floors=floors,
        cols=cols,
        is_sun_side=is_side_face,
        rng=rng,
        lit_prob=0.09,
        crown_color=None,
        vertical_accent=None,
        sun_proximity=0.88 if is_side_face else 0.45,
        style="curtain",
    )

    vv = np.linspace(0.0, 1.0, th, dtype=np.float32)[:, None]
    uu = np.linspace(0.0, 1.0, tw, dtype=np.float32)[None, :]

    # Continuous horizontal coordinate across BOTH towers so the LED art flows seamlessly
    if not is_side_face:
        g_u = uu * 0.43 if tower_index == 0 else (0.57 + uu * 0.43)
    else:
        g_u = (0.43 + uu * 0.09) if tower_index == 0 else (0.48 + uu * 0.09)

    # Crisp horizontal LED louver bars (3 fine horizontal LED strips per floor)
    louver_phase = np.sin(vv * floors * 3.0 * 2.0 * np.pi)
    louver_mask = smoothstep(-0.08, 0.62, louver_phase)
    # Dark vertical mullions subtly divide the LED louver bars
    mullion_break = 1.0 - 0.45 * (np.abs(np.sin(uu * cols * np.pi)) < 0.13).astype(np.float32)

    # Subtle dark architectural refuge/mechanical bands at 1/3 and 2/3 height
    refuge_mask = np.ones_like(vv)
    for rf in (0.335, 0.665):
        refuge_mask *= 1.0 - 0.58 * np.exp(-((vv - rf) / 0.0085) ** 2)

    screen_bounds = smoothstep(0.036, 0.058, vv) * (1.0 - smoothstep(0.89, 0.94, vv))

    # --- Lush Sweeping Golden Silk & Chengdu Sunset Wave LED Show (no sharp laser lines!) ---
    # Broad, graceful overlapping luminous silk waves flowing from Left Tower to Right Tower
    y_rib1 = 0.29 + 0.11 * np.sin(g_u * 4.2 + 0.25) + 0.025 * np.cos(g_u * 8.4)
    y_rib2 = 0.53 + 0.12 * np.sin(g_u * 3.9 - 1.55) + 0.022 * np.sin(g_u * 7.8)
    y_rib3 = 0.74 + 0.08 * np.cos(g_u * 4.6 + 0.9)

    d1 = np.abs(vv - y_rib1)
    d2 = np.abs(vv - y_rib2)
    d3 = np.abs(vv - y_rib3)

    # Soft, painterly Gaussian silk bands with gentle vertical texture
    rib1 = np.exp(-(d1 / 0.085) ** 2) * 0.95 + np.exp(-(d1 / 0.16) ** 2) * 0.32
    rib2 = np.exp(-(d2 / 0.095) ** 2) * 0.90 + np.exp(-(d2 / 0.18) ** 2) * 0.30
    rib3 = np.exp(-(d3 / 0.075) ** 2) * 0.72 + np.exp(-(d3 / 0.15) ** 2) * 0.25

    # Soft woven silk shimmer along the waves
    weave = 0.80 + 0.20 * np.sin(g_u * 12.0 + vv * 14.0) * np.cos(g_u * 5.0 - vv * 9.0)

    # Rich dark-twilight LED canvas backdrop (deep royal blue -> warm crimson-plum -> deep indigo)
    col_bg_top = np.array([0.07, 0.06, 0.22], dtype=np.float32)
    col_bg_mid = np.array([0.34, 0.07, 0.14], dtype=np.float32)
    col_bg_bot = np.array([0.20, 0.06, 0.14], dtype=np.float32)
    w_bg1 = smoothstep(0.05, 0.50, vv)[..., None]
    w_bg2 = smoothstep(0.50, 0.92, vv)[..., None]
    bg_led = col_bg_top * (1.0 - w_bg1) + col_bg_mid * w_bg1
    bg_led = bg_led * (1.0 - w_bg2) + col_bg_bot * w_bg2

    # Saturated architectural gold, molten amber, and Chengdu vermilion-crimson
    col_gold = np.array([2.05, 0.98, 0.18], dtype=np.float32)
    col_vermilion = np.array([1.72, 0.32, 0.11], dtype=np.float32)
    col_champagne = np.array([2.20, 1.32, 0.36], dtype=np.float32)

    led_rgb = (
        bg_led * 0.48
        + col_gold * (rib1 * weave)[..., None] * 0.68
        + col_vermilion * (rib2 * weave)[..., None] * 0.75
        + col_champagne * (rib3 * weave)[..., None] * 0.52
    )

    # Soft luminous highlight core (much broader & gentler than v2, reads like real LED video!)
    core1 = np.exp(-(d1 / 0.032) ** 2)
    core2 = np.exp(-(d2 / 0.036) ** 2)
    led_rgb += col_champagne * (core1 * 0.42 + core2 * 0.32)[..., None]

    # Micro LED pixel-pitch variation
    pitch_var = rng.uniform(0.86, 1.14, size=(floors * 3, cols * 2)).astype(np.float32)
    sy_i = np.clip((vv * floors * 3).astype(np.int32), 0, floors * 3 - 1)
    sx_i = np.clip((uu * cols * 2).astype(np.int32), 0, cols * 2 - 1)
    led_rgb *= pitch_var[sy_i, sx_i][..., None]

    angle_gain = 0.46 if is_side_face else 0.84
    led_mask = (louver_mask * mullion_break * refuge_mask * screen_bounds * angle_gain)[..., None]
    tex = tex + led_rgb * led_mask

    # --- Sleek Architectural Crown & Beveled Vertical Corner Grooves ---
    parapet = vv < 0.035
    tex = np.where(parapet[..., None], np.array([0.010, 0.014, 0.028], dtype=np.float32), tex)

    crown_main = np.exp(-((vv - 0.035) / 0.0040) ** 2)
    crown_top = np.exp(-((vv - 0.007) / 0.0030) ** 2) * 0.42
    tex += np.array([1.85, 1.05, 0.34], dtype=np.float32)[None, None, :] * (crown_main + crown_top)[..., None]

    if not is_side_face:
        # Subtle dark chamfered corner shadows + warm/cool architectural rim
        l_edge = np.exp(-((uu - 0.012) / 0.009) ** 2)
        r_edge = np.exp(-((uu - 0.988) / 0.009) ** 2)
        tex += np.array([0.85, 0.38, 0.14], dtype=np.float32)[None, None, :] * (l_edge * 0.40)[..., None]
        tex += np.array([0.32, 0.42, 0.74], dtype=np.float32)[None, None, :] * (r_edge * 0.22)[..., None]

    base_ao = 1.0 - 0.52 * smoothstep(0.86, 1.0, vv)
    tex *= base_ao[..., None]

    return tex


def paint_distant_skyline(
    canvas: Canvas2D,
    horizon_v: float = 0.625,
    seed: int = 201,
) -> None:
    """Paint soft distant Financial City / High-Tech Zone skyscrapers receding into basin mist."""
    rng = np.random.default_rng(seed)
    haze_col = np.array([0.19, 0.12, 0.18], dtype=np.float32)
    sun_haze = np.array([0.48, 0.22, 0.13], dtype=np.float32)

    xs = np.linspace(0.01, 0.99, 34)
    for cx in xs:
        if 0.41 < cx < 0.59:
            bh = rng.uniform(0.03, 0.075)
        else:
            bh = rng.uniform(0.055, 0.165)
        bw = rng.uniform(0.016, 0.038)
        x0 = cx - bw * 0.5
        x1 = cx + bw * 0.5
        y_top = horizon_v - bh
        y_bot = horizon_v + 0.008

        quad = [(x0, y_top), (x1, y_top), (x1, y_bot), (x0, y_bot)]
        tw, th = 32, 110
        vv = np.linspace(0.0, 1.0, th, dtype=np.float32)[:, None]
        uu = np.linspace(0.0, 1.0, tw, dtype=np.float32)[None, :]

        sun_w = float(np.exp(-((cx - 0.48) / 0.28) ** 2))
        sil_col = (
            np.array([0.042, 0.045, 0.090], dtype=np.float32) * (1.0 - 0.42 * sun_w)
            + sun_haze * (0.30 * sun_w)
            + haze_col * 0.18
        )
        tex = np.broadcast_to(sil_col[None, None, :], (th, tw, 3)).copy()
        tex += (haze_col * 0.26 + sun_haze * 0.22 * sun_w)[None, None, :] * (vv ** 1.5)[..., None]

        tex *= (0.93 + 0.07 * np.sin(uu * 20.0))[..., None]
        floors = max(12, int(bh * 230))
        cols = max(4, int(bw * 210))
        fy = np.clip((vv * floors).astype(np.int32), 0, floors - 1)
        fx = np.clip((uu * cols).astype(np.int32), 0, cols - 1)
        dots = (rng.uniform(0.0, 1.0, size=(floors, cols)) > 0.88).astype(np.float32)
        dots *= rng.uniform(0.12, 0.38, size=(floors, cols)).astype(np.float32)
        tex += dots[fy, fx][..., None] * np.array([1.1, 0.72, 0.32], dtype=np.float32) * 0.45

        canvas.paint_quad_texture(quad, tex, alpha=0.90)


def _paint_architectural_tower(
    canvas: Canvas2D,
    cx: float,
    base_v: float,
    height: float,
    front_w: float,
    side_w: float,
    side_on_left: bool,
    floors: int,
    cols: int,
    rng: np.random.Generator,
    lit_prob: float = 0.17,
    crown_color: tuple[float, float, float] | None = None,
    vertical_accent: tuple[float, float, float] | None = None,
    has_beacon: bool = False,
    roof_type: str = "flat",
    style: str = "curtain",
    haze_amount: float = 0.12,
) -> None:
    """Paint a 2D two-face perspective skyscraper with consistent backlit sunset lighting."""
    y_top = base_v - height
    y_bot = base_v + 0.008
    taper = 0.0018
    tilt = 0.0038 * (height / 0.25)
    sun_prox = float(np.exp(-((cx - 0.48) / 0.44) ** 2))

    slope_l = 0.016 if roof_type == "slope_right" else 0.0
    slope_r = 0.016 if roof_type == "slope_left" else 0.0

    # Backlit sunset physics: broad camera-facing front faces are in cool twilight shadow,
    # while narrow side faces angled toward the central sunset catch warm golden grazing light!
    front_is_sun = False
    side_is_sun = True

    if side_on_left:
        sx0 = cx - front_w * 0.5 - side_w
        sx1 = cx - front_w * 0.5
        fx0 = sx1
        fx1 = cx + front_w * 0.5
        side_quad = [
            (sx0 + taper, y_top + tilt + slope_l),
            (sx1, y_top + slope_l),
            (sx1, y_bot),
            (sx0, y_bot),
        ]
        front_quad = [
            (fx0, y_top + slope_l),
            (fx1 - taper, y_top + tilt * 0.5 + slope_r),
            (fx1, y_bot),
            (fx0, y_bot),
        ]
        peak_x = fx0 if slope_l <= slope_r else fx1
        peak_y = min(y_top + slope_l, y_top + tilt * 0.5 + slope_r)
    else:
        fx0 = cx - front_w * 0.5
        fx1 = cx + front_w * 0.5
        sx0 = fx1
        sx1 = fx1 + side_w
        front_quad = [
            (fx0 + taper, y_top + tilt * 0.5 + slope_l),
            (fx1, y_top + slope_r),
            (fx1, y_bot),
            (fx0, y_bot),
        ]
        side_quad = [
            (sx0, y_top + slope_r),
            (sx1 - taper, y_top + tilt + slope_r),
            (sx1, y_bot),
            (sx0, y_bot),
        ]
        peak_x = fx1 if slope_r <= slope_l else fx0
        peak_y = min(y_top + slope_r, y_top + tilt * 0.5 + slope_l)

    th = max(120, int(height * canvas.height * 1.15))
    tw_f = max(48, int(front_w * canvas.width * 1.2))
    tw_s = max(24, int(side_w * canvas.width * 1.2))

    front_tex = _generate_office_facade_texture(
        tw=tw_f, th=th, floors=floors, cols=cols, is_sun_side=front_is_sun,
        rng=rng, lit_prob=lit_prob, crown_color=crown_color,
        vertical_accent=vertical_accent, sun_proximity=sun_prox, style=style,
    )
    side_tex = _generate_office_facade_texture(
        tw=tw_s, th=th, floors=floors, cols=max(3, cols // 2), is_sun_side=side_is_sun,
        rng=rng, lit_prob=lit_prob * 0.80, crown_color=crown_color,
        vertical_accent=None, sun_proximity=sun_prox, style=style,
    )

    if haze_amount > 0.0:
        haze_col = np.array([0.24, 0.14, 0.17], dtype=np.float32) * (1.0 + 0.52 * sun_prox)
        vv = np.linspace(0.0, 1.0, th, dtype=np.float32)[:, None, None]
        hm = haze_amount * (0.38 + 0.62 * vv)
        front_tex = front_tex * (1.0 - hm) + haze_col * hm
        side_tex = side_tex * (1.0 - hm) + haze_col * hm

    canvas.paint_quad_texture(front_quad, front_tex)
    canvas.paint_quad_texture(side_quad, side_tex)

    if roof_type == "stepped":
        step_h = height * 0.085
        step_w = front_w * 0.64
        st_x0 = cx - step_w * 0.5
        st_x1 = cx + step_w * 0.5
        st_quad = [(st_x0, y_top - step_h), (st_x1, y_top - step_h), (st_x1, y_top + 0.002), (st_x0, y_top + 0.002)]
        st_tex = np.full((24, 48, 3), [0.010, 0.015, 0.032], dtype=np.float32)
        if crown_color is not None:
            st_tex[1:5, :, :] += np.array(crown_color, dtype=np.float32) * 0.85
        canvas.paint_quad_texture(st_quad, st_tex)
        peak_y = y_top - step_h
        peak_x = cx

    if roof_type == "spire":
        spire_h = 0.032
        canvas.paint_bezier_ribbon(
            (peak_x, peak_y), (peak_x, peak_y - spire_h * 0.5),
            (peak_x, peak_y - spire_h * 0.8), (peak_x, peak_y - spire_h),
            width_px=max(0.9, canvas.width * 0.0007),
            color_start=(0.05, 0.06, 0.10),
            color_end=(0.10, 0.09, 0.13),
            steps=24,
            additive=False,
        )
        peak_y -= spire_h

    if has_beacon:
        canvas.draw_soft_glow(
            cx_norm=peak_x,
            cy_norm=peak_y - 0.002,
            radius_x_norm=0.0020,
            radius_y_norm=0.0030,
            color=(4.2, 0.22, 0.10),
            power=2.2,
        )


def paint_midground_skyline(
    canvas: Canvas2D,
    horizon_v: float = 0.625,
    seed: int = 303,
) -> None:
    """Paint overlapping back-row and front-row Chengdu Financial City skyscrapers."""
    rng = np.random.default_rng(seed)

    back_row = [
        (0.080, 0.255, 0.044, 0.015, False, 34, 8, 0.14, None, None, False, "flat", "horizontal_band", 0.22),
        (0.205, 0.245, 0.048, 0.016, False, 32, 9, 0.15, (0.9, 0.65, 0.35), None, False, "stepped", "curtain", 0.20),
        (0.338, 0.185, 0.042, 0.014, False, 24, 8, 0.16, None, None, False, "flat", "vertical_fin", 0.22),
        (0.672, 0.205, 0.044, 0.014, True, 28, 8, 0.15, None, None, False, "flat", "horizontal_band", 0.22),
        (0.805, 0.260, 0.046, 0.016, True, 35, 9, 0.14, (0.7, 0.85, 1.3), None, False, "stepped", "curtain", 0.20),
        (0.945, 0.205, 0.044, 0.015, True, 28, 8, 0.14, None, None, False, "flat", "curtain", 0.22),
    ]
    for b in back_row:
        _paint_architectural_tower(canvas, b[0], horizon_v, *b[1:7], rng, *b[7:])

    front_row = [
        # Left Financial City cluster
        (0.032, 0.225, 0.052, 0.018, False, 30, 9, 0.20, (1.1, 0.72, 0.35), None, True, "slope_right", "curtain", 0.10),
        (0.122, 0.300, 0.048, 0.018, False, 42, 9, 0.18, (0.65, 0.88, 1.45), (0.45, 0.65, 1.15), True, "stepped", "vertical_fin", 0.09),
        (0.182, 0.190, 0.044, 0.015, False, 26, 8, 0.22, (1.2, 0.68, 0.30), None, False, "flat", "horizontal_band", 0.11),
        (0.248, 0.270, 0.052, 0.019, False, 38, 10, 0.19, (1.3, 0.88, 0.42), None, True, "spire", "curtain", 0.08),
        (0.308, 0.175, 0.046, 0.015, False, 24, 8, 0.21, None, None, False, "slope_left", "horizontal_band", 0.10),
        (0.365, 0.148, 0.038, 0.013, False, 20, 7, 0.18, (1.0, 0.62, 0.28), None, False, "flat", "curtain", 0.12),
        # Right Financial City cluster
        (0.642, 0.165, 0.040, 0.014, True, 22, 7, 0.19, (1.1, 0.72, 0.35), None, False, "flat", "horizontal_band", 0.12),
        (0.708, 0.278, 0.052, 0.019, True, 38, 10, 0.18, (1.3, 0.82, 0.38), (0.95, 0.58, 0.25), True, "stepped", "curtain", 0.09),
        (0.772, 0.215, 0.046, 0.016, True, 30, 8, 0.21, (0.65, 0.88, 1.40), None, False, "slope_right", "vertical_fin", 0.10),
        (0.844, 0.312, 0.054, 0.020, True, 44, 10, 0.17, (1.35, 0.84, 0.38), None, True, "spire", "curtain", 0.08),
        (0.912, 0.232, 0.046, 0.016, True, 32, 8, 0.20, (1.1, 0.70, 0.32), None, False, "slope_left", "horizontal_band", 0.10),
        (0.972, 0.172, 0.046, 0.016, True, 24, 8, 0.17, None, None, False, "flat", "curtain", 0.12),
    ]
    for b in front_row:
        _paint_architectural_tower(canvas, b[0], horizon_v, *b[1:7], rng, *b[7:])


def paint_twin_towers(
    canvas: Canvas2D,
    horizon_v: float = 0.625,
    seed: int = 404,
) -> None:
    """Paint the hero Chengdu Financial City Twin Towers (天府国际金融中心双子塔)."""
    rng = np.random.default_rng(seed)

    base_v = horizon_v + 0.008
    top_v = 0.150
    height = base_v - top_v

    towers = [
        {"idx": 0, "cx": 0.448, "front_w": 0.060, "side_w": 0.016, "side_on_left": False},
        {"idx": 1, "cx": 0.552, "front_w": 0.060, "side_w": 0.016, "side_on_left": True},
    ]

    canvas.draw_soft_glow(0.500, 0.47, 0.10, 0.18, (0.14, 0.058, 0.022), power=2.0)

    th = max(520, int(height * canvas.height * 1.30))
    tw_front = max(150, int(0.060 * canvas.width * 1.5))
    tw_side = max(48, int(0.016 * canvas.width * 1.7))

    for t in towers:
        cx = t["cx"]
        fw = t["front_w"]
        sw = t["side_w"]
        taper = 0.0020
        roof_tilt = 0.0042

        if t["side_on_left"]:
            sx0 = cx - fw * 0.5 - sw * 0.6
            sx1 = cx - fw * 0.5 + sw * 0.4
            fx0 = sx1
            fx1 = cx + fw * 0.5 + sw * 0.4
            side_quad = [
                (sx0 + taper, top_v + roof_tilt),
                (sx1 + taper * 0.3, top_v),
                (sx1, base_v),
                (sx0, base_v),
            ]
            front_quad = [
                (fx0 + taper * 0.3, top_v),
                (fx1 - taper, top_v + roof_tilt * 0.45),
                (fx1, base_v),
                (fx0, base_v),
            ]
            beacon_pts = [(fx0 + 0.0035, top_v - 0.0035), (fx1 - 0.0035, top_v - 0.002)]
        else:
            fx0 = cx - fw * 0.5 - sw * 0.4
            fx1 = cx + fw * 0.5 - sw * 0.4
            sx0 = fx1
            sx1 = fx1 + sw
            front_quad = [
                (fx0 + taper, top_v + roof_tilt * 0.45),
                (fx1 - taper * 0.3, top_v),
                (fx1, base_v),
                (fx0, base_v),
            ]
            side_quad = [
                (sx0 - taper * 0.3, top_v),
                (sx1 - taper, top_v + roof_tilt),
                (sx1, base_v),
                (sx0, base_v),
            ]
            beacon_pts = [(fx0 + 0.0035, top_v - 0.002), (fx1 - 0.0035, top_v - 0.0035)]

        front_tex = _generate_twin_tower_facade(
            tw=tw_front, th=th, tower_index=t["idx"], is_side_face=False, rng=rng
        )
        side_tex = _generate_twin_tower_facade(
            tw=tw_side, th=th, tower_index=t["idx"], is_side_face=True, rng=rng
        )

        vv = np.linspace(0.0, 1.0, th, dtype=np.float32)[:, None, None]
        mist = smoothstep(0.78, 1.0, vv) * 0.11
        mist_col = np.array([0.44, 0.22, 0.14], dtype=np.float32)
        front_tex = front_tex * (1.0 - mist) + mist_col * mist
        side_tex = side_tex * (1.0 - mist) + mist_col * mist

        canvas.paint_quad_texture(front_quad, front_tex)
        canvas.paint_quad_texture(side_quad, side_tex)

        for bx, by in beacon_pts:
            canvas.draw_soft_glow(bx, by, 0.0022, 0.0032, (4.8, 0.22, 0.10), power=2.2)

        canvas.draw_soft_glow(cx, 0.40, 0.048, 0.19, (0.15, 0.062, 0.018), power=2.0)

    # Refined rectilinear dark-glass commercial podium connecting the base of the Twin Towers
    podium_quad = [(0.402, horizon_v - 0.015), (0.598, horizon_v - 0.015), (0.598, base_v), (0.402, base_v)]
    ptex = np.full((44, 240, 3), [0.007, 0.011, 0.020], dtype=np.float32)
    pu = np.linspace(0, 1, 240, dtype=np.float32)[None, :]
    pv = np.linspace(0, 1, 44, dtype=np.float32)[:, None]
    mullions = (np.abs(np.sin(pu * 38.0 * np.pi)) > 0.22).astype(np.float32)
    floor_bar = (np.abs(pv - 0.50) > 0.09).astype(np.float32)
    bay_var = 0.35 + 0.65 * (np.sin(pu * 13.0 + 0.7) ** 2) * (0.6 + 0.4 * np.cos(pu * 29.0))
    glass_p = mullions * floor_bar * (pv > 0.16) * (pv < 0.88)
    ptex += np.array([0.82, 0.44, 0.16], dtype=np.float32) * (glass_p * bay_var * 0.48)[..., None]
    ptex[1:3, :, :] += np.array([0.85, 0.46, 0.18], dtype=np.float32) * 0.55
    canvas.paint_quad_texture(podium_quad, ptex)


def paint_jiaozi_ring_and_waterfront(
    canvas: Canvas2D,
    horizon_v: float = 0.625,
    waterline_v: float = 0.658,
    seed: int = 505,
) -> None:
    """Paint Jiaozi Ring (交子之环) with realistic architectural perspective, trees, lamps & traffic."""
    rng = np.random.default_rng(seed)
    w, h = canvas.width, canvas.height

    # Realistic low-angle architectural perspective for Jiaozi Ring (flatter, solid vermilion-orange bridge)
    ring_cx = 0.285
    ring_cy = horizon_v - 0.013
    rx = 0.098
    ry = 0.0115

    # 1. Jiaozi Ring BACK arc (darker distant vermilion-red steel fascia behind the trees)
    canvas.paint_bezier_ribbon(
        (ring_cx - rx, ring_cy),
        (ring_cx - rx, ring_cy - ry * 1.35),
        (ring_cx + rx, ring_cy - ry * 1.35),
        (ring_cx + rx, ring_cy),
        width_px=max(1.6, w * 0.0018),
        color_start=(0.72, 0.15, 0.05),
        color_end=(0.82, 0.18, 0.06),
        steps=180,
        additive=False,
    )

    # 2. Organic riverside park treeline silhouette (Jiaozi Park / Jinjiang embankment)
    u, v = canvas.u_grid()
    y0 = int(max(0, (horizon_v - 0.042) * h))
    y1 = int(min(h, (waterline_v + 0.005) * h))
    uu_s = u[y0:y1, :]
    vv_s = v[y0:y1, :]

    tree_macro = fbm_2d(uu_s * 24.0, np.zeros_like(uu_s) + 1.3, octaves=4, seed=seed + 7)
    tree_mid = fbm_2d(uu_s * 68.0, np.zeros_like(uu_s) + 4.7, octaves=4, seed=seed + 19)
    tree_leaf = fbm_2d(uu_s * 170.0, vv_s * 180.0, octaves=3, seed=seed + 31)

    center_dip = 1.0 - 0.58 * np.exp(-((uu_s - 0.50) / 0.16) ** 2)
    canopy_top = (
        horizon_v
        + 0.012
        - (0.008 + 0.025 * tree_macro + 0.010 * tree_mid) * center_dip
    )

    tree_mask = smoothstep(canopy_top - 0.0018, canopy_top + 0.0018, vv_s) * (
        1.0 - smoothstep(waterline_v - 0.009, waterline_v - 0.004, vv_s)
    )
    tree_col = (
        np.array([0.005, 0.010, 0.014], dtype=np.float32)
        + np.array([0.016, 0.014, 0.009], dtype=np.float32) * tree_leaf[..., None]
    )
    warm_uplight = smoothstep(canopy_top + 0.006, waterline_v - 0.010, vv_s) * tree_leaf
    tree_col += np.array([0.068, 0.032, 0.010], dtype=np.float32) * warm_uplight[..., None]
    canvas.blend_over(tree_col, tree_mask * 0.96, y0=y0, x0=0)

    # 3. Jiaozi Ring STRUCTURAL PIERS & SOLID FRONT FASCIA (in front of park trees)
    for px in (ring_cx - rx * 0.72, ring_cx - rx * 0.25, ring_cx + rx * 0.25, ring_cx + rx * 0.72):
        pier_quad = [
            (px - 0.0022, ring_cy + ry * 0.65),
            (px + 0.0022, ring_cy + ry * 0.65),
            (px + 0.0028, waterline_v - 0.008),
            (px - 0.0028, waterline_v - 0.008),
        ]
        pier_tex = np.full((16, 8, 3), [0.016, 0.013, 0.019], dtype=np.float32)
        canvas.paint_quad_texture(pier_quad, pier_tex)

    # Dark architectural underside soffit of the pedestrian bridge deck
    canvas.paint_bezier_ribbon(
        (ring_cx - rx, ring_cy + 0.0030),
        (ring_cx - rx, ring_cy + ry * 1.48 + 0.0030),
        (ring_cx + rx, ring_cy + ry * 1.48 + 0.0030),
        (ring_cx + rx, ring_cy + 0.0030),
        width_px=max(2.2, w * 0.0024),
        color_start=(0.022, 0.012, 0.014),
        color_end=(0.022, 0.012, 0.014),
        steps=180,
        additive=False,
    )
    # Iconic architectural vermilion-red/orange outer fascia (solid, rich, NOT blown-out yellow neon!)
    canvas.paint_bezier_ribbon(
        (ring_cx - rx, ring_cy),
        (ring_cx - rx, ring_cy + ry * 1.48),
        (ring_cx + rx, ring_cy + ry * 1.48),
        (ring_cx + rx, ring_cy),
        width_px=max(2.6, w * 0.0030),
        color_start=(1.38, 0.24, 0.06),
        color_end=(1.55, 0.30, 0.07),
        steps=200,
        additive=False,
    )
    # Fine warm architectural top parapet light along the ring
    canvas.paint_bezier_ribbon(
        (ring_cx - rx * 0.96, ring_cy - 0.0012),
        (ring_cx - rx * 0.96, ring_cy + ry * 1.38 - 0.0012),
        (ring_cx + rx * 0.96, ring_cy + ry * 1.38 - 0.0012),
        (ring_cx + rx * 0.96, ring_cy - 0.0012),
        width_px=max(0.85, w * 0.0009),
        color_start=(1.65, 0.62, 0.16),
        color_end=(1.65, 0.62, 0.16),
        steps=180,
        additive=True,
    )
    # Restrained warm glow beneath Jiaozi Ring
    canvas.draw_soft_glow(ring_cx, ring_cy + 0.006, 0.095, 0.020, (0.20, 0.045, 0.012), power=2.0)

    # 4. Dark stone embankment wall along the water's edge
    wall_mask = smoothstep(waterline_v - 0.010, waterline_v - 0.0085, vv_s) * (
        1.0 - smoothstep(waterline_v - 0.001, waterline_v + 0.001, vv_s)
    )
    wall_col = np.array([0.010, 0.013, 0.020], dtype=np.float32) + 0.008 * tree_leaf[..., None]
    canvas.blend_over(wall_col, wall_mask, y0=y0, x0=0)

    # 5. Organic long-exposure traffic light trails (varied discrete streaks, NOT a ruler-straight bar)
    road_y = waterline_v - 0.0122
    headlight_segments = [
        (0.05, 0.24, 0.85),
        (0.31, 0.56, 1.05),
        (0.64, 0.89, 0.90),
    ]
    for x_a, x_b, gain in headlight_segments:
        xm1 = x_a + (x_b - x_a) * 0.33
        xm2 = x_a + (x_b - x_a) * 0.66
        canvas.paint_bezier_ribbon(
            (x_a, road_y + 0.0010),
            (xm1, road_y - 0.0004),
            (xm2, road_y - 0.0004),
            (x_b, road_y + 0.0008),
            width_px=max(0.60, w * 0.00048),
            color_start=(0.30 * gain, 0.20 * gain, 0.10 * gain),
            color_end=(1.10 * gain, 0.78 * gain, 0.40 * gain),
            steps=120,
            additive=True,
        )

    taillight_segments = [
        (0.02, 0.34, 0.95),
        (0.42, 0.73, 1.10),
        (0.79, 0.97, 0.85),
    ]
    for x_a, x_b, gain in taillight_segments:
        xm1 = x_a + (x_b - x_a) * 0.33
        xm2 = x_a + (x_b - x_a) * 0.66
        canvas.paint_bezier_ribbon(
            (x_a, road_y + 0.0026),
            (xm1, road_y + 0.0012),
            (xm2, road_y + 0.0012),
            (x_b, road_y + 0.0024),
            width_px=max(0.68, w * 0.00054),
            color_start=(1.55 * gain, 0.12 * gain, 0.05 * gain),
            color_end=(0.45 * gain, 0.04 * gain, 0.02 * gain),
            steps=120,
            additive=True,
        )

    # 6. Warm waterfront promenade streetlamps (organic spacing, crisp pinpoint cores + warm halos)
    lamp_xs = np.linspace(0.032, 0.968, 24)
    for lx in lamp_xs:
        ux = float(np.clip(lx + rng.uniform(-0.008, 0.008), 0.015, 0.985))
        ly = waterline_v - 0.0135 + float(rng.uniform(-0.0016, 0.0014))
        bright = float(rng.uniform(0.65, 1.25))
        canvas.draw_soft_glow(ux, ly, 0.0011, 0.0017, (2.6 * bright, 1.42 * bright, 0.42 * bright), power=2.0)
        canvas.draw_soft_glow(ux, ly, 0.0062, 0.0092, (0.26 * bright, 0.11 * bright, 0.028 * bright), power=2.0)

    for bx in np.linspace(0.39, 0.61, 11):
        canvas.draw_soft_glow(float(bx), waterline_v - 0.0052, 0.00075, 0.0010, (1.15, 0.58, 0.18), power=2.0)
