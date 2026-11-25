"""Pure 2D Physical Brushstroke Engine (v4).

Every element in the painting — sky, clouds, distant buildings, Twin Towers,
foreground skyscraper, asphalt road, cars, lamps, and trees — is painted
exclusively with physical 2D brushstrokes (multi-bristle flat brushes, tapered
round strokes, wet-on-wet soft washes, impasto dabs, and luminous light dabs).

Zero 3D geometry, zero homography texture warping, zero raw noise fills,
zero AI models, zero external photo assets.
"""

from __future__ import annotations

import math
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, map_coordinates


class BrushCanvas:
    """Linear-HDR 2D canvas that composites pure brushstroke layers."""

    def __init__(self, width: int, height: int, seed: int = 2026):
        self.width = int(width)
        self.height = int(height)
        self.scale = self.width / 1200.0
        self.img = np.zeros((self.height, self.width, 3), dtype=np.float32)
        self.rng = np.random.default_rng(seed)
        self.total_strokes = 0

        # Active RGBA sRGB-ish paint layer for fast C-accelerated brushstroke accumulation
        self._layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        self._draw = ImageDraw.Draw(self._layer)

    def begin_layer(self) -> None:
        self._layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        self._draw = ImageDraw.Draw(self._layer)

    def commit_layer(
        self,
        blur_px: float = 0.0,
        additive: bool = False,
        hdr_gain: float = 1.0,
        opacity: float = 1.0,
    ) -> None:
        """Convert accumulated brushstrokes to linear HDR and composite onto the main canvas."""
        rgba = np.asarray(self._layer, dtype=np.float32) / 255.0
        if blur_px > 0.0:
            sig = blur_px * self.scale
            for c in range(4):
                rgba[..., c] = gaussian_filter(rgba[..., c], sigma=sig)

        rgb_lin = np.power(np.maximum(rgba[..., :3], 1e-6), 2.2) * float(hdr_gain)
        alpha = np.clip(rgba[..., 3] * float(opacity), 0.0, 1.0)

        if additive:
            self.img += rgb_lin * alpha[..., None]
        else:
            a = alpha[..., None]
            self.img = self.img * (1.0 - a) + rgb_lin * a

        self.begin_layer()

    def _to_rgba(self, col_rgb: tuple[float, float, float], alpha: float) -> tuple[int, int, int, int]:
        return (
            int(max(0, min(255, round(col_rgb[0] * 255.0)))),
            int(max(0, min(255, round(col_rgb[1] * 255.0)))),
            int(max(0, min(255, round(col_rgb[2] * 255.0)))),
            int(max(0, min(255, round(alpha * 255.0)))),
        )

    def bristle_stroke(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        width_px: float,
        color: tuple[float, float, float],
        alpha: float = 0.75,
        bristles: int = 4,
        jitter_col: float = 0.025,
        overshoot: float = 0.0,
    ) -> None:
        """Paint a single physical multi-bristle brushstroke in pixel coordinates."""
        dx = x1 - x0
        dy = y1 - y0
        length = math.hypot(dx, dy) + 1e-5
        nx = -dy / length
        ny = dx / length

        rng = self.rng
        w_sub = max(1, int(round(width_px / max(1.0, bristles * 0.65))))

        for b in range(bristles):
            if bristles == 1:
                ox = oy = 0.0
            else:
                frac = ((b + 0.5) / bristles - 0.5) * width_px
                j_off = float(rng.uniform(-0.18, 0.18)) * width_px
                ox = nx * (frac + j_off)
                oy = ny * (frac + j_off)
            if overshoot > 0.0:
                l_jit0 = float(rng.uniform(-overshoot, overshoot))
                l_jit1 = float(rng.uniform(-overshoot, overshoot))
            else:
                l_jit0 = l_jit1 = 0.0
            sx = x0 + ox + dx * l_jit0
            sy = y0 + oy + dy * l_jit0
            ex = x1 + ox + dx * l_jit1
            ey = y1 + oy + dy * l_jit1

            cj = float(rng.uniform(-jitter_col, jitter_col))
            col = (color[0] + cj, color[1] + cj * 0.9, color[2] + cj * 0.85)
            a_b = alpha * float(rng.uniform(0.74, 1.0))
            self._draw.line([(sx, sy), (ex, ey)], fill=self._to_rgba(col, a_b), width=w_sub)

        self.total_strokes += 1

    def curved_bristle_stroke(
        self,
        pts_px: list[tuple[float, float]],
        width_px: float,
        color: tuple[float, float, float],
        alpha: float = 0.72,
        bristles: int = 3,
        jitter_col: float = 0.02,
    ) -> None:
        """Paint a curved multi-bristle brushstroke through pixel waypoints."""
        rng = self.rng
        w_sub = max(1, int(round(width_px / max(1.0, bristles * 0.65))))
        for _ in range(bristles):
            ox = float(rng.uniform(-0.45, 0.45)) * width_px
            oy = float(rng.uniform(-0.45, 0.45)) * width_px
            cj = float(rng.uniform(-jitter_col, jitter_col))
            col = (color[0] + cj, color[1] + cj * 0.9, color[2] + cj * 0.85)
            shifted = [(p[0] + ox, p[1] + oy) for p in pts_px]
            self._draw.line(shifted, fill=self._to_rgba(col, alpha * float(rng.uniform(0.7, 1.0))), width=w_sub, joint="curve")
        self.total_strokes += 1

    def dab(
        self,
        cx: float,
        cy: float,
        rx: float,
        ry: float,
        color: tuple[float, float, float],
        alpha: float = 0.75,
        angle_rad: float = 0.0,
    ) -> None:
        """Paint a rotated painterly brush dab (ellipse or angled stroke)."""
        if abs(angle_rad) < 0.12 or abs(rx - ry) < 0.8:
            self._draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=self._to_rgba(color, alpha))
        else:
            ca = math.cos(angle_rad)
            sa = math.sin(angle_rad)
            # 6-point rotated oval dab
            pts = []
            for k in range(6):
                th = k * (math.pi / 3.0)
                lx = math.cos(th) * rx
                ly = math.sin(th) * ry
                pts.append((cx + lx * ca - ly * sa, cy + lx * sa + ly * ca))
            self._draw.polygon(pts, fill=self._to_rgba(color, alpha))
        self.total_strokes += 1

    def soft_glow_dab(
        self,
        u: float,
        v: float,
        ru: float,
        rv: float,
        color_hdr: tuple[float, float, float],
    ) -> None:
        """Additive radial light dab directly in linear HDR (for lamps, car lights, beacons)."""
        cx = u * self.width
        cy = v * self.height
        rx = max(ru * self.width, 0.7)
        ry = max(rv * self.height, 0.7)
        x0 = max(0, int(np.floor(cx - rx * 3.0)))
        x1 = min(self.width, int(np.ceil(cx + rx * 3.0)) + 1)
        y0 = max(0, int(np.floor(cy - ry * 3.0)))
        y1 = min(self.height, int(np.ceil(cy + ry * 3.0)) + 1)
        if x1 <= x0 or y1 <= y0:
            return
        xs = (np.arange(x0, x1, dtype=np.float32) - cx) / rx
        ys = (np.arange(y0, y1, dtype=np.float32) - cy) / ry
        xx, yy = np.meshgrid(xs, ys)
        falloff = np.exp(-(xx * xx + yy * yy) * 1.5)
        col = np.array(color_hdr, dtype=np.float32)[None, None, :]
        self.img[y0:y1, x0:x1] += col * falloff[..., None]
        self.total_strokes += 1

    def save_png(
        self,
        path: str,
        exposure: float = 1.04,
        bloom_strength: float = 0.14,
        vignette_strength: float = 0.20,
        grain_strength: float = 0.011,
        ca_pixels: float = 0.35,
        sharpen_amount: float = 0.18,
        seed: int = 999,
    ) -> None:
        """Apply camera optics, ACES filmic tone mapping, subtle sharpen & sensor grain."""
        hdr = np.maximum(self.img, 0.0) * float(exposure)
        scale = self.width / 1600.0

        # Restrained optical bloom on bright light dabs
        luma = 0.2126 * hdr[..., 0] + 0.7152 * hdr[..., 1] + 0.0722 * hdr[..., 2]
        bright = hdr * np.clip((luma - 0.80) / 1.4, 0.0, 4.0)[..., None]
        b1 = np.stack([gaussian_filter(bright[..., c], sigma=max(1.2, 2.5 * scale)) for c in range(3)], axis=-1)
        b2 = np.stack([gaussian_filter(bright[..., c], sigma=max(4.0, 9.5 * scale)) for c in range(3)], axis=-1)
        b3 = np.stack([gaussian_filter(bright[..., c], sigma=max(11.0, 26.0 * scale)) for c in range(3)], axis=-1)
        hdr = hdr + bloom_strength * (0.50 * b1 + 0.32 * b2 + 0.18 * b3)

        # Subtle lateral chromatic aberration
        u = np.linspace(0.0, 1.0, self.width, dtype=np.float32)
        v = np.linspace(0.0, 1.0, self.height, dtype=np.float32)
        uu, vv = np.meshgrid(u, v)
        if ca_pixels > 0.0:
            dx = (uu - 0.5) * 2.0
            dy = (vv - 0.5) * 2.0
            shift = ca_pixels * scale * (dx * dx + dy * dy)
            yy, xx = np.mgrid[0 : self.height, 0 : self.width].astype(np.float32)
            r_coords = np.array([yy - dy * shift * 0.5, xx - dx * shift * 0.5])
            b_coords = np.array([yy + dy * shift * 0.5, xx + dx * shift * 0.5])
            hdr_ca = hdr.copy()
            hdr_ca[..., 0] = map_coordinates(hdr[..., 0], r_coords, order=1, mode="nearest")
            hdr_ca[..., 2] = map_coordinates(hdr[..., 2], b_coords, order=1, mode="nearest")
            hdr = hdr_ca

        # Gentle lens vignette
        rx = (uu - 0.5) * 2.0
        ry = (vv - 0.5) * 2.0 * (self.height / self.width)
        vig = 1.0 - vignette_strength * np.clip(rx * rx + ry * ry, 0.0, 1.8) ** 1.45
        hdr *= np.clip(vig, 0.65, 1.0)[..., None]

        # ACES Filmic Tone Mapping
        a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
        mapped = np.clip((hdr * (a * hdr + b)) / (hdr * (c * hdr + d) + e), 0.0, 1.0)

        # sRGB encoding
        srgb = np.where(
            mapped <= 0.0031308,
            mapped * 12.92,
            1.055 * np.power(np.maximum(mapped, 1e-8), 1.0 / 2.4) - 0.055,
        )

        # Subtle optical micro-sharpening
        if sharpen_amount > 0.0:
            blurred = np.stack([gaussian_filter(srgb[..., ch], sigma=max(0.7, 0.9 * scale)) for ch in range(3)], axis=-1)
            srgb = np.clip(srgb + sharpen_amount * (srgb - blurred), 0.0, 1.0)

        # Fine sensor/canvas grain
        if grain_strength > 0.0:
            rng = np.random.default_rng(seed)
            lum_s = 0.2126 * srgb[..., 0] + 0.7152 * srgb[..., 1] + 0.0722 * srgb[..., 2]
            grain = rng.normal(0.0, 1.0, size=(self.height, self.width, 1)).astype(np.float32)
            chroma = rng.normal(0.0, 0.16, size=(self.height, self.width, 3)).astype(np.float32)
            weight = (0.35 + 0.65 * (1.0 - lum_s))[..., None]
            srgb = srgb + (grain + chroma) * grain_strength * weight

        srgb = np.clip(srgb, 0.0, 1.0)
        Image.fromarray((srgb * 255.0 + 0.5).astype(np.uint8), mode="RGB").save(
            path, format="PNG", optimize=True
        )
