# ChemLab: Per-Asset Visual & Physical Material Specification
**Engine:** Godot 4.7.2 Compatibility Renderer (OpenGL 3.3 / GLES3)  
**DCC Authoring:** Blender 5.2.3 LTS  
**Shader Pipeline:** `game/shaders/glass_shader.gdshader` (Borosilicate), `game/shaders/liquid_shader.gdshader` (Liquids)  
**Target Hardware:** Intel Iris Xe 80 EU (128 MB dedicated VRAM / 6 GB shared RAM staging)

---

## 1. Master Material Reference Table

| Asset Category | Master Material | Shader | IOR | Base Roughness | Primary Transmission |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Borosilicate Glassware** | `M_Borosilicate_Glass_3_3` | `glass_shader.gdshader` | 1.458 | 0.015 | 1.0 (Full dielectric) |
| **Soda-Lime / Safety Glass** | `M_Safety_Glass` | `glass_shader.gdshader` | 1.517 | 0.025 | 0.98 |
| **Aqueous Reagent Liquids** | `M_Dynamic_Liquid_Volume` | `liquid_shader.gdshader` | 1.333 | 0.02 | 0.95 (varies by turbidity) |
| **Organic Solvents** | `M_Dynamic_Liquid_Volume` | `liquid_shader.gdshader` | 1.36 – 1.38 | 0.015 | 0.95 |
| **Concentrated Acids/Bases** | `M_Dynamic_Liquid_Volume` | `liquid_shader.gdshader` | 1.35 – 1.40 | 0.02 | 0.90 |
| **Metallic Apparatus** (Stainless/Brass) | `M_Stainless_Steel` / `M_Brass_Polished` | StandardMaterial3D | N/A (Metal) | 0.15 / 0.12 | 0.0 (Opaque) |

---

## 2. Laboratory Glassware — Visual & Physical Specifications

### 2.1 Beaker (Griffin Low-Form, 50 mL – 1000 mL)

| Property | Value |
| :--- | :--- |
| **Glass Type** | Borosilicate 3.3 (Schott Duran equivalent) |
| **IOR (Blender / Godot)** | 1.458 / 1.458 (uniform `ior` in `glass_shader.gdshader`) |
| **Base Roughness** | 0.015 (fire-polished, slight manufacturing waviness) |
| **Glass Color Tint** | `RGB(0.96, 0.98, 1.0)` — cool blue-white representing ultra-low iron silica |
| **Glass Alpha** | 0.08 (shader `glass_color` alpha; refraction dominates visual) |
| **Fresnel Power** | 4.0 (Schlick approximation for $n=1.458$) |
| **Refraction Strength** | 0.035 (screen-space offset scalar) |
| **Abbe Dispersion** | 0.004 (chromatic aberration: $\Delta n \approx 0.006$ between 486–656 nm) |
| **Rim Intensity** | 0.85 (edge highlighting for meniscus visibility) |
| **Wall Thickness** | 2.0 mm (refraction depth / analytical ray-trace distance) |
| **Spout Radius** | 3.5 – 6.0 mm (geometry dependent) |
| **Graduation Marks** | Emissive ring decals at 10% volume increments; `Label3D` text at major ticks |
| **Collision** | Cylinder hull (outer) + thin cylinder (inner recipient volume) |

#### Liquid Content by Chemical Class (Beaker)
| Chemical | `liquid_color` (sRGB + Alpha) | IOR | Turbidity Base | Meniscus Curvature | Absorption Notes |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Water (DI, Distilled)** | `RGB(0.90, 0.95, 1.0, 0.20)` | 1.333 | 0.00 | 0.025 | None (pure transmittance) |
| **Copper Sulfate (CuSO₄·5H₂O)** | `RGB(0.05, 0.65, 0.95, 0.85)` | 1.333 | 0.00 | 0.025 | Deep blue, strong absorption at 800 nm |
| **Nickel Chloride (NiCl₂·6H₂O)** | `RGB(0.15, 0.85, 0.45, 0.85)` | 1.333 | 0.00 | 0.025 | Green, moderate absorption 400–500 nm |
| **Potassium Permanganate (KMnO₄)** | `RGB(0.55, 0.02, 0.65, 0.90)` | 1.333 | 0.00 | 0.025 | Intense purple, very high $\epsilon$ |
| **Sodium Hydroxide (NaOH, 1M)** | `RGB(0.90, 0.92, 1.0, 0.30)` | 1.335 | 0.00 | 0.025 | Slightly higher IOR |
| **Hydrochloric Acid (HCl, 1M)** | `RGB(0.95, 0.95, 1.0, 0.25)` | 1.334 | 0.00 | 0.025 | Near-water optical properties |
| **Silver Nitrate (AgNO₃, 0.1M)** | `RGB(0.92, 0.94, 1.0, 0.40)` | 1.334 | 0.00 | 0.025 | Clear, photochromic (darkens with light) |
| **Precipitating Mix (AgCl formation)**| `RGB(0.92, 0.92, 0.90, 0.98)` | 1.335 | 0.65 → 0.95 | 0.030 | Turbidity rises as reaction proceeds |

---

### 2.2 Erlenmeyer Flask (Conical, 50 mL – 1000 mL)

| Property | Value |
| :--- | :--- |
| **Glass Type** | Borosilicate 3.3 |
| **IOR** | 1.458 (identical to beaker) |
| **Roughness** | 0.018 (slightly higher due to mold seams on conical body) |
| **Neck Inner Diameter** | 22 mm (standard taper for stopper/condenser) |
| **Wall Thickness** | 2.2 mm (base), 1.8 mm (shoulders) |
| **Graduation Marks** | Single approximate mark at nominal volume (not calibrated) |
| **Liquid Surface** | Elliptical meniscus following flask tilt (world-aligned in shader) |
| **Stir Bar Compatibility** | 25 mm PTFE magnetic follower (separate `SK_StirBar_25mm.glb`) |

#### Liquid Parameters (Same as Beaker, adjusted for volume)
- `container_height`: 0.105 m (250 mL) to 0.210 m (1000 mL)
- `container_radius`: 0.052 m (250 mL base) to 0.092 m (1000 mL base)
- `fill_amount` driven by reaction stoichiometry (0.0 – 1.0)

---

### 2.3 Titration Buret (Class A, 50 mL, PTFE Stopcock)

| Property | Value |
| :--- | :--- |
| **Glass Type** | Borosilicate 3.3, calibrated to ±0.05 mL (Class A) |
| **IOR** | 1.458 |
| **Roughness** | 0.012 (precision bore tubing) |
| **Bore Diameter** | 5.0 mm ±0.01 mm (calibrated) |
| **Wall Thickness** | 1.5 mm (thin-wall for meniscus readability) |
| **Stopcock Material** | PTFE (Teflon®) — `M_PTFE_White`, IOR N/A, Metallic 0.0, Roughness 0.15 |
| **Stopcock IOR (if glass)** | 1.458 (glass stopcock variant) |
| **Graduations** | Every 0.1 mL, major ticks every 1.0 mL (emissive decal rings) |
| **Zero Mark Position** | Top of calibrated volume (50.00 mL at top) |
| **Meniscus Reading Aid** | Schellbach stripe (blue/white ceramic backing strip) — separate mesh `SM_Buret_Schellbach.glb` with `M_Ceramic_White` / `M_Safety_Cyan` |

#### Buret Liquid Specifics
| Chemical | `liquid_color` | Notes |
| :--- | :--- | :--- |
| **NaOH (0.1 M, standard)** | `RGB(0.94, 0.96, 1.0, 0.35)` | Clear, phenolphthalein indicator added during titration |
| **HCl (0.1 M, standard)** | `RGB(0.95, 0.95, 1.0, 0.30)` | Clear |
| **EDTA (0.01 M)** | `RGB(0.90, 0.95, 0.98, 0.30)` | Clear, slight violet tint if Eriochrome Black T present |

---

### 2.4 Volumetric Flask (Class A, 100 mL – 1000 mL)

| Property | Value |
| :--- | :--- |
| **Glass Type** | Borosilicate 3.3, single calibration mark at nominal volume |
| **IOR** | 1.458 |
| **Roughness** | 0.015 |
| **Neck Inner Diameter** | 14 mm (100 mL) to 29 mm (1000 mL) |
| **Calibration Line** | Single permanent enamel ring at calibrated volume (20 °C) |
| **Stopper** | Interchangeable polyethylene (PE) or PTFE (`M_PE_Translucent` / `M_PTFE_White`) |

---

### 2.5 NMR Tube (5 mm OD, 7″ / 178 mm, Wilmad 528-PP-7)

| Property | Value |
| :--- | :--- |
| **Glass Type** | Borosilicate 3.3 (high precision, low paramagnetic impurities) |
| **IOR** | 1.458 |
| **Roughness** | 0.008 (optical quality tubing) |
| **OD / ID** | 5.00 mm / 4.20 mm (0.40 mm wall) |
| **Length** | 178 mm |
| **Cap** | Polypropylene screw cap (`M_PP_Blue`) |
| **Sample Volume** | 0.6 mL (0.55 mL minimum for spinning) |
| **Deuterated Solvent Reference** | D₂O, CDCl₃, DMSO-d₆, MeOD-d₄ — `liquid_color` near-water with `turbidity = 0.0` |
| **Spinner Turbine** | Polypropylene (separate `SK_NMR_Spinner.glb`) |

---

### 2.6 GC-MS Column (Capillary, 30 m × 0.25 mm ID × 0.25 µm df)

| Property | Value |
| :--- | :--- |
| **Column Body** | Fused silica capillary (polyimide coating) — `M_Fused_Silica` |
| **Coating IOR** | 1.46 (polyimide) / 1.458 (silica) |
| **Roughness** | 0.05 (external polyimide texture) |
| **Internal Phase** | 5% Phenyl / 95% Polydimethylsiloxane (PDMS) — modeled as liquid shader if visualized |
| **Visualization** | Typically coiled cage `SM_GCMS_Column_Coil.glb` with emissive temperature gradient |
| **Column End Caps** | Brass ferrules + graphite vespel ferrules (`M_Brass_Polished` / `M_Graphite_Vespel`) |

---

## 3. Analytical & Benchtop Apparatus

### 3.1 Analytical Balance (Sartorius Cubis II / Mettler XPR equivalent)

| Component | Material | Visual Spec |
| :--- | :--- | :--- |
| **Weighing Chamber Glass** | Borosilicate 3.3 | `M_Borosilicate_Glass_3_3`, IOR 1.458, 2.5 mm thick sliding doors |
| **Chassis / Housing** | Die-cast aluminum, powder coat | `M_Aluminum_Matte_DarkGrey`: Metallic 0.85, Roughness 0.45, Base Color `RGB(0.18, 0.18, 0.20)` |
| **Weighing Pan** | Stainless Steel 316L | `M_Stainless_Steel_Polished`: Metallic 0.95, Roughness 0.12, Base Color `RGB(0.82, 0.84, 0.86)` |
| **Draft Shield Pillars** | Anodized aluminum | `M_Aluminum_Anodized`: Metallic 0.60, Roughness 0.25 |
| **Display (TFT)** | Emissive glass panel | `M_HUD_Glass_Panel`: Emission `RGB(0.0, 1.0, 0.6)` @ 150 nits |
| **Level Bubble** | Soda-lime glass + mineral spirit | `M_Safety_Glass` + `M_Liquid_Clear_Bubble` |
| **Feet** | PTFE + rubber | `M_PTFE_White` / `M_Rubber_Black` |

**Godot Scene**: `analytical_balance.tscn` — `RigidBody3D` with fine `fill_amount` control (0.1 mg resolution via scripted animation).

---

### 3.2 Magnetic Stirrer (IKA RCT basic / Heidolph MR equivalent)

| Component | Material | Visual Spec |
| :--- | :--- | :--- |
| **Top Plate** | Ceramic (Al₂O₃) or Stainless Steel | `M_Ceramic_White`: Metallic 0.0, Roughness 0.18, Base `RGB(0.96, 0.96, 0.97)` — OR `M_Stainless_Steel_Brushed` |
| **Hotplate Indicator Ring** | Silicone / LED | `M_LED_Red_Display` (hot warning), `M_LED_Green` (stir active) |
| **Chassis** | Powder-coated steel | `M_Steel_Frame`: Metallic 0.70, Roughness 0.40, Base `RGB(0.35, 0.38, 0.40)` |
| **Control Knobs** | Polyamide (PA6) | `M_PE_Translucent`: Metallic 0.0, Roughness 0.35, Base `RGB(0.20, 0.20, 0.22)` |
| **Stir Bar** (PTFE coated Alnico V) | `M_PTFE_White` (coating) | Separate `SK_StirBar_25mm.glb` — spins via `AnimatedMeshInstance3D` |
| **Speed Display** | 7-segment LED | `M_HUD_7Segment_Red` |

**Shader Note**: The top plate uses a standard `StandardMaterial3D` with subtle normal map (`T_Stirrer_Plate_N.png`) for brushed finish. Liquid interaction handled by `liquid_shader.gdshader` on vessel contents.

---

### 3.3 Bunsen Burner (Tirrill / Meker Type)

| Component | Material | Visual Spec |
| :--- | :--- | :--- |
| **Base** | Cast iron, nickel-plated | `M_Steel_Brushed`: Metallic 0.85, Roughness 0.35, Base `RGB(0.45, 0.47, 0.49)` |
| **Barrel / Tube** | Chrome-plated brass | `M_Chrome_Polished`: Metallic 0.95, Roughness 0.08, Base `RGB(0.92, 0.93, 0.94)` |
| **Air Inlet Collar** | Rotating brass sleeve | `M_Brass_Polished`: Metallic 0.90, Roughness 0.12, Base `RGB(0.85, 0.75, 0.45)` |
| **Gas Inlet** | Brass hose barb | `M_Brass_Polished` |
| **Flame** | **Custom Shader** (`flame_shader.gdshader`) | See §4.1 below |
| **Flame Cone (Inner)** | Emissive plasma | `M_Flame_InnerCone`: Emission `RGB(1.0, 0.7, 0.2)` @ 500 nits, Alpha Blend |
| **Flame Cone (Outer)** | Luminous gas envelope | `M_Flame_OuterCone`: Emission `RGB(1.0, 0.4, 0.05)` @ 150 nits |

**Flame Physics**: Two concentric cone meshes with `flame_shader.gdshader` using Perlin noise for flicker, color temperature shift (blue inner / yellow outer), and audio-reactive modulation.

---

### 3.4 Fume Hood (ANSI/AIHA Z9.5, 6 ft / 1.8 m width)

| Component | Material | Visual Spec |
| :--- | :--- | :--- |
| **Exterior Casing** | Powder-coated 18-gauge steel | `M_FumeHood_Body`: Metallic 0.15, Roughness 0.45, Base `RGB(0.88, 0.90, 0.92)` |
| **Interior Liner** | Epoxy-coated steel / phenolic resin | `M_FumeHood_Interior`: Metallic 0.0, Roughness 0.15, Base `RGB(0.95, 0.96, 0.98)` |
| **Work Surface** | Epoxy resin / stainless steel | `M_Epoxy_Resin_Dark`: Metallic 0.02, Roughness 0.25, Base `RGB(0.12, 0.13, 0.15)` |
| **Sash Glass** | Laminated safety glass (PVB interlayer) | `M_Safety_Glass`: IOR 1.517, Roughness 0.04, Alpha 0.28, Transmission 0.92 |
| **Sash Frame** | Anodized aluminum | `M_Aluminum_Anodized` |
| **Baffle / Slots** | Stainless steel | `M_Stainless_Steel_Brushed` |
| **Exhaust Plenum** | Galvanized steel duct | `M_Steel_Frame` |
| **Interior Light** | Vapor-proof LED fixture | `M_Hood_Light`: Emission `RGB(1.0, 0.98, 0.95)` @ 2,200 lux |
| **Airflow Monitor (Magnehelic)** | Polycarbonate face + brass | `M_PC_Clear` + `M_Brass_Polished` |

**Sash Animation**: `fill_amount` equivalent controls vertical sash position (0.0 = closed, 1.0 = max 450 mm open). Sash glass mesh uses `glass_shader.gdshader` with `refraction_strength = 0.01` (thin pane).

---

## 4. Specialized Shaders & Dynamic Materials

### 4.1 Flame Shader (`flame_shader.gdshader`)

```glsl
// Core parameters driven by gas/air ratio (0.0 – 1.0)
uniform float air_fuel_ratio : hint_range(0.0, 2.0) = 0.8;
uniform float gas_pressure : hint_range(0.0, 2.0) = 1.0;
uniform vec3 inner_cone_color = vec3(1.0, 0.7, 0.2);  // Blue cone (1900 K)
uniform vec3 outer_cone_color = vec3(1.0, 0.4, 0.05); // Yellow envelope (1200 K)
uniform float flicker_speed = 12.0;
uniform float noise_scale = 0.5;

// Vertex displacement for flame "dance"
vec3 pos = VERTEX + normal * sin(TIME * flicker_speed + VERTEX.y * 20.0) * noise_scale * 0.02;

// Fragment: additive blending, emissive only
EMISSION = mix(outer_cone_color, inner_cone_color, smoothstep(0.3, 0.7, UV.y)) * intensity;
ALPHA = intensity * 0.7;
```

---

### 4.2 Liquid Shader by Chemical Class (Godot `liquid_shader.gdshader` Uniforms)

The `liquid_shader.gdshader` implements world-aligned meniscus, Beer-Lambert absorption, Mie turbidity scattering, and capillary waves. Uniforms are driven at runtime from the reagent database (`chemlab_core.reagents`).

#### Color Mapping from Molar Absorptivity ($\epsilon$)
For common aqueous reagents at standard concentrations:

| Reagent (Conc.) | $\lambda_{max}$ (nm) | $\epsilon$ (L·mol⁻¹·cm⁻¹) | `liquid_color` (sRGB) | IOR | Turbidity |
| :--- | :---: | :---: | :--- | :---: | :---: |
| **CuSO₄·5H₂O (0.1 M)** | 800 | 12 | `RGB(0.05, 0.65, 0.95)` | 1.333 | 0.0 |
| **NiCl₂·6H₂O (0.1 M)** | 395, 650 | 4, 3 | `RGB(0.15, 0.85, 0.45)` | 1.333 | 0.0 |
| **CoCl₂·6H₂O (0.1 M)** | 510, 620 | 5, 6 | `RGB(0.75, 0.35, 0.85)` | 1.333 | 0.0 |
| **KMnO₄ (0.001 M)** | 525 | 2,300 | `RGB(0.55, 0.02, 0.65)` | 1.333 | 0.0 |
| **FeCl₃ (0.1 M)** | 300, 480 | 5000, 800 | `RGB(0.85, 0.55, 0.15)` | 1.335 | 0.0 |
| **K₂Cr₂O₇ (0.01 M)** | 350, 450 | 4500, 380 | `RGB(0.65, 0.15, 0.20)` | 1.334 | 0.0 |
| **I₂ in KI (0.01 M)** | 290, 360 | 400, 700 | `RGB(0.45, 0.15, 0.60)` | 1.334 | 0.0 |
| **Phenolphthalein (pH < 8.2)** | — | 0 | `RGB(0.95, 0.95, 1.0, 0.15)` | 1.333 | 0.0 |
| **Phenolphthalein (pH > 10)** | 553 | 30,000 | `RGB(1.0, 0.35, 0.65, 0.85)` | 1.333 | 0.0 |
| **Methyl Orange (pH < 3.1)** | 465 | 28,000 | `RGB(1.0, 0.25, 0.15, 0.85)` | 1.333 | 0.0 |
| **Methyl Orange (pH > 4.4)** | 520 | 12,000 | `RGB(0.95, 0.75, 0.15, 0.85)` | 1.333 | 0.0 |
| **Bromothymol Blue (pH 6.0)** | 430, 620 | 15000, 8000 | `RGB(0.95, 0.75, 0.15, 0.85)` | 1.333 | 0.0 |
| **Bromothymol Blue (pH 7.6)** | 620 | 8000 | `RGB(0.15, 0.75, 0.85, 0.85)` | 1.333 | 0.0 |
| **Precipitate (AgCl, white)** | Mie scatter | — | `RGB(0.92, 0.92, 0.90)` | 1.335 | 0.85 |
| **Precipitate (PbI₂, yellow)** | Mie scatter | — | `RGB(0.98, 0.85, 0.15)` | 1.335 | 0.85 |
| **Precipitate (BaSO₄, white)** | Mie scatter | — | `RGB(0.94, 0.94, 0.92)` | 1.335 | 0.90 |
| **Concentrated H₂SO₄ (98%)** | — | — | `RGB(0.96, 0.96, 0.98, 0.40)` | 1.40 | 0.0 |
| **Concentrated HNO₃ (70%)** | — | — | `RGB(0.94, 0.96, 1.0, 0.35)` | 1.38 | 0.0 |
| **Ethanol (96%)** | — | — | `RGB(0.96, 0.97, 1.0, 0.20)` | 1.36 | 0.0 |
| **Acetone** | — | — | `RGB(0.95, 0.96, 1.0, 0.18)` | 1.36 | 0.0 |
| **Diethyl Ether** | — | — | `RGB(0.94, 0.95, 1.0, 0.15)` | 1.35 | 0.0 |
| **DMSO** | — | — | `RGB(0.95, 0.96, 0.98, 0.30)` | 1.48 | 0.0 |

#### Runtime Uniform Update (GDScript)
```gdscript
func set_liquid_from_reagent(reagent: Reagent, fill_ratio: float, turbidity_override: float = -1.0):
    var liq_mat = $LiquidVolume.get_surface_material(0)
    liq_mat.set_shader_parameter("fill_amount", fill_ratio)
    liq_mat.set_shader_parameter("liquid_color", reagent.liquid_color)
    liq_mat.set_shader_parameter("ior", reagent.ior)
    liq_mat.set_shader_parameter("turbidity", turbidity_override if turbidity_override >= 0 else reagent.base_turbidity)
    liq_mat.set_shader_parameter("meniscus_curvature", reagent.meniscus_curvature)
    liq_mat.set_shader_parameter("container_height", vessel_height)
    liq_mat.set_shader_parameter("container_radius", vessel_inner_radius)
```

---

## 5. Texture Naming & Packing Convention for Export

| Texture Slot | Blender Source | Export Naming | Packing |
| :--- | :--- | :--- | :--- |
| **Albedo / Base Color** | Principled BSDF Base Color | `T_<AssetName>_BC.png` | sRGB, BC7 / ASTC 4×4 |
| **Normal Map** | Normal Map Node → Principled Normal | `T_<AssetName>_N.png` | OpenGL (+Y), BC5 / ASTC 4×4 |
| **ORM** | AO (R), Roughness (G), Metallic (B) | `T_<AssetName>_ORM.png` | Linear, BC7 / ASTC 4×4 |
| **Emission** | Emission Color × Strength | `T_<AssetName>_E.png` | sRGB, BC7 |
| **Glass Transmission Mask** | Transmission Weight (grayscale) | `T_<AssetName>_Trans.png` | Linear, BC4 (R only) |

**Resolution**: All textures authored at 2048², clamped to 1024² on export via Blender Python (`image.scale(1024, 1024)`).

---

## 6. Validation Gates

Before any material or asset is promoted to `game/assets/`:
1. **IOR Verification**: Glass IOR within ±0.005 of 1.458 (Borosilicate 3.3 spec).
2. **Energy Conservation**: `Metallic + Specular + Transmission ≤ 1.05` in Principled BSDF.
3. **Texture Compliance**: No texture exceeds 1024×1024; all ORM packed correctly (R=AO, G=Roughness, B=Metallic).
4. **Shader Parameter Audit**: `liquid_shader.gdshader` uniforms match reagent database entry (CIE ΔE < 2.0 vs. spectral reference).
5. **Draw Call Budget**: Scene total ≤ 65 draw calls at LOD0.
6. **VRAM Budget**: Scene total ≤ 128 MB dedicated + 384 MB clamped texture working set.