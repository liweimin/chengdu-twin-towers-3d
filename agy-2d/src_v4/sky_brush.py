"""Pure Brushstroke Dusk Sky & Impasto Sunset Clouds (v4).

Zero raw noise fills — the entire twilight sky and Chengdu sunset cloud deck
are built from ~12,000 layered wet-on-wet atmospheric brushstrokes, sweeping
billowy cloud-body dabs, and sunlit golden-coral impasto rim strokes!
"""

from __future__ import annotations

import math
import numpy as np

from brush_engine import BrushCanvas


def _sky_palette_srgb(elev: float, u: float) -> tuple[float, float, float]:
    """Natural DSLR twilight sky color in sRGB [0..1] for brushstroke sampling."""
    stops_t = [0.00, 0.10, 0.24, 0.42, 0.64, 0.84, 1.00]
    stops_c = [
        (0.95, 0.72, 0.50),  # Warm golden-apricot horizon
        (0.84, 0.56, 0.44),  # Soft coral-peach
        (0.58, 0.45, 0.52),  # Dusty mauve-slate
        (0.36, 0.37, 0.50),  # Cool twilight steel-blue
        (0.24, 0.29, 0.44),  # Cerulean twilight
        (0.16, 0.22, 0.37),  # Deep blue-hour indigo
        (0.11, 0.16, 0.30),  # Zenith night-blue
    ]
    t = max(0.0, min(1.0, elev))
    r = float(np.interp(t, stops_t, [c[0] for c in stops_c]))
    g = float(np.interp(t, stops_t, [c[1] for c in stops_c]))
    b = float(np.interp(t, stops_t, [c[2] for c in stops_c]))

    # Warm western sunset glow centered behind the Twin Towers gap (u ≈ 0.48)
    sun_w = math.exp(-((u - 0.48) / 0.26) ** 2) * (1.0 - min(1.0, t * 2.2))
    r = min(1.0, r + 0.14 * sun_w)
    g = min(1.0, g + 0.09 * sun_w)
    b = min(1.0, b + 0.03 * sun_w)
    return (r, g, b)


def paint_sky_by_brushstrokes(
    bc: BrushCanvas,
    horizon_v: float = 0.825,
) -> None:
    """Paint the entire Chengdu twilight sky and sunset clouds exclusively with brushstrokes."""
    w, h = bc.width, bc.height
    sc = bc.scale
    rng = bc.rng

    # --- Pass 1: Broad wet-on-wet atmospheric underpainting strokes across the sky ---
    bc.begin_layer()
    # Lay down ~1,800 broad overlapping horizontal-diagonal wash strokes from zenith to horizon
    n_rows = 58
    for row in range(n_rows):
        vf = (row + 0.5) / n_rows * (horizon_v + 0.04)
        elev = max(0.0, (horizon_v - vf) / horizon_v)
        n_cols = 28
        for col in range(n_cols):
            uf = (col + float(rng.uniform(-0.35, 0.85))) / n_cols
            cx = uf * w
            cy = vf * h + float(rng.uniform(-8, 8)) * sc
            slen = float(rng.uniform(75, 165)) * sc
            ang = float(rng.uniform(-0.10, 0.10))
            dx = math.cos(ang) * slen * 0.5
            dy = math.sin(ang) * slen * 0.5
            rgb = _sky_palette_srgb(elev, uf)
            bc.bristle_stroke(
                cx - dx, cy - dy, cx + dx, cy + dy,
                width_px=float(rng.uniform(22, 38)) * sc,
                color=rgb,
                alpha=0.82,
                bristles=3,
                jitter_col=0.018,
            )

    # Dark twilight ground wash below horizon (so no sky leaks under trees!)
    for row in range(16):
        vf = horizon_v + (row / 15.0) * (1.0 - horizon_v)
        for col in range(18):
            uf = (col + 0.5) / 18.0
            cx, cy = uf * w, vf * h
            bc.bristle_stroke(
                cx - 65 * sc, cy, cx + 65 * sc, cy,
                width_px=26 * sc,
                color=(0.06, 0.08, 0.09),
                alpha=0.95,
                bristles=2,
                jitter_col=0.012,
            )
    bc.commit_layer(blur_px=7.0, hdr_gain=1.08)

    # --- Pass 2: High wispy cirrus cloud strokes sweeping diagonally across twilight sky ---
    bc.begin_layer()
    cirrus_ribbons = [
        (0.00, 0.44, 0.44, 0.22, 1.0, 0.72),
        (0.06, 0.56, 0.46, 0.36, 0.85, 0.85),
        (0.36, 0.32, 0.80, 0.12, 1.05, 0.58),
        (0.45, 0.42, 0.88, 0.24, 0.90, 0.75),
        (0.54, 0.50, 0.98, 0.34, 0.75, 0.82),
        (0.16, 0.28, 0.58, 0.14, 0.80, 0.45),
    ]
    for u0, v0, u1, v1, th, warm in cirrus_ribbons:
        n_segs = 95
        for i in range(n_segs):
            t = i / max(1, n_segs - 1)
            uu = u0 + (u1 - u0) * t + float(rng.uniform(-0.032, 0.032))
            vv = v0 + (v1 - v0) * t + 0.018 * math.sin(t * 6.0) + float(rng.uniform(-0.018, 0.018))
            cx, cy = uu * w, vv * h
            ang = math.atan2((v1 - v0) * h, (u1 - u0) * w) + float(rng.uniform(-0.14, 0.14))
            slen = float(rng.uniform(45, 125)) * sc * th
            dx, dy = math.cos(ang) * slen * 0.5, math.sin(ang) * slen * 0.5
            c_r = 0.62 + 0.32 * warm
            c_g = 0.44 + 0.25 * warm
            c_b = 0.46 + 0.08 * (1.0 - warm)
            bc.bristle_stroke(
                cx - dx, cy - dy, cx + dx, cy + dy,
                width_px=float(rng.uniform(4.0, 12.0)) * sc * th,
                color=(c_r, c_g, c_b),
                alpha=float(rng.uniform(0.08, 0.22)),
                bristles=4,
                jitter_col=0.025,
                overshoot=0.08,
            )
    bc.commit_layer(blur_px=4.8, hdr_gain=1.10)

    # --- Pass 3: Silky wet-on-wet stratocumulus sunset cloud banks ("火烧云") ---
    # Split into soft shadow body pass (blur 6.5) + sunlit coral/gold rim pass (blur 3.8)
    cloud_banks = [
        (0.18, 0.32, 0.28, 0.085, 0.55),
        (0.12, 0.46, 0.28, 0.070, 0.76),
        (0.28, 0.52, 0.24, 0.060, 0.86),
        (0.50, 0.22, 0.26, 0.065, 0.40),
        (0.68, 0.28, 0.28, 0.080, 0.50),
        (0.66, 0.44, 0.26, 0.068, 0.80),
        (0.84, 0.38, 0.22, 0.060, 0.66),
        (0.36, 0.62, 0.20, 0.042, 0.92),
        (0.62, 0.60, 0.20, 0.042, 0.90),
    ]

    # 3A: Soft cool twilight cloud bellies
    bc.begin_layer()
    for cu, cv, wu, hv, fire in cloud_banks:
        for _ in range(130):
            rx = float(rng.normal(0.0, 0.40))
            ry = float(rng.normal(-0.14, 0.34))
            px = (cu + rx * wu) * w
            py = (cv + ry * hv) * h
            r_x = float(rng.uniform(18, 52)) * sc * (wu / 0.24)
            r_y = float(rng.uniform(6, 18)) * sc * (hv / 0.07)
            bc.dab(
                px, py, r_x, r_y,
                color=(0.24 + 0.06 * fire, 0.25 + 0.04 * fire, 0.37),
                alpha=float(rng.uniform(0.08, 0.20)),
                angle_rad=float(rng.uniform(-0.16, 0.16)),
            )
    bc.commit_layer(blur_px=7.5, hdr_gain=1.05)

    # 3B: Sunlit warm coral & golden-amber cloud undersides
    bc.begin_layer()
    for cu, cv, wu, hv, fire in cloud_banks:
        for _ in range(120):
            rx = float(rng.normal(0.0, 0.38))
            ry = float(rng.normal(0.20, 0.22))
            px = (cu + rx * wu) * w
            py = (cv + ry * hv) * h
            slen = float(rng.uniform(32, 85)) * sc
            ang = float(rng.uniform(-0.12, 0.12))
            dx, dy = math.cos(ang) * slen * 0.5, math.sin(ang) * slen * 0.5
            bc.bristle_stroke(
                px - dx, py - dy, px + dx, py + dy,
                width_px=float(rng.uniform(6, 15)) * sc,
                color=(0.78 + 0.18 * fire, 0.46 + 0.16 * fire, 0.36 + 0.06 * (1.0 - fire)),
                alpha=float(rng.uniform(0.09, 0.22)),
                bristles=3,
                jitter_col=0.025,
                overshoot=0.06,
            )
        for _ in range(75):
            rx = float(rng.normal(0.0, 0.34))
            ry = float(rng.normal(0.40, 0.13))
            px = (cu + rx * wu) * w
            py = (cv + ry * hv) * h
            slen = float(rng.uniform(22, 62)) * sc
            ang = float(rng.uniform(-0.10, 0.10))
            dx, dy = math.cos(ang) * slen * 0.5, math.sin(ang) * slen * 0.5
            bc.bristle_stroke(
                px - dx, py - dy, px + dx, py + dy,
                width_px=float(rng.uniform(3.5, 9.0)) * sc,
                color=(0.98, 0.68 + 0.14 * fire, 0.38),
                alpha=float(rng.uniform(0.10, 0.24)) * fire,
                bristles=3,
                jitter_col=0.02,
                overshoot=0.06,
            )
    bc.commit_layer(blur_px=4.5, hdr_gain=1.16)

    # Subtle warm horizon sun-glow dabs right behind the Twin Towers gap
    bc.soft_glow_dab(0.485, 0.78, 0.16, 0.14, (0.42, 0.22, 0.09))
    bc.soft_glow_dab(0.485, 0.81, 0.075, 0.065, (0.55, 0.30, 0.12))
