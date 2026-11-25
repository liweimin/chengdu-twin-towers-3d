"""Natural, desaturated DSLR-calibrated Chengdu dusk sky and textured clouds (v3).

Avoids oversaturated purple-magenta CG airbrush; uses authentic camera twilight
colors (slate-steel blue zenith, dusty warm apricot-gold horizon, crisp textured
altocumulus & stratocumulus clouds with dark blue-grey undersides and warm rims).
"""

from __future__ import annotations

import numpy as np

from canvas2d import Canvas2D
from noise2d import fbm_2d, ridged_fbm_2d, smoothstep


def paint_dusk_sky_v3(
    canvas: Canvas2D,
    horizon_v: float = 0.825,
    sun_u: float = 0.475,
    seed: int = 101,
) -> None:
    """Paint a realistic, DSLR-calibrated Chengdu dusk sky and dark ground plane."""
    u, v = canvas.u_grid()
    h, w = canvas.height, canvas.width
    aspect = float(w) / float(h)

    elev = np.clip((horizon_v - v) / max(horizon_v, 1e-5), 0.0, 1.0)

    # 1. Natural photographic dusk sky gradient (desaturated steel-blue -> dusty peach -> golden horizon)
    stops_t = np.array([0.00, 0.09, 0.22, 0.38, 0.58, 0.80, 1.00], dtype=np.float32)
    stops_rgb = np.array(
        [
            [1.18, 0.64, 0.32],  # Natural warm golden-apricot horizon
            [0.86, 0.46, 0.30],  # Dusty sunset peach-coral
            [0.44, 0.30, 0.34],  # Natural muted mauve-slate
            [0.20, 0.22, 0.32],  # Cool steel twilight blue-grey
            [0.10, 0.14, 0.26],  # Authentic twilight cerulean-slate
            [0.055, 0.088, 0.19],  # Deep twilight blue
            [0.035, 0.060, 0.14],  # Zenith twilight blue
        ],
        dtype=np.float32,
    )

    sky = np.empty((h, w, 3), dtype=np.float32)
    for c in range(3):
        sky[..., c] = np.interp(elev, stops_t, stops_rgb[:, c])

    # Subtle natural western Mie glow right behind the Twin Towers gap
    du = (u - sun_u) * aspect
    dv = v - (horizon_v - 0.025)
    sun_dist = np.sqrt(du * du + dv * dv)

    mie_wide = np.exp(-sun_dist * 2.2) * (1.0 - smoothstep(0.32, 0.86, elev))
    mie_core = np.exp(-(du * du * 6.5 + dv * dv * 18.0)) * (1.0 - smoothstep(0.06, 0.34, elev))
    sky += mie_wide[..., None] * np.array([0.34, 0.18, 0.08], dtype=np.float32)
    sky += mie_core[..., None] * np.array([0.52, 0.28, 0.11], dtype=np.float32)

    # 2. Multi-scale photographic clouds (crisp altocumulus cloudlets + sweeping stratocumulus)
    p_depth = np.power(np.maximum(horizon_v - v, 0.0), 0.80) + 0.18
    px = ((u - 0.50) * aspect) / p_depth
    py = 1.60 / p_depth

    horizon_fade = smoothstep(0.03, 0.20, elev)
    zenith_fade = 1.0 - smoothstep(0.86, 1.0, elev) * 0.28

    # Layer A: High crisp wispy cirrus & altocumulus ripples
    cu = px * 0.55 + py * 0.18
    cv = py * 0.72 - px * 0.08
    wx = fbm_2d(cu * 0.75, cv * 0.65, octaves=3, seed=seed + 11)
    wy = fbm_2d(cu * 0.75 + 5.1, cv * 0.65 + 2.9, octaves=3, seed=seed + 23)
    cirrus = ridged_fbm_2d(
        cu * 1.05 + (wx - 0.5) * 1.4,
        cv * 0.95 + (wy - 0.5) * 1.0,
        octaves=6,
        lacunarity=2.18,
        gain=0.52,
        seed=seed + 37,
    )
    cirrus_a = smoothstep(0.48, 0.84, cirrus) * horizon_fade * zenith_fade * 0.40
    sun_prox = np.exp(-sun_dist * 1.2)
    cirrus_col = (
        np.array([0.42, 0.30, 0.36], dtype=np.float32) * (1.0 - sun_prox[..., None])
        + np.array([1.45, 0.76, 0.36], dtype=np.float32) * sun_prox[..., None]
    )
    sky = sky * (1.0 - cirrus_a[..., None] * 0.36) + cirrus_col * cirrus_a[..., None]

    # Layer B: Textured stratocumulus cloud deck with crisp micro-cloudlet structure
    dw1 = fbm_2d(px * 0.55 + 2.4, py * 0.70 + 1.1, octaves=4, seed=seed + 53)
    dw2 = fbm_2d(px * 0.55 + 9.1, py * 0.70 + 4.6, octaves=4, seed=seed + 67)
    cx = px * 0.65 + py * 0.12 + (dw1 - 0.5) * 1.25
    cy = py * 1.05 - px * 0.06 + (dw2 - 0.5) * 0.88

    c_base = fbm_2d(cx, cy, octaves=7, lacunarity=2.18, gain=0.54, seed=seed + 79)
    c_cell = fbm_2d(cx * 3.4 + 4.2, cy * 3.4 + 1.9, octaves=4, lacunarity=2.2, gain=0.52, seed=seed + 109)
    macro = fbm_2d(px * 0.22 + 3.9, py * 0.32 + 1.5, octaves=3, seed=seed + 97)

    c_dens = c_base * 0.56 + c_cell * 0.26 + macro * 0.32 - 0.13
    c_alpha = smoothstep(0.46, 0.71, c_dens) * horizon_fade * zenith_fade

    # 2D directional light-marching toward sunset horizon
    sun_dx = (sun_u - u) * 0.30
    c_sun1 = fbm_2d(cx + sun_dx * 0.15, cy + 0.20, octaves=5, seed=seed + 79)
    c_sun2 = fbm_2d(cx + sun_dx * 0.30, cy + 0.42, octaves=4, seed=seed + 79)

    rim = np.clip((c_base - c_sun1) * 3.0 + (c_base - c_sun2) * 1.3 + 0.24, 0.0, 1.5)
    underlit = rim * (0.34 + 0.86 * np.exp(-sun_dist * 1.05)) * (1.0 - smoothstep(0.40, 0.94, elev) * 0.62)

    # Realistic slate blue-grey shadowed clouds + warm muted coral & golden undersides
    c_dark = (
        np.array([0.085, 0.098, 0.165], dtype=np.float32) * (0.55 + 0.45 * elev[..., None])
        + np.array([0.145, 0.115, 0.155], dtype=np.float32) * (1.0 - elev[..., None])
    )
    c_warm = np.array([0.92, 0.40, 0.28], dtype=np.float32)
    c_gold = np.array([1.88, 0.88, 0.34], dtype=np.float32)

    t1 = smoothstep(0.18, 0.62, underlit)[..., None]
    t2 = smoothstep(0.58, 1.15, underlit)[..., None]
    c_rgb = c_dark * (1.0 - t1) + c_warm * t1
    c_rgb = c_rgb * (1.0 - t2) + c_gold * t2

    haze_w = (1.0 - smoothstep(0.02, 0.20, elev)) * 0.42
    haze_c = np.array([0.88, 0.48, 0.28], dtype=np.float32)
    c_rgb = c_rgb * (1.0 - haze_w[..., None]) + haze_c * haze_w[..., None]

    a_mid = np.clip(c_alpha * 0.88, 0.0, 0.93)[..., None]
    sky = sky * (1.0 - a_mid) + c_rgb * a_mid

    # 3. Dark twilight urban ground plane below horizon
    ground_mask = smoothstep(horizon_v - 0.008, horizon_v + 0.004, v)
    g_noise = fbm_2d(u * 32.0, v * 48.0, octaves=4, seed=seed + 211)
    ground_col = (
        np.array([0.012, 0.016, 0.018], dtype=np.float32)
        + np.array([0.010, 0.014, 0.010], dtype=np.float32) * g_noise[..., None]
    )
    canvas.img[:] = sky * (1.0 - ground_mask[..., None]) + ground_col * ground_mask[..., None]
