# Asset Pipeline Specification — Google Images → Texture Extraction → Blender Materials → EEVEE → In-Game Loading
# Version 1.0 — 2026-11-02

## 1. Goal
Convert web-harvested lab-equipment photographs into optimized EEVEE-ready PBR materials and load them at runtime in the ChemLab engine with deterministic memory/VRAM budgets on Intel Iris Xe.

## 2. Stage Map
```
A0 Query & Harvest (Google Images)        → images/<slug>/<uuid>.jpg + manifest.jsonl
A1 Foreground/Texture Extraction          → albedo_raw.png, mask.png, depth.png
A2 PBR Derivation                         → albedo.png normal.png rough.png ao.png metal.png
A3 Blender Material Authoring (Principled) → .blend material library
A4 EEVEE Optimization                     → LODs, baked lightmaps, compressed textures
A5 Export (glTF 2.0 / .glb)              → assets/<slug>_lod{0,1,2}.glb
A6 In-Game Asset Loading (CAS cache)      → runtime handle + VRAM accounting
A7 QA & Budget Enforcement               → catalog.json + perf report
```

## 3. A0 — Harvest (reuse PHOTOGRAMMETRY S1)
- SerpAPI primary, Bing/DuckDuckGo fallback.
- License gate: only CC-*/PD/royalty-free. Unknown → reject.
- pHash dedup Hamming ≤ 8. Token bucket 30 req/min.

## 4. A1 — Texture Extraction
### 4.1 Foreground segmentation
```
rembg (U2-Net) → mask.png (alpha)
SAM (optional) for multi-object scenes
```
### 4.2 Perspective rectification
For planar labels/decals:
```
H = findHomography(src_corners, dst_corners)   # OpenCV
warped = warpPerspective(img, H, (W,H))
```
### 4.3 Color normalization
```
albedo = (img - mean) / std * target_std + target_mean   # per-channel, target mean=0.5, std=0.18
gamma: sRGB ↔ linear via OETF: V_srgb = 1.055*V_lin^(1/2.4) - 0.055
```
### 4.4 Depth (fallback assets)
MiDaS/Depth-Anything V2 → depth.png (16-bit PNG). Back-project:
```
X = (u - cx) * Z / fx
Y = (v - cy) * Z / fy
Z = depth[v,u]
```

## 5. A2 — PBR Derivation
### 5.1 Albedo
- Remove shadows via intrinsic decomposition (Retinex): `R = I / (I * G)` where G is Gaussian-blurred illumination (σ=15).
- Desaturate specular highlights: clamp top 5% luminance to median.
### 5.2 Normal (tangent space)
From depth gradient:
```
dZ/dx = (Z[x+1,y] - Z[x-1,y]) / 2
dZ/dy = (Z[x,y+1] - Z[x,y-1]) / 2
N = normalize([-dZ/dx, -dZ/dy, 1])   # OpenGL convention (Y up)
encode: N_rgb = (N + 1) / 2   # [0,1]
```
### 5.3 Roughness
```
rough = 1 - (local_variance(gray, 5x5) normalized)
rough = clamp(rough, 0.05, 0.95)
```
### 5.4 AO
Bent-cone / SSAO baked in Blender Cycles (128 samples) OR ambient occlusion from depth:
```
AO(p) = (1/N) Σ_i (n·ω_i) * V(p,ω_i)   # hemisphere sampling
```
### 5.5 Metalness
Heuristic for lab glassware: metalness=0.0 for glass/plastic; 0.8 for metal parts (detected via specular hue). Default 0.0.

## 6. A3 — Blender Material (Principled BSDF)
```python
import bpy
def build_material(name, tex_dir):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    # Albedo
    img = nt.nodes.new("ShaderNodeTexImage"); img.image = bpy.data.images.load(str(tex_dir/"albedo.png"))
    nt.links.new(img.outputs["Color"], bsdf.inputs["Base Color"])
    # Normal
    nimg = nt.nodes.new("ShaderNodeTexImage"); nimg.image = bpy.data.images.load(str(tex_dir/"normal.png"))
    nimg.image.colorspace_settings.name = 'Non-Color'
    nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(nimg.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    # Roughness
    rimg = nt.nodes.new("ShaderNodeTexImage"); rimg.image = bpy.data.images.load(str(tex_dir/"rough.png"))
    rimg.image.colorspace_settings.name = 'Non-Color'
    nt.links.new(rimg.outputs["Color"], bsdf.inputs["Roughness"])
    # AO multiply into base color (optional)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["IOR"].default_value = 1.45  # borosilicate glass
    return mat
```

## 7. A4 — EEVEE Optimization
### 7.1 Engine settings
```
scene.render.engine = 'BLENDER_EEVEE_NEXT'   # Blender 5.x
eevee.taa_render_samples = 16
eevee.use_gtao = True
eevee.gtao_distance = 0.3
eevee.use_ssr = True
eevee.ssr_quality = 0.25
eevee.use_volumetric_lights = False   # perf
```
### 7.2 Texture compression
- Albedo: BC7 (RGBA) or ASTC 4x4 for mobile; 2048² max.
- Normal: BC5 (RG) 2048².
- Roughness/AO: BC4 (R) 1024², packed R=rough, G=AO, B=metal.
- Mipmaps: full chain, bias -0.5 for sharpness.
### 7.3 LOD generation
```
for ratio in (1.0, 0.5, 0.25):
    dup = obj.copy(); dup.data = obj.data.copy()
    mod = dup.modifiers.new("dec", 'DECIMATE'); mod.ratio = ratio
    apply; link to collection
```
Budgets: LOD0 ≤ 25k tris, LOD1 ≤ 12k, LOD2 ≤ 6k.

### 7.4 Lightmap baking (static lab)
```
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'INDIRECT'})
# resolution 512² per object, 8-bit
```

## 8. A5 — Export (glTF 2.0)
```python
bpy.ops.export_scene.gltf(
    filepath=str(out),
    export_format='GLB',
    export_materials='EXPORT',
    export_textures=True,
    export_lights=False,
    export_cameras=False,
    draco_mesh_compression_enable=True,
    draco_mesh_compression_level=6,
)
```

## 9. A6 — In-Game Asset Loading
### 9.1 CAS cache (storage/asset_cache.py)
- Content-addressable: key = sha256(file bytes). Path = objects/<prefix>/<hash>.
- SQLite index with LRU eviction, max 500MB default.
- Integrity check on read.
### 9.2 Runtime loader (Python)
```python
class AssetLoader:
    def __init__(self, cache: AssetCacheManager, vram_budget_mb=128):
        self.cache = cache
        self.vram_used = 0
        self.vram_budget = vram_budget_mb * 1024 * 1024
    def load(self, uri: str) -> AssetHandle:
        data, meta = self.cache.get_asset(uri)
        handle = parse_glb(data)
        cost = estimate_vram(handle)  # textures + mesh
        if self.vram_used + cost > self.vram_budget:
            self.evict_lru_textures(cost)
        upload_to_gpu(handle)
        self.vram_used += cost
        return handle
```
### 9.3 VRAM estimation
```
texture_bytes = Σ (w*h*bytes_per_pixel / (4^mip_level))  # compressed: /4 for BC
mesh_bytes = verts*stride + indices*4
```
### 9.4 Streaming LOD
Distance thresholds: LOD0 < 2m, LOD1 2-5m, LOD2 > 5m. Swap via mesh replacement, keep textures.

## 10. A7 — QA & Budgets
- SSIM silhouette ≥ 0.7 vs source image (turntable render).
- VRAM ≤ 128MB scene total, tris ≤ 500k scene.
- Import time ≤ 5s per asset.
- pytest tests/test_asset_cache.py + tests/validate_scene_assets.py.

## 11. File Layout
```
chemlab/
  assets_pipeline/
    queries/queries.json
    images/<slug>/<uuid>.jpg
    extracted/<slug>/{albedo_raw.png,mask.png,depth.png}
    pbr/<slug>/{albedo.png,normal.png,rough.png,ao.png,metal.png}
    blend/<slug>.blend
    export/<slug>_lod{0,1,2}.glb
    catalog.json
  storage/asset_cache.py   (CAS)
```

## 12. Dependencies
Python 3.12: requests, imagehash, pillow, opencv-python, numpy, rembg, torch, onnxruntime, trimesh, pygltflib
Blender 5.2 (bpy), COLMAP/OpenMVS (optional), DRACO encoder.

## 13. Licensing & Ethics
Same as photogrammetry spec §14. Store source URL + license in catalog.

## 14. Performance Budget (per asset)
- Tri count LOD0 ≤ 25k, LOD2 ≤ 6k
- Texture memory ≤ 16MB (4× 2048² RGBA compressed)
- Import time ≤ 5s
- Scene total VRAM ≤ 128MB, tris ≤ 500k
```

Return spec.<|end|><|start|><|start|>assistant<|channel|>final<|message|>Spec written to `C:\Users\Win11 Pro\Desktop\chemlab\ASSET_PIPELINE_EEVEE_SPEC.md`. It covers the full chain: Google Image harvest → foreground/texture extraction (segmentation, rectification, color normalization, depth) → PBR derivation (albedo/normal/roughness/AO/metalness with exact equations) → Blender Principled BSDF material authoring → EEVEE Next optimization (compression, LODs, lightmaps) → glTF export → CAS-based in-game loading with VRAM accounting and LOD streaming → QA/budgets.<|end|><|start|>tool_calls_section_begin|>assistant to=mcp__ccd_turn__wrap_up<|channel|>analysis <|constrain|>xml<|message|><rfl:parameter name="actions">
[{"label": "Done", "action": "none"}]