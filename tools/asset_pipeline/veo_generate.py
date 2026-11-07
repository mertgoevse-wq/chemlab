#!/usr/bin/env python3
"""
Veo Video Generation Pipeline for ChemLab

Generates cinematic sequences (loading, transitions, story beats)
using Google AI Pro (Veo).

Requirements:
- Google AI Pro subscription (Mert.govse.neu@gmail.com)
- GEMINI_API_KEY from https://aistudio.google.com/apikey
- Veo access (may require allowlist)

Usage:
    python veo_generate.py --mode loading
    python veo_generate.py --mode story
    python veo_generate.py --mode all
    python veo_generate.py --dry-run  # Show prompts only
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[2]
ASSET_MANIFEST = ROOT / "game" / "data" / "media" / "manifest.json"

# ─── Veo Prompt Library ──────────────────────────────────────────────────────

CINEMATIC_VIDEOS = [
    # Loading / Menu Background Loops (5)
    {
        "id": "loading_lab_night",
        "name": "Loading: Laboratory at Night",
        "category": "loading",
        "prompt": (
            "Slow cinematic dolly through a dim laboratory at night, 24 fps, shallow depth of "
            "field. Foreground: a round-bottom flask with gently boiling amber liquid and a "
            "reflux condenser. Midground: a distillation column with visible vapour pulses and "
            "a burette dripping into a beaker. Background: racks of glassware, one warm task "
            "lamp, dust motes in the light beam. No people, no text, no camera shake, no "
            "speed ramps, seamless loop, muted teal and amber palette, photoreal, 16:9, 8 s."
        ),
        "negative": "text, logo, people, hands, fast motion, flicker, morphing glass, extra fingers, UI, HUD",
        "duration_sec": 8,
        "aspect": "16:9",
        "fps": 24,
        "loop": True,
        "model": "veo-2",
        "output": "game/assets/video/loading_lab_night.mp4",
    },
    {
        "id": "loading_synthesis_dawn",
        "name": "Loading: Synthesis Lab Dawn",
        "category": "loading",
        "prompt": (
            "Slow cinematic push through a synthesis laboratory at dawn, 24 fps. "
            "First light through high windows catches condensation on a rotary evaporator. "
            "Foreground: magnetic stirrer spinning a PTFE bar in a round-bottom flask, "
            "vortex catching light. Midground: fume hood sash rising slowly, vapour plume. "
            "Background: solvent cabinet, Schlenk line manifolds, coiled cooling hoses. "
            "Seamless loop, cool blue-grey to warm amber transition, photoreal, 16:9, 10 s."
        ),
        "negative": "text, logo, people, hands, fast motion, flicker, morphing glass, extra fingers, UI, HUD",
        "duration_sec": 10,
        "aspect": "16:9",
        "fps": 24,
        "loop": True,
        "model": "veo-2",
        "output": "game/assets/video/loading_synthesis_dawn.mp4",
    },
    {
        "id": "loading_analytical_instrument",
        "name": "Loading: Analytical Instrument Close-up",
        "category": "loading",
        "prompt": (
            "Extreme slow macro dolly across analytical instruments, 24 fps. "
            "HPLC pump pistons in precise motion, solvent gradient mixing, "
            "autosampler needle descending into vial, column oven door sealing. "
            "Shallow depth of field, focus pulls between components. "
            "Cool white LED lighting, stainless steel reflections, no people, seamless loop, 16:9, 12 s."
        ),
        "negative": "text, logo, people, hands, fast motion, flicker, morphing glass, extra fingers, UI, HUD",
        "duration_sec": 12,
        "aspect": "16:9",
        "fps": 24,
        "loop": True,
        "model": "veo-2",
        "output": "game/assets/video/loading_analytical_instrument.mp4",
    },
    {
        "id": "loading_radiochemistry_hotcell",
        "name": "Loading: Radiochemistry Hot Cell",
        "category": "loading",
        "prompt": (
            "Slow cinematic through leaded glass window into radiochemistry hot cell, 24 fps. "
            "Remote manipulators performing precise transfer: shielded vial to detector. "
            "Gamma survey meter needle responding. Concrete walls, warning trefoil symbols. "
            "Cold blue-green lighting through lead glass, dust motes, no people, seamless loop, 16:9, 10 s."
        ),
        "negative": "text, logo, people, hands, fast motion, flicker, morphing glass, extra fingers, UI, HUD",
        "duration_sec": 10,
        "aspect": "16:9",
        "fps": 24,
        "loop": True,
        "model": "veo-2",
        "output": "game/assets/video/loading_radiochemistry_hotcell.mp4",
    },
    {
        "id": "loading_genomics_sequencer",
        "name": "Loading: Genomics Sequencer Run",
        "category": "loading",
        "prompt": (
            "Cinematic slow motion through genomics lab, 24 fps. "
            "Thermal cycler block heating/cooling cycles visible via IR overlay. "
            "Gel rig: DNA bands migrating in electric field, blue transilluminator glow. "
            "Sequencer flow cell loading, reagent droplets, cluster generation. "
            "Clean cold lighting, blue/cyan palette, no people, seamless loop, 16:9, 10 s."
        ),
        "negative": "text, logo, people, hands, fast motion, flicker, morphing glass, extra fingers, UI, HUD",
        "duration_sec": 10,
        "aspect": "16:9",
        "fps": 24,
        "loop": True,
        "model": "veo-2",
        "output": "game/assets/video/loading_genomics_sequencer.mp4",
    },

    # Transition Videos (3)
    {
        "id": "transition_lab_to_lab",
        "name": "Transition: Lab to Lab",
        "category": "transition",
        "prompt": (
            "Smooth match-cut transition between laboratory environments, 24 fps, 3 s. "
            "Start: analytical lab HPLC, focus pull to window. "
            "Match cut through window to: synthesis lab fume hood interior. "
            "Camera continues dolly forward. Practical lighting only, "
            "color temperature shifts 4500K to 5500K, photoreal, 16:9."
        ),
        "negative": "text, logo, people, hands, fast motion, flicker, morphing glass, extra fingers, UI, HUD, crossfade, dissolve",
        "duration_sec": 3,
        "aspect": "16:9",
        "fps": 24,
        "loop": False,
        "model": "veo-2",
        "output": "game/assets/video/transition_lab_to_lab.mp4",
    },
    {
        "id": "transition_micro_to_macro",
        "name": "Transition: Micro to Macro",
        "category": "transition",
        "prompt": (
            "Seamless zoom transition from microscopic to macroscopic, 24 fps, 4 s. "
            "Start: SEM view of crystal lattice, atomic resolution. "
            "Continuous zoom out through: crystal grain, polished sample surface, "
            "SEM chamber, lab bench, full analytical lab wide. "
            "No cuts, single continuous virtual camera, photoreal, 16:9."
        ),
        "negative": "text, logo, people, hands, fast motion, flicker, morphing glass, extra fingers, UI, HUD, crossfade, dissolve",
        "duration_sec": 4,
        "aspect": "16:9",
        "fps": 24,
        "loop": False,
        "model": "veo-2",
        "output": "game/assets/video/transition_micro_to_macro.mp4",
    },
    {
        "id": "transition_reaction_closeup",
        "name": "Transition: Reaction Close-up",
        "category": "transition",
        "prompt": (
            "Match-cut from reaction macro to lab wide, 24 fps, 3 s. "
            "Extreme close-up: liquid-liquid interface in separatory funnel, "
            "droplets forming, phase boundary sharp. "
            "Camera pulls back rapidly through glass wall to reveal: "
            "full synthesis lab, fume hood, chemist's hands entering frame. "
            "Practical lighting, seamless, photoreal, 16:9."
        ),
        "negative": "text, logo, people, hands, fast motion, flicker, morphing glass, extra fingers, UI, HUD, crossfade, dissolve",
        "duration_sec": 3,
        "aspect": "16:9",
        "fps": 24,
        "loop": False,
        "model": "veo-2",
        "output": "game/assets/video/transition_reaction_closeup.mp4",
    },

    # Story Beat Cinematics (10)
    {
        "id": "story_intro_athanor_key",
        "name": "Story: Athanor Key Turn",
        "category": "story",
        "prompt": (
            "Cinematic sequence, 3 shots, 10-12 s total, 24 fps, handheld 35mm feel. "
            "Shot 1 (Macro, 3s): Brass key turns in old furnace door lock; "
            "sparks cascade, dust motes dance, warm key light from furnace interior, "
            "shallow depth of field on key teeth. "
            "Shot 2 (Wide, 5s): Young alchemist (matching character portrait) steps into "
            "converted industrial hall; morning light shafts through high windows, "
            "glassware on shelves catches light, no dialogue, natural motion. "
            "Shot 3 (Close, 3s): Gloved hands lift a beaker; liquid catches cyan rim light "
            "from fume hood; center of frame left empty for title card overlay; "
            "cut to black. Practical light only, no lens flare, no slow-motion, realistic physics."
        ),
        "negative": "text, logo, UI, HUD, title card, slow-motion, lens flare, fast motion, extra fingers, morphing",
        "duration_sec": 11,
        "aspect": "16:9",
        "fps": 24,
        "loop": False,
        "model": "veo-2",
        "output": "game/assets/video/story_intro_athanor_key.mp4",
    },
    {
        "id": "story_first_synthesis",
        "name": "Story: First Successful Synthesis",
        "category": "story",
        "prompt": (
            "Cinematic sequence, 4 shots, 15 s, 24 fps. "
            "Shot 1: Round-bottom flask on stirrer, reagents adding dropwise from addition funnel, "
            "color change from clear to pale yellow. "
            "Shot 2: TLC plate developing in chamber, UV lamp reveals separated spots. "
            "Shot 3: Rotary evaporator spinning, solvent condensing, crystalline product remaining. "
            "Shot 4: Analytical balance weighing product, display reads target yield, "
            "chemist's gloved hands recording in lab notebook. "
            "Handheld 35mm, practical light, natural motion blur, no text, no lens flare."
        ),
        "negative": "text, logo, UI, HUD, title card, slow-motion, lens flare, fast motion, extra fingers, morphing",
        "duration_sec": 15,
        "aspect": "16:9",
        "fps": 24,
        "loop": False,
        "model": "veo-2",
        "output": "game/assets/video/story_first_synthesis.mp4",
    },
    {
        "id": "story_radiochemistry_milestone",
        "name": "Story: Radiochemistry Breakthrough",
        "category": "story",
        "prompt": (
            "Cinematic sequence, 3 shots, 12 s, 24 fps. "
            "Shot 1: Through leaded glass, remote manipulators loading target into cyclotron. "
            "Shot 2: Beam current ramp, Cherenkov glow in water target, gamma spectrum on monitor. "
            "Shot 3: Hot cell: shielded vial transferred to dispensing station, "
            "radiochemical purity HPLC trace shows clean peak, "
            "technician's hands in lead gloves labeling vial. "
            "Cold blue-green palette, practical lighting, no text."
        ),
        "negative": "text, logo, UI, HUD, title card, slow-motion, lens flare, fast motion, extra fingers, morphing",
        "duration_sec": 12,
        "aspect": "16:9",
        "fps": 24,
        "loop": False,
        "model": "veo-2",
        "output": "game/assets/video/story_radiochemistry_milestone.mp4",
    },
    {
        "id": "story_genomics_discovery",
        "name": "Story: Genomics Discovery",
        "category": "story",
        "prompt": (
            "Cinematic sequence, 4 shots, 14 s, 24 fps. "
            "Shot 1: Thermal cycler running, faint glow through lid. "
            "Shot 2: Gel electrophoresis, bands separating, blue transilluminator. "
            "Shot 3: Sequencer flow cell, cluster generation timelapse (sped up 100x). "
            "Shot 4: Bioinformatics workstation, genome browser scrolling, "
            "variant highlighted, researcher's face illuminated by screen. "
            "Cool clean lighting, blue/cyan palette, no text."
        ),
        "negative": "text, logo, UI, HUD, title card, slow-motion, lens flare, fast motion, extra fingers, morphing",
        "duration_sec": 14,
        "aspect": "16:9",
        "fps": 24,
        "loop": False,
        "model": "veo-2",
        "output": "game/assets/video/story_genomics_discovery.mp4",
    },
    {
        "id": "story_fusor_ignition",
        "name": "Story: Fusor First Plasma",
        "category": "story",
        "prompt": (
            "Cinematic sequence, 3 shots, 10 s, 24 fps. "
            "Shot 1: Vacuum chamber pumping down, pressure gauge dropping, turbopump whine. "
            "Shot 2: Deuterium inlet valve opens, HV feedthrough energizes, "
            "first faint purple glow in grid center. "
            "Shot 3: Neutron detector counts rising, oscilloscope trace, "
            "operator's face reflected in viewport, quiet triumph. "
            "Cool industrial lighting, practical only, no text."
        ),
        "negative": "text, logo, UI, HUD, title card, slow-motion, lens flare, fast motion, extra fingers, morphing",
        "duration_sec": 10,
        "aspect": "16:9",
        "fps": 24,
        "loop": False,
        "model": "veo-2",
        "output": "game/assets/video/story_fusor_ignition.mp4",
    },
    {
        "id": "story_cleanroom_fabrication",
        "name": "Story: Cleanroom Device Fabrication",
        "category": "story",
        "prompt": (
            "Cinematic sequence, 4 shots, 16 s, 24 fps. "
            "Shot 1: Bunny-suited technician entering ISO 5 bay, air shower. "
            "Shot 2: Photolithography: yellow light, mask aligner exposure, resist spinning. "
            "Shot 3: Etch chamber plasma glow, endpoint detection flash. "
            "Shot 4: Finished wafer under microscope, die pattern perfect, "
            "cleanroom reflection in wafer surface. "
            "Pale yellow lithography light, no text, practical only."
        ),
        "negative": "text, logo, UI, HUD, title card, slow-motion, lens flare, fast motion, extra fingers, morphing",
        "duration_sec": 16,
        "aspect": "16:9",
        "fps": 24,
        "loop": False,
        "model": "veo-2",
        "output": "game/assets/video/story_cleanroom_fabrication.mp4",
    },
    {
        "id": "story_pilot_plant_scaleup",
        "name": "Story: Pilot Plant Scale-up",
        "category": "story",
        "prompt": (
            "Cinematic sequence, 4 shots, 15 s, 24 fps. "
            "Shot 1: Lab-scale reactor to pilot column transition (match cut). "
            "Shot 2: Heat exchangers, steam trace lines, insulation seams. "
            "Shot 3: PLC control room: operator adjusting setpoints, trends stabilizing. "
            "Shot 4: Product sampling, inline NIR confirm spec, drum filling. "
            "Industrial grime, steam, practical lighting, no text."
        ),
        "negative": "text, logo, UI, HUD, title card, slow-motion, lens flare, fast motion, extra fingers, morphing",
        "duration_sec": 15,
        "aspect": "16:9",
        "fps": 24,
        "loop": False,
        "model": "veo-2",
        "output": "game/assets/video/story_pilot_plant_scaleup.mp4",
    },
    {
        "id": "story_microgravity_experiment",
        "name": "Story: Microgravity Experiment",
        "category": "story",
        "prompt": (
            "Cinematic sequence, 3 shots, 12 s, 24 fps. "
            "Shot 1: Orbital lab module, Earth limb through window, equipment strapped down. "
            "Shot 2: Capillary flow experiment in glovebox, fluid behavior without gravity. "
            "Shot 3: Astronaut-scientist recording data on tablet, "
            "floating pen caught by Velcro, quiet focus. "
            "Cold blue-grey palette, practical lighting, no text."
        ),
        "negative": "text, logo, UI, HUD, title card, slow-motion, lens flare, fast motion, extra fingers, morphing",
        "duration_sec": 12,
        "aspect": "16:9",
        "fps": 24,
        "loop": False,
        "model": "veo-2",
        "output": "game/assets/video/story_microgravity_experiment.mp4",
    },
    {
        "id": "story_cryogenic_breakthrough",
        "name": "Story: Cryogenic Superconductivity",
        "category": "story",
        "prompt": (
            "Cinematic sequence, 3 shots, 11 s, 24 fps. "
            "Shot 1: Dilution fridge mixing chamber, temperature display: 10mK. "
            "Shot 2: Quantum device in sample holder, wire bonds visible, "
            "magnetic field ramp, resistance drops to zero. "
            "Shot 3: Data trace on screen: sharp transition, "
            "researcher's breath visible in cold room air. "
            "Cold blue-grey palette, frost on fittings, no text."
        ),
        "negative": "text, logo, UI, HUD, title card, slow-motion, lens flare, fast motion, extra fingers, morphing",
        "duration_sec": 11,
        "aspect": "16:9",
        "fps": 24,
        "loop": False,
        "model": "veo-2",
        "output": "game/assets/video/story_cryogenic_breakthrough.mp4",
    },
    {
        "id": "story_final_ascension",
        "name": "Story: Athanor Ascension Finale",
        "category": "story",
        "prompt": (
            "Cinematic sequence, 5 shots, 20 s, 24 fps - game ending montage. "
            "Shot 1: All lab environments in rapid succession (1s each), "
            "character's journey reflected in glass surfaces. "
            "Shot 2: Athanor furnace at full operation, golden light spilling out. "
            "Shot 3: Character places final catalyst, reaction cascades through "
            "interconnected labs (match cuts: synthesis → analytical → genomics → fusor). "
            "Shot 4: Product crystal forms in slow motion, perfect lattice. "
            "Shot 5: Title card space - center empty for 'ATHANAR ASCENSION' overlay, "
            "camera pulls back through facility roof to stars. "
            "Handheld 35mm, natural motion, practical light, emotional resolution."
        ),
        "negative": "text, logo, UI, HUD, title card (except designated space), lens flare, fast motion, extra fingers, morphing",
        "duration_sec": 20,
        "aspect": "16:9",
        "fps": 24,
        "loop": False,
        "model": "veo-2",
        "output": "game/assets/video/story_final_ascension.mp4",
    },
]


def load_manifest() -> dict:
    if ASSET_MANIFEST.exists():
        with open(ASSET_MANIFEST, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"version": 1, "assets": []}


def save_manifest(manifest: dict):
    ASSET_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(ASSET_MANIFEST, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def get_items_by_mode(mode: str):
    if mode == "loading":
        return [v for v in CINEMATIC_VIDEOS if v["category"] == "loading"]
    elif mode == "transition":
        return [v for v in CINEMATIC_VIDEOS if v["category"] == "transition"]
    elif mode == "story":
        return [v for v in CINEMATIC_VIDEOS if v["category"] == "story"]
    elif mode == "all":
        return CINEMATIC_VIDEOS
    else:
        return []


def generate_video(item: dict, api_key: str | None, use_bridge: bool, dry_run: bool) -> dict:
    result = {
        "id": item["id"],
        "name": item["name"],
        "category": item["category"],
        "status": "pending",
        "output_path": item["output"],
        "prompt": item["prompt"],
        "negative": item.get("negative", ""),
        "model": item["model"],
        "aspect": item.get("aspect", "16:9"),
        "duration_sec": item.get("duration_sec", 8),
        "fps": item.get("fps", 24),
        "loop": item.get("loop", False),
    }

    if dry_run:
        result["status"] = "dry-run"
        return result

    output_path = ROOT / item["output"]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Veo is not available via google_bridge.py - requires API
    if use_bridge:
        result["status"] = "skipped"
        result["error"] = "Veo video generation not supported via browser bridge; requires API access"
    elif api_key:
        # TODO: Implement direct Veo API call when available
        result["status"] = "skipped"
        result["error"] = "Direct Veo API not yet implemented; awaiting API access"
    else:
        result["status"] = "skipped"
        result["error"] = "No API key or bridge support for Veo"

    return result


def main():
    parser = argparse.ArgumentParser(description="Veo Video Generator")
    parser.add_argument("--mode", choices=["loading", "transition", "story", "all"],
                        default="all", help="Generation mode")
    parser.add_argument("--api-key", help="Gemini API key (from aistudio.google.com/apikey)")
    parser.add_argument("--bridge", action="store_true", help="Use browser bridge (not supported for Veo)")
    parser.add_argument("--dry-run", action="store_true", help="Show prompts without generating")
    parser.add_argument("--limit", type=int, help="Limit number of items to generate")
    parser.add_argument("--resume", action="store_true", help="Skip already-generated assets")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    items = get_items_by_mode(args.mode)
    if args.limit:
        items = items[:args.limit]

    manifest = load_manifest()
    existing_ids = {a["id"] for a in manifest.get("assets", [])}

    print(f"Mode: {args.mode}")
    print(f"Items to process: {len(items)}")
    if args.dry_run:
        print("\n--- DRY RUN: Veo Prompts ---\n")
        for item in items:
            if args.resume and item["id"] in existing_ids:
                continue
            print(f"[{item['id']}] {item['name']} ({item['category']})")
            print(f"  Duration: {item.get('duration_sec', 8)}s | FPS: {item.get('fps', 24)} | Loop: {item.get('loop', False)}")
            print(f"  Prompt: {item['prompt'][:150]}...")
            print(f"  Negative: {item.get('negative', '')[:80]}...")
            print(f"  Output: {item['output']}")
            print()
        return 0

    results = []
    for i, item in enumerate(items, 1):
        if args.resume and item["id"] in existing_ids:
            print(f"[{i}/{len(items)}] Skipping {item['id']} (already in manifest)")
            continue

        print(f"[{i}/{len(items)}] Processing {item['id']} ({item['name']})...")
        result = generate_video(item, api_key, args.bridge, args.dry_run)
        results.append(result)

        manifest.setdefault("assets", []).append(result)
        save_manifest(manifest)

        status = result["status"]
        if status == "generated":
            print(f"  ✓ Generated")
        elif status == "dry-run":
            print(f"  ○ Dry run")
        else:
            print(f"  ○ Skipped: {result.get('error', 'Unknown')}")

        if not args.dry_run and i < len(items):
            time.sleep(1)

    generated = sum(1 for r in results if r["status"] == "generated")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    print(f"\n--- Summary ---")
    print(f"Generated: {generated}")
    print(f"Skipped: {skipped}")
    print(f"Manifest updated: {ASSET_MANIFEST}")

    return 0


if __name__ == "__main__":
    sys.exit(main())