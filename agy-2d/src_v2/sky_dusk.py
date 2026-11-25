"""Pure 2D Chengdu golden-to-blue-hour dusk sky for Jiaozi Avenue perspective (v2.2).

Richer contrast, natural non-blown-out sunset horizon glow behind the Twin Towers,
and dark twilight ground plane below the horizon line.
"""

from __future__ import annotations

import numpy as np

from canvas2d import Canvas2D
from noise2d import fbm_2d, ridged_fbm_2d, smoothstep


def paint_dusk_sky_v2(
    canvas: Canvas2D,
    horizon_v: float = 0.825,
    sun_u: float = 0.48,
    seed: int = 101,
) -> None:
    """Paint an authentic Chengdu basin sunset sky and dark ground below horizon."""
    u, v = canvas.u_grid()
    h, w = canvas.height, canvas.width
    aspect = float(w) / float(h)

    elev = np.clip((horizon_v - v) / max(horizon_v, 1e-5), 0.0, 1.0)

    # 1. Rich photographic blue-hour-to-sunset Rayleigh gradient (controlled HDR, not blown-out white)
    stops_t = np.array([0.00, 0.08, 0.20, 0.36, 0.56, 0.78, 1.00], dtype=np.float32)
    stops_rgb = np.array(
        [
            [1.08, 0.46, 0.18],  # Warm golden-amber sunset horizon
            [0.92, 0.34, 0.19],  # Rich sunset coral-orange
            [0.48, 0.20, 0.26],  # Dusk rose-plum
            [0.18, 0.14, 0.26],  # Twilight violet-cobalt
            [0.068, 0.095, 0.21],  # Deep blue-hour cobalt
            [0.032, 0.056, 0.145],  # Deep twilight indigo
            [0.018, 0.034, 0.098],  # Deep zenith
        ],
        dtype=np.float32,
    )

    sky = np.empty((h, w, 3), dtype=np.float32)
    for c in range(3):
        sky[..., c] = np.interp(elev, stops_t, stops_rgb[:, c])

    # Restrained golden sunset glow behind the Twin Towers gap
    du = (u - sun_u) * aspect
    dv = v - (horizon_v - 0.03)
    sun_dist = np.sqrt(du * du + dv * dv)

    mie_wide = np.exp(-sun_dist * 2.3) * (1.0 - smoothstep(0.32, 0.88, elev))
    mie_core = np.exp(-(du * du * 7.5 + dv * dv * 20.0)) * (1.0 - smoothstep(0.06, 0.36, elev))
    sky += mie_wide[..., None] * np.array([0.36, 0.15, 0.05], dtype=np.float32)
    sky += mie_core[..., None] * np.array([0.55, 0.26, 0.09], dtype=np.float32)

    corner_cool = smoothstep(0.32, 1.0, np.abs(u - sun_u)) * smoothstep(0.14, 0.80, elev)
    sky *= 1.0 - corner_cool[..., None] * np.array([0.22, 0.11, -0.04], dtype=np.float32)

    # 2. Realistic 2D cloud layers with crisp shadowed bellies & glowing sunset undersides
    p_depth = np.power(np.maximum(horizon_v - v, 0.0), 0.82) + 0.17
    px = ((u - 0.52) * aspect) / p_depth
    py = 1.50 / p_depth

    horizon_fade = smoothstep(0.025, 0.18, elev)
    zenith_fade = 1.0 - smoothstep(0.84, 1.0, elev) * 0.35

    # Layer A: High wispy cirrus streaks catching rose-gold light
    cu = px * 0.40 + py * 0.15
    cv = py * 0.54 - px * 0.07
    wx = fbm_2d(cu * 0.62, cv * 0.52, octaves=3, seed=seed + 11)
    wy = fbm_2d(cu * 0.62 + 5.3, cv * 0.52 + 2.7, octaves=3, seed=seed + 23)
    cirrus = ridged_fbm_2d(
        cu * 0.78 + (wx - 0.5) * 1.3,
        cv * 0.70 + (wy - 0.5) * 0.9,
        octaves=5,
        seed=seed + 37,
    )
    cirrus_a = smoothstep(0.46, 0.84, cirrus) * horizon_fade * zenith_fade * 0.44
    sun_prox = np.exp(-sun_dist * 1.25)
    cirrus_col = (
        np.array([0.48, 0.22, 0.30], dtype=np.float32) * (1.0 - sun_prox[..., None])
        + np.array([1.55, 0.65, 0.25], dtype=np.float32) * sun_prox[..., None]
    )
    sky = sky * (1.0 - cirrus_a[..., None] * 0.38) + cirrus_col * cirrus_a[..., None]

    # Layer B: Billowy Chengdu stratocumulus sunset cloud banks ("火烧云")
    dw1 = fbm_2d(px * 0.44 + 2.4, py * 0.60 + 1.1, octaves=4, seed=seed + 53)
    dw2 = fbm_2d(px * 0.44 + 9.1, py * 0.60 + 4.6, octaves=4, seed=seed + 67)
    cx = px * 0.52 + py * 0.10 + (dw1 - 0.5) * 1.30
    cy = py * 0.88 - px * 0.06 + (dw2 - 0.5) * 0.92

    c_base = fbm_2d(cx, cy, octaves=6, lacunarity=2.14, gain=0.53, seed=seed + 79)
    c_fine = fbm_2d(cx * 2.8 + 3.8, cy * 2.8 + 1.7, octaves=4, seed=seed + 109)
    macro = fbm_2d(px * 0.18 + 3.9, py * 0.28 + 1.5, octaves=3, seed=seed + 97)

    c_dens = c_base * 0.62 + c_fine * 0.20 + macro * 0.34 - 0.12
    c_alpha = smoothstep(0.46, 0.73, c_dens) * horizon_fade * zenith_fade

    sun_dx = (sun_u - u) * 0.30
    c_sun1 = fbm_2d(cx + sun_dx * 0.16, cy + 0.22, octaves=5, seed=seed + 79)
    c_sun2 = fbm_2d(cx + sun_dx * 0.32, cy + 0.44, octaves=4, seed=seed + 79)

    rim = np.clip((c_base - c_sun1) * 3.0 + (c_base - c_sun2) * 1.3 + 0.25, 0.0, 1.5)
    underlit = rim * (0.34 + 0.88 * np.exp(-sun_dist * 1.0)) * (1.0 - smoothstep(0.42, 0.95, elev) * 0.64)

    c_dark = (
        np.array([0.055, 0.062, 0.135], dtype=np.float32) * (0.55 + 0.45 * elev[..., None])
        + np.array([0.11, 0.070, 0.125], dtype=np.float32) * (1.0 - elev[..., None])
    )
    c_rose = np.array([1.05, 0.28, 0.22], dtype=np.float32)
    c_gold = np.array([2.05, 0.78, 0.24], dtype=np.float32)

    t1 = smoothstep(0.16, 0.62, underlit)[..., None]
    t2 = smoothstep(0.56, 1.14, underlit)[..., None]
    c_rgb = c_dark * (1.0 - t1) + c_rose * t1
    c_rgb = c_rgb * (1.0 - t2) + c_gold * t2

    haze_w = (1.0 - smoothstep(0.02, 0.20, elev)) * 0.40
    haze_c = np.array([0.85, 0.38, 0.20], dtype=np.float32)
    c_rgb = c_rgb * (1.0 - haze_w[..., None]) + haze_c * haze_w[..., None]

    a_mid = np.clip(c_alpha * 0.88, 0.0, 0.94)[..., None]
    sky = sky * (1.0 - a_mid) + c_rgb * a_mid

    # 3. Dark urban park / ground plane below horizon (so sky NEVER bleeds under trees!)
    ground_mask = smoothstep(horizon_v - 0.008, horizon_v + 0.004, v)
    g_noise = fbm_2d(u * 28.0, v * 40.0, octaves=4, seed=seed + 211)
    ground_col = (
        np.array([0.010, 0.015, 0.018], dtype=np.float32)
        + np.array([0.012, 0.016, 0.012], dtype=np.float32) * g_noise[..., None]
    )
    canvas.img[:] = sky * (1.0 - ground_mask[..., None]) + ground_col * ground_mask[..., None]
