# Asset generation — materials from Google image models

The project has two ways to get photoreal surface maps. Both write into
`game/assets/textures/` and record a manifest so a texture can always be traced
back to the prompt and model that produced it.

## Access reality check (read this first)

- A **Google AI Pro subscription** covers the Gemini app. It does **not** create
  API credentials. API keys come from <https://aistudio.google.com/apikey>.
- **`GEMINI_API_KEY` is not set** in this environment (`GEMINI_API_KEY`,
  `GOOGLE_API_KEY`, `GOOGLE_AI_API_KEY` all absent). Nothing has been generated
  with Nano Banana yet — the pipelines are ready, the credentials are not.
- The browser bridge drives the **web app**, which is an unsupported interface.
  It can break whenever the UI changes, and automated access is restricted by
  Google's terms. Treat it as a convenience for a signed-in personal session,
  not as a production asset pipeline.

| Model | API id | Use |
|---|---|---|
| Nano Banana | `gemini-2.5-flash-image` | fast iteration on material ideas |
| Nano Banana Pro | `gemini-3-pro-image-preview` | final 2K/4K material detail |

## Path A — API (preferred)

```bash
export GEMINI_API_KEY=...                     # AI Studio key
python tools/generate_textures.py --model nano-banana-pro
python tools/generate_textures.py --model nano-banana --only floor_epoxy
python tools/generate_textures.py --dry-run   # prompts + manifest, no network
```

Output per material:

```
game/assets/textures/T_<id>_BC.png    albedo, prompted as seamless
game/assets/textures/T_<id>_N.png     normal map derived from albedo luminance
game/assets/textures/manifest.json    model id, full prompt, status, paths
```

The normal map is a luminance-height derivation, not a bake. It breaks a flat
surface under grazing light; it is not a substitute for a scanned normal.

Material ids: `floor_epoxy`, `wall_panel`, `benchtop_phenolic`, `steel_brushed`,
`ceiling_tile`, `safety_yellow`, `hazard_stripe`.

## Path B — browser bridge (signed-in session)

The bridge uses its own Chrome profile in `.cache/chrome-profile`; it never
touches your daily Chrome profile (which is locked while Chrome runs) and never
handles a password.

```bash
python tools/google_bridge.py --check            # reports SIGNED_IN / SIGNED_OUT
python tools/google_bridge.py --login            # visible window, sign in by hand
python tools/google_bridge.py --check --headless # confirm the session persisted

python tools/google_bridge.py --prompt "Seamless tileable texture, orthographic \
top-down, flat even lighting, no shadows, no text or watermark. Dark slate-grey \
laboratory epoxy resin floor, satin sheen, fine aggregate speckle, 2k, PBR albedo only." \
  --out game/assets/textures/T_floor_epoxy_BC.png --headless
```

Current state: **SIGNED_OUT** in the dedicated profile. Sign in once with
`--login`, then generation can run headless.

Limits of this path: it saves the displayed render (roughly display resolution),
not the original download, so it suits look-development and small props rather
than 4K hero materials. For finals, use Path A or the download button in the UI.

## Wiring generated maps into the game

The runtime lab is built procedurally in `game/scripts/visual/lab_cinematics.gd`
(`_retint_architecture`), so binding a map is a few lines:

```gdscript
var floor_tex := load("res://assets/textures/T_floor_epoxy_BC.png") as Texture2D
if floor_tex != null:
    floor_mat.albedo_texture = floor_tex
    floor_mat.uv1_scale = Vector3(4.0, 4.0, 1.0)
    floor_mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
```

Godot imports the PNG on next launch; no `.import` file needs to be written by
hand. Keep `albedo_color` at white when a map is bound, or the texture gets
multiplied twice.

## Until credentials exist

`_roughen()` in `lab_cinematics.gd` already gives the floor and benchtop a
noise-driven roughness map (tiled, anisotropic filtered) so those surfaces are
not perfectly uniform. That is a stopgap for CG-flatness, not a replacement for
real material maps.
