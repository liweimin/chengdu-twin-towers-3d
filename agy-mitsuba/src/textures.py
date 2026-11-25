"""
Procedural PBR & Emission Texture Generator v3 for Chengdu Financial City Twin Towers at Dusk.
Upgrades:
  - Razor-sharp 2048px architectural CBD office curtain walls with realistic window mullions,
    diverse corporate crowns (no repetitive yellow bars!), realistic office clusters & blinds
  - Synchronized Shu-brocade golden-amber & coral-gold silk wave flowing gracefully across
    BOTH Twin Towers with crisp horizontal LED louver bars and dark twilight breathing space
"""

import os
import numpy as np
from PIL import Image


def _save_rgb(arr, path):
    arr = np.clip(arr, 0.0, 1.0)
    Image.fromarray((arr * 255.0 + 0.5).astype(np.uint8), mode="RGB").save(path)


def _save_gray(arr, path):
    arr = np.clip(arr, 0.0, 1.0)
    Image.fromarray((arr * 255.0 + 0.5).astype(np.uint8), mode="L").save(path)


def _fbm_grid(h, w, freqs=(4, 8, 16, 32, 64), weights=(0.45, 0.25, 0.15, 0.10, 0.05), seed=42):
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), dtype=np.float32)
    for f, wt in zip(freqs, weights):
        gh = max(2, f)
        gw = max(2, int(f * w / h))
        coarse = rng.random((gh, gw), dtype=np.float32)
        pil = Image.fromarray((coarse * 255).astype(np.uint8)).resize((w, h), Image.Resampling.BICUBIC)
        acc += wt * (np.asarray(pil, dtype=np.float32) / 255.0)
    acc -= acc.min()
    if acc.max() > 1e-6:
        acc /= acc.max()
    return acc


def generate_twin_tower_led_textures(out_dir="assets"):
    """
    Synchronized Left (South, x=+42) & Right (North, x=-42) Twin Tower LED media louvers.
    Graceful sweeping golden-champagne & warm vermilion-rose Shu-brocade silk ribbons
    spanning cohesively across both towers with crisp architectural louver rasterization.
    """
    h, w = 2048, 1024
    u = np.linspace(0.0, 1.0, w, dtype=np.float32)
    v = np.linspace(0.0, 1.0, h, dtype=np.float32)
    uu, vv = np.meshgrid(u, v)

    # Crisp discrete horizontal LED louver strips (220 rows)
    strip_phase = (vv * 220.0) % 1.0
    louver_mask = np.clip((0.48 - np.abs(strip_phase - 0.5)) * 12.0, 0.0, 1.0)
    pixel_mod = 0.88 + 0.12 * np.sin(uu * 2.0 * np.pi * 150.0)

    # Mechanical refuge floors (crisp dark architectural rhythm)
    mech_mask = np.ones_like(vv)
    for mf in (0.26, 0.54, 0.81):
        mech_mask *= 1.0 - 0.55 * np.exp(-((vv - mf) / 0.0065) ** 2)

    paths = {}
    # Left on screen = "south" (x=+42), Right on screen = "north" (x=-42)
    # Smooth trigonometric screen-X projection: zero hairpin kinks on tower silhouette edges!
    # uu=0.25 -> theta=+pi/2 -> x_scr=-1.0 (left edge); uu=0.50 -> x_scr=0.0 (front); uu=0.75 -> x_scr=+1.0 (right edge)
    theta_u = (0.5 - uu) * 2.0 * np.pi
    x_scr = -np.sin(theta_u)  # Smoothly spans [-1, +1] left-to-right across camera-facing front!
    for label, gx_offset, seed in [("south", 0.0, 101), ("north", 1.28, 202)]:
        gx = gx_offset + 0.5 * (x_scr + 1.0)  # Left tower: [0, 1]; Right tower: [1.28, 2.28]

        # Graceful, unbroken sweeping golden Shu-brocade ribbon flowing diagonally across BOTH towers!
        w1 = 0.28 + 0.19 * gx + 0.075 * np.sin(gx * 2.15 - 0.3)
        w2 = 0.50 + 0.13 * gx - 0.070 * np.cos(gx * 1.95 + 0.5)
        w3 = 0.16 + 0.10 * gx + 0.045 * np.sin(gx * 2.6 + 1.0)

        d1 = np.abs(vv - w1)
        d2 = np.abs(vv - w2)
        d3 = np.abs(vv - w3)

        # Silk thread pleats
        p1 = 0.52 + 0.48 * np.cos((vv - w1) * 85.0 - gx * 4.5)
        p2 = 0.52 + 0.48 * np.cos((vv - w2) * 95.0 + gx * 4.0)
        p3 = 0.52 + 0.48 * np.cos((vv - w3) * 75.0 - gx * 5.0)

        r1 = np.exp(-((d1 / 0.105) ** 1.7)) * (0.45 + 0.55 * p1)
        r2 = np.exp(-((d2 / 0.088) ** 1.75)) * (0.42 + 0.58 * p2)
        r3 = np.exp(-((d3 / 0.080) ** 1.7)) * (0.45 + 0.55 * p3)

        sh = _fbm_grid(h // 4, w // 4, freqs=(12, 24, 48, 96), weights=(0.35, 0.30, 0.20, 0.15), seed=seed)
        sh = np.asarray(Image.fromarray((sh * 255).astype(np.uint8)).resize((w, h), Image.Resampling.BILINEAR), dtype=np.float32) / 255.0
        sparkles = np.clip((sh - 0.60) / 0.40, 0.0, 1.0) ** 2.2

        # Deep restrained architectural twilight ambient wash (keeps glass dark & reflective!)
        em = np.zeros((h, w, 3), dtype=np.float32)
        low_amb = np.exp(-vv * 4.8) * 0.11
        hi_cool = np.exp(-((vv - 0.80) / 0.22) ** 2) * 0.10
        em[..., 0] = low_amb * 0.92 + hi_cool * 0.08
        em[..., 1] = low_amb * 0.50 + hi_cool * 0.34
        em[..., 2] = low_amb * 0.16 + hi_cool * 0.95

        col_gold = np.array([1.00, 0.65, 0.20], dtype=np.float32)
        col_coral = np.array([0.96, 0.28, 0.14], dtype=np.float32)
        col_amber = np.array([0.92, 0.46, 0.12], dtype=np.float32)

        em += r1[..., None] * col_gold * 0.90
        em += r2[..., None] * col_coral * 0.78
        em += r3[..., None] * col_amber * 0.58

        core1 = np.exp(-((d1 / 0.013) ** 2))
        core2 = np.exp(-((d2 / 0.011) ** 2))
        em += (core1 * 0.65 + core2 * 0.45)[..., None] * np.array([1.00, 0.88, 0.62], dtype=np.float32)

        env = np.clip(r1 + r2 + r3, 0.0, 1.0)
        em += (sparkles * env * 0.50)[..., None] * np.array([1.00, 0.82, 0.50], dtype=np.float32)

        # Crisp twin architectural crown accent rings right below roof parapet
        crown = (
            np.exp(-((vv - 0.976) / 0.007) ** 2) * 0.80
            + np.exp(-((vv - 0.946) / 0.004) ** 2) * 0.32
        )
        em += crown[..., None] * np.array([1.00, 0.76, 0.40], dtype=np.float32)

        # Fade cleanly near podium attachment and top cap
        base_fade = np.clip((vv - 0.022) / 0.05, 0.0, 1.0) * np.clip((0.992 - vv) / 0.012, 0.0, 1.0)
        em *= (louver_mask * pixel_mod * mech_mask * base_fade)[..., None]

        out_path = os.path.join(out_dir, f"tower_led_{label}.png")
        _save_rgb(np.flipud(np.clip(em, 0.0, 1.0)), out_path)
        paths[label] = out_path

    return paths


def generate_twin_tower_interior_texture(out_dir="assets"):
    """Crisp warm architectural office rooms behind Twin Towers LOW-E glass curtain wall."""
    rng = np.random.default_rng(777)
    floors = 54
    bays = 40
    cell_h, cell_w = 24, 24
    H, W = floors * cell_h, bays * cell_w

    img = np.zeros((H, W, 3), dtype=np.float32)
    mech_floors = {0, 1, 14, 29, 43, 53}

    for f in range(floors):
        if f in mech_floors:
            continue
        floor_busy = rng.uniform(0.32, 0.66)
        b = 0
        while b < bays:
            span = int(rng.integers(2, 6))
            if rng.random() < floor_busy:
                tr = rng.random()
                if tr < 0.58:
                    col = np.array([1.00, 0.72, 0.36], dtype=np.float32)
                elif tr < 0.86:
                    col = np.array([1.00, 0.85, 0.62], dtype=np.float32)
                else:
                    col = np.array([0.80, 0.90, 1.00], dtype=np.float32)
                br = rng.uniform(0.35, 1.0)
                for bb in range(b, min(b + span, bays)):
                    y0, y1 = f * cell_h, (f + 1) * cell_h
                    x0, x1 = bb * cell_w, (bb + 1) * cell_w
                    yy = np.linspace(0.0, 1.0, cell_h, dtype=np.float32)[:, None]
                    xx = np.linspace(0.0, 1.0, cell_w, dtype=np.float32)[None, :]
                    slab_mask = ((yy > 0.18) & (yy < 0.86) & (xx > 0.12) & (xx < 0.88)).astype(np.float32)
                    vert_grad = 0.42 + 0.58 * np.clip((yy - 0.18) / 0.68, 0.0, 1.0)
                    if rng.random() < 0.25:
                        vert_grad *= np.where(yy > rng.uniform(0.45, 0.70), 0.22, 1.0)
                    img[y0:y1, x0:x1] = col[None, None, :] * (slab_mask * vert_grad * br * rng.uniform(0.84, 1.12))[..., None]
            b += span

    path = os.path.join(out_dir, "tower_interior.png")
    _save_rgb(np.flipud(np.clip(img, 0.0, 1.0)), path)
    return path


def generate_cbd_facade_textures(out_dir="assets"):
    """
    4 ultra-crisp, architecturally distinct Chengdu Financial City skyscraper facades.
    Key realism upgrades:
      - High pixel density (up to 1664x1024) with sharp dark structural mullions & spandrels
      - Authentic varied crown treatments (2 dark understated crowns, 1 subtle cool corporate
        crown rim, 1 subtle warm penthouse rim — NO repetitive thick yellow bars!)
      - Crisp discrete windowpanes with realistic blinds, partitions, and office occupancy
    """
    sets = []
    configs = [
        # (seed, floors, bays, mullion_rgb, glass_rgb, warm_ratio, crown_rgb, crown_amp)
        (11, 46, 30, (0.08, 0.11, 0.17), (0.012, 0.025, 0.058), 0.58, (1.0, 0.80, 0.52), 0.0),   # Sleek cool-blue corporate glass
        (22, 40, 26, (0.14, 0.14, 0.16), (0.016, 0.026, 0.050), 0.72, (1.0, 0.76, 0.42), 0.30),  # Champagne stone/slate finned tower
        (33, 50, 32, (0.07, 0.11, 0.19), (0.012, 0.030, 0.072), 0.40, (0.45, 0.78, 1.0), 0.38),  # Cool sapphire fintech tower
        (44, 34, 24, (0.12, 0.12, 0.14), (0.015, 0.022, 0.046), 0.80, (1.0, 0.68, 0.36), 0.0),   # Modern twilight hotel/office
    ]

    for idx, (seed, floors, bays, mul_c, glass_c, warm_r, crown_c, crown_amp) in enumerate(configs):
        rng = np.random.default_rng(seed)
        ch, cw = 32, 28
        H, W = floors * ch, bays * cw
        albedo = np.zeros((H, W, 3), dtype=np.float32)
        emissive = np.zeros((H, W, 3), dtype=np.float32)
        rough = np.full((H, W), 0.16, dtype=np.float32)

        albedo[:] = np.array(glass_c, dtype=np.float32)
        mech = {floors // 3, (2 * floors) // 3, floors - 1}

        for f in range(floors):
            y0, y1 = f * ch, (f + 1) * ch
            sp_h = 10  # Crisp architectural floor spandrel (31% of floor height)
            albedo[y0:y0 + sp_h, :] = np.array(mul_c, dtype=np.float32) * rng.uniform(0.92, 1.06)
            rough[y0:y0 + sp_h, :] = 0.45

            # Crisp dark vertical mullions separating every single glass pane
            for b in range(bays):
                x0 = b * cw
                albedo[y0:y1, x0:x0 + 4] = np.array(mul_c, dtype=np.float32)
                rough[y0:y1, x0:x0 + 4] = 0.42

            if f in mech:
                albedo[y0:y1, :] = np.array(mul_c, dtype=np.float32) * 0.68
                rough[y0:y1, :] = 0.58
                continue

            if f == 0:
                for b in range(bays):
                    if rng.random() < 0.78:
                        x0, x1 = b * cw + 4, (b + 1) * cw - 1
                        emissive[y0 + sp_h + 1:y1 - 2, x0:x1] = np.array([1.0, 0.72, 0.36], dtype=np.float32) * rng.uniform(0.35, 0.72)
                continue

            occ = rng.uniform(0.22, 0.54)
            b = 0
            while b < bays:
                span = int(rng.integers(1, 5))
                if rng.random() < occ:
                    if rng.random() < warm_r:
                        c = np.array([1.0, rng.uniform(0.68, 0.84), rng.uniform(0.34, 0.56)], dtype=np.float32)
                    else:
                        c = np.array([rng.uniform(0.74, 0.88), rng.uniform(0.86, 0.95), 1.0], dtype=np.float32)
                    inten = rng.uniform(0.22, 0.90)
                    for bb in range(b, min(b + span, bays)):
                        x0, x1 = bb * cw + 4, (bb + 1) * cw - 1
                        gh = (y1 - 2) - (y0 + sp_h + 1)
                        grad = np.linspace(0.35, 1.0, gh, dtype=np.float32)[:, None, None]
                        if rng.random() < 0.28:
                            grad[:gh // 2] *= 0.25
                        # Crisp horizontal ceiling light strip inside office
                        grad[-3:] *= 1.15
                        emissive[y0 + sp_h + 1:y1 - 2, x0:x1] = c[None, None, :] * grad * inten * rng.uniform(0.85, 1.12)
                b += span

        if crown_amp > 0.0:
            emissive[H - 4:H - 2, :] = np.array(crown_c, dtype=np.float32) * crown_amp

        albedo_p = os.path.join(out_dir, f"cbd_albedo_{idx}.png")
        emis_p = os.path.join(out_dir, f"cbd_emis_{idx}.png")
        rough_p = os.path.join(out_dir, f"cbd_rough_{idx}.png")
        _save_rgb(np.flipud(albedo), albedo_p)
        _save_rgb(np.flipud(emissive), emis_p)
        _save_gray(np.flipud(rough), rough_p)
        sets.append({"albedo": albedo_p, "emissive": emis_p, "roughness": rough_p})

    return sets


def generate_road_textures(out_dir="assets"):
    """Freshly-washed / damp boulevard asphalt with glossy wet tire tracks & crisp markings."""
    H, W = 2048, 1536
    u = np.linspace(0.0, 1.0, W, dtype=np.float32)
    v = np.linspace(0.0, 1.0, H, dtype=np.float32)
    uu, vv = np.meshgrid(u, v)

    macro = _fbm_grid(H // 4, W // 4, freqs=(4, 8, 16, 32), weights=(0.45, 0.30, 0.15, 0.10), seed=303)
    macro = np.asarray(Image.fromarray((macro * 255).astype(np.uint8)).resize((W, H), Image.Resampling.BILINEAR), dtype=np.float32) / 255.0

    micro = _fbm_grid(H // 2, W // 2, freqs=(32, 64, 128), weights=(0.5, 0.3, 0.2), seed=404)
    micro = np.asarray(Image.fromarray((micro * 255).astype(np.uint8)).resize((W, H), Image.Resampling.BILINEAR), dtype=np.float32) / 255.0

    wetness = np.clip((macro - 0.30) / 0.36, 0.0, 1.0)
    lane_centers = [0.14, 0.25, 0.36, 0.64, 0.75, 0.86]
    tire_polish = np.zeros_like(uu)
    for lc in lane_centers:
        tire_polish += np.exp(-((uu - (lc - 0.022)) / 0.015) ** 2)
        tire_polish += np.exp(-((uu - (lc + 0.022)) / 0.015) ** 2)
    tire_polish = np.clip(tire_polish, 0.0, 1.0)

    curb_wet = np.exp(-((uu - 0.06) / 0.04) ** 2) + np.exp(-((uu - 0.94) / 0.04) ** 2)
    damp_mask = np.clip(wetness * 0.84 + tire_polish * 0.32 + curb_wet * 0.48, 0.0, 1.0)

    base_val = (0.056 + 0.024 * micro) * (1.0 - 0.52 * damp_mask)
    albedo = np.stack([base_val * 0.95, base_val * 1.00, base_val * 1.09], axis=-1)

    rough = 0.40 * (1.0 - damp_mask) + 0.050 * damp_mask + 0.032 * (micro - 0.5)
    rough = np.clip(rough, 0.042, 0.50)

    wear = np.clip(0.75 + 0.30 * micro, 0.0, 1.0)
    yel_mask = (np.abs(uu - 0.472) < 0.0045) | (np.abs(uu - 0.528) < 0.0045)
    yel_col = np.array([0.62, 0.42, 0.07], dtype=np.float32)

    dash_v = ((vv * 6.0) % 1.0) < 0.44
    wht_dash = (
        (np.abs(uu - 0.195) < 0.0038) | (np.abs(uu - 0.305) < 0.0038) |
        (np.abs(uu - 0.695) < 0.0038) | (np.abs(uu - 0.805) < 0.0038)
    ) & dash_v
    wht_edge = (np.abs(uu - 0.082) < 0.0045) | (np.abs(uu - 0.918) < 0.0045)
    cross_v = (vv > 0.06) & (vv < 0.16)
    cross_u = (((uu * 36.0) % 1.0) < 0.48) & (uu > 0.09) & (uu < 0.91) & (np.abs(uu - 0.50) > 0.04)
    wht_mask = wht_dash | wht_edge | (cross_v & cross_u)
    wht_col = np.array([0.55, 0.56, 0.59], dtype=np.float32)

    albedo = np.where(yel_mask[..., None], albedo * (1.0 - 0.85 * wear[..., None]) + yel_col * (0.85 * wear[..., None]), albedo)
    albedo = np.where(wht_mask[..., None], albedo * (1.0 - 0.82 * wear[..., None]) + wht_col * (0.82 * wear[..., None]), albedo)
    rough = np.where(yel_mask | wht_mask, np.minimum(rough, 0.22), rough)

    albedo_p = os.path.join(out_dir, "road_albedo.png")
    rough_p = os.path.join(out_dir, "road_roughness.png")
    _save_rgb(albedo, albedo_p)
    _save_gray(rough, rough_p)
    return {"albedo": albedo_p, "roughness": rough_p}


def generate_all_textures(out_dir="assets"):
    os.makedirs(out_dir, exist_ok=True)
    led = generate_twin_tower_led_textures(out_dir)
    interior = generate_twin_tower_interior_texture(out_dir)
    cbd = generate_cbd_facade_textures(out_dir)
    road = generate_road_textures(out_dir)
    print(f"Generated all procedural architectural textures v3 in {out_dir}/")
    return {"led": led, "interior": interior, "cbd": cbd, "road": road}


if __name__ == "__main__":
    generate_all_textures()
