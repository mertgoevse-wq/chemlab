# Google Nano Banana & Emerging Google AI Tools — Molecular Rendering & Lab Environment Generation Spec
# Version 1.0 — 2026-11-02

## 1. Overview: "Nano Banana" (Gemini 2.5 Flash Image)

"Nano Banana" is Google DeepMind's codename for the image-generation capability of
Gemini 2.5 Flash Image (released Aug 2025). It is a native multimodal model:
text + image in, image out, with strong consistency, editing, and style control.
Key capabilities relevant to molecular rendering and lab environments:

- Text-to-image generation at up to 1024x1024 (square/landscape/portrait).
- Image-to-image editing (inpainting, outpainting, style transfer, object add/remove).
- Multi-turn conversational editing with identity/consistency lock.
- High-fidelity text rendering inside images (labels, formulas, signage).
- Photorealistic + stylized (scientific illustration) output.
- Safety filters for hazardous content (relevant for lab safety imagery).

API endpoint (Vertex AI / AI Studio):
  POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent

Request body:
```json
{
  "contents": [{
    "parts": [
      { "text": "<prompt>" },
      { "inlineData": { "mimeType": "image/png", "data": "<base64>" } }
    ]
  }],
  "generationConfig": {
    "responseModalities": ["TEXT", "IMAGE"],
    "imageConfig": { "aspectRatio": "16:9" }
  }
}
```

Response: candidate.parts[] contains inlineData with mimeType "image/png" + base64.

Python SDK:
```python
from google import genai
from google.genai import types
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
resp = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=[prompt],
    config=types.GenerateContentConfig(response_modalities=["TEXT","IMAGE"]),
)
img = resp.candidates[0].content.parts[0].inline_data.data  # bytes
```

## 2. Molecular Rendering Pipeline Using Nano Banana

### 2.1 Goal
Generate publication-quality 2D molecular illustrations and 3D-consistent molecular
diagrams (ball-and-stick, space-filling, skeletal) for compounds in the chemlab
asset catalog, with optional lab-environment context.

### 2.2 Input data structures
```python
@dataclass
class MoleculeRenderRequest:
    smiles: str
    style: Literal["ball_stick", "space_fill", "skeletal", "wireframe", "ribbon"]
    view: Literal["front", "side", "top", "isometric", "exploded"]
    background: Literal["transparent", "white", "dark", "lab_bench", "grid"]
    labels: bool = True          # show atom labels / formula
    highlight_atoms: list[int] = field(default_factory=list)  # atom indices
    highlight_bonds: list[tuple[int,int]] = field(default_factory=list)
    resolution: tuple[int,int] = (1024, 1024)
    seed: int | None = None
```

### 2.3 Prompt template (deterministic)
```
Scientific molecular illustration, {style} representation of molecule with SMILES: {smiles}.
View: {view}. Background: {background}. Atom colors follow CPK convention:
C gray, H white, O red, N blue, S yellow, Cl green, P orange.
Bonds: single solid, double two parallel, triple three parallel.
{labels ? "Label each atom with its element symbol in small sans-serif." : ""}
{highlights ? "Highlight atoms " + str(highlight_atoms) + " with a glowing cyan halo." : ""}
Clean vector-like aesthetic, no shadows beyond soft ambient occlusion, sharp edges,
high contrast, suitable for textbook. No watermark, no text artifacts.
```

### 2.4 Consistency strategy (multi-view)
For 3D-consistent multi-view renders, use image-to-image chaining:
1. Generate canonical front view (text-to-image).
2. Feed front view as reference image with prompt "same molecule, rotated 90 deg to the right, identical style and colors, consistent lighting".
3. Repeat for top/isometric.
4. Use Nano Banana's identity-lock to keep atom colors/bond thickness stable across views.

### 2.5 Post-processing
- Remove background via rembg or alpha channel if transparent requested.
- Upscale with Google's Imagen upscaler or Real-ESRGAN (2x/4x).
- Vectorize skeletal formulas with potrace for SVG export (optional).

### 2.6 Validation
- RDKit canonical SMILES round-trip: parse generated labels? (manual QA)
- Atom count check: rendered molecule atom count matches RDKit parsed count (human/automated vision check via Gemini 2.5 Pro vision).
- Color fidelity: sample pixel colors, compare to CPK palette (tolerance dE < 5).

## 3. Lab Environment Generation Pipeline

### 3.1 Goal
Generate photorealistic laboratory scenes (benches, fume hoods, equipment layouts)
as background plates or concept art for the ChemLab 3D scene, plus texture
reference images for the photogrammetry pipeline (Section 4 of PHOTOGRAMMETRY_PIPELINE_SPEC.md).

### 3.2 Scene descriptor
```python
@dataclass
class LabSceneRequest:
    scene_type: Literal["bench_closeup", "fume_hood", "stockroom", "instrument_room", "classroom_lab"]
    equipment: list[str]          # e.g. ["erlenmeyer flask", "bunsen burner"]
    style: Literal["photoreal", "stylized_illustration", "blueprint", "isometric_3d"]
    lighting: Literal["fluorescent_overhead", "warm_lamp", "natural_window", "dramatic"]
    time_of_day: Literal["morning", "afternoon", "evening"] = "afternoon"
    clutter_level: float = 0.3    # 0..1
    safety_props: bool = True     # goggles, gloves, spill kit visible
    resolution: tuple[int,int] = (1920, 1080)
    seed: int | None = None
```

### 3.3 Prompt template
```
{style} photograph of a {scene_type} laboratory, {lighting} lighting, {time_of_day}.
Equipment on bench: {", ".join(equipment)}. Clutter level {clutter_level:.0%}.
Safety equipment visible: {safety_props}. Clean modern university chemistry lab,
white/gray epoxy benchtop, tiled walls, organized. No people. High detail,
sharp focus, 35mm lens, f/2.8. No watermark.
```

### 3.4 Texture reference generation (for photogrammetry)
For assets lacking photos, generate multi-angle synthetic reference images:
- 8 views around object (every 45 deg) at fixed elevation 30 deg.
- Consistent lighting prompt suffix: "neutral studio lighting, white seamless background, soft shadow".
- Feed into COLMAP pipeline (S3) as if real photos; quality gates apply.

### 3.5 Lab safety imagery constraints
- Never generate images depicting hazardous procedures without safety context.
- Always include PPE in generated lab scenes (goggles, lab coat, gloves).
- Refuse prompts requesting "explosion", "toxic gas release", "unprotected handling".

## 4. Integration with ChemLab Repo

### 4.1 New module: src/ai_render/
```
src/ai_render/
  client.py          # Gemini Nano Banana wrapper
  molecule.py        # MoleculeRenderRequest + render_molecule()
  lab_scene.py       # LabSceneRequest + render_lab_scene()
  prompts.py         # prompt templates
  postprocess.py     # bg removal, upscale, validation
  cache.py           # content-addressed cache by (smiles, params) hash
```

### 4.2 CLI
```bash
python -m src.ai_render.molecule --smiles "CCO" --style ball_stick --view isometric --out assets/molecules/ethanol_iso.png
python -m src.ai_render.lab_scene --scene bench_closeup --equipment "beaker,flask" --out assets/scenes/bench.png
```

### 4.3 Caching
- Cache key = sha256(smiles + json.dumps(params, sort_keys=True)).
- Store in storage/ai_render_cache/<key>.png + <key>.json (metadata).
- Skip API call if cached and validated.

### 4.4 Rate limiting
- Token bucket: 10 req/min (free tier), 60 req/min (paid).
- Exponential backoff on 429/503.
- Batch jobs via async with concurrency limit 4.

## 5. Other Emerging Google AI Tools

### 5.1 Imagen 3 / Imagen 4 (Vertex AI)
- Higher fidelity photorealism, better text rendering.
- Use for final hero images; Nano Banana for iteration/editing.
- API: `imagen-3.0-generate-002` / `imagen-4.0-generate-001`.
- Supports mask-based editing and upscaling to 4K.

### 5.2 Veo 2 / Veo 3 (video generation)
- Generate short lab procedure videos (5-8s) for tutorial content.
- Input: text prompt or image (first frame) + prompt.
- Use for "reaction animation" previews where 3D sim is too heavy.
- Output: MP4, up to 1080p, 5-8 seconds.

### 5.3 Gemini 2.5 Pro (vision + reasoning)
- Validate rendered molecules: send image + SMILES, ask model to verify atom count, bond orders, labels.
- Generate alt-text and accessibility descriptions for all rendered images.
- Prompt: "Given this molecular image and SMILES {smiles}, list any discrepancies in atom count, bond order, or labeling. Return JSON."

### 5.4 NotebookLM
- Generate study guides / audio overviews from lab scenario documents.
- Use for educational content layer on top of ChemLab scenarios.

### 5.5 Google AI Studio / Vertex AI Agent Builder
- Orchestrate multi-step rendering pipelines as agents.
- Function calling to RDKit (via Python tool) + Nano Banana (image gen) + Imagen (upscale).

## 6. Quality Gates & Validation

| Gate | Metric | Threshold |
|------|--------|-----------|
| Atom count match | vision model check | 100% |
| CPK color fidelity | dE (CIE76) | < 5 |
| Background cleanliness | alpha/white border pixels | < 0.5% |
| Text legibility | OCR confidence on labels | > 0.9 |
| Lab safety props | vision classifier | goggles+coat present |
| Resolution | pixels | >= requested |

## 7. Cost Estimates (USD, Nov 2026)
- Nano Banana: ~$0.04/image (1024x1024).
- Imagen 4: ~$0.06/image.
- Veo 3: ~$0.50/8s clip.
- Gemini 2.5 Pro validation: ~$0.002/image.
- Estimated monthly for 1000 molecules x 4 views = 4000 images ≈ $160.

## 8. Security & Safety
- API keys via env vars only; never commit.
- Content safety filters enabled (HARM_CATEGORY_*).
- Generated images of hazardous reactions require manual review before publication.
- Cache stores only generated artifacts, never prompts containing PII.

## 9. Testing
- Unit: prompt template rendering, cache key determinism, request validation.
- Integration: mock Gemini client; verify image bytes saved; verify cache hit.
- Visual regression: golden images with SSIM >= 0.95 threshold.
- pytest tests/test_ai_render.py
