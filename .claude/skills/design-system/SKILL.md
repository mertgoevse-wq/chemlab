---
name: design-system
description: ChemLab Visual & Physical Design System. Enforces laboratory visual aesthetics, photorealistic material design tokens (glass IOR, liquid meniscus, metal finishes), GHS chemical safety standards, and scientific HUD readability.
---

# ChemLab Design System & Physical Tokens

This skill defines the unified aesthetic and physical material tokens for the ChemLab virtual laboratory. All assets, materials, shaders, and UI overlays must conform strictly to these standards to maintain a premium, cohesive, and non-slop visual presentation.

## 1. Laboratory Environment Palette & Finishes
- **Workbench Tops**: Heavy chemical-resistant dark epoxy resin. Base color: `#1A1D20` (Hex RGB: `0.015, 0.017, 0.021`), Roughness: `0.38`, Specular: `0.45`. Matte non-reflective surface resistant to acid etching.
- **Metal Framework / Racks**: Anodized extruded aluminum and brushed 316 stainless steel.
  - Brushed Stainless: Metallic `1.0`, Roughness `0.22`, Anisotropic `0.45`, Rotation `0.25`.
  - Powder-coated Frame: `#3A414A`, Roughness `0.55`, Metallic `0.0`.
- **Fume Hood Sash**: Clear tempered laminated safety glass with light blue edge tint (`#0E2A36`), IOR `1.52`, Roughness `0.02`.
- **Flooring**: Seamless chemical-resistant pale grey epoxy with drainage fall. Base: `#7F8489`, Roughness `0.30`.

## 2. Glassware & Fluid Material Tokens
- **Borosilicate Glass (Pyrex / Schott Duran)**:
  - Material Name: `Mat_Borosilicate_Glass`
  - IOR: `1.474` (Exact physical refractive index of borosilicate glass).
  - Roughness: `0.015` (Polished optical clarity).
  - Transmission Weight: `1.0`.
  - Wall Thickness: Explicit geometry thickness of `1.8mm` to `2.5mm` (never single-sheet faces).
- **Volumetric Meniscus Token**:
  - All liquids inside cylinders and pipettes must feature a concave capillary meniscus:
    - Meniscus height $h = \frac{2 \gamma \cos \theta}{\rho g r}$
    - Geometry: Toroidal lip curve meeting glass wall at contact angle $\theta \approx 15^\circ$ for aqueous solutions on clean glass.
- **Liquid Shading & Beer-Lambert Optical Absorption**:
  - Shaded with `Principled BSDF` + `Volume Absorption`.
  - Absorption Color $= \exp(-\vec{\epsilon} \cdot c \cdot d)$.

## 3. Chemical Color & Indicator Tokens
- **Acid-Base Indicators**:
  - *Phenolphthalein*: Acidic ($\text{pH} < 8.2$): Completely transparent (`1.0, 1.0, 1.0, 0.0`); Basic ($\text{pH} > 10.0$): Deep vibrant magenta (`#D62286`).
  - *Bromothymol Blue*: Acidic ($\text{pH} < 6.0$): Bright golden yellow (`#F5B800`); Neutral ($\text{pH} \approx 7.0$): Emerald green (`#10A348`); Basic ($\text{pH} > 7.6$): Prussian deep blue (`#0B4F9C`).
- **Oscillating Reaction Palettes**:
  - *Belousov-Zhabotinsky (Ferroin)*: Reduced state $\text{Fe}^{2+}$ deep ruby red (`#A81C1C`) $\longleftrightarrow$ Oxidized state $\text{Fe}^{3+}$ sky cerulean blue (`#389FD6`).
  - *Briggs-Rauscher*: Colorless $\longrightarrow$ Warm golden amber (`#E68A00`) $\longrightarrow$ Deep starch-triiodide inky navy/black (`#0D122B`).

## 4. UI, Graduation Markings & Scientific HUD
- **Graduation Lines**: Fine ceramic baked enamel markings (`#FFFFFF` on clear glass, `#202020` on opaque ware). Line thickness `0.25mm`, sub-milliliter ticks.
- **GHS Safety Pictograms**: Compliant with UN Globally Harmonized System (GHS diamond with red border `#CC0000`, white background, black pictogram).
- **Instrument Digital Readouts**: Monospace 7-segment or high-density OLED display font (`#38E1FF` cyan on dark bezel `#0A0D12`).
