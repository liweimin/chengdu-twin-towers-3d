"""
Photographic Linear-HDR Post-Processing & Atmospheric Pipeline for《成都金融城双塔黄昏》:
  1. Firefly outlier suppression + AOV-guided Edge-Preserving A-Trous Wavelet Denoiser
  2. Physical depth-based Chengdu basin twilight aerial perspective & evening mist
  3. Multi-scale optical lens bloom & atmospheric halation (4 octaves in linear HDR)
  4. f/8 8-blade aperture diffraction starbursts on pinpoint streetlamps/headlights
  5. AgX-inspired filmic tone mapping (creamy highlight roll-off, rich sunset saturation)
  6. Subtle optical lateral chromatic aberration, natural lens vignetting, ISO-200 grain
"""

import math
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter, median_filter
from PIL import Image


def suppress_fireflies(img, depth, thresh=2.6):
    """Two-pass firefly rejection: eliminates isolated 1-2px MC specular spikes cleanly."""
    out = img.copy()
    for ksize, thr in [(3, thresh), (5, thresh * 1.45)]:
        med = np.stack([median_filter(out[..., c], size=ksize) for c in range(3)], axis=-1)
        lum = 0.2126 * out[..., 0] + 0.7152 * out[..., 1] + 0.0722 * out[..., 2]
        med_lum = 0.2126 * med[..., 0] + 0.7152 * med[..., 1] + 0.0722 * med[..., 2]
        is_spike = (lum > (med_lum + 0.14) * thr) & (depth > 0.1) & (lum < 25.0)
        out = np.where(is_spike[..., None], med, out)
    return out


def atrous_aov_denoise(beauty, depth, normal, albedo, iterations=2, sigma_c=0.095, sigma_n=0.18, sigma_z=0.04, sigma_a=0.18):
    """
    Ultra-crisp edge-preserving A-Trous denoiser: tight perceptual luminance/color range (sigma_c=0.095)
    smooths low-frequency shadow noise while keeping every glass mullion, CBD windowpane,
    and Twin Tower ice-flower strut 100% razor-sharp!
    """
    H, W, _ = beauty.shape
    cur = np.log1p(np.maximum(beauty, 0.0)).astype(np.float32)

    z = np.where(depth > 0.01, depth, 1e5).astype(np.float32)
    z_log = np.log1p(z)
    n = normal.astype(np.float32)

    offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 0), (0, 1), (1, -1), (1, 0), (1, 1)]
    k_weights = [1/16, 2/16, 1/16, 2/16, 4/16, 2/16, 1/16, 2/16, 1/16]
    is_geo = (depth > 0.01).astype(np.float32)[..., None]

    for it in range(iterations):
        step = 1 << it
        c_sig = sigma_c * (0.72 ** it)
        acc = np.zeros_like(cur)
        w_sum = np.zeros((H, W, 1), dtype=np.float32)

        for (dy, dx), kw in zip(offsets, k_weights):
            sy = dy * step
            sx = dx * step
            y0_dst, y1_dst = max(0, -sy), min(H, H - sy)
            x0_dst, x1_dst = max(0, -sx), min(W, W - sx)
            y0_src, y1_src = max(0, sy), min(H, H + sy)
            x0_src, x1_src = max(0, sx), min(W, W + sx)

            c_nb = cur[y0_src:y1_src, x0_src:x1_src]
            z_nb = z_log[y0_src:y1_src, x0_src:x1_src]
            n_nb = n[y0_src:y1_src, x0_src:x1_src]

            c_me = cur[y0_dst:y1_dst, x0_dst:x1_dst]
            z_me = z_log[y0_dst:y1_dst, x0_dst:x1_dst]
            n_me = n[y0_dst:y1_dst, x0_dst:x1_dst]

            dc = np.sum((c_nb - c_me) ** 2, axis=-1)
            dz = (z_nb - z_me) ** 2
            dn = np.sum((n_nb - n_me) ** 2, axis=-1)

            w = kw * np.exp(
                -dc / (2.0 * c_sig * c_sig + 1e-6)
                - dz / (2.0 * sigma_z * sigma_z + 1e-6)
                - dn / (2.0 * sigma_n * sigma_n + 1e-6)
            )
            w = w[..., None]
            acc[y0_dst:y1_dst, x0_dst:x1_dst] += c_nb * w
            w_sum[y0_dst:y1_dst, x0_dst:x1_dst] += w

        denoised = acc / np.maximum(w_sum, 1e-6)
        cur = denoised * is_geo + cur * (1.0 - is_geo)

    return np.expm1(np.maximum(cur, 0.0)).astype(np.float32)


def apply_aerial_perspective(hdr, depth, mist_density=0.00042):
    """
    Physically-based Chengdu basin blue-hour aerial perspective & subtle evening mist.
    Preserves rich deep contrast on foreground/midground while softly veiling distant CBD towers.
    """
    H, W, _ = hdr.shape
    is_geo = depth > 0.01
    yy = np.linspace(0.0, 1.0, H, dtype=np.float32)[:, None]
    eff_dist = np.where(is_geo, np.maximum(depth - 70.0, 0.0), 0.0)
    trans = np.exp(-eff_dist * mist_density * (0.72 + 0.50 * yy))

    # Rich cool twilight sapphire-indigo aloft warming gently to dusky slate-amber near horizon
    mist_low = np.array([0.13, 0.095, 0.165], dtype=np.float32)
    mist_high = np.array([0.032, 0.062, 0.175], dtype=np.float32)
    t_h = np.clip((yy - 0.18) / 0.55, 0.0, 1.0)[..., None]
    mist_col = mist_high[None, None, :] * (1.0 - t_h) + mist_low[None, None, :] * t_h

    out = np.where(
        is_geo[..., None],
        hdr * trans[..., None] + mist_col * (1.0 - trans[..., None]),
        hdr,
    )
    return out.astype(np.float32)


def apply_optical_bloom_and_starburst(hdr, bloom_strength=0.18, starburst_strength=0.14):
    """
    Multi-scale physical lens bloom/halation + subtle f/8 8-blade diffraction starbursts
    on ultra-bright pinpoint light sources (streetlights, car headlights, tower beacons).
    """
    H, W, _ = hdr.shape
    scale = W / 1920.0

    # --- 1. Multi-scale optical bloom & atmospheric halation ---
    lum = 0.2126 * hdr[..., 0] + 0.7152 * hdr[..., 1] + 0.0722 * hdr[..., 2]
    # Soft knee threshold above 0.85 linear radiance
    knee = np.clip((lum - 0.85) / (lum + 0.55), 0.0, 1.0)
    bright = hdr * knee[..., None]
    # Soft cap extreme emitter spikes so bloom stays smooth and filmic
    bright = bright / (1.0 + 0.04 * bright)

    bloom = np.zeros_like(hdr)
    # 4 optical octaves: tight lens halo -> medium glow -> wide atmospheric mist scattering
    sigmas = [2.2 * scale, 7.5 * scale, 24.0 * scale, 72.0 * scale]
    weights = [0.42, 0.30, 0.18, 0.10]
    for s, wt in zip(sigmas, weights):
        s_eff = max(1.0, s)
        # Downsample for huge blurs (much faster & identical optically!)
        if s_eff > 12.0:
            ds = 4
            small = cv2.resize(bright, (W // ds, H // ds), interpolation=cv2.INTER_AREA)
            blur_s = np.stack([gaussian_filter(small[..., c], sigma=s_eff / ds) for c in range(3)], axis=-1)
            blur = cv2.resize(blur_s, (W, H), interpolation=cv2.INTER_LINEAR)
        else:
            blur = np.stack([gaussian_filter(bright[..., c], sigma=s_eff) for c in range(3)], axis=-1)
        bloom += blur * wt

    # --- 2. Subtle f/8 8-blade Aperture Diffraction Starbursts ---
    # Extract only ultra-bright small point lights (streetlights, headlights, beacons)
    pin_mask = np.clip((lum - 11.0) / 14.0, 0.0, 1.0)
    pin = hdr * (pin_mask ** 1.5)[..., None]
    pin = np.minimum(pin, 40.0)

    # Build lightweight separable 4-direction directional streak (8-point star rotated 15 deg!)
    star = np.zeros_like(hdr)
    if np.max(pin) > 0.05 and starburst_strength > 0.0:
        half_len = max(9, int(round(26 * scale)))
        ksize = 2 * half_len + 1
        angles_deg = [15.0, 60.0, 105.0, 150.0]
        yy, xx = np.mgrid[-half_len:half_len + 1, -half_len:half_len + 1].astype(np.float32)
        kernel = np.zeros((ksize, ksize), dtype=np.float32)
        for ang in angles_deg:
            rad = math.radians(ang)
            ca, sa = math.cos(rad), math.sin(rad)
            along = xx * ca + yy * sa
            perp = -xx * sa + yy * ca
            spike = np.exp(-(perp ** 2) / 0.85) * np.exp(-np.abs(along) / (half_len * 0.28))
            kernel += spike
        kernel[half_len, half_len] = 0.0
        kernel /= (np.sum(kernel) + 1e-6)
        # Downsample 2x for super fast FFT-like convolution via cv2.filter2D
        pin_s = cv2.resize(pin, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
        k_s = cv2.resize(kernel, (max(5, ksize // 2 | 1), max(5, ksize // 2 | 1)), interpolation=cv2.INTER_AREA)
        k_s /= (np.sum(k_s) + 1e-6)
        star_s = cv2.filter2D(pin_s, -1, k_s)
        star = cv2.resize(star_s, (W, H), interpolation=cv2.INTER_LINEAR)

    return hdr + bloom * bloom_strength + star * starburst_strength


def agx_tonemap(hdr, exposure=1.0):
    """
    AgX-inspired filmic tone mapping (Blender 4.x / Troy Sobotka philosophy):
    Applies subtle chromatic inset matrix before sigmoid shoulder roll-off so intense
    golden-orange LEDs & fiery sunset clouds roll off smoothly into creamy warm highlights
    without harsh hue-shifting or neon clipping!
    """
    x = np.maximum(hdr * exposure, 0.0)

    # AgX inset matrix (gently rotates primaries inward before compression)
    M_in = np.array([
        [0.84247906, 0.07843360, 0.07922375],
        [0.04232824, 0.87846864, 0.07916613],
        [0.04237565, 0.07843360, 0.87914297],
    ], dtype=np.float32)
    M_out = np.linalg.inv(M_in).astype(np.float32)

    xi = np.einsum("ij,hwj->hwi", M_in, x)

    # Smooth filmic curve in log-like domain (ACES-RRT inspired shoulder + rich shadow toe)
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    mapped = (xi * (a * xi + b)) / (xi * (c * xi + d) + e)
    mapped = np.clip(mapped, 0.0, 1.0)

    # Outset matrix restores natural color fidelity while preserving soft highlight desaturation
    xo = np.einsum("ij,hwj->hwi", M_out, mapped)
    xo = np.clip(xo, 0.0, 1.0)

    # Subtle photographic contrast S-curve + shadow richness
    xo = xo * xo * (3.0 - 2.0 * xo) * 0.18 + xo * 0.82
    return np.clip(xo, 0.0, 1.0)


def apply_photographic_finish(ldr_lin, vignette=0.14, ca_px=0.45, grain_sigma=0.0055):
    """Apply subtle full-frame camera optics: lateral CA, natural vignetting, sRGB OETF, ISO-200 grain."""
    H, W, _ = ldr_lin.shape
    # 1. Very subtle radial lateral chromatic aberration near frame corners
    if ca_px > 0.05:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        cx, cy = W * 0.5, H * 0.5
        dx = (xx - cx) / max(cx, 1.0)
        dy = (yy - cy) / max(cy, 1.0)
        r2 = dx * dx + dy * dy
        shift_r = (ca_px / W) * r2
        map_rx = (xx + (xx - cx) * shift_r).astype(np.float32)
        map_ry = (yy + (yy - cy) * shift_r).astype(np.float32)
        map_bx = (xx - (xx - cx) * shift_r).astype(np.float32)
        map_by = (yy - (yy - cy) * shift_r).astype(np.float32)
        r_ch = cv2.remap(ldr_lin[..., 0], map_rx, map_ry, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        b_ch = cv2.remap(ldr_lin[..., 2], map_bx, map_by, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        ldr_lin = np.stack([r_ch, ldr_lin[..., 1], b_ch], axis=-1)

    # 2. Natural full-frame optical vignetting (cos^4 lens falloff, gentle)
    if vignette > 0.0:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        nx = (xx - W * 0.5) / (W * 0.5)
        ny = (yy - H * 0.5) / (H * 0.5)
        r2 = nx * nx + ny * ny
        vig = np.clip(1.0 - vignette * (r2 ** 1.25), 0.72, 1.0)[..., None]
        ldr_lin = ldr_lin * vig

    # 3. Exact sRGB transfer function
    srgb = np.where(
        ldr_lin <= 0.0031308,
        12.92 * ldr_lin,
        1.055 * np.power(np.maximum(ldr_lin, 0.0031308), 1.0 / 2.4) - 0.055,
    )

    # 3.5 Subtle prime-lens micro-clarity unsharp mask on architectural edges
    blur_s = np.stack([gaussian_filter(srgb[..., c], sigma=0.85) for c in range(3)], axis=-1)
    srgb = np.clip(srgb + (srgb - blur_s) * 0.22, 0.0, 1.0)

    # 4. Subtle ISO-200 photographic luminance sensor grain (stronger slightly in shadows/midtones)
    if grain_sigma > 0.0:
        rng = np.random.default_rng(20261124)
        noise = rng.normal(0.0, grain_sigma, size=(H, W, 1)).astype(np.float32)
        # Slightly less grain in clipped pure highlights, natural filmic response
        weight = np.clip(1.0 - srgb * 0.55, 0.25, 1.0)
        srgb = srgb + noise * weight

    return np.clip(srgb, 0.0, 1.0)


def postprocess_render(
    aovs,
    out_png,
    exposure=0.95,
    denoise_iters=3,
    mist_density=0.00105,
    bloom_strength=0.18,
    starburst_strength=0.14,
):
    beauty = aovs["beauty"]
    depth = aovs["depth"]
    albedo = aovs["albedo"]
    normal = aovs["normal"]

    clean = suppress_fireflies(beauty, depth, thresh=2.5)
    if denoise_iters > 0:
        clean = atrous_aov_denoise(clean, depth, normal, albedo, iterations=denoise_iters)

    hazy = apply_aerial_perspective(clean, depth, mist_density=mist_density)
    optical = apply_optical_bloom_and_starburst(hazy, bloom_strength=bloom_strength, starburst_strength=starburst_strength)
    mapped = agx_tonemap(optical, exposure=exposure)
    final_srgb = apply_photographic_finish(mapped, vignette=0.13, ca_px=0.40, grain_sigma=0.0052)

    img_u8 = (final_srgb * 255.0 + 0.5).astype(np.uint8)
    Image.fromarray(img_u8, mode="RGB").save(out_png)
    print(f"Saved photographic render -> {out_png} ({img_u8.shape[1]}x{img_u8.shape[0]})")
    return out_png
