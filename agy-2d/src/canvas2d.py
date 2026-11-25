"""Pure 2D linear-HDR painting canvas and photographic optics pipeline.

Operates on a 2D float32 linear RGB image buffer (H, W, 3).
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, map_coordinates


class Canvas2D:
    """2D linear-HDR painting canvas with anti-aliased drawing and optics."""

    def __init__(self, width: int, height: int):
        self.width = int(width)
        self.height = int(height)
        self.img = np.zeros((self.height, self.width, 3), dtype=np.float32)

    def u_grid(self) -> tuple[np.ndarray, np.ndarray]:
        """Normalized 2D coordinates (u in [0, 1], v in [0, 1])."""
        u = np.linspace(0.0, 1.0, self.width, dtype=np.float32)
        v = np.linspace(0.0, 1.0, self.height, dtype=np.float32)
        return np.meshgrid(u, v)

    def blend_over(
        self,
        color: np.ndarray,
        alpha: np.ndarray,
        y0: int = 0,
        x0: int = 0,
    ) -> None:
        """Alpha-composite a 2D RGB patch over the canvas at (x0, y0)."""
        h, w = alpha.shape[:2]
        a = alpha[..., None] if alpha.ndim == 2 else alpha
        dst = self.img[y0 : y0 + h, x0 : x0 + w]
        self.img[y0 : y0 + h, x0 : x0 + w] = dst * (1.0 - a) + color * a

    def add_light(
        self,
        color: np.ndarray,
        mask: np.ndarray | float = 1.0,
        y0: int = 0,
        x0: int = 0,
    ) -> None:
        """Additively accumulate linear light onto the canvas."""
        if isinstance(mask, (int, float)):
            self.img += color * float(mask)
            return
        h, w = mask.shape[:2]
        m = mask[..., None] if mask.ndim == 2 else mask
        self.img[y0 : y0 + h, x0 : x0 + w] += color * m

    def draw_soft_glow(
        self,
        cx_norm: float,
        cy_norm: float,
        radius_x_norm: float,
        radius_y_norm: float,
        color: tuple[float, float, float],
        power: float = 2.0,
    ) -> None:
        """Additive radial 2D glow stamp (for lamps, sun, beacons, reflections)."""
        cx = cx_norm * self.width
        cy = cy_norm * self.height
        rx = max(radius_x_norm * self.width, 1.0)
        ry = max(radius_y_norm * self.height, 1.0)

        x0 = max(0, int(np.floor(cx - rx * 3.0)))
        x1 = min(self.width, int(np.ceil(cx + rx * 3.0)) + 1)
        y0 = max(0, int(np.floor(cy - ry * 3.0)))
        y1 = min(self.height, int(np.ceil(cy + ry * 3.0)) + 1)
        if x1 <= x0 or y1 <= y0:
            return

        xs = (np.arange(x0, x1, dtype=np.float32) - cx) / rx
        ys = (np.arange(y0, y1, dtype=np.float32) - cy) / ry
        xx, yy = np.meshgrid(xs, ys)
        d2 = xx * xx + yy * yy
        if power == 2.0:
            falloff = np.exp(-d2 * 1.5)
        else:
            falloff = 1.0 / np.power(1.0 + d2, power)
            falloff *= np.clip(1.0 - d2 / 9.0, 0.0, 1.0)

        col = np.array(color, dtype=np.float32)[None, None, :]
        self.img[y0:y1, x0:x1] += col * falloff[..., None]

    def rasterize_polygon_mask(
        self,
        pts_norm: list[tuple[float, float]],
        supersample: int = 2,
    ) -> tuple[np.ndarray, int, int]:
        """Anti-aliased 2D polygon mask in bounding box, returns (mask, x0, y0)."""
        xs = [p[0] * self.width for p in pts_norm]
        ys = [p[1] * self.height for p in pts_norm]
        x0 = max(0, int(np.floor(min(xs))) - 2)
        y0 = max(0, int(np.floor(min(ys))) - 2)
        x1 = min(self.width, int(np.ceil(max(xs))) + 2)
        y1 = min(self.height, int(np.ceil(max(ys))) + 2)
        bw = x1 - x0
        bh = y1 - y0
        if bw <= 0 or bh <= 0:
            return np.zeros((0, 0), dtype=np.float32), x0, y0

        ss = max(1, int(supersample))
        im = Image.new("L", (bw * ss, bh * ss), 0)
        draw = ImageDraw.Draw(im)
        poly = [((p[0] * self.width - x0) * ss, (p[1] * self.height - y0) * ss) for p in pts_norm]
        draw.polygon(poly, fill=255)
        if ss > 1:
            im = im.resize((bw, bh), Image.Resampling.LANCZOS)
        mask = np.asarray(im, dtype=np.float32) / 255.0
        return mask, x0, y0

    def paint_quad_texture(
        self,
        quad_norm: list[tuple[float, float]],
        texture_rgb: np.ndarray,
        alpha: float | np.ndarray = 1.0,
        additive: bool = False,
    ) -> None:
        """Paint a 2D texture onto an arbitrary 2D convex quad via homography.

        quad_norm order: [top-left, top-right, bottom-right, bottom-left] in normalized [0, 1] coords.
        Pure 2D projective mapping for architectural facades without any 3D geometry engine.
        """
        dst_pts = np.array(
            [(p[0] * self.width, p[1] * self.height) for p in quad_norm],
            dtype=np.float64,
        )
        th, tw = texture_rgb.shape[:2]
        src_pts = np.array(
            [(0.0, 0.0), (tw - 1.0, 0.0), (tw - 1.0, th - 1.0), (0.0, th - 1.0)],
            dtype=np.float64,
        )

        # Solve 2D homography H mapping destination pixel (x, y) -> source texture (u, v)
        H = _solve_homography_2d(dst_pts, src_pts)

        mask, x0, y0 = self.rasterize_polygon_mask(quad_norm, supersample=2)
        bh, bw = mask.shape
        if bh == 0 or bw == 0:
            return

        xs = np.arange(x0, x0 + bw, dtype=np.float64) + 0.5
        ys = np.arange(y0, y0 + bh, dtype=np.float64) + 0.5
        xx, yy = np.meshgrid(xs, ys)

        denom = H[2, 0] * xx + H[2, 1] * yy + H[2, 2]
        denom = np.where(np.abs(denom) < 1e-9, 1e-9, denom)
        su = (H[0, 0] * xx + H[0, 1] * yy + H[0, 2]) / denom
        sv = (H[1, 0] * xx + H[1, 1] * yy + H[1, 2]) / denom

        coords = np.array([sv, su], dtype=np.float64)
        sampled = np.empty((bh, bw, 3), dtype=np.float32)
        for c in range(3):
            sampled[..., c] = map_coordinates(
                texture_rgb[..., c], coords, order=1, mode="nearest"
            )

        if isinstance(alpha, np.ndarray):
            a_samp = map_coordinates(alpha, coords, order=1, mode="nearest")
            a = np.clip(mask * a_samp, 0.0, 1.0)
        else:
            a = np.clip(mask * float(alpha), 0.0, 1.0)

        if additive:
            self.add_light(sampled, a, y0=y0, x0=x0)
        else:
            self.blend_over(sampled, a, y0=y0, x0=x0)

    def paint_bezier_ribbon(
        self,
        p0: tuple[float, float],
        p1: tuple[float, float],
        p2: tuple[float, float],
        p3: tuple[float, float],
        width_px: float,
        color_start: tuple[float, float, float],
        color_end: tuple[float, float, float],
        steps: int = 240,
        additive: bool = True,
    ) -> None:
        """Paint a smooth cubic Bezier light trail or architectural arc in 2D."""
        t = np.linspace(0.0, 1.0, steps, dtype=np.float32)
        mt = 1.0 - t
        xs = (
            mt**3 * p0[0]
            + 3 * mt**2 * t * p1[0]
            + 3 * mt * t**2 * p2[0]
            + t**3 * p3[0]
        ) * self.width
        ys = (
            mt**3 * p0[1]
            + 3 * mt**2 * t * p1[1]
            + 3 * mt * t**2 * p2[1]
            + t**3 * p3[1]
        ) * self.height

        r = max(width_px, 0.8)
        pad = int(np.ceil(r * 3.5))
        x0 = max(0, int(np.floor(xs.min())) - pad)
        x1 = min(self.width, int(np.ceil(xs.max())) + pad + 1)
        y0 = max(0, int(np.floor(ys.min())) - pad)
        y1 = min(self.height, int(np.ceil(ys.max())) + pad + 1)
        if x1 <= x0 or y1 <= y0:
            return

        # Render onto a local bounding box by splatting soft Gaussian discs along the curve
        gx = np.arange(x0, x1, dtype=np.float32)
        gy = np.arange(y0, y1, dtype=np.float32)
        c0 = np.array(color_start, dtype=np.float32)
        c1 = np.array(color_end, dtype=np.float32)

        patch = np.zeros((y1 - y0, x1 - x0, 3), dtype=np.float32)
        w_acc = np.zeros((y1 - y0, x1 - x0), dtype=np.float32)

        # Segment-based distance for perfectly smooth ribbon without beading
        for i in range(steps - 1):
            ax, ay = xs[i], ys[i]
            bx, by = xs[i + 1], ys[i + 1]
            sx0 = max(x0, int(np.floor(min(ax, bx) - r * 3.0)))
            sx1 = min(x1, int(np.ceil(max(ax, bx) + r * 3.0)) + 1)
            sy0 = max(y0, int(np.floor(min(ay, by) - r * 3.0)))
            sy1 = min(y1, int(np.ceil(max(ay, by) + r * 3.0)) + 1)
            if sx1 <= sx0 or sy1 <= sy0:
                continue

            xx, yy = np.meshgrid(gx[sx0 - x0 : sx1 - x0], gy[sy0 - y0 : sy1 - y0])
            abx = bx - ax
            aby = by - ay
            ab2 = abx * abx + aby * aby + 1e-6
            proj = np.clip(((xx - ax) * abx + (yy - ay) * aby) / ab2, 0.0, 1.0)
            px = ax + proj * abx
            py = ay + proj * aby
            d2 = (xx - px) ** 2 + (yy - py) ** 2
            val = np.exp(-d2 / (2.0 * r * r))

            ti = 0.5 * (t[i] + t[i + 1])
            col = c0 * (1.0 - ti) + c1 * ti
            sl = (slice(sy0 - y0, sy1 - y0), slice(sx0 - x0, sx1 - x0))
            # Max-combine intensity along overlapping segments for uniform trail brightness
            prev = w_acc[sl]
            better = val > prev
            w_acc[sl] = np.where(better, val, prev)
            patch[sl] = np.where(better[..., None], col[None, None, :] * val[..., None], patch[sl])

        if additive:
            self.img[y0:y1, x0:x1] += patch
        else:
            a = np.clip(w_acc, 0.0, 1.0)[..., None]
            self.img[y0:y1, x0:x1] = self.img[y0:y1, x0:x1] * (1.0 - a) + patch

    def apply_photographic_post(
        self,
        exposure: float = 1.05,
        bloom_strength: float = 0.22,
        vignette_strength: float = 0.28,
        grain_strength: float = 0.011,
        ca_pixels: float = 0.65,
        seed: int = 42,
    ) -> np.ndarray:
        """Apply camera optics, multi-scale bloom, ACES filmic tone mapping, and grain.

        Returns sRGB uint8 array (H, W, 3).
        """
        hdr = np.maximum(self.img, 0.0) * float(exposure)

        # 1. Multi-scale optical bloom / halation on bright highlights
        luma = 0.2126 * hdr[..., 0] + 0.7152 * hdr[..., 1] + 0.0722 * hdr[..., 2]
        bright_mask = np.clip((luma - 0.65) / 1.5, 0.0, 4.0)
        bright = hdr * bright_mask[..., None]

        scale = self.width / 1600.0
        b1 = np.stack([gaussian_filter(bright[..., c], sigma=max(1.5, 3.0 * scale)) for c in range(3)], axis=-1)
        b2 = np.stack([gaussian_filter(bright[..., c], sigma=max(5.0, 12.0 * scale)) for c in range(3)], axis=-1)
        b3 = np.stack([gaussian_filter(bright[..., c], sigma=max(14.0, 36.0 * scale)) for c in range(3)], axis=-1)
        hdr = hdr + bloom_strength * (0.45 * b1 + 0.35 * b2 + 0.20 * b3)

        # 2. Subtle lateral chromatic aberration (red shifts slightly outward, blue inward)
        if ca_pixels > 0.0:
            u, v = self.u_grid()
            dx = (u - 0.5) * 2.0
            dy = (v - 0.5) * 2.0
            r2 = dx * dx + dy * dy
            shift = ca_pixels * scale * r2

            yy, xx = np.mgrid[0 : self.height, 0 : self.width].astype(np.float32)
            r_coords = np.array([yy - dy * shift * 0.6, xx - dx * shift * 0.6])
            b_coords = np.array([yy + dy * shift * 0.6, xx + dx * shift * 0.6])
            hdr_ca = hdr.copy()
            hdr_ca[..., 0] = map_coordinates(hdr[..., 0], r_coords, order=1, mode="nearest")
            hdr_ca[..., 2] = map_coordinates(hdr[..., 2], b_coords, order=1, mode="nearest")
            hdr = hdr_ca

        # 3. Natural 35mm lens vignetting
        u, v = self.u_grid()
        rx = (u - 0.5) * 2.0
        ry = (v - 0.5) * 2.0 * (self.height / self.width)
        dist2 = rx * rx + ry * ry
        vig = 1.0 - vignette_strength * np.clip(dist2, 0.0, 1.8) ** 1.35
        hdr *= np.clip(vig, 0.55, 1.0)[..., None]

        # 4. ACES Filmic Tone Mapping (Narkowicz 2015 fit)
        a = 2.51
        b = 0.03
        c = 2.43
        d = 0.59
        e = 0.14
        mapped = (hdr * (a * hdr + b)) / (hdr * (c * hdr + d) + e)
        mapped = np.clip(mapped, 0.0, 1.0)

        # 5. Subtle photographic color grading (slight shadow cool depth, warm golden highlights)
        lum_m = 0.2126 * mapped[..., 0] + 0.7152 * mapped[..., 1] + 0.0722 * mapped[..., 2]
        shadow_w = np.clip(1.0 - lum_m * 2.2, 0.0, 1.0)[..., None]
        high_w = np.clip((lum_m - 0.45) * 1.6, 0.0, 1.0)[..., None]
        mapped = mapped + shadow_w * np.array([-0.008, -0.002, 0.014], dtype=np.float32)
        mapped = mapped + high_w * np.array([0.012, 0.004, -0.008], dtype=np.float32)
        mapped = np.clip(mapped, 0.0, 1.0)

        # 6. Linear -> sRGB gamma encoding
        srgb = np.where(
            mapped <= 0.0031308,
            mapped * 12.92,
            1.055 * np.power(np.maximum(mapped, 1e-8), 1.0 / 2.4) - 0.055,
        )

        # 7. Subtle luminance-weighted sensor/film grain
        if grain_strength > 0.0:
            rng = np.random.default_rng(seed)
            grain = rng.normal(0.0, 1.0, size=(self.height, self.width, 1)).astype(np.float32)
            # Slightly colored fine chroma noise + mostly luminance noise
            chroma = rng.normal(0.0, 0.22, size=(self.height, self.width, 3)).astype(np.float32)
            weight = (0.35 + 0.65 * (1.0 - lum_m))[..., None]
            srgb = srgb + (grain + chroma) * grain_strength * weight

        srgb = np.clip(srgb, 0.0, 1.0)
        return (srgb * 255.0 + 0.5).astype(np.uint8)

    def save_png(self, path: str, **post_kwargs) -> None:
        rgb8 = self.apply_photographic_post(**post_kwargs)
        Image.fromarray(rgb8, mode="RGB").save(path, format="PNG", optimize=True)


def _solve_homography_2d(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """Compute 3x3 2D homography mapping 4 source points to 4 destination points."""
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A.append([-x, -y, -1.0, 0.0, 0.0, 0.0, u * x, u * y, u])
        A.append([0.0, 0.0, 0.0, -x, -y, -1.0, v * x, v * y, v])
    A_mat = np.asarray(A, dtype=np.float64)
    _, _, vt = np.linalg.svd(A_mat)
    H = vt[-1].reshape(3, 3)
    return H / H[2, 2]
