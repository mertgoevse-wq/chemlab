# Photogrammetry / Texture-Extraction Pipeline Specification
# "Real Lab Equipment → 3D Blender Assets"
# Version 1.0 — 2026-11-02

## 1. Goal
Automate discovery of real-world laboratory-equipment photographs (Google Images),
filter/clean them, reconstruct metric 3D geometry + PBR textures via photogrammetry,
and import the result into Blender 5.2 as a game-ready asset for the ChemLab scene.

## 2. End-to-End Pipeline Stages
```
S0  Query Generation        → query.json
S1  Google Images Harvest   → images/<query>/<uuid>.jpg + manifest.jsonl
S2  Quality Filter          → kept/  rejected/  + filter_report.json
S3  Photogrammetry          → sparse/ dense/ mesh/ texture/  (COLMAP)
S4  Mesh Cleanup + UV       → asset.glb + asset.blend
S5  PBR Material Bake       → albedo.png normal.png rough.png ao.png
S6  Blender Import + LOD    → final asset in chemlab.blend collection
S7  QA + Catalog            → catalog.json (id, bbox, tri count, license)
```

## 3. S0 — Query Generation
```python
# queries.py
EQUIPMENT = [
  "borosilicate beaker 250ml", "erlenmeyer flask 250ml",
  "graduated cylinder 100ml", "bunsen burner", "fume hood",
  "spectrophotometer cuvette", "titration burette 50ml",
  "pipette tip box", "petri dish glass", "magnetic stirrer hotplate",
]
ANGLES = ["front", "side", "top", "45 degree", "macro detail"]
def make_queries():
    return [f"{e} laboratory photo {a}" for e in EQUIPMENT for a in ANGLES]
```

## 4. S1 — Google Images Harvest
### 4.1 Provider abstraction
```python
class ImageSource(Protocol):
    def search(self, q: str, n: int) -> list[ImageHit]: ...
    def download(self, hit: ImageHit, dst: Path) -> Path: ...

class SerpAPIGoogleImages(ImageSource): ...   # primary
class BingImageSearch(ImageSource): ...       # fallback
class DuckDuckGoImages(ImageSource): ...      # fallback
```
### 4.2 Data structures
```python
@dataclass
class ImageHit:
    query: str
    url: str
    thumbnail: str
    width: int
    height: int
    source_domain: str
    license: str | None       # "CC-BY" | "royalty-free" | None
    sha256: str | None
```
```jsonl
{"query":"beaker front","url":"https://...","w":1920,"h":1080,"domain":"wikipedia.org","license":"CC-BY-SA","sha256":"...","path":"images/beaker_front/a1b2.jpg"}
```
### 4.3 Dedup + rate limits
- Perceptual hash (pHash, 64-bit) dedup with Hamming distance ≤ 8.
- Token bucket: 30 req/min for SerpAPI; exponential backoff on 429.
- Store original + thumbnail; never overwrite.

## 5. S2 — Quality Filter
Metrics computed per image:
```
sharpness S = variance(Laplacian(gray))        # > 100 keep
brightness B = mean(gray)                      # 40 < B < 215
contrast C = std(gray)                         # > 30
aspect A = w/h                                 # 0.5 < A < 2.0
min_dim  = min(w,h)                            # >= 512
background_uniformity U = 1 - (edge_density in border 5%)  # > 0.6
```
Keep if all thresholds pass. Rejected images are moved (not deleted) to `rejected/`
with a `reason` field in the report.

## 6. S3 — Photogrammetry (COLMAP)
### 6.1 CLI invocation
```bash
colmap feature_extractor \
  --database_path db.db --image_path images/kept \
  --ImageReader.single_camera 1 \
  --SiftExtraction.use_gpu 1

colmap exhaustive_matcher --database_path db.db --SiftMatching.use_gpu 1

colmap mapper --database_path db.db --image_path images/kept \
  --output_path sparse/0

colmap image_undistorter --image_path images/kept --input_path sparse/0 \
  --output_path dense --output_type COLMAP

colmap patch_match_stereo --workspace_path dense --workspace_format COLMAP \
  --PatchMatchStereo.geom_consistency true

colmap stereo_fusion --workspace_path dense --output_path dense/fused.ply

colmap poisson_mesher --input_path dense/fused.ply --output_path dense/mesh.ply
```
### 6.2 Texture projection
```bash
colmap model_converter --input_path dense --output_path dense --output_type TXT
# Then run texture projection via OpenMVS or COLMAP's colorize:
colmap colorize_pointcloud --input_path dense/fused.ply \
  --output_path dense/colored.ply
```
For UV-atlased textures use `openmvs TextureMesh`:
```bash
TextureMesh -i dense/mesh.ply -o textured.obj \
  --texture-resolution 4096 --max-texture-size 4096
```

### 6.3 Quality gates
- Sparse reconstruction must have >= 8 registered images.
- Dense point cloud: >= 50k points.
- Mesh: manifold, no non-manifold edges, hole count <= 5.
- If gate fails: fall back to single-image texture extraction + primitive mesh.

## 7. S4 — Mesh Cleanup + UV (Blender Python)
```python
import bpy, bmesh
def cleanup(mesh_obj):
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(mesh_obj.data)
    bmesh.ops.remove_doubles(bm, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.update_edit_mesh(mesh_obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    # Decimate to budget
    mod = mesh_obj.modifiers.new("dec", 'DECIMATE')
    mod.ratio = 0.35
    bpy.ops.object.modifier_apply(modifier=mod.name)
    # Smart UV project
    bpy.ops.uv.smart_project(angle_limit=66, island_margin=0.02)
```

## 8. S5 — PBR Material Bake
Bake in Blender (Cycles, 128 samples):
- Diffuse → albedo.png (sRGB, 2048²)
- Normal (tangent space) → normal.png (Linear, 2048²)
- Roughness → rough.png (Linear, 1024²)
- AO (baked) → ao.png (Linear, 1024²)
```python
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.samples = 128
# bake diffuse
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'})
```

## 9. S6 — Blender Import + LOD
```python
def import_asset(glb_path):
    bpy.ops.import_scene.gltf(filepath=str(glb_path))
    obj = bpy.context.selected_objects[0]
    obj.name = f"lab_{slug}"
    # LOD generation
    for ratio in (1.0, 0.5, 0.25):
        dup = obj.copy(); dup.data = obj.data.copy()
        bpy.context.collection.objects.link(dup)
        mod = dup.modifiers.new("dec", 'DECIMATE'); mod.ratio = ratio
        bpy.ops.object.modifier_apply({"object": dup}, modifier=mod.name)
    # Place in collection
    coll = bpy.data.collections.get("LabEquipment") or bpy.data.collections.new("LabEquipment")
    bpy.context.scene.collection.children.link(coll)
```

## 10. S7 — QA + Catalog
```json
{
  "id": "beaker_250ml_v1",
  "source_query": "borosilicate beaker 250ml front",
  "source_urls": ["https://..."],
  "license": "CC-BY-SA",
  "mesh": {"tris": 12480, "verts": 6320, "manifold": true, "holes": 0},
  "textures": {"albedo": "albedo.png", "normal": "normal.png", "rough": "rough.png", "ao": "ao.png"},
  "lod": [1.0, 0.5, 0.25],
  "bbox_m": [0.08, 0.12, 0.08],
  "validated": true
}
```

## 11. Single-Image Fallback (when photogrammetry fails)
When < 8 usable images:
1. Segment foreground with SAM (Segment Anything Model) or rembg.
2. Estimate depth with MiDaS / Depth-Anything V2.
3. Back-project depth → point cloud → Poisson mesh.
4. Project original image as albedo; generate normal from depth gradient:
   `N = normalize([-dI/dx, -dI/dy, 1])`.
5. Import as billboard-ish asset with limited parallax.

## 12. File Layout
```
chemlab/
  assets_pipeline/
    queries/queries.json
    images/<query>/<uuid>.jpg
    images/kept/  images/rejected/
    photogrammetry/{db.db,sparse/,dense/}
    output/{mesh.ply,textured.obj,albedo.png,...}
    blend_import.py
    catalog.json
```

## 13. Dependencies
- Python 3.12: requests, imagehash, pillow, opencv-python, numpy, tqdm, pydantic
- COLMAP >= 3.9 (GPU build)
- OpenMVS (TextureMesh)
- Blender 5.2 (bpy, Cycles)
- SAM / rembg, MiDaS (fallback)
- SerpAPI key (env: SERPAPI_KEY)

## 14. Licensing & Ethics
- Only download images whose license permits reuse (CC-*, public domain, or
  explicitly royalty-free). Reject unknown-license images in S2.
- Store source URL + license in catalog.json for attribution.
- Rate-limit to avoid hammering sources; respect robots.txt.

## 15. Performance Budget (per asset)
- Tri count LOD0 <= 25k, LOD2 <= 6k
- Texture memory <= 16MB (4× 2048² RGBA compressed)
- Import time into Blender <= 5s

## 16. Validation
- `pytest tests/test_pipeline.py` (unit tests for filter metrics, dedup, catalog schema)
- Blender headless check: `blender --background --python validate_asset.py -- asset.glb`
- Visual QA: render turntable of each asset, compare silhouette to source image (SSIM >= 0.7)
