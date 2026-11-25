"""Pure 2D procedural noise utilities (v3)."""

from __future__ import annotations

import numpy as np


def _hash2(ix: np.ndarray, iy: np.ndarray, seed: int) -> np.ndarray:
    n = (
        ix.astype(np.int64) * 374761393
        + iy.astype(np.int64) * 668265263
        + int(seed) * 1442695041
    )
    n = (n ^ (n >> 13)) * 1274126177
    n = n ^ (n >> 16)
    return ((n & 0x7FFFFFFF).astype(np.float32)) / float(0x80000000)


def value_noise_2d(x: np.ndarray, y: np.ndarray, seed: int = 0) -> np.ndarray:
    ix = np.floor(x).astype(np.int64)
    iy = np.floor(y).astype(np.int64)
    fx = (x - ix).astype(np.float32)
    fy = (y - iy).astype(np.float32)

    ux = fx * fx * fx * (fx * (fx * 6.0 - 15.0) + 10.0)
    uy = fy * fy * fy * (fy * (fy * 6.0 - 15.0) + 10.0)

    v00 = _hash2(ix, iy, seed)
    v10 = _hash2(ix + 1, iy, seed)
    v01 = _hash2(ix, iy + 1, seed)
    v11 = _hash2(ix + 1, iy + 1, seed)

    vx0 = v00 + (v10 - v00) * ux
    vx1 = v01 + (v11 - v01) * ux
    return vx0 + (vx1 - vx0) * uy


def fbm_2d(
    x: np.ndarray,
    y: np.ndarray,
    octaves: int = 5,
    lacunarity: float = 2.08,
    gain: float = 0.5,
    seed: int = 0,
    rotate: bool = True,
) -> np.ndarray:
    val = np.zeros_like(x, dtype=np.float32)
    amp = 0.5
    norm = 0.0
    cx = x.astype(np.float32, copy=True)
    cy = y.astype(np.float32, copy=True)
    cos_a, sin_a = np.float32(0.8), np.float32(0.6)

    for i in range(octaves):
        val += amp * value_noise_2d(cx, cy, seed=seed + i * 101)
        norm += amp
        if rotate:
            nx = (cos_a * cx - sin_a * cy) * lacunarity + 17.3
            ny = (sin_a * cx + cos_a * cy) * lacunarity + 31.7
            cx, cy = nx, ny
        else:
            cx = cx * lacunarity + 13.7
            cy = cy * lacunarity + 29.1
        amp *= gain

    return val / max(norm, 1e-6)


def ridged_fbm_2d(
    x: np.ndarray,
    y: np.ndarray,
    octaves: int = 5,
    lacunarity: float = 2.12,
    gain: float = 0.5,
    seed: int = 0,
) -> np.ndarray:
    val = np.zeros_like(x, dtype=np.float32)
    amp = 0.5
    norm = 0.0
    cx = x.astype(np.float32, copy=True)
    cy = y.astype(np.float32, copy=True)
    cos_a, sin_a = np.float32(0.8), np.float32(0.6)

    for i in range(octaves):
        n = value_noise_2d(cx, cy, seed=seed + i * 137)
        ridge = 1.0 - np.abs(n * 2.0 - 1.0)
        val += amp * (ridge * ridge)
        norm += amp
        nx = (cos_a * cx - sin_a * cy) * lacunarity + 11.1
        ny = (sin_a * cx + cos_a * cy) * lacunarity + 23.9
        cx, cy = nx, ny
        amp *= gain

    return val / max(norm, 1e-6)


def smoothstep(
    edge0: np.ndarray | float,
    edge1: np.ndarray | float,
    x: np.ndarray | float,
) -> np.ndarray:
    diff = edge1 - edge0
    safe_diff = np.where(np.abs(diff) < 1e-6, 1e-6, diff)
    t = np.clip((x - edge0) / safe_diff, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)
