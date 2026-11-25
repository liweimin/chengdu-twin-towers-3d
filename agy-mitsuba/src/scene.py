"""
Mitsuba 3 Physically-Based Scene Assembler for《成都金融城双塔黄昏》.
Uses Python-native Unicode-safe file loading into Mitsuba 3 in-memory `mi.Mesh`
and `mi.Bitmap` objects (works cleanly on any Windows path including non-ASCII folders).
"""

import os
import numpy as np
from PIL import Image
import mitsuba as mi


def _load_png_bitmap(png_path, linear_scale=None, gamma=2.2, grayscale=False):
    """Load a PNG via PIL (Unicode-safe) and return a Mitsuba mi.Bitmap."""
    if grayscale:
        arr = np.asarray(Image.open(png_path).convert("L"), dtype=np.float32) / 255.0
        return mi.Bitmap(arr)
    arr = np.asarray(Image.open(png_path).convert("RGB"), dtype=np.float32) / 255.0
    if linear_scale is not None:
        arr = np.power(np.clip(arr, 0.0, 1.0), gamma) * float(linear_scale)
    return mi.Bitmap(arr)


def _load_ply_mesh(name, ply_path, bsdf_obj, emitter_obj=None):
    """Read binary PLY written by MeshBuilder (Unicode-safe) into a native Mitsuba mi.Mesh."""
    n_v = 0
    n_f = 0
    with open(ply_path, "rb") as fp:
        while True:
            line = fp.readline().decode("ascii").strip()
            if line.startswith("element vertex "):
                n_v = int(line.split()[-1])
            elif line.startswith("element face "):
                n_f = int(line.split()[-1])
            elif line == "end_header":
                break
        v_raw = np.frombuffer(fp.read(n_v * 8 * 4), dtype="<f4").reshape(n_v, 8)
        f_dtype = np.dtype([("cnt", "u1"), ("idx", "<i4", (3,))])
        f_raw = np.frombuffer(fp.read(n_f * f_dtype.itemsize), dtype=f_dtype)

    verts = np.ascontiguousarray(v_raw[:, 0:3], dtype=np.float32)
    norms = np.ascontiguousarray(v_raw[:, 3:6], dtype=np.float32)
    uvs = np.ascontiguousarray(v_raw[:, 6:8], dtype=np.float32)
    faces = np.ascontiguousarray(f_raw["idx"], dtype=np.uint32)

    props = mi.Properties()
    if bsdf_obj is not None:
        props["bsdf"] = bsdf_obj
    if emitter_obj is not None:
        props["emitter"] = emitter_obj

    mesh = mi.Mesh(name, n_v, n_f, props, True, True)
    params = mi.traverse(mesh)
    params["vertex_positions"] = verts.ravel()
    params["vertex_normals"] = norms.ravel()
    params["vertex_texcoords"] = uvs.ravel()
    params["faces"] = faces.ravel()
    params.update()
    return mesh


def build_mitsuba_scene(
    width=1280,
    height=720,
    spp=32,
    max_depth=6,
    assets_dir="assets",
    cam_origin=(-8.5, 25.5, -248.0),
    cam_target=(0.0, 96.0, 138.0),
    cam_fov=67.5,
    sky_scale=0.92,
    sky_yaw_deg=6.0,
    tower_led_scale=4.6,
    tower_interior_scale=2.8,
    cbd_emis_scale=2.4,
    jiaozi_led_scale=6.4,
    streetlamp_scale=24.0,
    trail_white_scale=11.5,
    trail_red_scale=16.5,
):
    mi.set_variant("scalar_rgb")
    mesh_dir = os.path.join(assets_dir, "meshes")

    # Load HDR twilight sky array
    sky_arr = np.load(os.path.join(assets_dir, "dusk_sky.npy")).astype(np.float32)
    sky_bmp = mi.Bitmap(sky_arr)

    # Load PBR & linear HDR emission bitmaps
    led_n_bmp = _load_png_bitmap(os.path.join(assets_dir, "tower_led_north.png"), linear_scale=tower_led_scale)
    led_s_bmp = _load_png_bitmap(os.path.join(assets_dir, "tower_led_south.png"), linear_scale=tower_led_scale)
    int_bmp = _load_png_bitmap(os.path.join(assets_dir, "tower_interior.png"), linear_scale=tower_interior_scale)
    road_alb_bmp = _load_png_bitmap(os.path.join(assets_dir, "road_albedo.png"))
    road_rgh_bmp = _load_png_bitmap(os.path.join(assets_dir, "road_roughness.png"), grayscale=True)

    # Instantiate shared BSDF objects
    mats = {
        "tower_glass": mi.load_dict({
            "type": "blendbsdf",
            "weight": 0.28,
            "bsdf_0": {"type": "thindielectric", "int_ior": 1.62, "ext_ior": 1.0},
            "bsdf_1": {
                "type": "roughconductor",
                "alpha": 0.08,
                "eta": {"type": "rgb", "value": [0.16, 0.22, 0.34]},
                "k": {"type": "rgb", "value": [1.8, 2.2, 2.8]},
            },
        }),
        "iceflower_alu": mi.load_dict({
            "type": "roughconductor",
            "distribution": "ggx",
            "alpha": 0.30,
            "eta": {"type": "rgb", "value": [1.15, 1.18, 1.24]},
            "k": {"type": "rgb", "value": [5.4, 5.5, 5.9]},
        }),
        "mullion_dark": mi.load_dict({
            "type": "principled",
            "base_color": {"type": "rgb", "value": [0.06, 0.07, 0.09]},
            "metallic": 0.75,
            "roughness": 0.34,
        }),
        "crown_metal": mi.load_dict({
            "type": "principled",
            "base_color": {"type": "rgb", "value": [0.58, 0.60, 0.65]},
            "metallic": 0.88,
            "roughness": 0.22,
        }),
        "podium_stone": mi.load_dict({
            "type": "principled",
            "base_color": {"type": "rgb", "value": [0.14, 0.14, 0.15]},
            "roughness": 0.38,
            "specular": 0.55,
        }),
        "jiaozi_orange": mi.load_dict({
            "type": "principled",
            "base_color": {"type": "rgb", "value": [0.84, 0.17, 0.055]},
            "metallic": 0.18,
            "roughness": 0.28,
            "clearcoat": 0.45,
            "clearcoat_gloss": 0.72,
        }),
        "jiaozi_deck": mi.load_dict({
            "type": "principled",
            "base_color": {"type": "rgb", "value": [0.22, 0.19, 0.17]},
            "roughness": 0.52,
        }),
        "ring_glass": mi.load_dict({
            "type": "thindielectric",
            "int_ior": 1.52,
            "ext_ior": 1.0,
        }),
        "road_asphalt": mi.load_dict({
            "type": "principled",
            "base_color": {"type": "bitmap", "bitmap": road_alb_bmp, "wrap_mode": "repeat"},
            "roughness": {"type": "bitmap", "bitmap": road_rgh_bmp, "wrap_mode": "repeat", "raw": True},
            "specular": 0.65,
            "clearcoat": 0.22,
            "clearcoat_gloss": 0.82,
        }),
        "sidewalk": mi.load_dict({
            "type": "principled",
            "base_color": {"type": "rgb", "value": [0.11, 0.115, 0.125]},
            "roughness": 0.36,
            "specular": 0.45,
        }),
        "tree_trunk": mi.load_dict({
            "type": "diffuse",
            "reflectance": {"type": "rgb", "value": [0.07, 0.055, 0.045]},
        }),
        "tree_foliage": mi.load_dict({
            "type": "principled",
            "base_color": {"type": "rgb", "value": [0.024, 0.052, 0.024]},
            "roughness": 0.80,
            "specular": 0.08,
        }),
        "pole_dark": mi.load_dict({
            "type": "principled",
            "base_color": {"type": "rgb", "value": [0.08, 0.085, 0.095]},
            "metallic": 0.80,
            "roughness": 0.32,
        }),
        "pedestrian": mi.load_dict({
            "type": "diffuse",
            "reflectance": {"type": "rgb", "value": [0.05, 0.05, 0.06]},
        }),
        "car_body": mi.load_dict({
            "type": "principled",
            "base_color": {"type": "rgb", "value": [0.04, 0.045, 0.055]},
            "metallic": 0.65,
            "roughness": 0.16,
            "clearcoat": 0.85,
            "clearcoat_gloss": 0.92,
        }),
        "car_glass": mi.load_dict({
            "type": "roughconductor",
            "alpha": 0.04,
            "eta": {"type": "rgb", "value": [0.12, 0.14, 0.18]},
            "k": {"type": "rgb", "value": [1.5, 1.7, 2.0]},
        }),
        "cbd_fins": mi.load_dict({
            "type": "principled",
            "base_color": {"type": "rgb", "value": [0.22, 0.23, 0.26]},
            "metallic": 0.55,
            "roughness": 0.32,
        }),
        "dark_emit_base": mi.load_dict({
            "type": "diffuse",
            "reflectance": {"type": "rgb", "value": [0.08, 0.08, 0.10]},
        }),
    }

    for i in range(4):
        alb = _load_png_bitmap(os.path.join(assets_dir, f"cbd_albedo_{i}.png"))
        rgh = _load_png_bitmap(os.path.join(assets_dir, f"cbd_rough_{i}.png"), grayscale=True)
        mats[f"cbd_{i}"] = mi.load_dict({
            "type": "principled",
            "base_color": {"type": "bitmap", "bitmap": alb, "wrap_mode": "repeat"},
            "roughness": {"type": "bitmap", "bitmap": rgh, "wrap_mode": "repeat", "raw": True},
            "metallic": 0.35,
            "specular": 0.65,
        })

    def make_rgb_emitter(rgb):
        return mi.load_dict({"type": "area", "radiance": {"type": "rgb", "value": list(rgb)}})

    def make_bmp_emitter(bmp):
        return mi.load_dict({"type": "area", "radiance": {"type": "bitmap", "bitmap": bmp, "raw": True}})

    scene_dict = {
        "type": "scene",
        "integrator": {
            "type": "path",
            "max_depth": max_depth,
            "rr_depth": 4,
            "hide_emitters": False,
        },
        "sensor": {
            "type": "perspective",
            "fov": cam_fov,
            "fov_axis": "x",
            "near_clip": 0.5,
            "far_clip": 2500.0,
            "to_world": mi.ScalarTransform4f().look_at(
                origin=list(cam_origin),
                target=list(cam_target),
                up=[0.0, 1.0, 0.0],
            ),
            "sampler": {
                "type": "independent",
                "sample_count": spp,
            },
            "film": {
                "type": "hdrfilm",
                "width": width,
                "height": height,
                "pixel_format": "rgb",
                "rfilter": {"type": "gaussian", "stddev": 0.55},
            },
        },
        "env_sky": {
            "type": "envmap",
            "bitmap": sky_bmp,
            "scale": sky_scale,
            "to_world": mi.ScalarTransform4f().rotate([0.0, 1.0, 0.0], sky_yaw_deg),
        },
        "sun_key": {
            "type": "directional",
            "direction": [-0.52, -0.14, 0.842],
            "irradiance": {"type": "rgb", "value": [0.42, 0.17, 0.075]},
        },
    }

    def add_mesh(key, ply_name, mat_key, emitter=None):
        scene_dict[key] = _load_ply_mesh(key, os.path.join(mesh_dir, ply_name), mats[mat_key], emitter)

    # 1. Twin Towers
    add_mesh("sh_tower_glass", "tower_glass.ply", "tower_glass")
    add_mesh("sh_tower_mullions", "tower_mullions.ply", "mullion_dark")
    add_mesh("sh_tower_iceflower", "tower_iceflower.ply", "iceflower_alu")
    add_mesh("sh_tower_crown", "tower_crown.ply", "crown_metal")
    add_mesh("sh_tower_interior", "tower_interior.ply", "dark_emit_base", make_bmp_emitter(int_bmp))
    add_mesh("sh_tower_led_north", "tower_led_north.ply", "dark_emit_base", make_bmp_emitter(led_n_bmp))
    add_mesh("sh_tower_led_south", "tower_led_south.ply", "dark_emit_base", make_bmp_emitter(led_s_bmp))
    add_mesh("sh_podium_glass", "podium_glass.ply", "tower_glass")
    add_mesh("sh_podium_stone", "podium_stone.ply", "podium_stone")
    add_mesh("sh_podium_glow", "podium_glow.ply", "dark_emit_base", make_rgb_emitter([1.85, 1.08, 0.44]))
    add_mesh("sh_tower_beacons", "tower_beacons.ply", "dark_emit_base", make_rgb_emitter([60.0, 3.0, 1.5]))

    # 2. Jiaozi Ring
    add_mesh("sh_jiaozi_steel", "jiaozi_steel.ply", "jiaozi_orange")
    add_mesh("sh_jiaozi_deck", "jiaozi_deck.ply", "jiaozi_deck")
    add_mesh("sh_jiaozi_glass", "jiaozi_glass.ply", "ring_glass")
    add_mesh("sh_jiaozi_peds", "jiaozi_pedestrians.ply", "pedestrian")
    add_mesh(
        "sh_jiaozi_leds", "jiaozi_leds.ply", "dark_emit_base",
        make_rgb_emitter([jiaozi_led_scale * 1.0, jiaozi_led_scale * 0.56, jiaozi_led_scale * 0.22]),
    )

    # 3. Streetscape
    add_mesh("sh_road", "road_surface.ply", "road_asphalt")
    add_mesh("sh_sidewalks", "sidewalks.ply", "sidewalk")
    add_mesh("sh_trunks", "tree_trunks.ply", "tree_trunk")
    add_mesh("sh_foliage", "tree_foliage.ply", "tree_foliage")
    add_mesh("sh_lamp_poles", "streetlamp_poles.ply", "pole_dark")
    add_mesh(
        "sh_lamp_bulbs", "streetlamp_bulbs.ply", "dark_emit_base",
        make_rgb_emitter([streetlamp_scale * 1.0, streetlamp_scale * 0.72, streetlamp_scale * 0.36]),
    )
    add_mesh(
        "sh_trails_w", "light_trails_white.ply", "dark_emit_base",
        make_rgb_emitter([trail_white_scale * 1.0, trail_white_scale * 0.86, trail_white_scale * 0.58]),
    )
    add_mesh(
        "sh_trails_r", "light_trails_red.ply", "dark_emit_base",
        make_rgb_emitter([trail_red_scale * 1.0, trail_red_scale * 0.11, trail_red_scale * 0.05]),
    )
    add_mesh("sh_cars_body", "car_bodies.ply", "car_body")
    add_mesh("sh_cars_glass", "car_glass.ply", "car_glass")
    add_mesh("sh_cars_head", "car_headlights.ply", "dark_emit_base", make_rgb_emitter([32.0, 28.0, 20.0]))
    add_mesh("sh_cars_tail", "car_taillights.ply", "dark_emit_base", make_rgb_emitter([28.0, 2.2, 0.8]))

    # 4. CBD Skyline
    for i in range(4):
        cbd_ebmp = _load_png_bitmap(os.path.join(assets_dir, f"cbd_emis_{i}.png"), linear_scale=cbd_emis_scale)
        add_mesh(f"sh_cbd_{i}", f"cbd_style_{i}.ply", f"cbd_{i}", make_bmp_emitter(cbd_ebmp))
    add_mesh("sh_cbd_fins", "cbd_fins.ply", "cbd_fins")
    add_mesh("sh_cbd_retail", "cbd_retail_glow.ply", "dark_emit_base", make_rgb_emitter([5.5, 3.2, 1.3]))

    return mi.load_dict(scene_dict)


def render_with_aovs(scene, spp=32):
    """Render Mitsuba beauty pass via native path integrator + fast native depth pass."""
    beauty = np.array(mi.render(scene, spp=spp), dtype=np.float32)
    depth_int = mi.load_dict({"type": "depth"})
    depth_rgb = np.array(mi.render(scene, integrator=depth_int, spp=2), dtype=np.float32)
    depth = depth_rgb[..., 0] if depth_rgb.ndim == 3 else depth_rgb

    # Compute smooth screen-space geometric normal approximation from depth for edge-guided denoising
    H, W = depth.shape
    dz_dy, dz_dx = np.gradient(np.where(depth > 0.01, depth, 1e4).astype(np.float32))
    scale_n = np.maximum(depth * 0.008, 0.25)
    nx = -dz_dx / scale_n
    ny = -dz_dy / scale_n
    nz = np.ones_like(nx)
    n_len = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-6
    normal = np.stack([nx / n_len, ny / n_len, nz / n_len], axis=-1).astype(np.float32)

    return {
        "beauty": np.nan_to_num(beauty, nan=0.0, posinf=500.0, neginf=0.0),
        "depth": np.nan_to_num(depth, nan=0.0, posinf=1e6, neginf=0.0),
        "albedo": np.ones((H, W, 3), dtype=np.float32),
        "normal": normal,
    }
