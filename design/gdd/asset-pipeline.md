# ChemLab: 3D Asset Pipeline & EEVEE Next Specification
**Engine:** Godot 4.7.2 (Compatibility / OpenGL 3.3 / Forward+)  
**DCC Authoring:** Blender 5.2.3 LTS  
**Target Hardware Baseline:** Intel Iris Xe Graphics (80 EU, Dell Latitude 5530 baseline)  
**Document Version:** 1.0.0 (Production Release)

---

## 1. Executive Summary & Architectural Scope

The ChemLab asset pipeline establishes a deterministic, physically accurate bridge between scientific apparatus modeling in **Blender 5.2 LTS** and real-time interactive rendering in **Godot 4.7.2**. Laboratory simulation places unique demands on real-time computer graphics:
1. **Pervasive Glassware Refraction**: Transparent vessels (beakers, flasks, burets, NMR tubes) occupy the central player frustum, requiring dielectric refraction, dispersion, and fresnel reflection.
2. **Dynamic Liquid Volumes**: Reagents undergo continuous phase transitions, turbidity changes, meniscus capillary deformation, and fluid transfer.
3. **Severe Hardware Budget**: The target mobile workstation (Intel Iris Xe 80 EU) operates on a shared 51.2 GB/s DDR4 memory bus with a nominal 128 MB dedicated video slice. Unconstrained raymarching, uncompressed textures, or excessive draw calls lead to immediate thermal throttling and frame drops.

This document formalizes naming conventions, poly-count/memory budgets, format standards, EEVEE Next master material networks, cleanroom illumination, and automated Godot export workflows.

---

## 2. Asset Naming Conventions & Organization

All assets follow strict PascalCase and snake_case taxonomies with unambiguous classification prefixes. No spaces, uppercase file extensions, or special characters are permitted.

### 2.1 Prefix Classification

| Asset Type | Prefix | Example | Description |
| :--- | :--- | :--- | :--- |
| **Static Apparatus Mesh** | `SM_` | `SM_Beaker_400ml.glb` | Non-deforming lab equipment |
| **Articulated Mesh** | `SK_` | `SK_AnalyticalBalance_Doors.glb` | Meshes with bones/blendshapes |
| **Master Material** | `M_` | `M_Borosilicate_Glass_3_3` | Core shader node graph in Blender |
| **Material Instance** | `MI_` | `MI_Beaker_Graduated_Blue` | Parameterized instance with specific textures |
| **Godot Spatial Shader** | `SH_` | `glass_shader.gdshader` | Custom GLSL/Godot shading language file |
| **Texture: Albedo/Base Color**| `T_*_BC` | `T_Balance_Chassis_BC.png` | sRGB albedo map (neutral diffuse) |
| **Texture: Normal Map** | `T_*_N` | `T_FumeHood_Panel_N.png` | OpenGL format (+Y green tangent space) |
| **Texture: Packed ORM** | `T_*_ORM` | `T_MagneticStirrer_ORM.png` | R = Occlusion, G = Roughness, B = Metallic |
| **Texture: Emission** | `T_*_E` | `T_Display_7Segment_E.png` | Emissive illumination mask |
| **Collision Shape** | `COL_` | `COL_Workbench_UCX` | Simplified convex hull / primitive collider |

### 2.2 Directory Structure

```
chemlab/
├── chemlab.blend                     # Master authoring scene & material library
├── design/gdd/                       # Game design & technical art documentation
│   ├── asset-pipeline.md             # This document
│   ├── materials-spec.md             # Per-asset visual & physical specifications
│   └── game-concept.md               # Core RPG gameplay loop & systems
├── game/
│   ├── assets/                       # Final runtime game assets (glTF 2.0 / .glb)
│   │   ├── apparatus/                # Beakers, flasks, burners, stirrers
│   │   ├── architecture/             # Cleanroom walls, flooring, benches, hood
│   │   ├── consumables/              # Pipette tips, filter paper, test tubes
│   │   ├── instrumentation/          # NMR, GC-MS, analytical balance
│   │   └── textures/                 # Compressed 1K texture atlases (ORM packed)
│   ├── scenes/apparatus/             # Instantiated Godot 4 .tscn nodes
│   └── shaders/                      # Godot spatial & post-processing shaders
└── tools/
    ├── generate_analytical_lab.py    # Cleanroom procedural scene builder
    └── export_assets_to_godot.py     # Automated batch export pipeline
```

---

## 3. Geometric & File Size Budgets

Hardware constraints on the Intel Iris Xe GPU require aggressive Level of Detail (LOD) tiering. High-frequency geometric details (screw heads, graduation line bevels, chamfers) must be baked into normal maps rather than modeled into base meshes.

### 3.1 Triangle Count Budgets

| Category | LOD0 (0.0 m – 1.0 m) | LOD1 (1.0 m – 3.0 m) | LOD2 (> 3.0 m) | Maximum Draw Calls |
| :--- | :--- | :--- | :--- | :--- |
| **Standard Glassware** (Beaker, Flask) | 4,000 – 8,000 tris | 1,500 – 3,000 tris | 400 – 800 tris | 2 (Glass + Liquid) |
| **Precision Glassware** (Buret, Condenser)| 6,000 – 12,000 tris | 2,500 – 5,000 tris | 800 – 1,200 tris | 3 (Glass + Fluid + Stopcock) |
| **Benchtop Apparatus** (Stirrer, Burner)| 8,000 – 16,000 tris | 3,000 – 6,000 tris | 1,000 – 2,000 tris| 2 – 3 |
| **Analytical Instruments** (Balance, GC-MS)| 12,000 – 25,000 tris| 4,000 – 10,000 tris| 1,500 – 3,500 tris| 4 – 5 |
| **Architectural Fixtures** (Fume Hood) | 15,000 – 28,000 tris| 6,000 – 12,000 tris| 2,000 – 4,000 tris| 3 – 4 |
| **Full Cleanroom Scene Budget** | **≤ 250,000 tris** | **≤ 120,000 tris** | **≤ 40,000 tris** | **≤ 65 Draw Calls** |

### 3.2 Texture Memory & Resolution Constraints

- **Resolution Clamp**: All diffuse, normal, and ORM textures are strictly clamped to a maximum of **1024 × 1024** pixels. Micro-details (graduation numbers, warning decals) use packed sprite sheets or dynamic text labels (`Label3D`).
- **Channel Packing**: ORM packing (Red = Ambient Occlusion, Green = Roughness, Blue = Metallic) saves 66% of memory bandwidth compared to individual grayscale textures.
- **VRAM Footprint**: A single 1024×1024 BC7 compressed texture occupies ~1.33 MB. An ORM packed texture occupies ~1.33 MB. An asset with Albedo + Normal + ORM consumes < 4.0 MB total VRAM.
- **Draco Compression**: Runtime `.glb` files must have Draco geometric compression enabled (Encoding level 6, position quantization 14 bits, normal quantization 10 bits), keeping individual file sizes below 1.5 MB on disk.

---

## 4. Format Standards: Blender (.blend) to Godot (.glb)

The authoritative source file is `chemlab.blend`. All geometry must be exported to binary glTF 2.0 (`.glb`) using Blender's Python API or automated export batch scripts.

### 4.1 Export Configuration Standards

```python
# Standard glTF 2.0 Export parameters for ChemLab pipeline
bpy.ops.export_scene.gltf(
    filepath="game/assets/apparatus/SM_Beaker_400ml.glb",
    export_format='GLB',
    use_selection=True,
    export_apply=True,                     # Apply transforms & modifiers
    export_yup=True,                       # Godot Y-Up coordinate system
    export_texcoords=True,
    export_normals=True,
    export_tangents=True,                  # Required for high-precision normal mapping
    export_materials='EXPORT',             # Export PBR Principled material definition
    export_vertex_color='NONE',            # Vertex colors omitted unless specifically baked
    export_draco_mesh_compression_enable=True,
    export_draco_mesh_compression_level=6,
    export_draco_position_quantization=14,
    export_draco_normal_quantization=10,
    export_draco_texcoord_quantization=12,
    export_lights=False,                   # Lighting authored in Godot world environment
    export_cameras=False
)
```

### 4.2 Material Conversion Mapping

| Blender 5.2 Node Socket | glTF 2.0 PBR Standard | Godot 4 Spatial Shader Equivalent |
| :--- | :--- | :--- |
| `Base Color` (sRGB) | `pbrMetallicRoughness.baseColorTexture` | `ALBEDO` |
| `Metallic` (Scalar) | `pbrMetallicRoughness.metallicFactor` (B)| `METALLIC` |
| `Roughness` (Scalar) | `pbrMetallicRoughness.roughnessFactor` (G)| `ROUGHNESS` |
| `Normal Map` (Tangent space)| `normalTexture` (OpenGL Y+) | `NORMAL_MAP` |
| `Emission Color * Strength` | `emissiveTexture` + `emissiveFactor` | `EMISSION` |
| `Transmission Weight` | `KHR_materials_transmission` | Custom `glass_shader.gdshader` Screen Texture |
| `IOR` | `KHR_materials_ior` | Uniform `ior` (1.458 for Borosilicate 3.3) |
| `Volume Absorption` | `KHR_materials_volume` | Custom `liquid_shader.gdshader` Beer-Lambert |

---

## 5. Blender 5.2 EEVEE Next Master Material Networks

Blender 5.2 features the overhauled **EEVEE Next** engine with unified screen-space raytracing, fast global illumination, and redesigned Principled BSDF v2 sockets.

### 5.1 Borosilicate Glass 3.3 (`M_Borosilicate_Glass_3_3`)

Borosilicate glass (Schott Duran / Pyrex) has an index of refraction of $n = 1.458$ at $\lambda = 589.3\text{ nm}$ (sodium D-line) and an Abbe number $V_d \approx 65$, showing minimal optical dispersion.

#### Blender 5.2 Node Parameters:
- **Base Color**: `RGBA(0.96, 0.98, 1.0, 1.0)` (subtle cool tint representing ultra-low iron silica)
- **Metallic**: `0.0`
- **Roughness**: `0.015` (ultra-smooth fire-polished laboratory glass)
- **IOR**: `1.458`
- **Transmission Weight**: `1.0`
- **Specular IOR Level**: `0.5` (dielectric Fresnel calculation derived from IOR)
- **Coat Weight**: `0.0`
- **Thin Film Thickness**: `0.0 nm` (clean glass) / `150.0 nm` with IOR `1.33` (wet exterior)
- **Raytrace Settings**:
  - `Screen Trace`: Enabled
  - `Refraction Depth`: Equal to physical vessel wall thickness (e.g., $0.002\text{ m}$ / $2.0\text{ mm}$)
  - `Shadow Mode`: None / Alpha Hashed (avoids cast shadow artifacts on benchtop)

```
[TexCoord: UV] ────> [Mapping] ────> [Graduation Lines Decal] ──┐ (Alpha)
                                                                ▼
[Principled BSDF v2] ◄────────────────────────────────── [Mix Shader]
  ├─ Base Color: (0.96, 0.98, 1.0)                               │
  ├─ Roughness: 0.015                                            │
  ├─ IOR: 1.458                                                  ▼
  ├─ Transmission Weight: 1.0                       [Diffuse White BSDF]
  └─ Specular IOR Level: 0.5                          (Enamel Markings)
```

### 5.2 Volumetric Liquid Material Network (`M_Dynamic_Liquid_Volume`)

Liquids in ChemLab obey the **Beer-Lambert Law**:
$$T = \frac{I}{I_0} = 10^{-\epsilon \cdot c \cdot d} = \exp(-\alpha \cdot d)$$
where $\alpha = \epsilon \cdot c \cdot \ln(10)$ is the linear absorption coefficient, $c$ is molar concentration ($\text{mol/L}$), and $d$ is path length ($\text{m}$).

#### Blender 5.2 EEVEE Next Implementation:
- **Approach**: Dual-representation. Inside Blender 5.2, EEVEE Next uses Principled BSDF with interior Absorption Volume. Inside Godot 4, the real-time equivalent is driven by `game/shaders/liquid_shader.gdshader` using analytical ray-plane intersection and world-aligned clipping.
- **Base Color**: Derived from solute transmission spectra (e.g., Copper Sulfate $\text{Cu}^{2+}$: `RGB(0.05, 0.65, 0.95)`).
- **Roughness**: `0.02` (calm surface) to `0.25` (turbulent stirring).
- **IOR**: $n = 1.333$ (pure water at 20 °C) up to $n = 1.380$ (concentrated organic solvents/acids).
- **Transmission Weight**: `0.95` for clear aqueous solutions; scaled down to `0.0` as precipitation turbidity approaches 1.0.

---

## 6. Cleanroom Lighting & Global Illumination

Accurate color discrimination (e.g., phenolphthalein end-point titration from clear to pale pink at $\text{pH } 8.2$) demands standardized cleanroom lighting:

### 6.1 Photometric Specifications
- **Correlated Color Temperature (CCT)**: **4000 K** (Neutral White, ISO 14644 cleanroom standard).
- **Color Rendering Index (CRI)**: $R_a \ge 95$ (simulated via balanced spectral emission).
- **Benchtop Illuminance Target**: **1,000 – 1,200 lux** at working height ($0.90\text{ m}$ above finished floor).
- **Ambient Room Illuminance**: **500 lux** uniform background lighting.
- **Fume Hood Interior Illuminance**: **1,500 lux** vapor-proof task lighting.

### 6.2 EEVEE Next Engine Parameters (Tuned for Hardware Baseline)

```python
# Hardware-constrained EEVEE Next render settings (Intel Iris Xe 60 FPS)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'

eevee = scene.eevee
eevee.taa_samples = 24                         # Viewport sample count (optimizer budget)
eevee.taa_render_samples = 64                  # Final render sample count
eevee.shadow_pool_size = 512                   # Shared shadow map atlas
eevee.shadow_cube_size = 1024                  # Clamped point light shadow resolution
eevee.shadow_step_count = 6                    # Shadow ray steps

# Fast Global Illumination (Fast GI)
eevee.fast_gi_method = 'GLOBAL_ILLUMINATION'
eevee.fast_gi_resolution = 2                   # Half-resolution screen trace
eevee.fast_gi_ray_count = 2
eevee.fast_gi_step_count = 8
eevee.fast_gi_quality = 0.25
eevee.fast_gi_bias = 0.05

# Screen-Space Raytracing (SSR & Transmittance)
rto = eevee.ray_tracing_options
rto.resolution_scale = 2                       # Half-res ray trace (enable_half_res_trace=True)
rto.screen_trace_quality = 0.25
rto.trace_max_roughness = 0.5
rto.use_backface_hit = True
rto.denoise_temporal = True
```

---

## 7. Intel Iris Xe Performance Budget & Optimizer Verification

The performance characteristics implemented in `src/chemlab/graphics/iris_xe_optimizer.py` and validated in `tests/test_iris_xe_optimizer.py` dictate hard engine gates:

### 7.1 Hardware Partitioning Metrics

| Metric | Target / Limit | Hardware Constraint Origin |
| :--- | :--- | :--- |
| **Target Framerate** | **60 FPS** (16.67 ms) | Display VSync smooth simulation |
| **Minimum Framerate (1% low)**| **≥ 52 FPS** (19.23 ms) | Prevents CV hand-tracking jitter |
| **Dedicated VRAM Slice** | **≤ 128 MB** | Intel WDDM reported dedicated memory |
| **Shared System RAM Staging**| **≤ 6,144 MB** | 40% of 16 GB dual-channel DDR4-3200 |
| **Draw Calls per Frame** | **≤ 65 calls** | CPU driver submission overhead on i5-1245U |
| **Texture Dimension Clamp** | **1024 × 1024** | Preserves 51.2 GB/s UMA bus bandwidth |
| **Internal Resolution Scale**| **0.67x (Performance)** | Emulates XeSS/CAS upscaling (~45% fragment count) |
| **Screen Space Ray Trace** | **Half-Resolution (2x)** | Halves raymarching load on 80 EUs |

### 7.2 Dynamic Upscaling Strategy
When running at 1920×1080 (1080p target):
- `calculate_internal_resolution(1920, 1080, UpscalePreset.PERFORMANCE)` derives a scale factor of `0.67`, producing an internal rendering buffer of `1286 × 722`.
- Total rendered pixels per frame drops from $2,073,600$ to $928,492$ (a **55.2% reduction in fragment shading load**).
- A lightweight Contrast Adaptive Sharpening (CAS) pass reconstructs sharp meniscus edges, graduation decals, and specular highlights without EU occupancy degradation.

---

## 8. Quality Assurance & Pipeline Automation Checklist

Before any asset is committed to `game/assets/`:
1. **Geometric Integrity**: Zero non-manifold edges, zero unapplied object scales (scale must be `Vector3(1.0, 1.0, 1.0)`), origin point placed at base center of support.
2. **Dimension Verification**: Scaled 1:1 in SI metric meters (e.g., $400\text{ mL}$ beaker height $= 0.11\text{ m}$).
3. **Texture Conformance**: 1024×1024 maximum resolution, PNG/WebP lossless format, ORM packed.
4. **Collision Hull**: Simplified collision mesh assigned to collision layer 1 (`apparatus`) and layer 2 (`recipient_volume`).
5. **Headless Verification**: Runs through `pytest tests/test_iris_xe_optimizer.py` and headless Blender validation with 0 errors.
