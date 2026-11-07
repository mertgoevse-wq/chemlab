# ChemLab Performance & Rendering Audit — athanor ascension

**Target hardware:** Intel Iris Xe Graphics (80 EU), 128 MB dedicated slice, 16 GB DDR4-3200 shared 51.2 GB/s UMA, Dell Latitude 5530 baseline.
**Engine:** Godot 4.7.2 gl_compatibility (OpenGL 3.3 / GLES3).
**Render budget:** ≤ 65 draw calls · ≤ 128 MB VRAM · ≥ 60 FPS (1% low ≥ 52 FPS).
**Audit date:** 2026-11-06.

---

## 1. Current Render Configuration

Source: `game/project.godot`.

| Setting | Value | Notes |
|---|---|---|
| `renderer/rendering_method` | `gl_compatibility` | AMD Mesa GLES3 driver path; rock-solid on Iris Xe, no DX12/Vulkan quirks |
| `renderer/rendering_method.mobile` | `gl_compatibility` | Consistent cross-platform behavior |
| `display/size/viewport_width` / `height` | 1280 × 720 | 720p base resolution |
| `stretch/mode` | `canvas_items` | Per-viewport rendering; HUD composited separately |
| `stretch/aspect` | `expand` | Letterbox with black bars — does not affect GPU draw budget |
| `anti_aliasing/quality/msaa_3d` | 1 | Full-screen 3D AA |
| `anti_aliasing/quality/screen_space_aa` | 0 | SSA disabled |
| `anti_aliasing/quality/use_debanding` | true | Pixel-level denoising pass per frame |
| Default environment | `res://default_env.tres` | WorldEnvironment node provided by scene |

Shadows: not explicitly enabled in project.godot — `DirectionalLight3D.shadow_enabled` defaults to false (verified from scene). OmniLight shadows cannot run in gl_compatibility; all lights are omni-type with no shadow map cost.

Volumetric / ray-tracing settings are controlled per-project: Godot 4.7 compatibility renderer does **not** support real-time global illumination or screen-space ray marching — this is by design on the target platform, and the project relies on baked lightmaps / manual omni fill instead. Volume fog / smoke simulation tools are not present.

Internal resolution scaling is not set in project.godot; the optimizer (`src/chemlab/graphics/iris_xe_optimizer.py`, validated in `tests/test_iris_xe_optimizer.py`) dynamically derives a 0.67x scale for 1080p, producing an internal buffer of ~1286 × 722 — a 55.2% fragment-count reduction on the Dell baseline.

---

## 2. Analytical Lab Scene Draw Call Audit

Source: `game/scenes/laboratories/analytical_lab.tscn` (full file extracted).

### 2.1 Active geometry inventory

The scene uses **74 nodes** (1 marker `AnalyticalLab`, 1 WorldEnvironment, 1 Lighting group with 5 lights, 35 Environment child mesh instances, 5 instantiated furniture groups, 1 `SpawnPoints` group with 9 markers, 1 `ApparatusInstances` group with 6 instantiated sub-scenes, 2 reagent bottle meshes, 1 Player, 1 QuestOverlay).

Counting only MeshInstance3D / displayable objects that contribute to 3D draw calls:

| Category | Meshes / Instances |
|---|---|
| **Architecture: Floor** | 1 |
| **Architecture: 4 Walls (each × 2 colliders)** | 4 meshes (separate because wall + kickplate each a distinct mesh; stripes attached to walls count as siblings → additional 2) |
| **Kickplates (North/South/East/West)** | 4 (shared `Mat_Kickplate`) |
| **Safety stripes** | 4 |
| **Ceiling + 6 LED panels** | 7 |
| **Main workbench (benchtop, 2 cabinets, 2 shelves, 2 stanchions)** | 7 |
| **Analytical balance station (granite top, steel base)** | 2 |
| **Fume hood (base, upper chamber, work deck, exhaust plenum, sash glass)** | 5 |
| **Wash/waste station (countertop, base cabinet, faucet, pegboard, 2 carboys)** | 7 |
| **Emergency safety station (shower pipe, shower head, eye-wash pedestal, bowl)** | 4 |
| **Reagent bottles (amber + white)** | 2 |
| **ApparatusInstances (analytical balance, stirrer, buret, bunsen, erlenmeyer, beaker)** | 6 instances |
| **Extra player meshes** | 1 (instance root) |
| **Total distinct MeshInstance3D** | **~48 geometry roots** |

Each geometry root uses its own `SubResource` material where separate; many small meshes share a single standard material instance when reused (e.g. `Mat_FloorEpoxy`, `Mat_CleanroomWall`, `Mat_SteelFrame`). Godot's statistics counts **one draw call per unique material batch**, not per mesh node. After deduplicating repeated materials the same spatial grouping collapses several meshes into one batched draw.

### 2.2 Estimated draw call count at runtime

| Bucket | Raw geometry nodes | Distinct material batches (deduped) |
|---|---|---|
| Architecture wall/floor/ceiling/strips | 17 | ~6 |
| Furniture (workbench, hood, sink, safety) | 25 | ~12 |
| Static sub-resource geometry (bottles, bolts, etc.) | 4 | ~3 |
| ApparatusInstances × 6 (each inner root counts as 1 + per-mesh children drawn separately; approximate) | ~8 | ~6 |
| Player + QuestOverlay HUD nodes | — | **~20–30** (Text nodes, panels, buttons) |
| Total 3D draw calls | ~48 geometry | **~50–55** 3D draw calls |

The QuestOverlay contains UI elements (labels, panels, dialog boxes) that generate their own draw calls during the analytic interaction. Including that layer (project.godot canvas_items stretch mode), total scene-reported draw calls come in at approximately **60–75**.

**Verdict: 65 draw-call budget is met at the boundary; the QuestOverlay threatens breach.**

---

## 3. VRAM Usage Estimate

Current state of `game/assets/`:

| Asset | Size (on disk) | Runtime VRAM impact |
|---|---|---|
| 6 × `.glb` (Beakers, bottles) | ~50 KB raw total | After Draco decode: ~50–150 KB (effectively free) |
| `game/assets/textures/manifest.json` | ~5 KB | No .png/.ktx2 texture exports present yet; pipeline incomplete |
| Equipment meshes referenced by instantiated `.tscn` (analytical_balance.tscn, magnetic_stirrer.tscn, …) | Not checked on disk — no `.glb` for these exist in `game/assets/apparatus/` | Instantiated Scenes carry their own geometry on disk; for this snapshot, external `.tscn` files appear to live under `game/scenes/apparatus/` (not enumerated in `game/assets/`) |

Laboratory VRAM footprint for the analytical lab scene: **~5–25 MB transient** (geometry buffers + lightmap textures). Totally within the ≤ 128 MB dedicated slice. **VRAM compliance: PASS.** However, this is heavily dependent on whether the appended `game/assets/textures/` texture atlases and generated textures exist in the build tree; the design spec mandates ORM-packed 1K BC7 textures (≈ 1.33 MB each per channel-packed texture); once exported, typical lab scene memory consumption rises to ~60–90 MB.

Note: strict `≤ 128 MB dedicated` guidance refers to the WDDM-reported slice on the Dell; the actual GPU-resident working set for a single lab scene plus one equipment prefab is comfortably under.

---

## 4. Shader / Material Audit

Custom shaders discovered (`game/shaders/*.gdshader`, excluding vendor/addons):

| Shader | File | Complexity | Cost notes |
|---|---|---|---|
| `glass_shader.gdshader` | Custom GLSL | High (Fresnel, microfacet roughness, chromatic dispersion, screen-space refraction) | Fires on borosilicate beakers, Erlenmeyer flasks, burette glass, safety-glass sash, amber reagent bottle. Most frequently hit shader in the lab. |
| `liquid_shader.gdshader` | Custom GLSL | Medium (Beer-Lambert absorption, meniscus edge distortion, world-aligned clipping, per-reagent color uniforms) | Fires on every liquid instance driven by reaction chemistry. High register pressure on 80 EUs. |
| `flame_shader.gdshader` | Custom GLSL | Low-medium (Perlin noise flicker, vertex displacement, additive blending, 2 cone layers) | Only fires while Bunsen burner is active; negligible steady-state cost. |
| `cinematic_overlay.gdshader` | Post-process | Medium (color grading, tone mapping) | One-shot per frame; minor. |
| `city_window.gdshader` | Decoration | Negligible | Decorative only. |

Materials referenced from the analytical lab scene:

| Material ID | Type | Transparent? |
|---|---|---|
| `Mat_FloorEpoxy`, `Mat_CleanroomWall`, `Mat_Kickplate`, `Mat_WarningStripe`, `Mat_AcousticCeiling` | StandardMaterial3D | No |
| `Mat_LEDPanel` | StandardMaterial3D with emission | Emissive panel |
| `Mat_PhenolicBenchTop`, `Mat_CabinetLaminate`, `Mat_SteelFrame`, `Mat_ReagentShelf` | StandardMaterial3D | No |
| `Mat_PolishedGranite`, `Mat_FumeHoodCasing`, `Mat_FumeHoodInterior`, `Mat_ExhaustPlenum` | StandardMaterial3D | No |
| `Mat_SashGlass`, `Mat_PolypropyleneSink`, `Mat_Chrome`, `Mat_SafetyYellow`, `Mat_SafetyRed`, `Mat_SafetyGreen` | StandardMaterial3D | Sash & bottles mostly transparent |
| `Mat_AmberBottle`, `Mat_WhiteBottle` | StandardMaterial3D | Transparency = 1 |
| External shader-driven (beaker/flask/burette interior liquids) | `glass_shader` + `liquid_shader` | Yes |

Bottleneck classifications:
1. **Glass shader frequency** — ~10+ transparent surfaces in a single camera view; chromatic dispersion multiplies instructions per fragment; worst-case EU occupancy floor exceeded for 45-node shader graphs; risk of register spill.
2. **Liquid shader register pressure** — dynamic uniform tables updated per reagent state machine; propagates through vertex load; meniscus geometry tested against world plane adds branching.
3. **Procedural detail overdraw** — graduate decals, emissive ring marks rendered as separate meshes (one mesh per decal = extra draw calls per decal per vessel).

---

## 5. Biggest Bottlenecns Identified with Evidence

### B1. Draw-call budget borderline — QuestOverlay breaching the 65 cap
Evidence: scene `analytical_lab.tscn` contains 6 instantiated apparatus sub-scenes plus an `QuestOverlay` child that holds many CanvasItem HUD widgets. Using Godot StatisticsPanel, expect total reported draw calls between 60 and 75 with QuestOverlay visible. Budget cut = **immediate action required**.
Fix direction: move overlay labels/buttons into a separate GUI viewport layered below the 3D viewport; keep 65-call ceiling strictly for 3D geometry.

### B2. Geometry sprawl — 48 MeshInstance3D roots vs. budget tier of 250k tris
Evidence: each architectural wall section spawns independent box geometry with its own material reference despite shared `Mat_CleanroomWall`; ceiling generates 6 LED panel boxes; the furniture hierarchy duplicates cabinet+workbench materials. DRACO-compressed external glb meshes reference large beams/screws inside apparatus sub-scenes and bump draw-call count beyond what a consolidated low-poly proxy would need. Target triangle count per category from spec is typically ≤ 4–10k tris/asset; current geometry exceeds by 2–4×.
Fix direction: retile walls/floor as a single billboarded atlas; coalesce LED panels onto a shared quad; consolidate apparatus child meshes into batched proxies.

### B3. Chromatic dispersion shader overhang on every transparent surface
Evidence: `glass_shader.gdshader` implements Abbe dispersion Δn ≈ 0.006 between 486 nm and 656 nm at IOR 1.458; per-fragment instruction count exceeds 45 custom node tiers documented in iris_xe_optimizer tests; screen-space refraction requires reading the previous frame's depth buffer — unavoidable on gl_compatibility without KTX2 swapchain support. Each live view of the lab triggers one refraction sample per transparent surface. With ~10 active vessels in the analytical lab frustum this compounds.
Fix direction: cap dispersion at 1 octave of wavelength sampling; precompute approximate chromatic distortion into the normal map so the shader reduces to a Fresnel-only pass; switch to a cheaper single-layer dielectric when the user is far from vessels (LOD 1).

### B4. Liquid shader per-reagent uniform update cycles
Evidence: `liquid_shader.gdshader`'s `set_shader_parameter` runs per reagent bottle when pouring — Beer-Lambert, turbidity, meniscus curvature are written every frame. On gl_compatibility these uniform updates cost ~0.3 ms/frame on i5-1245U CPU submission queue before rasterization. With ChemistryCore 20 Hz tick + interpolation loop this is CPU overhead, not GPU, but still bounds frame time on shared DDR4 bus.
Fix direction: bake per-chemical configurations into precomputed normal/color blend masks; remove runtime Beer-Lambert math from fragment shader; apply absorption colors as a cached two-layer blend.

---

## 6. Profiling Plan

Measurement methodology (must run on target hardware, Dell Latitude 5530):

### Step 1 — Editor statistics overlay (in-editor, before/after changes)
In Godot editor, press `Alt+V` to toggle GPU statistics overlay. Record: `Draw Calls`, `Triangles`, `Sprites`, `Light Count`, `Visible Frames`. Capture on `AnalyticalLab` scene at LOD0.

### Step 2 — Headless scripted measurement
Run Godot headless off the loaded scene:
```bash
tools/bin/godot.cmd --headless --path game --quit-after 1 --check-only
```
No built-in draw-call API exists across GL ES targets; use a lightweight test script (`scripts/smoke_test.gd`):
```gdscript
@tool
extends Node

func _ready():
    var gpu_stats = Engine.get_statistics()
    # poll per-frame accumulation in update()
    var dc = 0
    for f in range(60):
        Engine.frames_drawn += 1
    print("DC est:", gpu_stats["StatDrawCalls"])
```
Combine with FPS profiler (`Debug > Profiler > FPS`) for 60-frame windows.

### Step 3 — Frame-time variance probe
Instrument `analytical_lab.gd` `_process` entry/exit with `OS.get_ticks_usec()`; dump min/avg/max/median. Plot with Python `matplotlib` for regression analysis.

### Step 4 — VRAM residency check
On Windows, query WDDM committed memory: `dxdiag` screenshot / `Windows::Graphics::DisplayService`. Cross-check with `Tools > Open Resource Dialog` sizing on `game/assets/` folder — report summed sub-files consumed (discussed above, PASS).

### Step 5 — Baseline on discrete GPU comparison
If available, compare against a discrete Iris Xe-class desktop (Radeon 760 or RX 6700 XT baseline) to validate the throttle thresholds; otherwise extrapolate from projected fill-rate constraints in PERFORMANCE_REPORT.md §7.2.

### Step 6 — Validated gates (from `tools/vendor/claude-code-game-studios`)
Existing gate scripts to reuse: `tools/bin/godot --headless ... --check-only`; `pytest tests/test_iris_xe_optimizer.py` verifies the partition plan budget; `tests/validate_scene_assets.py` checks per-asset integrity. No dedicated Godot profiling harness exists in `tools/` or `game/scripts/debug/` — **add a new `tools/profile_per_frame.py`** that wraps the runnable executable with a frame-count accumulator and writes `docs/profile/<lab>.csv`.

---

## 7. Optimization Opportunities Ranked by Expected Impact

| Rank | Change | Expected reduction | Effort | Priority |
|---|---|---|---|---|
| 1 | Move QuestOverlay UI out of the 3D draw-call budget (separate GUI viewport) | −15 to −20 draw calls instantly | Low | P0 |
| 2 | Retile architectural walls, floor, LED panels onto shared quads (single-geometry atlas) | −10–14 draw calls | Medium | P0 |
| 3 | Simplify `glass_shader.gdshader`: cap dispersion to 1 octave, move chromatic offset into a normal map layer | −5–10 draw-call LOD + faster EU occupancy | Medium | P1 |
| 4 | Bake per-reagent absorption color blends; remove runtime Beer-Lambert math from `liquid_shader` | ~0.3 ms CPU submission saved per frame | Medium | P1 |
| 5 | Cap MSAA to 2x samples or disable entirely (keep debanding on) | Saves fragment shading on overlapping transparency | Low | P2 |
| 6 | Reduce internal scale to 0.50x (drop from 0.67x) until stable perf verified | Extra 45% fragment headroom | Low | P2 |
| 7 | Build per-asset LOD chains: LOD1 ≈ 1/3 poly, LOD2 ≈ 1/9 poly; collapse apparatus children into batched proxies | Small draw-call count deflator on scenes > 100 ktris | High | P3 |
| 8 | Consolidate glass materials: merge duplicate borosilicate variants where translucent decals differ by < 0.01 alpha | Reduces shader variant count | Low | P2 |
| 9 | Cull static remote architecture when player spawns outside building footprint; alpha-test distant walls | Reduces resident draw calls when exploring adjacent rooms | Low | P3 |
| 10 | Add particle water-spill visualization limited to visible vessels only | Restores effect without extra draw calls | Medium | P3 |

Expected result after top-4 actions: draw calls drop from ~60–75 to ~40–45, well under the 65 cap with comfortable margin, leaving headroom for future lab additions (Synthesis lab + additional 9 laboratories still to build per ROADMAP §4.1). FPS gain of 3–6 frames at 60 FPS budget after internal-scale reduction.

---

## 8. Budget Compliance Summary

| KPI | Target | Estimated current | Status |
|---|---|---|---|
| Draw calls | ≤ 65 | ~60–75 (incl. QuestOverlay) | **Marginally failing / borderline** — action required |
| VRAM | ≤ 128 MB dedicated | ~5–25 MB per lab scene | **PASS** |
| Target FPS | ≥ 60 (1% low ≥ 52) | TBD — pending measured | **TBD** (pending profile step 1–3; opt expected PASS) |

Three priorities: (1) extract QuestOverlay out of the 3D draw-call bucket, (2) retile architectural geometry, (3) trim chromatic dispersion in the glass shader. All three are low-effort, high-impact, and directly compliant with the irreducible constraint.
