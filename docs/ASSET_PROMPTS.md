# Build-Time Asset Prompts — Nano Banana & Veo

These prompts are written to be pasted into Google AI Pro tools (Nano Banana Pro /
Nano Banana 2 for stills, Veo for video). They are **build-time only**: export the
result, drop it into the path listed in `game/data/media/manifest.json`, and the
game loads it as a normal asset. Nothing in the runtime calls Google.

Hard rules used throughout (anti-slop):
- no text, no logos, no watermarks, no UI overlays baked into the image
- no glossy plastic CGI look, no over-saturated teal/orange grade
- physically plausible glass, metal, dust and wear
- consistent lighting direction and color temperature across a set
- 16:9 for environments and video, 1:1 for icons, 3:4 for character sheets

## 1. Brand sigil (Nano Banana Pro)

> A single alchemical sigil for a laboratory RPG called Athanor Ascension: a thin
> engraved brass circle enclosing a compact athanor furnace silhouette merged with
> a round-bottom flask, one triangle and one horizontal line, minimal geometry,
> symmetrical, flat vector-like rendering on transparent background, muted brass
> and pale cyan patina, archival alchemy manuscript precision, no text, no letters,
> no gradients, no glow, centered, 1:1.

Negative: `text, letters, watermark, 3D render, bevel, chrome, neon, busy details`.

Path: `game/assets/branding/sigil.png` (also export SVG if available).

## 2. Character creation portraits (Nano Banana Pro)

Four species, same framing and light so they read as one set:

> Head-and-shoulders character portrait, neutral dark laboratory background,
> soft key light from camera left at 4500 K, practical rim light from a fume hood
> on the right, documentary photography realism, visible skin texture and pores,
> calm neutral expression, work clothes with subtle chemical stains, no jewelry,
> no text, 3:4.

Variants:
1. **Human** — mid-30s, weathered, short dark hair, small burn scar on left forearm.
2. **Sylvan (plant-kin)** — bark-like skin plates along the jaw, moss at the
   collar, human-like eyes, no antlers, no elf ears.
3. **Cinder-kin** — charcoal skin with fine glowing seams at the knuckles, heat
   shimmer only at the shoulders, no horns, no demon styling.
4. **Deep-kin** — pale blue-grey skin, small translucent eyelid ridge, wet-looking
   hair, no fish scales, no gills on the neck.

Negative: `fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text`.

## 3. Laboratory environments (Nano Banana Pro, 16:9)

Base prompt:

> Wide interior photograph of a working scientific laboratory, 35 mm lens at eye
> height, practical fluorescent and task lighting, realistic material wear, faint
> dust in the air, no people, no text, no logos, documentary architectural
> photography, natural color, 16:9.

Per lab, append:
- **Analytical**: HPLC and GC-MS benches, nitrogen cylinders chained to the wall,
  sample trays, laminated SOP binders, scuffed epoxy floor.
- **Synthesis**: two fume hoods, rotary evaporator, Schlenk line, solvent cabinet,
  blast shield, fire extinguisher, coiled cooling hoses.
- **Radiochemistry hot cell**: leaded glass window, remote manipulators, warning
  trefoil signage (symbol only, no words), concrete walls, gamma survey meter.
- **Accelerator hall**: concrete tunnel, blue dipole magnets, beam pipe, cable
  trays, radiation interlock pillars, cold industrial lighting.
- **Fusor workshop**: stainless vacuum chamber on a steel bench, turbopump, HV
  feedthrough, deuterium regulator, neutron survey meter, coiled ballast resistor.
- **Genomics**: separated pre- and post-PCR rooms, thermal cyclers, gel rig,
  sequencer, blue transilluminator glow, cold clean lighting.
- **Cleanroom**: ISO 5 bay, bunny suits hanging, wafer tools, particle counter,
  pale yellow lithography light.
- **Pilot plant**: columns, heat exchangers, PLC control room glass, relief valves,
  steam trace lines, industrial grime.
- **Microgravity**: orbital lab module, strapped equipment, handrails, Velcro
  patches, Earth limb through a small window, no floating hair cliché.
- **Cryogenic**: dewars, transfer lines, oxygen monitor, frost on fittings,
  condensation, cold blue-grey palette.

Negative: `people, text, logo, hologram UI, sci-fi blue glow, lens flare, oversaturated, sterile showroom`.

## 4. Loading / menu background loop (Veo)

> Slow cinematic dolly through a dim laboratory at night, 24 fps, shallow depth of
> field. Foreground: a round-bottom flask with gently boiling amber liquid and a
> reflux condenser. Midground: a distillation column with visible vapour pulses and
> a burette dripping into a beaker. Background: racks of glassware, one warm task
> lamp, dust motes in the light beam. No people, no text, no camera shake, no
> speed ramps, seamless loop, muted teal and amber palette, photoreal, 16:9, 8 s.

Negative: `text, logo, people, hands, fast motion, flicker, morphing glass, extra fingers`.

## 5. Intro story clip (Veo, 10–12 s, three shots)

1. **Macro**: a brass key turns in an old furnace door; sparks, dust, warm key light.
2. **Wide**: a young alchemist (matching the chosen character portrait) steps into
   a converted industrial hall; glassware catches the light; no dialogue.
3. **Close**: hands lift a beaker; liquid catches a cyan rim light; cut to title card
   space (leave the center empty for the game's own title overlay).

Prompt suffix: `handheld 35 mm, natural motion blur, practical light only, no text,
no lens flare, no slow-motion, realistic physics, 24 fps`.

## 6. Apparatus icons (Nano Banana 2, 1:1)

> Single laboratory object, centered, three-quarter view, isolated on transparent
> background, soft studio light, matte painted technical illustration style with
> visible material grain, no cast shadow, no text, 1:1.

Objects: beaker, Erlenmeyer flask, round-bottom flask, burette, analytical balance,
Bunsen burner, magnetic stirrer, reflux condenser, rotary evaporator, vacuum pump,
thermal cycler, NMR tube, fusor chamber, dipole magnet, lead pig, cleanroom hood.

Negative: `text, label, reflection of studio, multiple objects, cartoon outline, glow`.

## 7. Import checklist

1. Export stills as PNG (sRGB, no alpha unless stated), video as H.264 MP4.
2. Keep the file name identical to `manifest.json` (`id` field).
3. Run the Godot importer; do not commit 4K sources — 2048 px long edge max for
   stills, 1920×1080 for video loops.
4. Check the asset against the manifest `fallback` entry: the game must still run
   with the fallback procedural drawing if the file is absent.
5. Record the prompt ID and model in `manifest.json` under `provenance`.
