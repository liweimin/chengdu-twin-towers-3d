"""
Procedural 3D Architectural Mesh Generator for Chengdu Financial City Twin Towers at Dusk.
Generates watertight binary PLY meshes (positions, normals, UVs) for Mitsuba 3 path tracing:
  1. Tianfu International Financial Center Twin Towers (218m elliptical-spindle towers,
     micro-perturbed LOW-E glass panes, 3D "ice-flower" metallic filigree lattice,
     integrated LED louver strips, recessed office interiors, crowns & podiums)
  2. Jiaozi Ring Pedestrian Bridge (104m outer dia undulating vermilion-orange steel ring,
     folded-ribbon canopy ribs, 4 V-shaped inclined columns, glass balustrades, linear LEDs,
     and pedestrian silhouettes)
  3. Jiaozi Avenue & Yizhou Avenue streetscape (wet asphalt, sidewalks, granite curbs,
     70+ procedural 3D trees, modern streetlamps, long-exposure car light trails, 3D cars)
  4. Surrounding Chengdu Financial City CBD Skyline (34 diverse skyscrapers & illuminated
     street-level retail podiums)
"""

import os
import math
import struct
import numpy as np


class MeshBuilder:
    """Fast vectorized triangle mesh accumulator with binary PLY export."""

    def __init__(self):
        self.v_list = []
        self.n_list = []
        self.uv_list = []
        self.f_list = []
        self.v_count = 0

    def add_mesh(self, verts, faces, normals=None, uvs=None):
        verts = np.asarray(verts, dtype=np.float32)
        faces = np.asarray(faces, dtype=np.int32)
        if len(verts) == 0 or len(faces) == 0:
            return
        if normals is None:
            normals = self._compute_normals(verts, faces)
        else:
            normals = np.asarray(normals, dtype=np.float32)
        if uvs is None:
            uvs = np.zeros((len(verts), 2), dtype=np.float32)
        else:
            uvs = np.asarray(uvs, dtype=np.float32)

        self.v_list.append(verts)
        self.n_list.append(normals)
        self.uv_list.append(uvs)
        self.f_list.append(faces + self.v_count)
        self.v_count += len(verts)

    @staticmethod
    def _compute_normals(verts, faces):
        v0 = verts[faces[:, 0]]
        v1 = verts[faces[:, 1]]
        v2 = verts[faces[:, 2]]
        fn = np.cross(v1 - v0, v2 - v0)
        vn = np.zeros_like(verts, dtype=np.float32)
        np.add.at(vn, faces[:, 0], fn)
        np.add.at(vn, faces[:, 1], fn)
        np.add.at(vn, faces[:, 2], fn)
        lens = np.linalg.norm(vn, axis=1, keepdims=True)
        vn = np.where(lens > 1e-8, vn / np.maximum(lens, 1e-8), np.array([0.0, 1.0, 0.0], dtype=np.float32))
        return vn

    def add_quad(self, p0, p1, p2, p3, uv0=(0, 0), uv1=(1, 0), uv2=(1, 1), uv3=(0, 1), normal=None):
        verts = np.array([p0, p1, p2, p3], dtype=np.float32)
        faces = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.int32)
        uvs = np.array([uv0, uv1, uv2, uv3], dtype=np.float32)
        if normal is not None:
            n = np.asarray(normal, dtype=np.float32)
            n = n / max(np.linalg.norm(n), 1e-8)
            normals = np.tile(n, (4, 1))
        else:
            normals = None
        self.add_mesh(verts, faces, normals=normals, uvs=uvs)

    def add_box(self, cx, cy, cz, sx, sy, sz, yaw=0.0, uv_scale=None, uv_fit=False):
        """Add an oriented box centered at (cx, cy, cz) with full dimensions (sx, sy, sz)."""
        hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
        # 6 faces, 4 verts each (flat normals for crisp architectural edges!)
        face_defs = [
            # (+Z, -Z, +X, -X, +Y, -Y)
            ([(-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)], (0, 0, 1), sx, sy),
            ([(hx, -hy, -hz), (-hx, -hy, -hz), (-hx, hy, -hz), (hx, hy, -hz)], (0, 0, -1), sx, sy),
            ([(hx, -hy, hz), (hx, -hy, -hz), (hx, hy, -hz), (hx, hy, hz)], (1, 0, 0), sz, sy),
            ([(-hx, -hy, -hz), (-hx, -hy, hz), (-hx, hy, hz), (-hx, hy, -hz)], (-1, 0, 0), sz, sy),
            ([(-hx, hy, hz), (hx, hy, hz), (hx, hy, -hz), (-hx, hy, -hz)], (0, 1, 0), sx, sz),
            ([(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz)], (0, -1, 0), sx, sz),
        ]
        cyaw, syaw = math.cos(yaw), math.sin(yaw)
        all_v, all_n, all_uv, all_f = [], [], [], []
        idx = 0
        for pts, nrm, fw, fh in face_defs:
            for (x, y, z) in pts:
                rx = x * cyaw + z * syaw + cx
                rz = -x * syaw + z * cyaw + cz
                all_v.append((rx, y + cy, rz))
            nx = nrm[0] * cyaw + nrm[2] * syaw
            nz = -nrm[0] * syaw + nrm[2] * cyaw
            for _ in range(4):
                all_n.append((nx, nrm[1], nz))
            if uv_fit:
                u1, v1 = 1.0, 1.0
            elif uv_scale is not None:
                u1, v1 = fw / uv_scale[0], fh / uv_scale[1]
            else:
                u1, v1 = 1.0, 1.0
            all_uv.extend([(0.0, 0.0), (u1, 0.0), (u1, v1), (0.0, v1)])
            all_f.append((idx, idx + 1, idx + 2))
            all_f.append((idx, idx + 2, idx + 3))
            idx += 4
        self.add_mesh(all_v, all_f, all_n, all_uv)

    def add_strut(self, p0, p1, w=0.25, d=0.32, outward_hint=None):
        """Add a 3D rectangular-section structural beam/fin from p0 to p1."""
        p0 = np.asarray(p0, dtype=np.float32)
        p1 = np.asarray(p1, dtype=np.float32)
        axis = p1 - p0
        L = float(np.linalg.norm(axis))
        if L < 1e-4:
            return
        t = axis / L
        if outward_hint is None:
            up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
            if abs(np.dot(t, up)) > 0.95:
                up = np.array([1.0, 0.0, 0.0], dtype=np.float32)
            out = np.cross(t, up)
        else:
            out = np.asarray(outward_hint, dtype=np.float32)
            out = out - np.dot(out, t) * t
            if np.linalg.norm(out) < 1e-4:
                out = np.cross(t, np.array([0.0, 1.0, 0.0], dtype=np.float32))
        out = out / max(np.linalg.norm(out), 1e-8)
        side = np.cross(out, t)
        side = side / max(np.linalg.norm(side), 1e-8)

        hw, hd = w * 0.5, d * 0.5
        c0 = [p0 - side * hw - out * hd, p0 + side * hw - out * hd,
              p0 + side * hw + out * hd, p0 - side * hw + out * hd]
        c1 = [p1 - side * hw - out * hd, p1 + side * hw - out * hd,
              p1 + side * hw + out * hd, p1 - side * hw + out * hd]

        # 4 longitudinal faces with flat normals
        sides_n = [-out, side, out, -side]
        verts, norms, faces = [], [], []
        idx = 0
        for k in range(4):
            kn = (k + 1) % 4
            verts.extend([c0[k], c0[kn], c1[kn], c1[k]])
            norms.extend([sides_n[k]] * 4)
            faces.append((idx, idx + 1, idx + 2))
            faces.append((idx, idx + 2, idx + 3))
            idx += 4
        self.add_mesh(verts, faces, norms)

    def add_cylinder(self, p0, p1, r0, r1=None, segs=12):
        """Add a tapered cylinder / column from p0 to p1."""
        if r1 is None:
            r1 = r0
        p0 = np.asarray(p0, dtype=np.float32)
        p1 = np.asarray(p1, dtype=np.float32)
        axis = p1 - p0
        L = float(np.linalg.norm(axis))
        if L < 1e-4:
            return
        t = axis / L
        ref = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        if abs(np.dot(t, ref)) > 0.92:
            ref = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        u = np.cross(t, ref)
        u /= np.linalg.norm(u)
        v = np.cross(t, u)

        ang = np.linspace(0.0, 2.0 * np.pi, segs, endpoint=False, dtype=np.float32)
        ca, sa = np.cos(ang), np.sin(ang)
        dirs = ca[:, None] * u[None, :] + sa[:, None] * v[None, :]

        v0 = p0[None, :] + dirs * r0
        v1 = p1[None, :] + dirs * r1
        verts = np.vstack([v0, v1])
        norms = np.vstack([dirs, dirs])
        faces = []
        for i in range(segs):
            ni = (i + 1) % segs
            faces.append((i, ni, segs + ni))
            faces.append((i, segs + ni, segs + i))
        self.add_mesh(verts, faces, norms)

    def add_icosphere(self, center, radius, subdivisions=1, scale=(1.0, 1.0, 1.0), jitter=0.0, rng=None):
        """Add an organic sphere/foliage cluster."""
        phi = (1.0 + math.sqrt(5.0)) / 2.0
        verts = np.array([
            [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
            [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
            [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1],
        ], dtype=np.float32)
        verts /= np.linalg.norm(verts, axis=1, keepdims=True)
        faces = [
            (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
            (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
            (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
            (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
        ]
        for _ in range(subdivisions):
            mid_cache = {}
            v_list = list(verts)
            new_faces = []
            def get_mid(a, b):
                key = (min(a, b), max(a, b))
                if key not in mid_cache:
                    m = (v_list[a] + v_list[b]) * 0.5
                    m /= np.linalg.norm(m)
                    mid_cache[key] = len(v_list)
                    v_list.append(m)
                return mid_cache[key]
            for a, b, c in faces:
                ab = get_mid(a, b)
                bc = get_mid(b, c)
                ca = get_mid(c, a)
                new_faces.extend([(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)])
            verts = np.array(v_list, dtype=np.float32)
            faces = new_faces

        if jitter > 0.0 and rng is not None:
            r_mod = 1.0 + rng.uniform(-jitter, jitter, size=(len(verts), 1)).astype(np.float32)
            verts = verts * r_mod

        sc = np.array(scale, dtype=np.float32) * radius
        verts = verts * sc[None, :] + np.asarray(center, dtype=np.float32)[None, :]
        self.add_mesh(verts, np.array(faces, dtype=np.int32))

    def save_ply(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if self.v_count == 0:
            # Write minimal valid empty dummy triangle far away so Mitsuba never errors
            self.add_quad((0, -100, 0), (0.01, -100, 0), (0.01, -100, 0.01), (0, -100, 0.01))
        verts = np.vstack(self.v_list).astype(np.float32)
        norms = np.vstack(self.n_list).astype(np.float32)
        uvs = np.vstack(self.uv_list).astype(np.float32)
        faces = np.vstack(self.f_list).astype(np.int32)

        n_v = len(verts)
        n_f = len(faces)
        header = (
            "ply\n"
            "format binary_little_endian 1.0\n"
            f"element vertex {n_v}\n"
            "property float x\n"
            "property float y\n"
            "property float z\n"
            "property float nx\n"
            "property float ny\n"
            "property float nz\n"
            "property float u\n"
            "property float v\n"
            f"element face {n_f}\n"
            "property list uchar int vertex_indices\n"
            "end_header\n"
        ).encode("ascii")

        # Interleave vertex attributes (8 float32 per vertex)
        v_buf = np.empty((n_v, 8), dtype="<f4")
        v_buf[:, 0:3] = verts
        v_buf[:, 3:6] = norms
        v_buf[:, 6:8] = uvs

        # Pack faces: uchar(3) + 3 int32
        f_dtype = np.dtype([("cnt", "u1"), ("idx", "<i4", (3,))])
        f_buf = np.empty(n_f, dtype=f_dtype)
        f_buf["cnt"] = 3
        f_buf["idx"] = faces

        with open(path, "wb") as fp:
            fp.write(header)
            fp.write(v_buf.tobytes())
            fp.write(f_buf.tobytes())
        return n_v, n_f


# =============================================================================
# 1. CHENGDU FINANCIAL CITY TWIN TOWERS (天府国际金融中心双塔, 218m)
# =============================================================================

def _tower_profile_point(cx, cz, theta, y, H=218.0, rx_base=19.2, rz_base=13.0, radial_offset=0.0):
    """
    Evaluate 3D point & outward normal on the sculptural elliptical-spindle Twin Tower shell.
    Superellipse cross-section (p=2.6) + graceful vertical spindle taper (bulging mid-height,
    tapering cleanly toward base and crown).
    """
    t = np.clip(y / H, 0.0, 1.0)
    # Sculptural spindle scale: 0.91 at base -> 1.01 at mid -> 0.84 at crown
    s = 0.91 + 0.11 * np.sin(np.pi * (t ** 0.86)) - 0.075 * (t ** 2.6)
    rx = rx_base * s + radial_offset
    rz = rz_base * s + radial_offset

    # Superellipse exponent p=2.6 (smooth rounded elliptical-rectangular modern form)
    p = 2.6
    ct, st = np.cos(theta), np.sin(theta)
    ex = np.sign(ct) * (np.abs(ct) ** (2.0 / p))
    ez = np.sign(st) * (np.abs(st) ** (2.0 / p))

    x = cx + rx * ex
    z = cz + rz * ez

    # Approximate outward horizontal normal
    nx = np.sign(ct) * (np.abs(ct) ** (2.0 - 2.0 / p)) / max(rx, 1.0)
    nz = np.sign(st) * (np.abs(st) ** (2.0 - 2.0 / p)) / max(rz, 1.0)
    nlen = np.sqrt(nx * nx + nz * nz) + 1e-8
    return np.array([x, y, z], dtype=np.float32), np.array([nx / nlen, 0.0, nz / nlen], dtype=np.float32)


def build_twin_towers(mesh_dir="assets/meshes"):
    """Build both Twin Towers (North at x=-46, South at x=+46, z=+135, H=218m)."""
    rng = np.random.default_rng(2026)
    H = 218.0
    n_floors = 54
    n_bays = 48

    glass_mb = MeshBuilder()
    mullion_mb = MeshBuilder()
    iceflower_mb = MeshBuilder()
    interior_mb = MeshBuilder()
    crown_mb = MeshBuilder()
    podium_glass_mb = MeshBuilder()
    podium_stone_mb = MeshBuilder()
    podium_glow_mb = MeshBuilder()
    beacon_mb = MeshBuilder()

    led_mbs = {"north": MeshBuilder(), "south": MeshBuilder()}

    towers = [
        ("north", -42.0, 138.0),
        ("south", +42.0, 138.0),
    ]

    for label, cx, cz in towers:
        led_mb = led_mbs[label]
        ys = np.linspace(14.0, H, n_floors + 1)  # Podium spans y=0..16m
        # Angle convention: theta=-pi/2 -> -Z (facing camera/West!)
        # Make u=0.5 correspond to theta=-pi/2 (west center facing Jiaozi Ring)
        thetas = np.linspace(0.5 * np.pi, -1.5 * np.pi, n_bays + 1)

        # Precompute grid points on glass skin (offset=0.0) and ice-flower lattice (offset=+0.48m)
        G_pts = np.zeros((n_floors + 1, n_bays + 1, 3), dtype=np.float32)
        G_nrm = np.zeros((n_floors + 1, n_bays + 1, 3), dtype=np.float32)
        L_pts = np.zeros((n_floors + 1, n_bays + 1, 3), dtype=np.float32)
        I_pts = np.zeros((n_floors + 1, n_bays + 1, 3), dtype=np.float32)

        for fi, y in enumerate(ys):
            for bi, th in enumerate(thetas):
                p_g, n_g = _tower_profile_point(cx, cz, th, y, H=H, radial_offset=0.0)
                p_l, _ = _tower_profile_point(cx, cz, th, y, H=H, radial_offset=0.46)
                p_i, _ = _tower_profile_point(cx, cz, th, y, H=H, radial_offset=-1.25)
                G_pts[fi, bi] = p_g
                G_nrm[fi, bi] = n_g
                L_pts[fi, bi] = p_l
                I_pts[fi, bi] = p_i

        # --- Layer 1: Micro-Perturbed LOW-E Curtain Wall Glass Panes ---
        # Each individual pane gets a subtle independent normal tilt (+/- 0.5 deg) so
        # sunset reflections shimmer authentically like real architectural glass!
        for fi in range(n_floors):
            v0 = fi / n_floors
            v1 = (fi + 1) / n_floors
            for bi in range(n_bays):
                u0 = bi / n_bays
                u1 = (bi + 1) / n_bays
                p00 = G_pts[fi, bi]
                p10 = G_pts[fi, bi + 1]
                p11 = G_pts[fi + 1, bi + 1]
                p01 = G_pts[fi + 1, bi]

                n_avg = G_nrm[fi, bi] + G_nrm[fi, bi + 1] + G_nrm[fi + 1, bi] + G_nrm[fi + 1, bi + 1]
                n_avg /= max(np.linalg.norm(n_avg), 1e-8)
                # Micro normal perturbation (~0.009 rad ~ 0.5 deg)
                jitter_n = n_avg + rng.normal(0.0, 0.0085, size=3).astype(np.float32)
                jitter_n /= max(np.linalg.norm(jitter_n), 1e-8)

                glass_mb.add_quad(p00, p10, p11, p01, (u0, v0), (u1, v0), (u1, v1), (u0, v1), normal=jitter_n)

                # Recessed interior office cylinder
                ip00 = I_pts[fi, bi]
                ip10 = I_pts[fi, bi + 1]
                ip11 = I_pts[fi + 1, bi + 1]
                ip01 = I_pts[fi + 1, bi]
                interior_mb.add_quad(ip00, ip10, ip11, ip01, (u0, v0), (u1, v0), (u1, v1), (u0, v1), normal=n_avg)

        # --- Layer 2: Horizontal Spandrel Mullions & Vertical Structural Fins ---
        for fi in range(0, n_floors + 1, 1):
            for bi in range(n_bays):
                p0 = G_pts[fi, bi] + G_nrm[fi, bi] * 0.12
                p1 = G_pts[fi, bi + 1] + G_nrm[fi, bi + 1] * 0.12
                out = (G_nrm[fi, bi] + G_nrm[fi, bi + 1]) * 0.5
                # Thicker bands on mechanical refuge floors
                thick = 0.52 if fi in (14, 29, 43, n_floors) else 0.18
                mullion_mb.add_strut(p0, p1, w=thick, d=0.28, outward_hint=out)

        for bi in range(0, n_bays, 2):
            for fi in range(n_floors):
                p0 = G_pts[fi, bi] + G_nrm[fi, bi] * 0.14
                p1 = G_pts[fi + 1, bi] + G_nrm[fi + 1, bi] * 0.14
                mullion_mb.add_strut(p0, p1, w=0.16, d=0.26, outward_hint=G_nrm[fi, bi])

        # --- Layer 3: Signature 3D "Ice-Flower" (冰花) Metallic Aluminum Exoskeleton ---
        # Crystalline branching geometric filigree lattice standing proud of the glass skin!
        # Builds alternating diamond + Y-branch ice-crystal cells wrapped around the spindle!
        for fi in range(0, n_floors - 1, 2):
            for bi in range(0, n_bays, 2):
                b_next = (bi + 2) % n_bays
                b_mid = (bi + 1) % n_bays
                # Only need high-detail filigree everywhere (fast in Embree!)
                p_bl = L_pts[fi, bi]
                p_br = L_pts[fi, bi + 2]
                p_tr = L_pts[fi + 2, bi + 2]
                p_tl = L_pts[fi + 2, bi]
                p_c = L_pts[fi + 1, bi + 1]
                p_bm = L_pts[fi, bi + 1]
                p_tm = L_pts[fi + 2, bi + 1]
                p_ml = L_pts[fi + 1, bi]
                p_mr = L_pts[fi + 1, bi + 2]
                n_c = G_nrm[fi + 1, bi + 1]

                # Organic crystalline "ice-flower" pattern:
                # Staggered Voronoi-like Y-branches + crisp diagonal facets
                if ((fi // 2) + (bi // 2)) % 2 == 0:
                    # Star / Ice-flower diamond + central crystalline branches
                    iceflower_mb.add_strut(p_bm, p_ml, w=0.22, d=0.34, outward_hint=n_c)
                    iceflower_mb.add_strut(p_bm, p_mr, w=0.22, d=0.34, outward_hint=n_c)
                    iceflower_mb.add_strut(p_tm, p_ml, w=0.22, d=0.34, outward_hint=n_c)
                    iceflower_mb.add_strut(p_tm, p_mr, w=0.22, d=0.34, outward_hint=n_c)
                    # Inner crystalline cross-branch
                    iceflower_mb.add_strut(p_c, p_bl, w=0.14, d=0.22, outward_hint=n_c)
                    iceflower_mb.add_strut(p_c, p_tr, w=0.14, d=0.22, outward_hint=n_c)
                else:
                    # Complementary crystalline Y-lattice node
                    iceflower_mb.add_strut(p_bl, p_c, w=0.22, d=0.34, outward_hint=n_c)
                    iceflower_mb.add_strut(p_br, p_c, w=0.22, d=0.34, outward_hint=n_c)
                    iceflower_mb.add_strut(p_tl, p_c, w=0.22, d=0.34, outward_hint=n_c)
                    iceflower_mb.add_strut(p_tr, p_c, w=0.22, d=0.34, outward_hint=n_c)
                    iceflower_mb.add_strut(p_ml, p_mr, w=0.14, d=0.22, outward_hint=n_c)

        # --- Layer 4: Integrated Horizontal LED Media Louver Strips ---
        # Real thin horizontal emissive slats sitting at offset=+0.26m (just inside ice-flower
        # outer ribs, outside the glass) — 3 crisp louver strips per floor with open glass gaps!
        strips_per_floor = 3
        strip_h = 0.34  # 34cm crisp louver bar leaving generous dark reflective glass gaps!
        for fi in range(n_floors):
            y_base = ys[fi]
            y_next = ys[fi + 1]
            dy_f = y_next - y_base
            for si in range(strips_per_floor):
                ys0 = y_base + (si + 0.28) * (dy_f / strips_per_floor)
                ys1 = ys0 + strip_h
                v0 = (ys0 - 14.0) / (H - 14.0)
                v1 = (ys1 - 14.0) / (H - 14.0)
                for bi in range(n_bays):
                    u0 = bi / n_bays
                    u1 = (bi + 1) / n_bays
                    th0, th1 = thetas[bi], thetas[bi + 1]
                    q00, n0 = _tower_profile_point(cx, cz, th0, ys0, H=H, radial_offset=0.26)
                    q10, n1 = _tower_profile_point(cx, cz, th1, ys0, H=H, radial_offset=0.26)
                    q11, _ = _tower_profile_point(cx, cz, th1, ys1, H=H, radial_offset=0.26)
                    q01, _ = _tower_profile_point(cx, cz, th0, ys1, H=H, radial_offset=0.26)
                    navg = (n0 + n1) * 0.5
                    led_mb.add_quad(q00, q10, q11, q01, (u0, v0), (u1, v0), (u1, v1), (u0, v1), normal=navg)

        # --- Layer 5: Architectural Crown, Crisp Brushed Cornice & Aviation Beacons ---
        # Crisp horizontal metallic crown flange + recessed dark louver penthouse
        for bi in range(n_bays):
            th0, th1 = thetas[bi], thetas[bi + 1]
            p0, n0 = _tower_profile_point(cx, cz, th0, H - 1.2, H=H, radial_offset=0.58)
            p1, n1 = _tower_profile_point(cx, cz, th1, H - 1.2, H=H, radial_offset=0.58)
            p0t, _ = _tower_profile_point(cx, cz, th0, H + 1.8, H=H, radial_offset=0.42)
            p1t, _ = _tower_profile_point(cx, cz, th1, H + 1.8, H=H, radial_offset=0.42)
            crown_mb.add_quad(p0, p1, p1t, p0t, normal=(n0 + n1) * 0.5)
            # Flat crisp architectural top cap
            p0i, _ = _tower_profile_point(cx, cz, th0, H + 1.8, H=H, radial_offset=-2.5)
            p1i, _ = _tower_profile_point(cx, cz, th1, H + 1.8, H=H, radial_offset=-2.5)
            crown_mb.add_quad(p0t, p1t, p1i, p0i, normal=(0, 1, 0))
            # Dark recessed crown vertical fin band
            if bi % 2 == 0:
                mullion_mb.add_strut(p0, p0t + np.array([0, 0.8, 0], dtype=np.float32), w=0.22, d=0.35, outward_hint=n0)

        # Recessed rooftop mechanical core
        mullion_mb.add_box(cx, H + 1.8, cz, 20.0, 3.8, 12.0)
        # Red aviation obstruction beacons on twin corners of each crown
        beacon_mb.add_icosphere((cx - 10.5, H + 3.2, cz), 0.36, subdivisions=1)
        beacon_mb.add_icosphere((cx + 10.5, H + 3.2, cz), 0.36, subdivisions=1)

        # --- Layer 6: Sculptural 4-Story Glazed & Granite Podium ---
        # Modern cantilevered podium flanking tower base (y=0..16.5m) with crisp multi-floor mullions!
        podium_stone_mb.add_box(cx, 1.2, cz - 2.0, 58.0, 2.4, 42.0)  # Granite plinth
        podium_glass_mb.add_box(cx, 8.8, cz - 2.0, 54.0, 12.6, 36.0)  # Glazed podium body
        podium_glow_mb.add_box(cx, 8.2, cz - 2.0, 51.5, 10.6, 33.5)   # Warm golden lobby core
        # Sleek overhanging canopy slabs & horizontal floor spandrels (breaks lobby into 3 crisp stories!)
        podium_stone_mb.add_box(cx, 15.6, cz - 3.5, 60.0, 1.4, 42.0)
        podium_stone_mb.add_box(cx, 11.2, cz - 20.3, 54.5, 0.75, 1.2)
        podium_stone_mb.add_box(cx, 6.8, cz - 20.3, 54.5, 0.75, 1.2)
        podium_stone_mb.add_box(cx, 5.2, cz - 22.0, 32.0, 0.65, 6.5)   # Entrance drop-off canopy
        # Exterior vertical stone/metal colonnade fins around podium
        for px_off in np.linspace(-25.5, 25.5, 16):
            podium_stone_mb.add_box(cx + px_off, 8.8, cz - 20.4, 0.65, 13.8, 1.2)

    # Grand connecting central low plaza bridge / terrace between North & South towers
    podium_stone_mb.add_box(0.0, 1.2, 132.0, 54.0, 2.4, 34.0)
    podium_stone_mb.add_box(0.0, 6.2, 142.0, 48.0, 1.0, 16.0)

    out = {}
    for name, mb in [
        ("tower_glass", glass_mb),
        ("tower_mullions", mullion_mb),
        ("tower_iceflower", iceflower_mb),
        ("tower_interior", interior_mb),
        ("tower_led_north", led_mbs["north"]),
        ("tower_led_south", led_mbs["south"]),
        ("tower_crown", crown_mb),
        ("podium_glass", podium_glass_mb),
        ("podium_stone", podium_stone_mb),
        ("podium_glow", podium_glow_mb),
        ("tower_beacons", beacon_mb),
    ]:
        p = os.path.join(mesh_dir, f"{name}.ply")
        nv, nf = mb.save_ply(p)
        out[name] = p
        print(f"  [TwinTowers] {name}: {nv} verts, {nf} tris")
    return out


# =============================================================================
# 2. JIAOZI RING PEDESTRIAN BRIDGE (交子之环 — 104m Vermilion-Orange Iconic Ring)
# =============================================================================

def _ring_deck_y(phi):
    """Graceful undulating elevation profile of Jiaozi Ring (6.6m to 9.3m above avenue)."""
    # Higher graceful crests over Jiaozi Avenue (phi=0 east, phi=pi west) and gentle dips at sides
    return 7.6 + 1.15 * math.cos(2.0 * phi) + 0.35 * math.sin(3.0 * phi + 0.4)


def build_jiaozi_ring(mesh_dir="assets/meshes", center_z=-90.0):
    """
    Build the iconic '交子之环' (Jiaozi Ring) circular pedestrian overpass spanning
    Jiaozi Avenue x Yizhou Avenue directly west of the Twin Towers.
    """
    rng = np.random.default_rng(1024)
    r_in = 41.5
    r_out = 51.5
    r_mid = 0.5 * (r_in + r_out)
    n_seg = 168

    steel_mb = MeshBuilder()
    deck_mb = MeshBuilder()
    glass_mb = MeshBuilder()
    led_mb = MeshBuilder()
    ped_mb = MeshBuilder()

    phis = np.linspace(0.0, 2.0 * np.pi, n_seg + 1)

    # Cross-section profile of the sculpted orange-red steel ring girder (relative to r_mid, y_deck)
    # Aerodynamic curved soffit tapering cleanly toward crisp outer & inner rims!
    # Profile points (dr, dy): goes around outer rim -> soffit underside -> inner rim
    profile = [
        (+5.15, +0.25),   # Outer upper fascia edge
        (+5.35, -0.15),   # Outer aerodynamic nose
        (+4.40, -0.82),   # Outer curved soffit
        (+2.20, -1.42),   # Mid-outer soffit belly
        (0.00,  -1.62),   # Center keel deepest point
        (-2.20, -1.42),   # Mid-inner soffit belly
        (-4.40, -0.82),   # Inner curved soffit
        (-5.35, -0.15),   # Inner aerodynamic nose
        (-5.15, +0.25),   # Inner upper fascia edge
    ]
    n_prof = len(profile)

    # Extrude ring steel girder smoothly
    ring_v = np.zeros((n_seg + 1, n_prof, 3), dtype=np.float32)
    for i, phi in enumerate(phis):
        yc = _ring_deck_y(phi)
        cp, sp = math.cos(phi), math.sin(phi)
        for j, (dr, dy) in enumerate(profile):
            rr = r_mid + dr
            # Ring lies in X-Z plane centered at (0, 0, center_z)
            # phi=0 -> +Z (East toward Twin Towers), phi=pi -> -Z (West near camera)
            ring_v[i, j] = (rr * sp, yc + dy, center_z + rr * cp)

    verts, faces = [], []
    for i in range(n_seg):
        for j in range(n_prof - 1):
            p00 = ring_v[i, j]
            p10 = ring_v[i + 1, j]
            p11 = ring_v[i + 1, j + 1]
            p01 = ring_v[i, j + 1]
            steel_mb.add_quad(p00, p01, p11, p10)

    # Top pedestrian deck surface (warm architectural timber/stone paving)
    for i in range(n_seg):
        phi0, phi1 = phis[i], phis[i + 1]
        y0, y1 = _ring_deck_y(phi0), _ring_deck_y(phi1)
        c0, s0 = math.cos(phi0), math.sin(phi0)
        c1, s1 = math.cos(phi1), math.sin(phi1)
        p_in0 = (r_in * s0, y0 + 0.05, center_z + r_in * c0)
        p_ou0 = (r_out * s0, y0 + 0.05, center_z + r_out * c0)
        p_ou1 = (r_out * s1, y1 + 0.05, center_z + r_out * c1)
        p_in1 = (r_in * s1, y1 + 0.05, center_z + r_in * c1)
        deck_mb.add_quad(p_in0, p_ou0, p_ou1, p_in1, normal=(0, 1, 0))

        # Inner & outer glass balustrades (height 1.25m) + sleek metallic handrail cap
        for r_rail, sgn in [(r_in + 0.15, -1.0), (r_out - 0.15, +1.0)]:
            g0 = (r_rail * s0, y0 + 0.25, center_z + r_rail * c0)
            g1 = (r_rail * s1, y1 + 0.25, center_z + r_rail * c1)
            g2 = (r_rail * s1, y1 + 1.48, center_z + r_rail * c1)
            g3 = (r_rail * s0, y0 + 1.48, center_z + r_rail * c0)
            n_r = (sgn * (s0 + s1) * 0.5, 0.0, sgn * (c0 + c1) * 0.5)
            glass_mb.add_quad(g0, g1, g2, g3, normal=n_r)
            # Crisp orange-steel top handrail bar
            steel_mb.add_strut(g3, g2, w=0.14, d=0.14, outward_hint=n_r)

        # Continuous glowing warm linear LED strips along outer rim, inner rim & soffit edge!
        for r_led, dy_led, w_led in [
            (r_mid + 5.38, -0.05, 0.16),   # Outer sculptural edge rim light
            (r_mid - 5.38, -0.05, 0.16),   # Inner sculptural edge rim light
            (r_mid + 3.40, -1.18, 0.14),   # Outer underside soffit linear wash
            (r_mid - 3.40, -1.18, 0.14),   # Inner underside soffit linear wash
        ]:
            l0 = (r_led * s0, y0 + dy_led, center_z + r_led * c0)
            l1 = (r_led * s1, y1 + dy_led, center_z + r_led * c1)
            n_l = ((s0 + s1) * 0.5, -0.3, (c0 + c1) * 0.5)
            led_mb.add_strut(l0, l1, w=w_led, d=w_led, outward_hint=n_l)

    # --- Signature Undulating "Folded Jiaozi" Wind-Rain Canopy & Ribbed Arches ---
    # Sweeping sculptural vermilion-orange steel canopy arches along both sides of the ring!
    canopy_segments = []
    for i in range(n_seg + 1):
        phi = phis[i]
        # Canopy height undulates gracefully like a folded paper ribbon (higher on left/right sides,
        # lower sleek open viewing terrace facing straight east/west so Twin Towers aren't blocked!)
        wave = 0.5 - 0.5 * math.cos(2.0 * phi)  # 0 at phi=0,pi (avenue center); 1 at phi=pi/2,3pi/2 (sides)
        h_canopy = 2.6 + 3.2 * (wave ** 0.85)
        y_base = _ring_deck_y(phi)
        cp, sp = math.cos(phi), math.sin(phi)
        # Outer rib foot, outer canopy crest, inner canopy edge
        p_foot = np.array([(r_out + 0.15) * sp, y_base + 0.15, center_z + (r_out + 0.15) * cp], dtype=np.float32)
        p_top_out = np.array([(r_out + 0.45) * sp, y_base + h_canopy, center_z + (r_out + 0.45) * cp], dtype=np.float32)
        p_top_in = np.array([(r_mid - 1.2 + 2.4 * (1.0 - wave)) * sp, y_base + h_canopy + 0.55, center_z + (r_mid - 1.2 + 2.4 * (1.0 - wave)) * cp], dtype=np.float32)
        canopy_segments.append((wave, p_foot, p_top_out, p_top_in, np.array([sp, 0.0, cp], dtype=np.float32)))

    # Extrude continuous sculptural canopy roof ribbon where wave > 0.12
    for i in range(n_seg):
        w0, f0, to0, ti0, n0 = canopy_segments[i]
        w1, f1, to1, ti1, n1 = canopy_segments[i + 1]
        if w0 > 0.12 or w1 > 0.12:
            # Tapered canopy roof skin (top + underside)
            steel_mb.add_quad(to0, to1, ti1, ti0, normal=(0, 1, 0))
            off = np.array([0.0, -0.32, 0.0], dtype=np.float32)
            steel_mb.add_quad(ti0 + off, ti1 + off, to1 + off, to0 + off, normal=(0, -1, 0))
            steel_mb.add_quad(to0 + off, to1 + off, to1, to0, normal=(n0 + n1) * 0.5)
            steel_mb.add_quad(ti1 + off, ti0 + off, ti0, ti1, normal=-(n0 + n1) * 0.5)
            # Glowing warm underside strip along inner canopy fascia
            led_mb.add_strut(ti0 + off * 0.8, ti1 + off * 0.8, w=0.12, d=0.12, outward_hint=(0, -1, 0))

        # Sculptural curved structural portal ribs every 3 segments
        if i % 3 == 0 and w0 > 0.15:
            # Curved arch rib from outer deck edge up to canopy crest and over to inner lip
            p_mid = 0.5 * (f0 + to0) + n0 * 0.45
            steel_mb.add_strut(f0, p_mid, w=0.34, d=0.45, outward_hint=n0)
            steel_mb.add_strut(p_mid, to0, w=0.34, d=0.45, outward_hint=n0)
            steel_mb.add_strut(to0, ti0, w=0.30, d=0.38, outward_hint=(0, 1, 0))

    # --- 4 Iconic Sculptural V-Shaped Inclined Steel Support Columns ---
    # Positioned neatly on the 4 plaza quadrants of the intersection (not blocking traffic lanes!)
    for corner_deg in (42.0, 138.0, 222.0, 318.0):
        phi_c = math.radians(corner_deg)
        cp, sp = math.cos(phi_c), math.sin(phi_c)
        base_r = r_mid + 1.5
        p_base = np.array([base_r * sp, -0.3, center_z + base_r * cp], dtype=np.float32)

        # Two splayed V-arms reaching up to grip the ring girder +-9 deg along circumference
        for d_deg in (-9.5, +9.5):
            phi_a = math.radians(corner_deg + d_deg)
            ya = _ring_deck_y(phi_a) - 1.25
            ca, sa = math.cos(phi_a), math.sin(phi_a)
            p_top = np.array([r_mid * sa, ya, center_z + r_mid * ca], dtype=np.float32)
            # Tapered bold orange-red architectural steel column arm
            steel_mb.add_cylinder(p_base, p_top, r0=1.05, r1=0.78, segs=16)

        # Concrete/granite plinth collar at column base
        deck_mb.add_cylinder(p_base, p_base + np.array([0, 0.85, 0], dtype=np.float32), r0=1.65, r1=1.45, segs=16)

    # --- Human Scale: Pedestrian Silhouettes strolling / photographing along Jiaozi Ring ---
    for _ in range(52):
        phi = rng.uniform(0.0, 2.0 * np.pi)
        rr = rng.uniform(r_in + 1.1, r_out - 1.1)
        y_p = _ring_deck_y(phi) + 0.05
        px = rr * math.sin(phi)
        pz = center_z + rr * math.cos(phi)
        h_person = rng.uniform(1.62, 1.82)
        # Torso + legs + head silhouette (clean simple sculptural figure)
        ped_mb.add_cylinder((px, y_p, pz), (px, y_p + h_person * 0.80, pz), r0=0.22, r1=0.18, segs=8)
        ped_mb.add_icosphere((px, y_p + h_person * 0.90, pz), 0.13, subdivisions=1)

    out = {}
    for name, mb in [
        ("jiaozi_steel", steel_mb),
        ("jiaozi_deck", deck_mb),
        ("jiaozi_glass", glass_mb),
        ("jiaozi_leds", led_mb),
        ("jiaozi_pedestrians", ped_mb),
    ]:
        p = os.path.join(mesh_dir, f"{name}.ply")
        nv, nf = mb.save_ply(p)
        out[name] = p
        print(f"  [JiaoziRing] {name}: {nv} verts, {nf} tris")
    return out


# =============================================================================
# 3. JIAOZI AVENUE STREETSCAPE, TREES, STREETLAMPS, CARS & LIGHT TRAILS
# =============================================================================

def build_streetscape(mesh_dir="assets/meshes", ring_z=-90.0):
    rng = np.random.default_rng(888)
    road_mb = MeshBuilder()
    sidewalk_mb = MeshBuilder()
    trunk_mb = MeshBuilder()
    foliage_mb = MeshBuilder()
    pole_mb = MeshBuilder()
    lamp_bulb_mb = MeshBuilder()
    trail_w_mb = MeshBuilder()
    trail_r_mb = MeshBuilder()
    car_body_mb = MeshBuilder()
    car_glass_mb = MeshBuilder()
    car_head_mb = MeshBuilder()
    car_tail_mb = MeshBuilder()

    # --- Road Surface: Jiaozi Avenue (East-West along Z) ---
    # Tiled every 60m along Z so our high-res wet asphalt & lane markings stay razor sharp!
    road_w = 48.0  # X in [-24, +24]
    z_min, z_max = -320.0, 140.0
    tile_len = 60.0
    z_cur = z_min
    while z_cur < z_max:
        z_next = min(z_cur + tile_len, z_max)
        v1 = (z_next - z_cur) / tile_len
        road_mb.add_quad(
            (-road_w * 0.5, 0.0, z_cur),
            (+road_w * 0.5, 0.0, z_cur),
            (+road_w * 0.5, 0.0, z_next),
            (-road_w * 0.5, 0.0, z_next),
            (0.0, 0.0), (1.0, 0.0), (1.0, v1), (0.0, v1),
            normal=(0, 1, 0),
        )
        z_cur = z_next

    # Intersecting Yizhou Avenue (North-South along X, centered at z = ring_z)
    cross_w = 40.0
    for x0, x1 in [(-240.0, -24.0), (+24.0, +240.0)]:
        n_tiles = max(1, int(round((x1 - x0) / 60.0)))
        xs = np.linspace(x0, x1, n_tiles + 1)
        for i in range(n_tiles):
            road_mb.add_quad(
                (xs[i], -0.01, ring_z - cross_w * 0.5),
                (xs[i], -0.01, ring_z + cross_w * 0.5),
                (xs[i + 1], -0.01, ring_z + cross_w * 0.5),
                (xs[i + 1], -0.01, ring_z - cross_w * 0.5),
                (0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0),
                normal=(0, 1, 0),
            )

    # Wide urban ground plane & paved granite plazas / sidewalks flanking the avenues
    # Raised sidewalks (+0.22m above asphalt) with crisp curbs!
    for sx_sign in (-1.0, +1.0):
        # West of intersection (z in [-320, ring_z - 22])
        sidewalk_mb.add_box(sx_sign * 134.0, 0.11, (-320.0 + (ring_z - 22.0)) * 0.5, 220.0, 0.22, (ring_z - 22.0) - (-320.0))
        # East of intersection toward Twin Towers (z in [ring_z + 22, +220])
        sidewalk_mb.add_box(sx_sign * 134.0, 0.11, ((ring_z + 22.0) + 220.0) * 0.5, 220.0, 0.22, 220.0 - (ring_z + 22.0))
    # Grand ground plane behind Twin Towers so horizon never leaks
    sidewalk_mb.add_box(0.0, -0.05, 420.0, 1400.0, 0.10, 600.0)
    sidewalk_mb.add_box(0.0, -0.15, 0.0, 1600.0, 0.10, 1200.0)

    # Central landscaped avenue median strips (except inside the Jiaozi Ring intersection!)
    for z0, z1 in [(-290.0, ring_z - 32.0), (ring_z + 32.0, 110.0)]:
        sidewalk_mb.add_box(0.0, 0.18, 0.5 * (z0 + z1), 2.4, 0.36, z1 - z0)

    # --- Procedural 3D Boulevard Trees (Lush Camphor & Ginkgo Street Trees) ---
    tree_positions = []
    # Lining both sides of Jiaozi Avenue
    for z_t in np.arange(-225.0, 115.0, 15.5):
        # Skip crossing Yizhou Ave intersection zone
        if abs(z_t - ring_z) < 28.0:
            continue
        tree_positions.append((-27.5, z_t))
        tree_positions.append((+27.5, z_t))
        # Second row of lush plaza trees slightly set back
        if int(abs(z_t)) % 2 == 0:
            tree_positions.append((-36.0, z_t + 6.0))
            tree_positions.append((+36.0, z_t + 6.0))

    # Central median ornamental shrubs/small trees
    for z_t in np.arange(-210.0, 102.0, 19.0):
        if abs(z_t - ring_z) < 36.0:
            continue
        tree_positions.append((0.0, z_t))

    # Plaza cluster trees framing the 4 Jiaozi Ring plaza quadrants & lower corners
    for sx in (-1.0, +1.0):
        for sz in (-1.0, +1.0):
            for k in range(7):
                tx = sx * rng.uniform(34.0, 74.0)
                tz = ring_z + sz * rng.uniform(34.0, 68.0)
                if math.hypot(tx, tz - ring_z) > 54.0 and tz > -185.0:
                    tree_positions.append((tx, tz))

    for (tx, tz) in tree_positions:
        is_median = abs(tx) < 2.0
        # Keep immediate foreground camera view clean of oversized canopy clutter
        if tz < -215.0:
            continue
        h_tree = rng.uniform(3.8, 5.0) if is_median else rng.uniform(6.0, 8.8)
        r_trunk = 0.12 if is_median else rng.uniform(0.16, 0.24)
        trunk_top = np.array([tx + rng.uniform(-0.18, 0.18), h_tree * 0.54, tz + rng.uniform(-0.18, 0.18)], dtype=np.float32)
        trunk_mb.add_cylinder((tx, 0.2, tz), trunk_top, r0=r_trunk, r1=r_trunk * 0.58, segs=6)

        # Fine botanical branching + 28-40 jagged overlapping leaf-cluster sprigs (NOT smooth clay balls!)
        n_branches = 5 if not is_median else 3
        for bi in range(n_branches):
            ang = bi * (2.0 * np.pi / n_branches) + rng.uniform(-0.35, 0.35)
            blen = h_tree * rng.uniform(0.28, 0.44)
            b_end = trunk_top + np.array([
                math.cos(ang) * blen * 0.78,
                blen * rng.uniform(0.45, 0.88),
                math.sin(ang) * blen * 0.78,
            ], dtype=np.float32)
            trunk_mb.add_cylinder(trunk_top, b_end, r0=r_trunk * 0.40, r1=r_trunk * 0.14, segs=5)
            # Sub-twigs & fine organic foliage sprigs around each branch
            n_sprigs = 7 if not is_median else 4
            for _ in range(n_sprigs):
                off = rng.normal(0.0, 0.85 if not is_median else 0.48, size=3).astype(np.float32)
                off[1] *= 0.65
                s_rad = rng.uniform(0.42, 0.82) if not is_median else rng.uniform(0.32, 0.55)
                foliage_mb.add_icosphere(
                    b_end + off,
                    s_rad, subdivisions=0, scale=(1.15, 0.72, 1.15), jitter=0.36, rng=rng
                )

    # --- Sleek Modern Architectural Streetlights along Jiaozi Avenue ---
    for z_l in np.arange(-220.0, 115.0, 26.0):
        if abs(z_l - ring_z) < 25.0:
            continue
        for sx in (-1.0, +1.0):
            px = sx * 24.4
            h_pole = 9.4
            pole_mb.add_cylinder((px, 0.2, z_l), (px, h_pole, z_l), r0=0.14, r1=0.075, segs=8)
            # Sleek cantilevered arm curving slightly over the outer traffic lane
            arm_end = (px - sx * 2.6, h_pole + 0.35, z_l)
            pole_mb.add_strut((px, h_pole - 0.1, z_l), arm_end, w=0.11, d=0.14)
            # Luminaire housing & intense warm LED emitter plate facing downward
            pole_mb.add_box(arm_end[0], arm_end[1] + 0.06, arm_end[2], 0.95, 0.12, 0.38)
            lamp_bulb_mb.add_box(arm_end[0], arm_end[1] - 0.03, arm_end[2], 0.82, 0.06, 0.28)

    # Warm pedestrian plaza light bollards around the Jiaozi Ring plaza & sidewalks
    for sx in (-1.0, +1.0):
        for z_b in np.arange(-172.0, 88.0, 18.0):
            if abs(z_b - ring_z) < 26.0:
                continue
            bx = sx * 33.5
            pole_mb.add_cylinder((bx, 0.2, z_b), (bx, 3.6, z_b), r0=0.08, r1=0.06, segs=6)
            lamp_bulb_mb.add_icosphere((bx, 3.72, z_b), 0.16, subdivisions=0)
    # Plaza ring perimeter warm uplight bollards (56m radius circle around Jiaozi Ring)
    for deg_b in np.linspace(18, 342, 16):
        rad_b = math.radians(deg_b)
        bx = 58.0 * math.sin(rad_b)
        bz = ring_z + 58.0 * math.cos(rad_b)
        if abs(bx) > 26.0 and abs(bz - ring_z) > 22.0:
            pole_mb.add_cylinder((bx, 0.2, bz), (bx, 3.2, bz), r0=0.07, r1=0.06, segs=6)
            lamp_bulb_mb.add_icosphere((bx, 3.32, bz), 0.15, subdivisions=0)
    # Smooth flowing ribbon streams running along all 6 lanes of Jiaozi Avenue + curving on Yizhou Ave!
    # Right-hand traffic in China:
    #   Eastbound (+Z, heading away from camera toward Twin Towers) -> Right side of road (+X or -X?)
    #   Wait: camera looks toward +Z, up=+Y. In right-handed coords, +Z x +Y = -X (so -X is RIGHT on screen, +X is LEFT on screen!).
    #   Wait: let's make RIGHT side of frame (-X) = Eastbound (heading toward Twin Towers -> glowing RUBY TAILLIGHTS!)
    #   and LEFT side of frame (+X) = Westbound (coming toward camera -> glowing WARM-WHITE HEADLIGHTS!)
    #   Let's double-check that! In China (right-hand drive), cars moving AWAY from you are on the RIGHT side of the road -> you see their RED TAILLIGHTS on the right! Cars moving TOWARD you are on the LEFT side of the road -> you see their WHITE HEADLIGHTS on the left!
    def add_light_trail(mb, pts, radius=0.085):
        for i in range(len(pts) - 1):
            mb.add_strut(pts[i], pts[i + 1], w=radius * 2.0, d=radius * 2.0, outward_hint=(0, 1, 0))

    # Eastbound lanes (right side of frame, X in [-18, -5.5]) -> RUBY RED TAILLIGHTS
    eb_lanes = [-17.2, -12.0, -6.8]
    for lane_idx, lx in enumerate(eb_lanes):
        # Slight organic lane weave for natural photographic feel
        zs = np.linspace(-235.0, 108.0, 65)
        weave = 0.28 * np.sin(zs * 0.025 + lane_idx * 1.9)
        y_tail = 0.84 + 0.06 * (lane_idx % 2)
        for dx_lamp in (-0.76, +0.76):
            pts = [(lx + weave[k] + dx_lamp, y_tail, zs[k]) for k in range(len(zs))]
            # Break trails gently into long sweeping streaks (2-3s shutter exposure look!)
            for seg_start, seg_end in [(0, 26), (30, 56), (58, 65)]:
                add_light_trail(trail_r_mb, pts[seg_start:seg_end], radius=0.052)

    # Westbound lanes (left side of frame, X in [+5.5, +18]) -> WARM-WHITE/PALE-GOLD HEADLIGHTS
    wb_lanes = [+6.8, +12.0, +17.2]
    for lane_idx, lx in enumerate(wb_lanes):
        zs = np.linspace(-235.0, 108.0, 65)
        weave = 0.25 * np.cos(zs * 0.022 + lane_idx * 2.1)
        y_head = 0.72 + 0.05 * (lane_idx % 2)
        for dx_lamp in (-0.74, +0.74):
            pts = [(lx + weave[k] + dx_lamp, y_head, zs[k]) for k in range(len(zs))]
            for seg_start, seg_end in [(2, 32), (35, 62)]:
                add_light_trail(trail_w_mb, pts[seg_start:seg_end], radius=0.054)

    # Subtle broken cross-street light trails tucked neatly beneath Jiaozi Ring (Yizhou Ave)
    for side_s, mb_t, z_off in [(-1.0, trail_r_mb, -8.0), (+1.0, trail_w_mb, +8.0)]:
        xs = np.linspace(-52.0, 52.0, 28)
        for dz_l in (-0.68, +0.68):
            pts = [(xs[k], 0.76, ring_z + z_off + dz_l) for k in range(len(xs))]
            add_light_trail(mb_t, pts[2:11], radius=0.036)
            add_light_trail(mb_t, pts[16:26], radius=0.036)

    # Graceful curved turning light trail bending underneath Jiaozi Ring!
    t_arc = np.linspace(0.0, 0.5 * np.pi, 20)
    r_turn = 24.0
    for dl in (-0.68, +0.68):
        pts_arc = [(-22.0 - r_turn + (r_turn + dl) * math.cos(a), 0.78, ring_z - 22.0 - r_turn + (r_turn + dl) * math.sin(a)) for a in t_arc]
        add_light_trail(trail_r_mb, pts_arc, radius=0.040)

    # --- Sculpted 3D Evening Vehicles (Slow/Stopped at Intersection for Realism) ---
    car_specs = [
        # (x, z, yaw, is_eastbound)
        (-12.0, -148.0, 0.0, True),
        (-6.8,  -125.0, 0.02, True),
        (-17.2, -55.0, -0.01, True),
        (-12.0, -20.0, 0.0, True),
        (-6.8,  +38.0, 0.0, True),
        (-17.2, +68.0, 0.0, True),
        (+6.8,  -152.0, math.pi, False),
        (+12.0, -118.0, math.pi - 0.02, False),
        (+17.2, -48.0, math.pi, False),
        (+12.0, +18.0, math.pi, False),
        (+6.8,  +55.0, math.pi, False),
        (-42.0, ring_z - 8.0, 0.5 * math.pi, True),
        (+38.0, ring_z + 8.0, -0.5 * math.pi, False),
    ]
    for (cx, cz, cyaw, is_eb) in car_specs:
        L, W, Hc = rng.uniform(4.4, 4.9), rng.uniform(1.82, 1.96), rng.uniform(1.38, 1.62)
        # Lower body + tapered cabin
        car_body_mb.add_box(cx, 0.56, cz, W, 0.72, L, yaw=cyaw)
        car_glass_mb.add_box(cx, 0.56 + 0.55, cz - 0.15 * math.cos(cyaw), W * 0.86, Hc * 0.42, L * 0.54, yaw=cyaw)
        # Headlights & Taillights
        fwd = np.array([math.sin(cyaw), 0.0, math.cos(cyaw)], dtype=np.float32)
        rt = np.array([math.cos(cyaw), 0.0, -math.sin(cyaw)], dtype=np.float32)
        for s_lr in (-0.68, +0.68):
            p_f = np.array([cx, 0.68, cz]) + fwd * (L * 0.505) + rt * s_lr
            p_b = np.array([cx, 0.76, cz]) - fwd * (L * 0.505) + rt * s_lr
            car_head_mb.add_box(p_f[0], p_f[1], p_f[2], 0.34, 0.16, 0.08, yaw=cyaw)
            car_tail_mb.add_box(p_b[0], p_b[1], p_b[2], 0.38, 0.14, 0.08, yaw=cyaw)

    out = {}
    for name, mb in [
        ("road_surface", road_mb),
        ("sidewalks", sidewalk_mb),
        ("tree_trunks", trunk_mb),
        ("tree_foliage", foliage_mb),
        ("streetlamp_poles", pole_mb),
        ("streetlamp_bulbs", lamp_bulb_mb),
        ("light_trails_white", trail_w_mb),
        ("light_trails_red", trail_r_mb),
        ("car_bodies", car_body_mb),
        ("car_glass", car_glass_mb),
        ("car_headlights", car_head_mb),
        ("car_taillights", car_tail_mb),
    ]:
        p = os.path.join(mesh_dir, f"{name}.ply")
        nv, nf = mb.save_ply(p)
        out[name] = p
        print(f"  [Street] {name}: {nv} verts, {nf} tris")
    return out


# =============================================================================
# 4. SURROUNDING CHENGDU FINANCIAL CITY CBD SKYLINE (34 Diverse Skyscrapers)
# =============================================================================

def build_cbd_skyline(mesh_dir="assets/meshes"):
    """
    Build surrounding Chengdu Financial City skyscrapers flanking Jiaozi Avenue and
    receding behind the Twin Towers into the Sichuan basin dusk haze.
    """
    rng = np.random.default_rng(4096)
    style_mbs = [MeshBuilder() for _ in range(4)]
    fin_mb = MeshBuilder()
    retail_mb = MeshBuilder()

    # Curated architectural masterplan (x, z, w, d, h, style_idx, yaw, has_setback, has_fins)
    # Remember: -X is RIGHT of frame, +X is LEFT of frame, +Z is EAST (toward Twin Towers at x=+-46, z=135)
    # Keep Jiaozi Ave corridor (x in [-45, +45], z < 115) & Twin Tower silhouette completely clean!
    buildings = [
        # --- Left side of Jiaozi Avenue (+X, North Financial City block — organic asymmetric heights!) ---
        (+96,  -155, 34, 28, 92,  0, 0.0,  True,  True),
        (+94,  -16,  38, 32, 136, 1, 0.0,  True,  True),
        (+98,  +52,  34, 30, 118, 2, 0.0,  False, True),
        (+138, -90,  38, 34, 158, 3, 0.04, True,  False),
        (+146, +18,  42, 34, 142, 0, 0.0,  True,  True),
        (+150, +94,  38, 36, 128, 1, 0.0,  True,  True),
        (+126, +154, 36, 32, 134, 2, 0.0,  False, True),
        (+190, -40,  44, 38, 116, 1, 0.0,  True,  False),
        (+204, +70,  46, 40, 148, 0, 0.0,  True,  True),

        # --- Right side of Jiaozi Avenue (-X, South Financial City block / Intime side — varied skyline!) ---
        (-96,  -152, 34, 30, 102, 1, 0.0,  True,  True),
        (-94,  -12,  38, 32, 152, 0, 0.0,  True,  True),
        (-98,  +56,  36, 30, 124, 3, 0.0,  True,  True),
        (-140, -86,  40, 34, 132, 2, -0.04, True, False),
        (-148, +22,  42, 36, 168, 1, 0.0,  True,  True),
        (-148, +100, 38, 34, 136, 0, 0.0,  False, True),
        (-128, +158, 36, 34, 126, 3, 0.0,  True,  False),
        (-194, -34,  46, 38, 124, 2, 0.0,  True,  False),
        (-204, +76,  44, 40, 144, 1, 0.0,  True,  True),

        # --- Mid-rise street-front commercial podiums along Jiaozi Avenue (east of Jiaozi Ring!) ---
        (+58,  -18,  22, 32, 22,  3, 0.0,  False, False),
        (+58,  +44,  22, 34, 24,  1, 0.0,  False, False),
        (-58,  -16,  22, 32, 23,  3, 0.0,  False, False),
        (-58,  +48,  22, 34, 21,  0, 0.0,  False, False),

        # --- Distant Eastern Chengdu Financial City / Jinjiang Backdrop Skyline (z = +210..+420m) ---
        # Deliberately lower than the 218m Twin Towers so Twin Towers stand majestically above!
        (-210, +235, 44, 38, 135, 0, 0.05, True,  False),
        (-145, +260, 40, 36, 128, 2, 0.0,  False, False),
        (-78,  +295, 38, 34, 118, 1, 0.0,  True,  False),
        (-18,  +325, 42, 36, 108, 0, 0.0,  False, False),
        (+45,  +310, 40, 34, 116, 2, 0.0,  True,  False),
        (+112, +275, 42, 36, 132, 1, 0.0,  True,  False),
        (+178, +245, 46, 38, 146, 0, -0.04, True, False),
        (-265, +175, 50, 42, 115, 3, 0.0,  False, False),
        (+265, +175, 50, 42, 122, 2, 0.0,  False, False),
        (0,    +410, 56, 38, 96,  1, 0.0,  False, False),
    ]

    for (bx, bz, bw, bd, bh, style_idx, yaw, has_setback, has_fins) in buildings:
        mb = style_mbs[style_idx]
        if has_setback and bh > 60.0:
            h1 = bh * 0.72
            h2 = bh - h1
            mb.add_box(bx, h1 * 0.5, bz, bw, h1, bd, yaw=yaw, uv_fit=True)
            mb.add_box(bx, h1 + h2 * 0.5, bz, bw * 0.80, h2, bd * 0.80, yaw=yaw, uv_fit=True)
            # Rooftop architectural crown frame & mechanical penthouse
            fin_mb.add_box(bx, bh + 1.8, bz, bw * 0.82, 3.6, bd * 0.82, yaw=yaw)
            fin_mb.add_box(bx, bh + 4.2, bz, bw * 0.45, 3.2, bd * 0.45, yaw=yaw)
        else:
            mb.add_box(bx, bh * 0.5, bz, bw, bh, bd, yaw=yaw, uv_fit=True)
            fin_mb.add_box(bx, bh + 1.2, bz, bw * 1.02, 2.4, bd * 1.02, yaw=yaw)

        # Architectural vertical metal/stone facade fins on hero flanking buildings!
        if has_fins and bh > 80.0 and abs(bz) < 180.0:
            n_f = max(5, int(bw / 4.2))
            for fx in np.linspace(-bw * 0.46, bw * 0.46, n_f):
                # Front (camera-facing -Z) vertical ribs
                fin_mb.add_box(bx + fx, bh * 0.38, bz - bd * 0.505, 0.45, bh * 0.76, 0.65, yaw=yaw)
            # Horizontal architectural belt courses
            for fy in (bh * 0.33, bh * 0.66):
                fin_mb.add_box(bx, fy, bz, bw * 1.02, 1.1, bd * 1.02, yaw=yaw)

        # Warm glowing street-level commercial retail/cafe vitrines (only along inner avenue east of ring!)
        if abs(bx) < 88.0 and -45.0 < bz < 80.0:
            side_in = -1.0 if bx > 0 else +1.0
            rx = bx + side_in * (bw * 0.5 + 0.12)
            # Divided storefront bays instead of one solid glowing block
            for z_off in np.linspace(-bd * 0.36, bd * 0.36, 4):
                retail_mb.add_box(rx, 2.6, bz + z_off, 0.20, 3.6, bd * 0.16, yaw=yaw)

    out = {}
    for idx, mb in enumerate(style_mbs):
        p = os.path.join(mesh_dir, f"cbd_style_{idx}.ply")
        nv, nf = mb.save_ply(p)
        out[f"cbd_style_{idx}"] = p
        print(f"  [CBD] cbd_style_{idx}: {nv} verts, {nf} tris")

    for name, mb in [("cbd_fins", fin_mb), ("cbd_retail_glow", retail_mb)]:
        p = os.path.join(mesh_dir, f"{name}.ply")
        nv, nf = mb.save_ply(p)
        out[name] = p
        print(f"  [CBD] {name}: {nv} verts, {nf} tris")
    return out


def build_all_geometry(mesh_dir="assets/meshes"):
    os.makedirs(mesh_dir, exist_ok=True)
    print("Building procedural 3D architectural geometry...")
    m = {}
    m.update(build_twin_towers(mesh_dir))
    m.update(build_jiaozi_ring(mesh_dir))
    m.update(build_streetscape(mesh_dir))
    m.update(build_cbd_skyline(mesh_dir))
    print(f"Finished building all {len(m)} architectural mesh layers in {mesh_dir}/")
    return m


if __name__ == "__main__":
    build_all_geometry()
