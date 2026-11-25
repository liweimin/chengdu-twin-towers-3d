# 《成都金融城双塔黄昏》— Pure-Code Physically-Based CGI Artwork

A 100% procedural, physically-based path-traced architectural dusk photograph of **Chengdu Financial City Twin Towers (天府国际金融中心双塔)**, **Jiaozi Ring (交子之环)**, **Jiaozi Avenue (交子大道)**, and the surrounding **Financial City CBD Skyline** — created purely with code (**zero AI image generation models, zero existing photographs**).

## Final Artwork
- **4K UHD Final (`3840×2160`)**: [`outputs/chengdu_twin_towers_dusk_4k.png`](outputs/chengdu_twin_towers_dusk_4k.png)
- **Iterative Previews**: `outputs/chengdu_twin_towers_dusk_draft.png` → `v2.png` → `v3.png` → `v4.png`

## Technical Architecture

1. **Volumetric Twilight Sky & Backlit Sunset Clouds (`src/sky_gen.py`)**
   - Generates a `4096×2048` 32-bit float linear HDR equirectangular sky environment map (`assets/dusk_sky.npy`).
   - Combines physically-inspired Rayleigh/Mie twilight atmospheric gradients (deep sapphire-indigo zenith → Belt of Venus dusk band → warm apricot-tangerine horizon) with multi-octave domain-warped cirrus and altocumulus/mackerel clouds (`火烧云`) projected onto curved planetary atmospheric shells with two-step Beer-Lambert directional self-shadowing from the low western setting sun.

2. **Procedural PBR & Architectural Emission Textures (`src/textures.py`)**
   - **Twin Towers Synchronized LED Louver Media Facade (`2048×1024`)**: Continuous diagonal Shu-brocade (`蜀锦流光`) golden-champagne and coral-amber silk ribbons flowing seamlessly across both towers with discrete horizontal LED louver rasterization and dark refuge-floor rhythm.
   - **Recessed Office Interiors**: 54-floor randomized office occupancy with varied warm/neutral/cool color temperatures, ceiling strip gradients, and venetian blind shadows.
   - **CBD Skyscraper Curtain Walls**: 4 distinct high-resolution architectural facade sets (albedo, emissive office windows, roughness) with crisp mullions, spandrels, blinds, and varied roofline crowns.
   - **Damp Boulevard Asphalt (`2048×1536`)**: Multi-octave puddle wetness, glossy tire tracks, weathered white dashed lane lines, double yellow median lines, and intersection crosswalks.

3. **Procedural 3D Architectural Geometry (`src/geometry.py`)**
   - Generates **34 watertight binary PLY meshes (~280,000 triangles)**:
     - **Twin Towers (`218m` exact scale)**: Elliptical-spindle superellipse cross-section; 3-layer facade with micro-perturbed LOW-E glass panes (`±0.5°` individual pane tilt for authentic oil-canning sunset reflections), 3D metallic aluminum "ice-flower" (`冰花`) crystalline filigree exoskeleton (`57,024` triangles), discrete horizontal LED louver slats, recessed interior office cylinder, architectural crown cornice, red aviation beacons, and 3-story glazed colonnade podiums.
     - **Jiaozi Ring (`交子之环`, `104m` outer diameter)**: Undulating vermilion-orange (`高新橙`) aerodynamic steel box girder, folded-ribbon wind-rain canopy portal ribs, 4 tapered V-shaped inclined columns, glass balustrades, continuous warm linear soffit/fascia LEDs, and 52 human-scale pedestrian silhouettes.
     - **Jiaozi Avenue & Urban Streetscape**: Damp paved avenue & Yizhou Avenue intersection, sidewalks & curbs, botanical branching trees (`57,720` foliage triangles), architectural streetlamps & plaza bollards, sculpted 3D evening vehicles, and long-exposure golden headlight & ruby taillight streams.
     - **Chengdu Financial City CBD Skyline**: 34 varied flanking and background skyscrapers with setbacks, vertical architectural fins, and avenue-level retail bays.

4. **Physically-Based Path Tracing (`src/scene.py`)**
   - Powered by **Mitsuba 3 (`scalar_rgb` multi-threaded CPU Embree)** using physically-based `principled`, `roughconductor`, `thindielectric`, and `blendbsdf` materials with native `path` + `depth` integrators.

5. **Linear-HDR Photographic Post-Processing (`src/postprocess.py`)**
   - Two-pass Monte Carlo firefly rejection + conservative depth/normal-guided À-Trous denoiser (`sigma_c = 0.095`) that preserves razor-sharp architectural mullions and ice-flower lattice.
   - Depth-based Chengdu basin twilight aerial perspective & evening mist.
   - 4-octave physical optical bloom & atmospheric halation + `f/8` 8-blade aperture diffraction starbursts on bright point lights.
   - AgX-inspired inset-matrix filmic tone mapping, prime-lens micro-clarity, subtle lateral chromatic aberration, natural full-frame vignetting, and ISO-200 luminance grain.

## Reproduction

```powershell
# 1. Create virtual environment and install dependencies
uv venv .venv --python 3.12
uv pip install --python .venv\Scripts\python.exe mitsuba numpy scipy pillow opencv-python-headless trimesh

# 2. Fast preview (1280x720, 32 spp, ~1 min path tracing)
.venv\Scripts\python.exe render.py --preset draft --rebuild-sky --rebuild-textures --rebuild-geo

# 3. Full HD render (1920x1080, 64 spp)
.venv\Scripts\python.exe render.py --preset medium

# 4. 4K UHD Masterpiece (3840x2160, 48 spp)
.venv\Scripts\python.exe render.py --preset final --rebuild-sky --out outputs\chengdu_twin_towers_dusk_4k.png
```
