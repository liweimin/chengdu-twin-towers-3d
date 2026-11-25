"""Pure 2D procedural twilight sky and volumetric-looking dusk clouds (v3).

Fixes vertical perspective-center streaking by decoupling the cloud wind-shear
plane from the Twin Towers axis and layering rich horizontal-diagonal
Chengdu basin "火烧云" stratocumulus cloud banks across the entire frame.
"""

from __future__ import annotations

import numpy as np

from canvas2d import Canvas2D
from noise2d import fbm_2d, ridged_fbm_2d, smoothstep


def paint_dusk_sky(
    canvas: Canvas2D,
    horizon_v: float = 0.625,
    sun_u: float = 0.48,
    sun_v: float = 0.625,
    seed: int = 101,
) -> None:
    """Paint a dramatic, high-dynamic-range Chengdu twilight sky."""
    u, v = canvas.u_grid()
    h, w = canvas.height, canvas.width
    aspect = float(w) / float(h)

    elev = np.clip((horizon_v - v) / max(horizon_v, 1e-5), 0.0, 1.0)

    # 1. Deep, rich blue-hour-to-sunset Rayleigh sky gradient (linear HDR)
    stops_t = np.array([0.00, 0.08, 0.19, 0.34, 0.54, 0.76, 1.00], dtype=np.float32)
    stops_rgb = np.array(
        [
            [1.10, 0.40, 0.13],  # Warm sunset amber at horizon
            [0.84, 0.27, 0.15],  # Rich sunset coral-orange
            [0.40, 0.15, 0.22],  # Dusk crimson-plum
            [0.14, 0.10, 0.23],  # Deep twilight violet-blue
            [0.048, 0.068, 0.18],  # Rich blue-hour cobalt
            [0.022, 0.040, 0.12],  # Deep indigo
            [0.012, 0.024, 0.078],  # Near-night zenith
        ],
        dtype=np.float32,
    )

    sky = np.empty((h, w, 3), dtype=np.float32)
    for c in range(3):
        sky[..., c] = np.interp(elev, stops_t, stops_rgb[:, c])

    # Restrained Mie forward-scattering glow where the sun just dipped below the western horizon
    du = (u - sun_u) * aspect
    dv = v - sun_v
    sun_dist = np.sqrt(du * du + dv * dv)

    mie_wide = np.exp(-sun_dist * 2.5) * (1.0 - smoothstep(0.28, 0.85, elev))
    mie_core = np.exp(-(du * du * 7.0 + dv * dv * 24.0)) * (1.0 - smoothstep(0.05, 0.34, elev))
    sky += mie_wide[..., None] * np.array([0.48, 0.17, 0.05], dtype=np.float32)
    sky += mie_core[..., None] * np.array([0.88, 0.40, 0.11], dtype=np.float32)

    # Cooler sky deepening toward upper-left & upper-right corners
    edge_cool = smoothstep(0.32, 0.95, np.abs(u - sun_u)) * smoothstep(0.08, 0.72, elev)
    sky *= 1.0 - edge_cool[..., None] * np.array([0.26, 0.12, -0.05], dtype=np.float32)

    # 2. 2D Perspective-foreshortened sky plane (gentle horizontal strata, no vertical funnel!)
    sky_mask = (v <= horizon_v + 0.03).astype(np.float32)
    # Use a softer perspective depth floor (0.14) + non-linear compression so overhead clouds
    # stay natural horizontal-diagonal bands instead of pinching into a vertical plume at center.
    p_depth = np.power(np.maximum(horizon_v - v, 0.0), 0.85) + 0.14
    px = ((u - 0.50) * aspect) / p_depth
    py = 1.65 / p_depth

    horizon_fade = smoothstep(0.015, 0.15, elev)
    zenith_fade = 1.0 - smoothstep(0.84, 1.0, elev) * 0.45

    # --- Layer A: High-altitude sweeping cirrus wisps across the twilight sky ---
    # Slightly tilted diagonal flow (from mid-left up toward upper-right)
    c_u = px * 0.42 + py * 0.18
    c_v = py * 0.55 - px * 0.08
    wx = fbm_2d(c_u * 0.65, c_v * 0.55, octaves=3, seed=seed + 11)
    wy = fbm_2d(c_u * 0.65 + 6.1, c_v * 0.55 + 2.9, octaves=3, seed=seed + 23)
    cirrus = ridged_fbm_2d(
        c_u * 0.85 + (wx - 0.5) * 1.4,
        c_v * 0.72 + (wy - 0.5) * 0.9,
        octaves=5,
        lacunarity=2.15,
        gain=0.52,
        seed=seed + 37,
    )
    cirrus_alpha = smoothstep(0.48, 0.85, cirrus) * horizon_fade * zenith_fade * 0.48
    sun_prox = np.exp(-sun_dist * 1.35)
    cirrus_col = (
        np.array([0.52, 0.21, 0.30], dtype=np.float32) * (1.0 - sun_prox[..., None])
        + np.array([1.65, 0.64, 0.24], dtype=np.float32) * sun_prox[..., None]
    )
    sky = sky * (1.0 - cirrus_alpha[..., None] * 0.42) + cirrus_col * cirrus_alpha[..., None]

    # --- Layer B: Dramatic sweeping Chengdu "火烧云" stratocumulus cloud deck ---
    # Horizontal-diagonal cloud bands with organic billowing domain warp
    dw1 = fbm_2d(px * 0.45 + 3.2, py * 0.65 + 1.4, octaves=4, seed=seed + 53)
    dw2 = fbm_2d(px * 0.45 + 10.7, py * 0.65 + 5.8, octaves=4, seed=seed + 67)
    cx = px * 0.55 + py * 0.12 + (dw1 - 0.5) * 1.35
    cy = py * 0.92 - px * 0.07 + (dw2 - 0.5) * 0.95

    cloud_base = fbm_2d(cx, cy, octaves=6, lacunarity=2.15, gain=0.54, seed=seed + 79)
    cloud_detail = fbm_2d(cx * 2.8 + 4.5, cy * 2.8 + 2.1, octaves=4, lacunarity=2.2, gain=0.5, seed=seed + 109)
    macro_banks = fbm_2d(px * 0.20 + 4.8, py * 0.32 + 1.9, octaves=3, seed=seed + 97)

    # Rich mid-sky cloud coverage with natural openings showing deep twilight indigo
    cloud_density = cloud_base * 0.62 + cloud_detail * 0.20 + macro_banks * 0.34 - 0.11
    cloud_alpha = smoothstep(0.45, 0.72, cloud_density) * horizon_fade * zenith_fade

    # 2D directional light-marching toward the western horizon sun
    sun_dx = (sun_u - u) * 0.35
    c_step1 = fbm_2d(cx + sun_dx * 0.18, cy + 0.24, octaves=5, lacunarity=2.15, gain=0.54, seed=seed + 79)
    c_step2 = fbm_2d(cx + sun_dx * 0.36, cy + 0.48, octaves=4, lacunarity=2.15, gain=0.54, seed=seed + 79)

    # Illuminated cloud undersides & glowing rims vs dark indigo-violet cloud bellies
    rim = np.clip((cloud_base - c_step1) * 3.1 + (cloud_base - c_step2) * 1.3 + 0.26, 0.0, 1.55)
    elev_atten = 1.0 - smoothstep(0.36, 0.94, elev) * 0.68
    underlit = rim * (0.34 + 0.88 * np.exp(-sun_dist * 1.05)) * elev_atten

    cloud_shadow = (
        np.array([0.045, 0.050, 0.120], dtype=np.float32) * (0.55 + 0.45 * elev[..., None])
        + np.array([0.105, 0.058, 0.115], dtype=np.float32) * (1.0 - elev[..., None])
    )
    cloud_crimson = np.array([1.22, 0.28, 0.19], dtype=np.float32)
    cloud_molten = np.array([2.30, 0.84, 0.22], dtype=np.float32)

    t1 = smoothstep(0.15, 0.60, underlit)[..., None]
    t2 = smoothstep(0.54, 1.12, underlit)[..., None]
    cloud_rgb = cloud_shadow * (1.0 - t1) + cloud_crimson * t1
    cloud_rgb = cloud_rgb * (1.0 - t2) + cloud_molten * t2

    # Warm atmospheric perspective blend very close to horizon
    haze_w = (1.0 - smoothstep(0.01, 0.18, elev)) * 0.40
    haze_col = np.array([0.82, 0.35, 0.18], dtype=np.float32)
    cloud_rgb = cloud_rgb * (1.0 - haze_w[..., None]) + haze_col * haze_w[..., None]

    a_mid = np.clip(cloud_alpha * 0.92, 0.0, 0.95)[..., None]
    sky = sky * (1.0 - a_mid) + cloud_rgb * a_mid

    # --- Layer C: Lower crisp dark-violet dusk cloud wisps catching fiery gold rims ---
    cx2 = px * 0.78 + 16.4 + (dw2 - 0.5) * 0.85
    cy2 = py * 1.25 + 8.3
    low_n = fbm_2d(cx2, cy2, octaves=5, lacunarity=2.15, gain=0.52, seed=seed + 131)
    low_sun = fbm_2d(cx2 + sun_dx * 0.16, cy2 + 0.22, octaves=4, seed=seed + 131)
    low_mask = (
        smoothstep(0.54, 0.76, low_n)
        * smoothstep(0.04, 0.20, elev)
        * (1.0 - smoothstep(0.45, 0.78, elev))
    )
    low_rim = np.clip((low_n - low_sun) * 3.8 + 0.14, 0.0, 1.35) * np.exp(-sun_dist * 1.0)

    low_dark = np.array([0.038, 0.040, 0.095], dtype=np.float32)
    low_fire = np.array([2.15, 0.72, 0.19], dtype=np.float32)
    low_col = low_dark + low_fire * smoothstep(0.24, 0.90, low_rim)[..., None]

    a_low = np.clip(low_mask * 0.82, 0.0, 0.88)[..., None]
    sky = sky * (1.0 - a_low) + low_col * a_low

    # 3. Delicate warm horizon mist band
    mist_band = np.exp(-((v - horizon_v) / 0.050) ** 2)
    mist_col = (
        np.array([0.46, 0.21, 0.13], dtype=np.float32)
        + np.array([0.46, 0.23, 0.09], dtype=np.float32) * np.exp(-du * du * 2.8)[..., None]
    )
    sky += mist_col * (mist_band * 0.24)[..., None]

    canvas.img = np.where(sky_mask[..., None] > 0.5, sky, canvas.img)
