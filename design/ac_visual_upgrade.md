# Assassin's Creed Visual Upgrade — Design Specification

**Project:** Athanor Ascension (ChemLab)  
**Target:** Godot 4.7.2, gl_compatibility renderer, Intel Iris Xe (128 MB VRAM, ≤65 draw calls, 0.67× internal + CAS upscaling)  
**Date:** 2026-11-06  

---

## 1. Visual Identity — Three Pillars

| Pillar | AC Source | Lab Mapping |
|--------|-----------|-------------|
| **Architectural Gravitas** | Heavy stone, visible structure, massing | Exposed concrete/steel structure, heavy equipment frames, visible load paths, industrial massing |
| **Chiaroscuro Lighting** | Strong directional key + deep shadows | Replace flat 4000K fluorescent with 3-light setup: dramatic key, controlled fill, rim separation |
| **Readability First** | Silhouette clarity, navigation aids, high contrast | Apparatus readable at distance, hazard states instantly visible, HUD fades when not needed |

**Explicitly NOT doing:** Fantasy elements, historical settings, parkour mechanics, magical effects, non-diegetic UI.

---

## 2. Color Palette (Exact Hex Codes)

| Role | Hex | sRGB | Use Cases |
|------|-----|------|-----------|
| Background | `#1A1C1E` | (26, 28, 30) | Deep near-black, main UI bg, screen bg |
| Mid-tone | `#3A3F44` | (58, 63, 68) | Panel backgrounds, secondary surfaces |
| Highlight | `#6B7278` | (107, 114, 120) | Disabled text, subtle borders, inactive icons |
| Accent Primary | `#D97706` | (217, 119, 6) | **Signature copper-amber** — active elements, focus, highlights, CTAs |
| Accent Secondary | `#00A8A8` | (0, 168, 168) | **Verdigris cyan** — scientific readouts, reagent tags, scanner UI |
| Danger/Warning | `#C41E3A` | (196, 30, 58) | Critical alerts, radiation, incapacitation, errors |

**Derived tones:**
- Accent Primary hover: `#F08C1A` (lighter 15%)
- Accent Primary pressed: `#B05F05` (darker 15%)
- Glass reflection tint: `#D97706` at 8% opacity
- Emissive Cherenkov: `#00A8A8` with bloom threshold 1.2

---

## 3. Lighting Design

### 3-Light Rig (replace flat fluorescent)

| Light | Type | Angle | Color Temp | Intensity | Purpose |
|-------|------|-------|------------|-----------|---------|
| **Key** | Directional | 45° elevation, -30° azimuth | 5600 K (cool daylight) | 1500 lux | Primary form definition, casts shadows |
| **Fill** | Directional | 30° elevation, 150° azimuth | 4000 K (neutral) | 600 lux | Softens shadows, keeps readability |
| **Rim** | Spot (narrow) | 10° elevation, behind player | 5000 K | 300 lux | Separation from background, silhouette pop |

**GI / Ambient faking on Iris Xe:**
- Screen-Space Ambient Occlusion (SSAO) — radius 0.8m, intensity 0.6
- Baked lightmaps for static geometry (analytical bench, walls, heavy equipment)
- Light probes (irradiance volumes) at 2m grid for dynamic objects
- No real-time GI — too expensive

**Emissive uses (cheap, high impact):**
- Display panels: `#00A8A8` @ 200 nits
- Status LEDs: `#D97706` (active), `#C41E3A` (warning), `#00A8A8` (idle)
- Cherenkov glow (accelerator/fusor): `#00A8A8` with additive blend, animated noise
- Flame (Bunsen/burner): `#D97706` → `#F08C1A` gradient, flicker shader

**Draw call budget:** 4 lights = 4 shadow passes max. Use cascaded shadow maps (2 cascades, 512×512 each). Static objects: baked only.

---

## 4. HUD / UI Language

### Typography (2 fonts max)

| Font | Weights | Use |
|------|---------|-----|
| **Roboto Mono** | 400, 500, 700 | All data readouts, numbers, codes, terminal text |
| **Open Sans** | 400, 600, 700 | UI labels, buttons, quest text, tooltips |

### Color Rules

| State | Text | Background | Border/Accent |
|-------|------|------------|---------------|
| Default | `#E8ECEF` (Highlight + 20%) | `#1A1C1E` @ 90% | `#3A3F44` |
| Active/Focus | `#FFFFFF` | `#1A1C1E` @ 95% | `#D97706` (2px) |
| Warning | `#F08C1A` | `#1A1C1E` @ 95% | `#D97706` |
| Danger/Critical | `#FF6B6B` | `#2D1010` @ 95% | `#C41E3A` |
| Disabled | `#6B7278` | `#1A1C1E` @ 70% | `#3A3F44` |

### Fade Logic (AC-style contextual HUD)

| Element | Fade In Trigger | Fade Out Delay |
|---------|-----------------|----------------|
| Vitals bar | Damage taken, radiation > 0.01 mSv, injury added | 5s no change |
| Compass/Quest | Lean (Q/E), objective update, new quest | 3s after lean release |
| Reagent Scanner | Interact with apparatus (E), scan mode | 2s after interact release |
| Inventory | Tab / I key, crafting open | Immediate on close |
| Codex entry | Discovery, first synthesis of reagent | Manual dismiss |

**Implementation note:** Modify `game/ui/vitals_hud.gd` — add `visible_alpha` property, animate with `Tween`, hook into `PlayerVitals` signals.

---

## 5. Camera / Cinematography

### First-Person Lab Camera Behaviour

| Behaviour | Parameter | AC Reference |
|-----------|-----------|--------------|
| **Lean tilt** | ±5° roll on Q/E lean, 0.15s ease | AC corner lean |
| **Surface bob** | Amplitude 0.02m, freq 1.8Hz (walk), 0.8Hz (stand) | AC grounded feel |
| **Quick 180°** | Double-tap Sprint + Back, 0.3s snap | AC combat turn |
| **Entry transition** | 0.5s dolly + FOV 75→65, low angle hero | AC viewpoint reveal |
| **Exit transition** | 0.4s pull back, slight height gain | AC leaving area |
| **Interaction zoom** | On apparatus focus: FOV 65→55, 0.2s | AC inspect object |

**FOV defaults:** 70° (walking), 65° (stationary at bench), 55° (inspecting)

**No third-person implementation** — the concept doc §3.3 mentions "optional third-person toggle" but AC visual language works in first-person. If implemented later: shoulder offset, orbit distance 2.5m, collision push-in.

---

## 6. Material Upgrades

### Per-Category Shader Parameters

| Material | Base (Current) | AC Upgrade | Shader Params |
|----------|----------------|------------|---------------|
| **Borosilicate Glass** | IOR 1.458, clear | IOR 1.458, subtle copper reflection tint | `reflection_tint = #D97706 @ 0.08`, `roughness = 0.02`, `anisotropy = 0.1` |
| **Metals (steel, brass, copper)** | Clean, uniform | Brushed, worn, roughness variation | `roughness_map` (noise), `wear_mask` (edges), `specular = 0.6-0.9` |
| **Epoxy Benchtop** | Flat color | Scuffs, chemical stains, subtle specular | `detail_normal` (scratches), `stain_map` (procedural), `roughness = 0.35` |
| **Concrete/Steel Architecture** | Clean | Dirt, wear, AO in normal map | `ao_detail` (baked), `grime_mask` (procedural), `roughness = 0.7` |
| **Cherenkov/Emissive** | Basic | Animated noise, additive bloom | `emission = #00A8A8 * noise(t)`, `bloom_threshold = 1.2` |

**Texture compliance (Iris Xe):**
- All textures ≤ 1024×1024
- ORM packed (Occlusion=R, Roughness=G, Metallic=B)
- Normal maps BC5, albedo BC7, ORM BC7
- Draco compression on all glTF meshes
- Texture atlas for apparatus UI icons (1024×1024, 16×16 grid)

---

## 7. Performance Budget Allocation

| Budget | Target | Allocation |
|--------|--------|------------|
| **Draw calls** | ≤ 65 | Static geometry: 18 (batched), Dynamic: 12, UI: 8, Particles: 12, Lights: 4 shadows = 54 max |
| **VRAM** | ≤ 128 MB | Textures: 80 MB (atlas + lightmaps), Meshes: 25 MB (Draco), Shaders: 8 MB, Buffers: 15 MB |
| **Shader variants** | ≤ 12 | 3 base (opaque, glass, emissive) × 4 quality (full/med/low/ultra-low) |
| **LOD steps** | 2 per asset | LOD0: full, LOD1: 50% tris, LOD2: 15% tris (billboard for distant) |

**Texture atlas strategy:**
- Atlas A: Apparatus UI icons (1024²)
- Atlas B: Lab surface details (2048² → downsampled to 1024² at import)
- Atlas C: Companion textures (512²)
- Atlas D: Particle flipbooks (512²)

---

## 8. Implementation Roadmap (5 Phases, Screenshot-Verifiable)

| Phase | Deliverable | Verification Screenshot | Files Touched |
|-------|-------------|-------------------------|---------------|
| **1** | Lighting rig + palette + HUD refresh | Analytical bench: new 3-light, copper/verdigris HUD, no flat fluorescent | `default_env.tres`, `game/ui/vitals_hud.gd`, `game/scripts/chemlab_hud.gd`, shaders |
| **2** | Material upgrades + shader tweaks | Glassware with copper reflection, brushed metals, worn benchtop | Material `.tres` files, `materials/glass.gdshader`, `materials/metal.gdshader` |
| **3** | Full HUD/UI with fade logic | Vitals fades in on damage, compass on lean, scanner on interact | `game/ui/*.gd`, `game/scripts/input/input_manager.gd` (lean detection) |
| **4** | Camera behaviour + transitions | Lean tilt, surface bob, entry/exit dolly, interaction zoom | `game/scenes/player/player_controller.gd`, camera logic |
| **5** | Performance audit + final screenshots | `docs/screenshots/ac_bench_final.png`, draw call counter ≤ 65, VRAM ≤ 128 MB | Profiler script, all above |

**Phase 1 is achievable in one session** — lighting, palette, HUD refresh are code/tres changes only, no new assets required.

---

## 9. File Implementation Map

| File | Purpose | Status |
|------|---------|--------|
| `game/project.godot` | Renderer, display, autoload config | ✅ Exists |
| `game/default_env.tres` | WorldEnvironment (lighting, SSAO, tonemap) | ❌ Create/Update |
| `game/ui/vitals_hud.gd` | Vitals bar, dose, injuries | ✅ Exists — modify |
| `game/scripts/chemlab_hud.gd` | Compass, scanner, inventory, codex | ❌ Create |
| `game/scripts/input/input_manager.gd` | Lean detection, camera inputs | ✅ Exists — extend |
| `game/scenes/player/player_controller.gd` | Camera behaviour | ✅ Exists — extend |
| `game/materials/glass.gdshader` | Borosilicate with AC tint | ❌ Create |
| `game/materials/metal.gdshader` | Brushed/worn metal | ❌ Create |
| `game/materials/epoxy.gdshader` | Worn benchtop | ❌ Create |
| `game/materials/emissive.gdshader` | Cherenkov, displays, flame | ❌ Create |
| `game/assets/materials/atlas_*.png` | Texture atlases | ❌ Generate (Blender → PNG) |

---

*End of design specification. This document is the single source of truth for the AC visual upgrade implementation.*