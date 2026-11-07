"""ChemLab material generation — Gemini image models (Nano Banana / Nano Banana Pro).

Generates seamless albedo maps for the laboratory surfaces, derives a tangent
space normal map from each, and writes a manifest so the exact prompts and
models used are reproducible.

    export GEMINI_API_KEY=...           # https://aistudio.google.com/apikey
    python tools/generate_textures.py --model nano-banana-pro
    python tools/generate_textures.py --dry-run        # prompts + manifest only
    python tools/generate_textures.py --only floor_epoxy steel_brushed

Models
    nano-banana       gemini-2.5-flash-image     fast iteration, cheap
    nano-banana-pro   gemini-3-pro-image-preview 4K detail, better material read

Note on access: a Google AI Pro *subscription* covers the Gemini app, not this
API. API usage needs a key from AI Studio (free tier exists, paid tier for
volume). The script refuses to guess credentials.

Output
    game/assets/textures/T_<id>_BC.png   albedo, seamless
    game/assets/textures/T_<id>_N.png    normal map derived from albedo height
    game/assets/textures/manifest.json
"""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "game", "assets", "textures")
MANIFEST = os.path.join(OUT_DIR, "manifest.json")

MODELS = {
    "nano-banana": "gemini-2.5-flash-image",
    "nano-banana-pro": "gemini-3-pro-image-preview",
}

# Prompts are written as material briefs, not as art directions: the model has
# to produce something a PBR shader can multiply, so no baked lighting, no
# shadows, no vignette, no props.
PROMPTS = {
    "floor_epoxy": (
        "Seamless tileable texture, orthographic top-down, flat even lighting, no shadows, "
        "no perspective, no objects, no text or watermark. Dark slate-grey laboratory epoxy "
        "resin floor, satin sheen, fine aggregate speckle, very subtle cloudiness from wear, "
        "faint hairline seams on a 1 metre grid, 2k, photorealistic PBR albedo only."
    ),
    "wall_panel": (
        "Seamless tileable texture, straight-on orthographic, flat even lighting, no shadows, "
        "no perspective, no text or watermark. Off-white powder-coated steel cleanroom wall "
        "panel with a fine matte orange-peel grain, one recessed seam line every panel edge, "
        "2k, photorealistic PBR albedo only."
    ),
    "benchtop_phenolic": (
        "Seamless tileable texture, orthographic top-down, flat even lighting, no shadows, "
        "no perspective, no text or watermark. Black phenolic resin laboratory benchtop, "
        "dense matte surface with faint speckle, subtle satin polish from cleaning, "
        "2k, photorealistic PBR albedo only."
    ),
    "steel_brushed": (
        "Seamless tileable texture, flat even lighting, no shadows, no perspective, no text "
        "or watermark. Brushed 304 stainless steel sheet, horizontal linear brush grain, "
        "neutral cool grey, micro-scratches, 2k, photorealistic PBR metal albedo only."
    ),
    "ceiling_tile": (
        "Seamless tileable texture, orthographic top-down, flat even lighting, no shadows, "
        "no perspective, no text or watermark. Mineral fibre acoustic ceiling tile, white "
        "micro-perforated fissured surface, square edge, 2k, photorealistic PBR albedo only."
    ),
    "safety_yellow": (
        "Seamless tileable texture, flat even lighting, no shadows, no perspective, no text "
        "or watermark. Safety yellow powder-coated steel, fine matte texture, slight wear at "
        "micro scale, 2k, photorealistic PBR albedo only."
    ),
    "hazard_stripe": (
        "Seamless tileable texture, straight-on, flat even lighting, no shadows, no "
        "perspective, no text or watermark. Diagonal black and safety-yellow hazard warning "
        "stripe tape on a steel plate, scuffed edges, 1k, photorealistic PBR albedo only."
    ),
}


def build_request(prompt: str) -> dict:
    return {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }


def call_gemini(model_id: str, api_key: str, prompt: str, timeout: int = 180) -> bytes:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_id}:generateContent?key={api_key}"
    )
    body = json.dumps(build_request(prompt)).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:600]
        raise SystemExit(f"Gemini API error {exc.code} for {model_id}: {detail}") from exc

    parts = payload.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    for part in parts:
        inline = part.get("inlineData") or part.get("inline_data")
        if inline and inline.get("data"):
            return base64.b64decode(inline["data"])
    raise SystemExit(f"No image returned by {model_id}. Raw response: {json.dumps(payload)[:600]}")


def write_normal_map(albedo_path: str, normal_path: str, strength: float = 2.0) -> bool:
    """Derive a tangent-space normal map from albedo luminance.

    This is a height proxy, not a scan: enough to break a flat surface under
    grazing light, not a substitute for a real normal bake.
    """
    try:
        from PIL import Image, ImageFilter
    except ImportError:
        return False

    img = Image.open(albedo_path).convert("L").filter(ImageFilter.GaussianBlur(0.6))
    w, h = img.size
    px = list(img.getdata())
    out = Image.new("RGB", (w, h))
    data = []
    for y in range(h):
        for x in range(w):
            xl, xr = (x - 1) % w, (x + 1) % w
            yu, yd = (y - 1) % h, (y + 1) % h
            dx = (px[y * w + xr] - px[y * w + xl]) / 255.0
            dy = (px[yd * w + x] - px[yu * w + x]) / 255.0
            nx, ny, nz = -dx * strength, -dy * strength, 1.0
            length = math.sqrt(nx * nx + ny * ny + nz * nz)
            data.append(
                (
                    int((nx / length * 0.5 + 0.5) * 255),
                    int((ny / length * 0.5 + 0.5) * 255),
                    int((nz / length * 0.5 + 0.5) * 255),
                )
            )
    out.putdata(data)
    out.save(normal_path)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=sorted(MODELS), default="nano-banana-pro")
    parser.add_argument("--only", nargs="*", default=None, help="subset of material ids")
    parser.add_argument("--out", default=OUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--key-env", default="GEMINI_API_KEY")
    args = parser.parse_args()

    targets = {k: v for k, v in PROMPTS.items() if not args.only or k in args.only}
    if not targets:
        raise SystemExit(f"No matching material ids. Known: {', '.join(sorted(PROMPTS))}")

    os.makedirs(args.out, exist_ok=True)

    api_key = os.environ.get(args.key_env, "").strip()
    if not api_key and not args.dry_run:
        raise SystemExit(
            "No API key. Set GEMINI_API_KEY (from https://aistudio.google.com/apikey).\n"
            "A Google AI Pro subscription does not create API credentials.\n"
            "Run with --dry-run to inspect prompts and write the manifest only."
        )

    model_id = MODELS[args.model]
    manifest = {
        "generator": "tools/generate_textures.py",
        "model": args.model,
        "model_id": model_id,
        "materials": {},
    }

    for mat_id, prompt in targets.items():
        entry = {"prompt": prompt, "status": "planned", "albedo": None, "normal": None}
        if args.dry_run:
            print(f"[dry-run] {mat_id}: {prompt[:70]}...")
            manifest["materials"][mat_id] = entry
            continue

        print(f"[gen] {mat_id} via {model_id}")
        image = call_gemini(model_id, api_key, prompt)
        albedo_path = os.path.join(args.out, f"T_{mat_id}_BC.png")
        with open(albedo_path, "wb") as fh:
            fh.write(image)
        normal_path = os.path.join(args.out, f"T_{mat_id}_N.png")
        has_normal = write_normal_map(albedo_path, normal_path)

        entry.update(
            status="ok",
            albedo=os.path.relpath(albedo_path, ROOT).replace("\\", "/"),
            normal=os.path.relpath(normal_path, ROOT).replace("\\", "/") if has_normal else None,
        )
        manifest["materials"][mat_id] = entry
        print(f"      -> {albedo_path}")

    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"[manifest] {MANIFEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
