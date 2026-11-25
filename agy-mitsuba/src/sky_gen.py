"""
Physically-based 32-bit HDR twilight sky & high-detail backlit Sichuan basin sunset clouds (火烧云)
v3: Multi-octave billowy + mackerel-ripple altocumulus clouds with crisp backlit golden-coral rims,
deep indigo-plum cloud shadows, and velvety cobalt blue-hour zenith.
"""

import os
import math
import numpy as np
from PIL import Image


def _hash2(ix, iy):
    n = ix * 374761393 + iy * 668265263
    n = (n ^ (n >> 13)) * 1274126177
    return ((n ^ (n >> 16)) & 0x7FFFFFFF) / 2147483647.0


def value_noise_2d(x, y):
    ix = np.floor(x).astype(np.int64)
    iy = np.floor(y).astype(np.int64)
    fx = x - ix
    fy = y - iy
    ux = fx * fx * (3.0 - 2.0 * fx)
    uy = fy * fy * (3.0 - 2.0 * fy)

    a = _hash2(ix, iy)
    b = _hash2(ix + 1, iy)
    c = _hash2(ix, iy + 1)
    d = _hash2(ix + 1, iy + 1)

    return a + (b - a) * ux + (c - a) * uy + (a - b - c + d) * ux * uy


def fbm_2d(x, y, octaves=7, lacunarity=2.12, gain=0.53, rot_angle=0.61):
    val = np.zeros_like(x, dtype=np.float32)
    amp = 0.5
    freq = 1.0
    ca, sa = math.cos(rot_angle), math.sin(rot_angle)
    px, py = x.astype(np.float32), y.astype(np.float32)
    for _ in range(octaves):
        val += amp * value_noise_2d(px * freq, py * freq)
        nx = px * ca - py * sa + 19.1
        ny = px * sa + py * ca + 37.3
        px, py = nx, ny
        freq *= lacunarity
        amp *= gain
    return val


def generate_dusk_sky(out_dir="assets", width=3072, height=1536):
    os.makedirs(out_dir, exist_ok=True)
    npy_path = os.path.join(out_dir, "dusk_sky.npy")
    preview_path = os.path.join(out_dir, "dusk_sky_preview.png")

    u = (np.arange(width, dtype=np.float32) + 0.5) / width
    v = (np.arange(height, dtype=np.float32) + 0.5) / height
    uu, vv = np.meshgrid(u, v)

    phi = (uu - 0.5) * 2.0 * np.pi
    theta = vv * np.pi

    sin_t = np.sin(theta)
    dx = sin_t * np.sin(phi)
    dy = np.cos(theta)
    dz = sin_t * np.cos(phi)  # +1 at u=0.5 -> East, directly behind Twin Towers!

    # Low western-southwest setting sun (-Z, +X) creating rich warm raking skylight & glossy reflection
    sun_elev = math.radians(5.5)
    sun_azim = math.radians(144.0)
    sun_dir = np.array([
        math.cos(sun_elev) * math.sin(sun_azim),
        math.sin(sun_elev),
        math.cos(sun_elev) * math.cos(sun_azim),
    ], dtype=np.float32)
    sun_dir /= np.linalg.norm(sun_dir)

    cos_sun = np.clip(dx * sun_dir[0] + dy * sun_dir[1] + dz * sun_dir[2], -1.0, 1.0)
    elev = np.maximum(dy, 0.0)

    # --- 1. Photographic Blue-Hour-to-Sunset Atmospheric Gradient ---
    t_zen = np.power(np.clip(elev, 0.0, 1.0), 0.48)

    col_zenith = np.array([0.012, 0.044, 0.195], dtype=np.float32)      # Deep sapphire-indigo zenith
    col_mid_blue = np.array([0.042, 0.098, 0.295], dtype=np.float32)    # Rich twilight cobalt
    col_violet = np.array([0.24, 0.145, 0.275], dtype=np.float32)       # Refined subtle Belt of Venus
    col_hor_east = np.array([1.32, 0.48, 0.20], dtype=np.float32)       # Natural warm apricot-tangerine horizon
    col_hor_west = np.array([2.50, 0.94, 0.26], dtype=np.float32)       # Golden western twilight glow

    west_w = np.clip(0.5 * (cos_sun + 1.0), 0.0, 1.0) ** 1.65
    col_hor = col_hor_east * (1.0 - west_w[..., None]) + col_hor_west * west_w[..., None]

    h_band = np.exp(-elev * 9.8)[..., None]
    vio_band = np.exp(-((elev - 0.13) / 0.10) ** 2)[..., None]
    mid_band = np.exp(-((elev - 0.34) / 0.24) ** 2)[..., None]

    sky = col_zenith[None, None, :] * (0.38 + 0.62 * t_zen[..., None])
    sky += col_mid_blue[None, None, :] * mid_band * 0.44
    sky += col_violet[None, None, :] * vio_band * 0.45
    sky = sky * (1.0 - h_band) + col_hor * h_band

    east_glow = np.exp(-elev * 13.0) * np.clip(0.45 + 0.55 * dz, 0.0, 1.0)
    sky += east_glow[..., None] * np.array([0.78, 0.28, 0.13], dtype=np.float32)

    # Broad, silky western sunset glow (replaces harsh delta-sun specular needles with broad warm sunset reflection!)
    mie_broad = np.power(np.clip(cos_sun, 0.0, 1.0), 3.5) * np.exp(-elev * 2.8)
    mie_core = np.power(np.clip(cos_sun, 0.0, 1.0), 18.0) * np.exp(-elev * 2.0)
    sky += mie_broad[..., None] * np.array([2.4, 0.98, 0.36], dtype=np.float32)
    sky += mie_core[..., None] * np.array([7.5, 3.1, 1.05], dtype=np.float32)

    # --- 2. High-Detail Backlit Chengdu Altocumulus + Mackerel Dusk Clouds ---
    R_earth = 6371.0
    above = dy > 0.004

    # Layer A: Delicate high-altitude wind-streaked cirrus (altitude 10 km)
    h_cir = 10.0
    t_c = np.where(above, np.sqrt((R_earth * dy) ** 2 + 2.0 * R_earth * h_cir + h_cir ** 2) - R_earth * dy, 1e5)
    cx = dx * t_c * 0.055
    cz = dz * t_c * 0.055
    cu = cx * 0.85 + cz * 0.52
    cv = -cx * 0.52 + cz * 0.85
    wc1 = fbm_2d(cu * 0.85 + 1.7, cv * 0.85 - 2.1, octaves=4)
    wc2 = fbm_2d(cu * 0.85 - 3.9, cv * 0.85 + 3.4, octaves=4)
    cir_n = fbm_2d(cu * 2.2 + wc1 * 1.15, cv * 0.55 + wc2 * 0.85, octaves=6)
    cirrus = np.clip((cir_n - 0.45) / 0.28, 0.0, 1.0) ** 1.35
    cirrus *= np.clip((dy - 0.03) / 0.14, 0.0, 1.0) * np.exp(-t_c * 0.0018)

    # Layer B: Crisp multi-scale altocumulus + rippled mackerel fire-clouds (altitude 3.3 km)
    h_m = 3.3
    t_m = np.where(above, np.sqrt((R_earth * dy) ** 2 + 2.0 * R_earth * h_m + h_m ** 2) - R_earth * dy, 1e5)
    mx = dx * t_m * 0.155
    mz = dz * t_m * 0.155

    bu = mx * 0.66 + mz * 0.75 + 1.8
    bv = -mx * 0.75 + mz * 0.66 - 0.9

    wm1 = fbm_2d(bu * 0.55 + 3.7, bv * 0.55 + 1.9, octaves=4)
    wm2 = fbm_2d(bu * 0.55 - 2.4, bv * 0.55 - 4.8, octaves=4)

    c_macro = fbm_2d(bu * 0.95 + wm1 * 1.05, bv * 0.52 + wm2 * 0.85, octaves=6)
    c_med = fbm_2d(bu * 2.8 - wm2 * 0.70, bv * 2.2 + wm1 * 0.60, octaves=5)
    # Fine mackerel-sky altocumulus ripples (gives unmistakable photographic cloud texture!)
    c_mackerel = fbm_2d(bu * 7.5 + wm1 * 0.55, bv * 4.8 - wm2 * 0.45, octaves=5)
    # Ridged puffiness for crisp cumulus edges
    c_puffs = 1.0 - np.abs(c_mackerel * 2.0 - 1.0)

    ribbon_mod = 0.075 * np.sin(bv * 1.25 + wm1 * 2.1) + 0.035 * np.exp(-((elev - 0.22) / 0.16) ** 2) - 0.045 * np.clip((elev - 0.32) / 0.22, 0.0, 1.0)
    raw_d = c_macro * 0.54 + c_med * 0.24 + c_mackerel * 0.13 + c_puffs * 0.09 + ribbon_mod
    density = np.clip((raw_d - 0.525) / 0.28, 0.0, 1.0) ** 1.24

    # Two-step Beer-Lambert directional self-shadowing toward western sun
    def sample_d(dx_s, dz_s):
        sx = mx + dx_s
        sz = mz + dz_s
        su = sx * 0.66 + sz * 0.75 + 1.8
        sv = -sx * 0.75 + sz * 0.66 - 0.9
        cm = fbm_2d(su * 0.95 + wm1 * 1.05, sv * 0.52 + wm2 * 0.85, octaves=5)
        cf = fbm_2d(su * 2.8 - wm2 * 0.70, sv * 2.2 + wm1 * 0.60, octaves=4)
        return np.clip((cm * 0.68 + cf * 0.32 + ribbon_mod - 0.525) / 0.28, 0.0, 1.0)

    d_s1 = sample_d(sun_dir[0] * 0.22, sun_dir[2] * 0.22)
    d_s2 = sample_d(sun_dir[0] * 0.58, sun_dir[2] * 0.58)

    opt_d = np.maximum(d_s1 - density * 0.18, 0.0) * 2.6 + np.maximum(d_s2 - density * 0.18, 0.0) * 1.9 + density * 1.45
    sun_trans = np.exp(-opt_d * 1.08)

    # Authentic fiery golden-apricot & warm coral edges + deep cool slate-indigo cloud shadows (less magenta cast!)
    rim_fire = np.exp(-((density - 0.24) / 0.20) ** 2) * (0.65 + 0.60 * sun_trans)
    low_fire = np.exp(-elev * 3.8) * (0.38 + 0.62 * (1.0 - density * 0.65))

    col_gold = np.array([4.80, 1.68, 0.44], dtype=np.float32)       # Authentic molten sunset apricot-gold
    col_crimson = np.array([2.20, 0.62, 0.38], dtype=np.float32)    # Warm sunset coral-tangerine underside
    col_shadow = np.array([0.062, 0.082, 0.205], dtype=np.float32)  # Deep cool twilight slate-indigo bulk

    gold_mix = np.clip(low_fire * 0.85 + rim_fire * 0.72 + west_w * 0.22, 0.0, 1.0)[..., None]
    lit_rgb = col_crimson * (1.0 - gold_mix) + col_gold * gold_mix

    lit_amt = np.clip(sun_trans * 1.38 + rim_fire * 0.58 + low_fire * 0.34, 0.0, 1.0)[..., None]
    cloud_rgb = col_shadow * (1.0 - lit_amt) + lit_rgb * lit_amt

    fade_m = np.clip((dy - 0.015) / 0.085, 0.0, 1.0) * np.exp(-t_m * 0.0052)
    alpha_m = np.clip(density * 0.94 * fade_m, 0.0, 0.96)[..., None]

    cir_col = np.array([2.05, 0.76, 0.42], dtype=np.float32) * (0.72 + 0.45 * west_w[..., None])
    sky = sky * (1.0 - cirrus[..., None] * 0.46) + cir_col * (cirrus[..., None] * 0.46)
    sky = sky * (1.0 - alpha_m) + cloud_rgb * alpha_m

    below = dy <= 0.0
    ground_col = (
        np.array([0.028, 0.032, 0.052], dtype=np.float32)
        + np.exp(dy * 11.0)[..., None] * np.array([0.20, 0.09, 0.06], dtype=np.float32)
    )
    sky = np.where(below[..., None], ground_col, sky)

    sky = np.nan_to_num(sky, nan=0.0, posinf=80.0, neginf=0.0).astype(np.float32)
    sky = np.maximum(sky, 0.0)

    np.save(npy_path, sky)

    x = sky * 0.85
    mapped = (x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14)
    mapped = np.clip(mapped, 0.0, 1.0) ** (1.0 / 2.2)
    Image.fromarray((mapped * 255).astype(np.uint8)).save(preview_path)
    print(f"Generated volumetric HDR dusk sky v3: {npy_path} ({width}x{height})")
    return npy_path, preview_path


if __name__ == "__main__":
    generate_dusk_sky()
