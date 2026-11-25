"""Pure 2D linear-HDR painting canvas with fast stroke stamping and DSLR optics (v3)."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, map_coordinates


class Canvas2D:
    """2D linear-HDR painting canvas (H, W, 3) float32."""

    def __init__(self, width: int, height: int):
        self.width = int(width)
        self.height = int(height)
        self.img = np.zeros((self.height, self.width, 3), dtype=np.float32)

    def u_grid(self) -> tuple[np.ndarray, np.ndarray]:
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
        cx = cx_norm * self.width
        cy = cy_norm * self.height
        rx = max(radius_x_norm * self.width, 0.7)
        ry = max(radius_y_norm * self.height, 0.7)

        x0 = max(0, int(np.floor(cx - rx * 3.2)))
        x1 = min(self.width, int(np.ceil(cx + rx * 3.2)) + 1)
        y0 = max(0, int(np.floor(cy - ry * 3.2)))
        y1 = min(self.height, int(np.ceil(cy + ry * 3.2)) + 1)
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
            falloff *= np.clip(1.0 - d2 / 10.0, 0.0, 1.0)

        col = np.array(color, dtype=np.float32)[None, None, :]
        self.img[y0:y1, x0:x1] += col * falloff[..., None]

    def rasterize_polygon_mask(
        self,
        pts_norm: list[tuple[float, float]],
        supersample: int = 2,
    ) -> tuple[np.ndarray, int, int]:
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

    def fill_polygon(
        self,
        pts_norm: list[tuple[float, float]],
        color: tuple[float, float, float],
        alpha: float = 1.0,
        supersample: int = 2,
    ) -> None:
        mask, x0, y0 = self.rasterize_polygon_mask(pts_norm, supersample=supersample)
        if mask.size == 0:
            return
        col = np.array(color, dtype=np.float32)[None, None, :]
        self.blend_over(col, mask * float(alpha), y0=y0, x0=x0)

    def draw_line(
        self,
        p0: tuple[float, float],
        p1: tuple[float, float],
        width_px: float,
        color: tuple[float, float, float],
        alpha: float = 1.0,
        additive: bool = False,
    ) -> None:
        ax, ay = p0[0] * self.width, p0[1] * self.height
        bx, by = p1[0] * self.width, p1[1] * self.height
        r = max(width_px * 0.5, 0.45)
        pad = int(np.ceil(r + 2.5))
        x0 = max(0, int(np.floor(min(ax, bx))) - pad)
        x1 = min(self.width, int(np.ceil(max(ax, bx))) + pad + 1)
        y0 = max(0, int(np.floor(min(ay, by))) - pad)
        y1 = min(self.height, int(np.ceil(max(ay, by))) + pad + 1)
        if x1 <= x0 or y1 <= y0:
            return

        xs = np.arange(x0, x1, dtype=np.float32)
        ys = np.arange(y0, y1, dtype=np.float32)
        xx, yy = np.meshgrid(xs, ys)
        abx, aby = bx - ax, by - ay
        ab2 = abx * abx + aby * aby + 1e-6
        proj = np.clip(((xx - ax) * abx + (yy - ay) * aby) / ab2, 0.0, 1.0)
        dist = np.sqrt((xx - (ax + proj * abx)) ** 2 + (yy - (ay + proj * aby)) ** 2)
        mask = np.clip(1.0 - (dist - r) / 1.05, 0.0, 1.0) * float(alpha)

        col = np.array(color, dtype=np.float32)[None, None, :]
        if additive:
            self.add_light(col, mask, y0=y0, x0=x0)
        else:
            self.blend_over(col, mask, y0=y0, x0=x0)

    def paint_quad_texture(
        self,
        quad_norm: list[tuple[float, float]],
        texture_rgb: np.ndarray,
        alpha: float | np.ndarray = 1.0,
        additive: bool = False,
    ) -> None:
        dst_pts = np.array(
            [(p[0] * self.width, p[1] * self.height) for p in quad_norm],
            dtype=np.float64,
        )
        th, tw = texture_rgb.shape[:2]
        src_pts = np.array(
            [(0.0, 0.0), (tw - 1.0, 0.0), (tw - 1.0, th - 1.0), (0.0, th - 1.0)],
            dtype=np.float64,
        )
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
        width_start_px: float,
        width_end_px: float,
        color_start: tuple[float, float, float],
        color_end: tuple[float, float, float],
        steps: int = 120,
        additive: bool = True,
    ) -> None:
        t = np.linspace(0.0, 1.0, steps, dtype=np.float32)
        mt = 1.0 - t
        xs = (
            mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
        ) * self.width
        ys = (
            mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
        ) * self.height
        rs = np.maximum(width_start_px * (1.0 - t) + width_end_px * t, 0.45)

        pad = int(np.ceil(float(rs.max()) * 3.2))
        x0 = max(0, int(np.floor(xs.min())) - pad)
        x1 = min(self.width, int(np.ceil(xs.max())) + pad + 1)
        y0 = max(0, int(np.floor(ys.min())) - pad)
        y1 = min(self.height, int(np.ceil(ys.max())) + pad + 1)
        if x1 <= x0 or y1 <= y0:
            return

        gx = np.arange(x0, x1, dtype=np.float32)
        gy = np.arange(y0, y1, dtype=np.float32)
        c0 = np.array(color_start, dtype=np.float32)
        c1 = np.array(color_end, dtype=np.float32)

        patch = np.zeros((y1 - y0, x1 - x0, 3), dtype=np.float32)
        w_acc = np.zeros((y1 - y0, x1 - x0), dtype=np.float32)

        for i in range(steps - 1):
            ax, ay = xs[i], ys[i]
            bx, by = xs[i + 1], ys[i + 1]
            r = 0.5 * (rs[i] + rs[i + 1])
            sx0 = max(x0, int(np.floor(min(ax, bx) - r * 3.0)))
            sx1 = min(x1, int(np.ceil(max(ax, bx) + r * 3.0)) + 1)
            sy0 = max(y0, int(np.floor(min(ay, by) - r * 3.0)))
            sy1 = min(y1, int(np.ceil(max(ay, by) + r * 3.0)) + 1)
            if sx1 <= sx0 or sy1 <= sy0:
                continue

            xx, yy = np.meshgrid(gx[sx0 - x0 : sx1 - x0], gy[sy0 - y0 : sy1 - y0])
            abx, aby = bx - ax, by - ay
            ab2 = abx * abx + aby * aby + 1e-6
            proj = np.clip(((xx - ax) * abx + (yy - ay) * aby) / ab2, 0.0, 1.0)
            d2 = (xx - (ax + proj * abx)) ** 2 + (yy - (ay + proj * aby)) ** 2
            val = np.exp(-d2 / (2.0 * r * r))

            ti = 0.5 * (t[i] + t[i + 1])
            col = c0 * (1.0 - ti) + c1 * ti
            sl = (slice(sy0 - y0, sy1 - y0), slice(sx0 - x0, sx1 - x0))
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
        exposure: float = 1.02,
        bloom_strength: float = 0.13,
        vignette_strength: float = 0.20,
        grain_strength: float = 0.011,
        ca_pixels: float = 0.40,
        sharpen_amount: float = 0.22,
        seed: int = 42,
    ) -> np.ndarray:
        """DSLR optical post-processing: micro-sharpening, restrained bloom, natural filmic curve & grain."""
        hdr = np.maximum(self.img, 0.0) * float(exposure)
        scale = self.width / 1600.0

        # 1. Restrained multi-scale optical bloom ONLY on genuinely bright light sources (> 0.85)
        luma = 0.2126 * hdr[..., 0] + 0.7152 * hdr[..., 1] + 0.0722 * hdr[..., 2]
        bright_mask = np.clip((luma - 0.85) / 1.5, 0.0, 4.0)
        bright = hdr * bright_mask[..., None]

        b1 = np.stack([gaussian_filter(bright[..., c], sigma=max(1.2, 2.4 * scale)) for c in range(3)], axis=-1)
        b2 = np.stack([gaussian_filter(bright[..., c], sigma=max(4.0, 9.5 * scale)) for c in range(3)], axis=-1)
        b3 = np.stack([gaussian_filter(bright[..., c], sigma=max(11.0, 26.0 * scale)) for c in range(3)], axis=-1)
        hdr = hdr + bloom_strength * (0.50 * b1 + 0.32 * b2 + 0.18 * b3)

        # 2. Subtle lateral chromatic aberration
        if ca_pixels > 0.0:
            u, v = self.u_grid()
            dx = (u - 0.5) * 2.0
            dy = (v - 0.5) * 2.0
            shift = ca_pixels * scale * (dx * dx + dy * dy)
            yy, xx = np.mgrid[0 : self.height, 0 : self.width].astype(np.float32)
            r_coords = np.array([yy - dy * shift * 0.5, xx - dx * shift * 0.5])
            b_coords = np.array([yy + dy * shift * 0.5, xx + dx * shift * 0.5])
            hdr_ca = hdr.copy()
            hdr_ca[..., 0] = map_coordinates(hdr[..., 0], r_coords, order=1, mode="nearest")
            hdr_ca[..., 2] = map_coordinates(hdr[..., 2], b_coords, order=1, mode="nearest")
            hdr = hdr_ca

        # 3. Natural wide-angle lens vignetting
        u, v = self.u_grid()
        rx = (u - 0.5) * 2.0
        ry = (v - 0.5) * 2.0 * (self.height / self.width)
        vig = 1.0 - vignette_strength * np.clip(rx * rx + ry * ry, 0.0, 1.8) ** 1.45
        hdr *= np.clip(vig, 0.65, 1.0)[..., None]

        # 4. ACES Filmic Tone Mapping
        a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
        mapped = np.clip((hdr * (a * hdr + b)) / (hdr * (c * hdr + d) + e), 0.0, 1.0)

        # 5. Linear -> sRGB
        srgb = np.where(
            mapped <= 0.0031308,
            mapped * 12.92,
            1.055 * np.power(np.maximum(mapped, 1e-8), 1.0 / 2.4) - 0.055,
        )

        # 6. Subtle DSLR optical micro-sharpening (unsharp mask for crisp architectural & leaf detail!)
        if sharpen_amount > 0.0:
            blurred = np.stack([gaussian_filter(srgb[..., ch], sigma=max(0.7, 0.9 * scale)) for ch in range(3)], axis=-1)
            srgb = np.clip(srgb + sharpen_amount * (srgb - blurred), 0.0, 1.0)

        # 7. Authentic ISO-400 DSLR sensor grain (luminance + subtle chroma)
        if grain_strength > 0.0:
            rng = np.random.default_rng(seed)
            lum_s = 0.2126 * srgb[..., 0] + 0.7152 * srgb[..., 1] + 0.0722 * srgb[..., 2]
            grain = rng.normal(0.0, 1.0, size=(self.height, self.width, 1)).astype(np.float32)
            chroma = rng.normal(0.0, 0.18, size=(self.height, self.width, 3)).astype(np.float32)
            weight = (0.35 + 0.65 * (1.0 - lum_s))[..., None]
            srgb = srgb + (grain + chroma) * grain_strength * weight

        srgb = np.clip(srgb, 0.0, 1.0)
        return (srgb * 255.0 + 0.5).astype(np.uint8)

    def save_png(self, path: str, **post_kwargs) -> None:
        rgb8 = self.apply_photographic_post(**post_kwargs)
        Image.fromarray(rgb8, mode="RGB").save(path, format="PNG", optimize=True)


def _solve_homography_2d(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A.append([-x, -y, -1.0, 0.0, 0.0, 0.0, u * x, u * y, u])
        A.append([0.0, 0.0, 0.0, -x, -y, -1.0, v * x, v * y, v])
    A_mat = np.asarray(A, dtype=np.float64)
    _, _, vt = np.linalg.svd(A_mat)
    H = vt[-1].reshape(3, 3)
    return H / H[2, 2]
