#!/usr/bin/env python3
"""
Nano Banana Pro Image Generation Pipeline for ChemLab

Generates lab environments, equipment closeups, and character portraits
using Google AI Pro (Nano Banana Pro / Nano Banana 2).

Requirements:
- Google AI Pro subscription (Mert.govse.neu@gmail.com)
- GEMINI_API_KEY from https://aistudio.google.com/apikey
- Or use browser bridge via tools/google_bridge.py

Usage:
    python nano_banana_generate.py --mode environments
    python nano_banana_generate.py --mode equipment
    python nano_banana_generate.py --mode characters
    python nano_banana_generate.py --mode all
    python nano_banana_generate.py --dry-run  # Show prompts only
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[2]
ASSET_MANIFEST = ROOT / "game" / "data" / "media" / "manifest.json"
PROMPTS_FILE = ROOT / "docs" / "ASSET_PROMPTS.md"

# ─── Prompt Library ──────────────────────────────────────────────────────────

LAB_ENVIRONMENTS = [
    {
        "id": "analytical_lab",
        "name": "Analytical Laboratory",
        "prompt": (
            "Wide interior photograph of a working scientific laboratory, 35 mm lens at eye "
            "height, practical fluorescent and task lighting, realistic material wear, faint "
            "dust in the air, no people, no text, no logos, documentary architectural "
            "photography, natural color, 16:9. "
            "HPLC and GC-MS benches, nitrogen cylinders chained to the wall, "
            "sample trays, laminated SOP binders, scuffed epoxy floor."
        ),
        "negative": "people, text, logo, hologram UI, sci-fi blue glow, lens flare, oversaturated, sterile showroom",
        "aspect": "16:9",
        "model": "nano-banana-pro",
        "output": "game/assets/environments/analytical_lab.png",
    },
    {
        "id": "synthesis_lab",
        "name": "Synthesis Laboratory",
        "prompt": (
            "Wide interior photograph of a working scientific laboratory, 35 mm lens at eye "
            "height, practical fluorescent and task lighting, realistic material wear, faint "
            "dust in the air, no people, no text, no logos, documentary architectural "
            "photography, natural color, 16:9. "
            "Two fume hoods, rotary evaporator, Schlenk line, solvent cabinet, "
            "blast shield, fire extinguisher, coiled cooling hoses."
        ),
        "negative": "people, text, logo, hologram UI, sci-fi blue glow, lens flare, oversaturated, sterile showroom",
        "aspect": "16:9",
        "model": "nano-banana-pro",
        "output": "game/assets/environments/synthesis_lab.png",
    },
    {
        "id": "radiochemistry_hot_cell",
        "name": "Radiochemistry Hot Cell",
        "prompt": (
            "Wide interior photograph of a working scientific laboratory, 35 mm lens at eye "
            "height, practical fluorescent and task lighting, realistic material wear, faint "
            "dust in the air, no people, no text, no logos, documentary architectural "
            "photography, natural color, 16:9. "
            "Leaded glass window, remote manipulators, warning trefoil signage (symbol only, no words), "
            "concrete walls, gamma survey meter."
        ),
        "negative": "people, text, logo, hologram UI, sci-fi blue glow, lens flare, oversaturated, sterile showroom",
        "aspect": "16:9",
        "model": "nano-banana-pro",
        "output": "game/assets/environments/radiochemistry_hot_cell.png",
    },
    {
        "id": "accelerator_hall",
        "name": "Accelerator Hall",
        "prompt": (
            "Wide interior photograph of a working scientific laboratory, 35 mm lens at eye "
            "height, practical fluorescent and task lighting, realistic material wear, faint "
            "dust in the air, no people, no text, no logos, documentary architectural "
            "photography, natural color, 16:9. "
            "Concrete tunnel, blue dipole magnets, beam pipe, cable trays, "
            "radiation interlock pillars, cold industrial lighting."
        ),
        "negative": "people, text, logo, hologram UI, sci-fi blue glow, lens flare, oversaturated, sterile showroom",
        "aspect": "16:9",
        "model": "nano-banana-pro",
        "output": "game/assets/environments/accelerator_hall.png",
    },
    {
        "id": "fusor_workshop",
        "name": "Fusor Workshop",
        "prompt": (
            "Wide interior photograph of a working scientific laboratory, 35 mm lens at eye "
            "height, practical fluorescent and task lighting, realistic material wear, faint "
            "dust in the air, no people, no text, no logos, documentary architectural "
            "photography, natural color, 16:9. "
            "Stainless vacuum chamber on a steel bench, turbopump, HV feedthrough, "
            "deuterium regulator, neutron survey meter, coiled ballast resistor."
        ),
        "negative": "people, text, logo, hologram UI, sci-fi blue glow, lens flare, oversaturated, sterile showroom",
        "aspect": "16:9",
        "model": "nano-banana-pro",
        "output": "game/assets/environments/fusor_workshop.png",
    },
    {
        "id": "genomics_lab",
        "name": "Genomics Laboratory",
        "prompt": (
            "Wide interior photograph of a working scientific laboratory, 35 mm lens at eye "
            "height, practical fluorescent and task lighting, realistic material wear, faint "
            "dust in the air, no people, no text, no logos, documentary architectural "
            "photography, natural color, 16:9. "
            "Separated pre- and post-PCR rooms, thermal cyclers, gel rig, "
            "sequencer, blue transilluminator glow, cold clean lighting."
        ),
        "negative": "people, text, logo, hologram UI, sci-fi blue glow, lens flare, oversaturated, sterile showroom",
        "aspect": "16:9",
        "model": "nano-banana-pro",
        "output": "game/assets/environments/genomics_lab.png",
    },
    {
        "id": "cleanroom_iso5",
        "name": "Cleanroom ISO 5",
        "prompt": (
            "Wide interior photograph of a working scientific laboratory, 35 mm lens at eye "
            "height, practical fluorescent and task lighting, realistic material wear, faint "
            "dust in the air, no people, no text, no logos, documentary architectural "
            "photography, natural color, 16:9. "
            "ISO 5 bay, bunny suits hanging, wafer tools, particle counter, "
            "pale yellow lithography light."
        ),
        "negative": "people, text, logo, hologram UI, sci-fi blue glow, lens flare, oversaturated, sterile showroom",
        "aspect": "16:9",
        "model": "nano-banana-pro",
        "output": "game/assets/environments/cleanroom_iso5.png",
    },
    {
        "id": "pilot_plant",
        "name": "Pilot Plant",
        "prompt": (
            "Wide interior photograph of a working scientific laboratory, 35 mm lens at eye "
            "height, practical fluorescent and task lighting, realistic material wear, faint "
            "dust in the air, no people, no text, no logos, documentary architectural "
            "photography, natural color, 16:9. "
            "Columns, heat exchangers, PLC control room glass, relief valves, "
            "steam trace lines, industrial grime."
        ),
        "negative": "people, text, logo, hologram UI, sci-fi blue glow, lens flare, oversaturated, sterile showroom",
        "aspect": "16:9",
        "model": "nano-banana-pro",
        "output": "game/assets/environments/pilot_plant.png",
    },
    {
        "id": "microgravity_lab",
        "name": "Microgravity Laboratory",
        "prompt": (
            "Wide interior photograph of a working scientific laboratory, 35 mm lens at eye "
            "height, practical fluorescent and task lighting, realistic material wear, faint "
            "dust in the air, no people, no text, no logos, documentary architectural "
            "photography, natural color, 16:9. "
            "Orbital lab module, strapped equipment, handrails, Velcro patches, "
            "Earth limb through a small window, no floating hair cliché."
        ),
        "negative": "people, text, logo, hologram UI, sci-fi blue glow, lens flare, oversaturated, sterile showroom",
        "aspect": "16:9",
        "model": "nano-banana-pro",
        "output": "game/assets/environments/microgravity_lab.png",
    },
    {
        "id": "cryogenic_lab",
        "name": "Cryogenic Laboratory",
        "prompt": (
            "Wide interior photograph of a working scientific laboratory, 35 mm lens at eye "
            "height, practical fluorescent and task lighting, realistic material wear, faint "
            "dust in the air, no people, no text, no logos, documentary architectural "
            "photography, natural color, 16:9. "
            "Dewars, transfer lines, oxygen monitor, frost on fittings, "
            "condensation, cold blue-grey palette."
        ),
        "negative": "people, text, logo, hologram UI, sci-fi blue glow, lens flare, oversaturated, sterile showroom",
        "aspect": "16:9",
        "model": "nano-banana-pro",
        "output": "game/assets/environments/cryogenic_lab.png",
    },
    {
        "id": "materials_characterization",
        "name": "Materials Characterization",
        "prompt": (
            "Wide interior photograph of a working scientific laboratory, 35 mm lens at eye "
            "height, practical fluorescent and task lighting, realistic material wear, faint "
            "dust in the air, no people, no text, no logos, documentary architectural "
            "photography, natural color, 16:9. "
            "SEM/FIB station, XRD diffractometer, glove box, sputter coater, "
            "vibration-isolated table, amber safety lighting."
        ),
        "negative": "people, text, logo, hologram UI, sci-fi blue glow, lens flare, oversaturated, sterile showroom",
        "aspect": "16:9",
        "model": "nano-banana-pro",
        "output": "game/assets/environments/materials_characterization.png",
    },
    {
        "id": "electrochemistry_lab",
        "name": "Electrochemistry Laboratory",
        "prompt": (
            "Wide interior photograph of a working scientific laboratory, 35 mm lens at eye "
            "height, practical fluorescent and task lighting, realistic material wear, faint "
            "dust in the air, no people, no text, no logos, documentary architectural "
            "photography, natural color, 16:9. "
            "Potentiostat racks, rotating disk electrodes, Faraday cage, "
            "electrolyte baths, reference electrode bank, cable management trays."
        ),
        "negative": "people, text, logo, hologram UI, sci-fi blue glow, lens flare, oversaturated, sterile showroom",
        "aspect": "16:9",
        "model": "nano-banana-pro",
        "output": "game/assets/environments/electrochemistry_lab.png",
    },
    {
        "id": "photochemistry_lab",
        "name": "Photochemistry Laboratory",
        "prompt": (
            "Wide interior photograph of a working scientific laboratory, 35 mm lens at eye "
            "height, practical fluorescent and task lighting, realistic material wear, faint "
            "dust in the air, no people, no text, no logos, documentary architectural "
            "photography, natural color, 16:9. "
            "Xenon arc lamp reactor, LED arrays, quartz photoreactors, optical filters, "
            "actinometer station, amber glassware storage, darkroom safe lights."
        ),
        "negative": "people, text, logo, hologram UI, sci-fi blue glow, lens flare, oversaturated, sterile showroom",
        "aspect": "16:9",
        "model": "nano-banana-pro",
        "output": "game/assets/environments/photochemistry_lab.png",
    },
    {
        "id": "biocatalysis_lab",
        "name": "Biocatalysis Laboratory",
        "prompt": (
            "Wide interior photograph of a working scientific laboratory, 35 mm lens at eye "
            "height, practical fluorescent and task lighting, realistic material wear, faint "
            "dust in the air, no people, no text, no logos, documentary architectural "
            "photography, natural color, 16:9. "
            "Bioreactors, anaerobic chamber, enzyme immobilization station, "
            "centrifuge bank, -80°C freezer, CO2 incubator, laminar flow hood."
        ),
        "negative": "people, text, logo, hologram UI, sci-fi blue glow, lens flare, oversaturated, sterile showroom",
        "aspect": "16:9",
        "model": "nano-banana-pro",
        "output": "game/assets/environments/biocatalysis_lab.png",
    },
    {
        "id": "flow_chemistry_lab",
        "name": "Flow Chemistry Laboratory",
        "prompt": (
            "Wide interior photograph of a working scientific laboratory, 35 mm lens at eye "
            "height, practical fluorescent and task lighting, realistic material wear, faint "
            "dust in the air, no people, no text, no logos, documentary architectural "
            "photography, natural color, 16:9. "
            "Continuous flow reactors, syringe pumps, inline IR/UV monitoring, "
            "backpressure regulators, fraction collector, solvent recycle system."
        ),
        "negative": "people, text, logo, hologram UI, sci-fi blue glow, lens flare, oversaturated, sterile showroom",
        "aspect": "16:9",
        "model": "nano-banana-pro",
        "output": "game/assets/environments/flow_chemistry_lab.png",
    },
    {
        "id": "process_safety_lab",
        "name": "Process Safety Laboratory",
        "prompt": (
            "Wide interior photograph of a working scientific laboratory, 35 mm lens at eye "
            "height, practical fluorescent and task lighting, realistic material wear, faint "
            "dust in the air, no people, no text, no logos, documentary architectural "
            "photography, natural color, 16:9. "
            "DSC/TGA instruments, adiabatic calorimeter (ARC), vent sizing station, "
            "pressure relief test rig, explosion severity apparatus, safety data archive."
        ),
        "negative": "people, text, logo, hologram UI, sci-fi blue glow, lens flare, oversaturated, sterile showroom",
        "aspect": "16:9",
        "model": "nano-banana-pro",
        "output": "game/assets/environments/process_safety_lab.png",
    },
    {
        "id": "analytical_instrumentation",
        "name": "Analytical Instrumentation Suite",
        "prompt": (
            "Wide interior photograph of a working scientific laboratory, 35 mm lens at eye "
            "height, practical fluorescent and task lighting, realistic material wear, faint "
            "dust in the air, no people, no text, no logos, documentary architectural "
            "photography, natural color, 16:9. "
            "NMR magnet with shim stack, LC-MS/MS triple quad, ICP-OES, "
            "autosampler carousel, data system workstations, UPS backup."
        ),
        "negative": "people, text, logo, hologram UI, sci-fi blue glow, lens flare, oversaturated, sterile showroom",
        "aspect": "16:9",
        "model": "nano-banana-pro",
        "output": "game/assets/environments/analytical_instrumentation.png",
    },
]

EQUIPMENT_CLOSEUPS = [
    # Glassware (15)
    {"id": "beaker_250ml", "name": "Beaker 250mL", "category": "glassware",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Borosilicate glass beaker 250mL, white graduations, spout, slight meniscus visible, subtle surface scratches.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/beaker_250ml.png"},
    {"id": "erlenmeyer_500ml", "name": "Erlenmeyer Flask 500mL", "category": "glassware",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Borosilicate Erlenmeyer flask 500mL, narrow neck, white graduation marks, conical body, slight condensation droplets.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/erlenmeyer_500ml.png"},
    {"id": "round_bottom_250ml", "name": "Round-Bottom Flask 250mL", "category": "glassware",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Round-bottom flask 250mL, single neck, ground glass joint, spherical body, clear borosilicate.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/round_bottom_250ml.png"},
    {"id": "burette_50ml", "name": "Burette 50mL", "category": "glassware",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Glass burette 50mL, PTFE stopcock, white Schellbach stripe, precise graduations, tip visible.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/burette_50ml.png"},
    {"id": "volumetric_100ml", "name": "Volumetric Flask 100mL", "category": "glassware",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Class A volumetric flask 100mL, single ring graduation, ground glass stopper, pear-shaped body.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/volumetric_100ml.png"},
    {"id": "graduated_cylinder_100ml", "name": "Graduated Cylinder 100mL", "category": "glassware",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Tall form graduated cylinder 100mL, hexagonal base, pour spout, white enamel graduations.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/graduated_cylinder_100ml.png"},
    {"id": "separatory_funnel_250ml", "name": "Separatory Funnel 250mL", "category": "glassware",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Pear-shaped separatory funnel 250mL, PTFE stopcock, ground glass stopper, conical bottom.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/separatory_funnel_250ml.png"},
    {"id": "condenser_reflux", "name": "Reflux Condenser", "category": "glassware",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Liebig reflux condenser, straight inner tube, water jacket, ground glass joints both ends, hose barbs.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/condenser_reflux.png"},
    {"id": "distillation_head", "name": "Distillation Head", "category": "glassware",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Claisen distillation head with thermometer adapter, three ground glass joints, vacuum take-off.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/distillation_head.png"},
    {"id": "nmr_tube", "name": "NMR Tube", "category": "glassware",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. 5mm NMR tube, precision bore, borosilicate, cap, sample height marker.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/nmr_tube.png"},
    {"id": "cuvette_quartz", "name": "Quartz Cuvette", "category": "glassware",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. UV-Vis quartz cuvette 10mm path length, four clear windows, frosted sides, PTFE lid.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/cuvette_quartz.png"},
    {"id": "pipette_10ml", "name": "Volumetric Pipette 10mL", "category": "glassware",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Class A volumetric pipette 10mL, single graduation ring, color-coded band, tapered tip.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/pipette_10ml.png"},
    {"id": "micropipette_set", "name": "Micropipette Set", "category": "glassware",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Three single-channel micropipettes (P10, P200, P1000), ergonomic handles, tip ejectors, calibration marks.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/micropipette_set.png"},
    {"id": "syringe_glass_10ml", "name": "Glass Syringe 10mL", "category": "glassware",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Gas-tight glass syringe 10mL, PTFE plunger, Luer lock, graduation marks, stainless needle hub.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/syringe_glass_10ml.png"},

    # Instruments (20)
    {"id": "analytical_balance", "name": "Analytical Balance", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Analytical balance 0.1mg readability, glass draft shield, stainless pan, backlit LCD, level bubble.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/analytical_balance.png"},
    {"id": "magnetic_stirrer", "name": "Magnetic Stirrer Hotplate", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Digital magnetic stirrer hotplate, ceramic top, PTFE stir bar, temperature probe, RPM display.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/magnetic_stirrer.png"},
    {"id": "rotary_evaporator", "name": "Rotary Evaporator", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Rotary evaporator: motorized lift, diagonal condenser, rotating flask, water bath, vacuum controller, digital speed/temp display.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/rotary_evaporator.png"},
    {"id": "vacuum_pump", "name": "Diaphragm Vacuum Pump", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Chemical-resistant diaphragm vacuum pump, PTFE heads, gauge, muffler, carrying handle.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/vacuum_pump.png"},
    {"id": "thermal_cycler", "name": "PCR Thermal Cycler", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. 96-well gradient thermal cycler, heated lid, touchscreen interface, block visible, Peltier elements.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/thermal_cycler.png"},
    {"id": "centrifuge_refrigerated", "name": "Refrigerated Centrifuge", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Refrigerated benchtop centrifuge, rotor with 24×1.5mL tubes, digital RPM/RCF, temperature control, imbalance detection.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/centrifuge_refrigerated.png"},
    {"id": "spectrophotometer", "name": "UV-Vis Spectrophotometer", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Double-beam UV-Vis spectrophotometer, cuvette holder, deuterium/tungsten lamps, monochromator, touchscreen.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/spectrophotometer.png"},
    {"id": "ph_meter", "name": "Benchtop pH Meter", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Benchtop pH/ion meter, glass electrode, ATC probe, magnetic stirrer, GLP documentation, large display.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/ph_meter.png"},
    {"id": "conductivity_meter", "name": "Conductivity Meter", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Benchtop conductivity/TDS meter, 4-pole cell, automatic temperature compensation, calibration history.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/conductivity_meter.png"},
    {"id": "potentiostat", "name": "Potentiostat Galvanostat", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Multi-channel potentiostat/galvanostat, Faraday cage, rotating disk electrode, bipotentiostat mode, EIS capability.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/potentiostat.png"},
    {"id": "glove_box", "name": "Inert Atmosphere Glove Box", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Double-station glove box, stainless steel, antechamber, O2/H2O monitors, automatic purge, butyl gloves.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/glove_box.png"},
    {"id": "schlenk_line", "name": "Schlenk Line", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Dual-manifold Schlenk line: vacuum/inert gas, liquid N2 trap, pressure gauge, 4 ports, ground glass stopcocks.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/schlenk_line.png"},
    {"id": "hplc_system", "name": "HPLC System", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. UHPLC system: binary pump, autosampler, column oven, DAD detector, solvent degasser, waste management.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/hplc_system.png"},
    {"id": "gc_ms", "name": "GC-MS System", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Gas chromatograph-mass spectrometer: split/splitless injector, quadrupole MS, autosampler, gas supply panel.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/gc_ms.png"},
    {"id": "nmr_spectrometer", "name": "NMR Spectrometer", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. 400MHz NMR spectrometer: superconducting magnet, shim stack, probe, sample changer, workstation console.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/nmr_spectrometer.png"},
    {"id": "ftir_spectrometer", "name": "FTIR Spectrometer", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. FTIR spectrometer: diamond ATR accessory, interferometer, DTGS detector, sample compartment, purge gas.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/ftir_spectrometer.png"},
    {"id": "raman_spectrometer", "name": "Raman Spectrometer", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Confocal Raman microscope: 785nm laser, objective turret, motorized stage, CCD detector, safety interlock.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/raman_spectrometer.png"},
    {"id": "particle_analyzer", "name": "Particle Size Analyzer", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Laser diffraction particle analyzer: wet/dry dispersion unit, sample cell, detector array, refractive index database.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/particle_analyzer.png"},
    {"id": "thermal_analyzer", "name": "DSC/TGA Thermal Analyzer", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Simultaneous DSC/TGA: dual furnaces, autosampler, gas switching, reference pan, touchscreen controller.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/thermal_analyzer.png"},
    {"id": "xrd_diffractometer", "name": "XRD Diffractometer", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. X-ray powder diffractometer: theta-theta goniometer, Cu tube, position-sensitive detector, sample spinner, radiation enclosure.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/xrd_diffractometer.png"},
    {"id": "sem_fib", "name": "SEM/FIB System", "category": "instruments",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Dual-beam SEM/FIB: Schottky emitter, gallium FIB column, EDS detector, EBSD, cryo-stage, vibration isolation.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/sem_fib.png"},

    # PPE & Safety (15)
    {"id": "lab_coat", "name": "Flame-Resistant Lab Coat", "category": "ppe",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Flame-resistant lab coat, snap front, knit cuffs, chest pocket, subtle chemical stain on sleeve, hanging on hook.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/lab_coat.png"},
    {"id": "nitrile_gloves", "name": "Nitrile Gloves (Box)", "category": "ppe",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Box of powder-free nitrile gloves, blue, textured fingertips, 100 count, perforated dispensing opening.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/nitrile_gloves.png"},
    {"id": "safety_goggles", "name": "Chemical Splash Goggles", "category": "ppe",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Indirect-vent chemical splash goggles, polycarbonate lens, adjustable strap, anti-fog coating, ANSI Z87.1.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/safety_goggles.png"},
    {"id": "face_shield", "name": "Face Shield", "category": "ppe",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Full-face shield, polycarbonate visor, ratchet headgear, chin protection, anti-fog, replaceable visor.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/face_shield.png"},
    {"id": "respirator_n95", "name": "N95 Respirator", "category": "ppe",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Cup-style N95 filtering facepiece, dual straps, adjustable nose clip, exhalation valve, NIOSH approved.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/respirator_n95.png"},
    {"id": "respirator_half", "name": "Half-Face Respirator", "category": "ppe",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Silicone half-face respirator, dual cartridge ports, speaking diaphragm, adjustable head harness, organic vapor/acid gas cartridges.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/respirator_half.png"},
    {"id": "apron_rubber", "name": "Chemical Apron", "category": "ppe",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Heavy-duty chemical apron, butyl rubber, bib style, adjustable neck/waist straps, heat-sealed seams.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/apron_rubber.png"},
    {"id": "sleeve_protectors", "name": "Sleeve Protectors", "category": "ppe",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Pair of chemical-resistant sleeve protectors, Tyvek, elastic cuffs, thumb loops, disposable.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/sleeve_protectors.png"},
    {"id": "eyewash_station", "name": "Emergency Eyewash Station", "category": "ppe",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Plumbed emergency eyewash station, dual aerated heads, bowl, push-handle activation, ANSI Z358.1, green/white signage.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/eyewash_station.png"},
    {"id": "safety_shower", "name": "Emergency Safety Shower", "category": "ppe",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Ceiling-mounted emergency safety shower, pull-rod activation, 20gpm flow, stay-open valve, floor drain, high-visibility pull handle.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/safety_shower.png"},
    {"id": "fire_extinguisher_abc", "name": "ABC Fire Extinguisher", "category": "ppe",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. 5lb ABC dry chemical fire extinguisher, pressure gauge, safety pin, mounting bracket, UL rated.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/fire_extinguisher_abc.png"},
    {"id": "fire_extinguisher_co2", "name": "CO2 Fire Extinguisher", "category": "ppe",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. 5lb CO2 fire extinguisher, horn nozzle, pressure gauge, mounting bracket, no residue, electrical fires.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/fire_extinguisher_co2.png"},
    {"id": "spill_kit", "name": "Chemical Spill Kit", "category": "ppe",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Universal spill kit in wall-mount case: absorbent pads, socks, pillows, neutralizer, PPE, disposal bags, instruction card.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/spill_kit.png"},
    {"id": "first_aid_kit", "name": "Laboratory First Aid Kit", "category": "ppe",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. ANSI Class B first aid kit, wall-mounted metal case, burn gel, eye wash, trauma supplies, inventory list.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/first_aid_kit.png"},
    {"id": "radiation_monitor", "name": "Radiation Survey Meter", "category": "ppe",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Portable gamma/beta survey meter, pancake GM probe, digital display, audible clicker, dose rate alarm, NIST traceable calibration.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/radiation_monitor.png"},

    # Specialized Equipment (10+)
    {"id": "fusor_chamber", "name": "Fusor Vacuum Chamber", "category": "specialized",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Stainless steel fusor chamber, spherical, multiple conflat ports, viewport, HV feedthrough, turbo pump flange.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/fusor_chamber.png"},
    {"id": "dipole_magnet", "name": "Dipole Magnet", "category": "specialized",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. C-shaped dipole magnet, laminated steel yoke, copper coils, pole faces, cooling channels, alignment fiducials.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/dipole_magnet.png"},
    {"id": "lead_pig", "name": "Lead Shielding Pig", "category": "specialized",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Lead shielding pig for radioisotopes, interlocking bricks, lifting handle, 50mm wall thickness, painted grey.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/lead_pig.png"},
    {"id": "cleanroom_hood", "name": "Laminar Flow Hood", "category": "specialized",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Horizontal laminar flow hood, HEPA filter, stainless work surface, UV germicidal lamp, magnehelic gauge, acrylic sash.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/cleanroom_hood.png"},
    {"id": "bioreactor", "name": "Bioreactor Vessel", "category": "specialized",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Stirred-tank bioreactor 10L: jacketed glass vessel, Rushton impeller, sparger, baffles, probe ports (pH, DO, temp), harvest valve.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/bioreactor.png"},
    {"id": "flow_reactor", "name": "Continuous Flow Reactor", "category": "specialized",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Microfluidic flow reactor chip, PTFE tubing, inline mixer, backpressure regulator, temperature control module, fluidic connectors.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/flow_reactor.png"},
    {"id": "photoreactor", "name": "Photochemical Reactor", "category": "specialized",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Quartz photoreactor vessel, LED array cooling jacket, gas sparging, optical window, temperature probe, magnetic stirrer base.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/photoreactor.png"},
    {"id": "cryogenic_dewar", "name": "Liquid Nitrogen Dewar", "category": "specialized",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. 50L liquid nitrogen dewar, vacuum jacketed, pressure relief valve, phase separator, withdrawal fitting, casters, level gauge.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/cryogenic_dewar.png"},
    {"id": "freeze_dryer", "name": "Freeze Dryer", "category": "specialized",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Benchtop freeze dryer: acrylic chamber, shelf heating, condenser coil, vacuum pump, pirate valve, touchscreen controller, sample vials on shelves.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/freeze_dryer.png"},
    {"id": "spray_dryer", "name": "Spray Dryer", "category": "specialized",
     "prompt": "Single laboratory object, centered, three-quarter view, isolated on transparent background, soft studio light, matte painted technical illustration style with visible material grain, no cast shadow, no text, 1:1. Lab-scale spray dryer: two-fluid nozzle, drying chamber, cyclone separator, peristaltic feed pump, inlet/outlet temp control, collection vessel.",
     "negative": "text, label, reflection of studio, multiple objects, cartoon outline, glow", "aspect": "1:1", "model": "nano-banana-2", "output": "game/assets/equipment/spray_dryer.png"},
]

CHARACTERS = [
    # 4 Base species × multiple variants = 26 portraits
    {"id": "human_male_01", "name": "Human Male - Senior Chemist", "species": "human",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Male, mid-40s, greying dark hair, safety glasses on forehead, "
        "small burn scar on left forearm, pen in breast pocket."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/human_male_01.png"},
    {"id": "human_female_01", "name": "Human Female - Process Engineer", "species": "human",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Female, early 30s, dark hair in practical bun, subtle safety goggle tan lines, "
        "small acid splash scar on chin, confident posture."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/human_female_01.png"},
    {"id": "human_male_02", "name": "Human Male - Junior Researcher", "species": "human",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Male, mid-20s, messy dark hair, eager expression, clean lab coat, "
        "slight ink stain on fingers from note-taking."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/human_male_02.png"},
    {"id": "human_female_02", "name": "Human Female - Safety Officer", "species": "human",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Female, late 30s, short grey-streaked hair, authoritative calm, "
        "radiation badge visible, clipboard imprint on palm."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/human_female_02.png"},
    {"id": "human_nb_01", "name": "Human Non-Binary - Analytical Lead", "species": "human",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Non-binary, early 30s, androgynous features, silver-streaked locs, "
        "NMR magnet quench scar on neck, focused intensity."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/human_nb_01.png"},
    {"id": "human_male_03", "name": "Human Male - Veteran Technician", "species": "human",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Male, late 50s, white beard, weathered hands, reading glasses on chain, "
        "machinist calluses, decades of institutional knowledge."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/human_male_03.png"},
    {"id": "human_female_03", "name": "Human Female - Director", "species": "human",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Female, early 50s, silver bob, sharp eyes, tailored lab coat, "
        "pen tucked behind ear, command presence without arrogance."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/human_female_03.png"},

    # Sylvan (6)
    {"id": "sylvan_male_01", "name": "Sylvan Male - Biocatalysis Specialist", "species": "sylvan",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Sylvan male: bark-like skin plates along jawline, moss at collar, "
        "human-like amber eyes, chlorophyll-tinted veins at temples, "
        "no antlers, no elf ears, wearing standard lab coat."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/sylvan_male_01.png"},
    {"id": "sylvan_female_01", "name": "Sylvan Female - Genomics Curator", "species": "sylvan",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Sylvan female: fine bark texture at jaw, small fern fronds at hairline, "
        "green-gold irises, root-like patterns on neck, "
        "wearing cleanroom bunny suit, no elf ears."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/sylvan_female_01.png"},
    {"id": "sylvan_nb_01", "name": "Sylvan Non-Binary - Photochemistry", "species": "sylvan",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Sylvan non-binary: smooth bark skin, bioluminescent moss patches at cheeks, "
        "photosynthetic pigment streaks in hair, human eye structure, "
        "protective UV-filtering visor, no fantasy elements."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/sylvan_nb_01.png"},
    {"id": "sylvan_male_02", "name": "Sylvan Male - Senior Botanist", "species": "sylvan",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Sylvan elder: thick cork-like bark plates, lichen colonies at shoulders, "
        "deep-set human eyes, seasonal leaf-shedding at hairline, "
        "worn field jacket over lab clothes, no antlers."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/sylvan_male_02.png"},
    {"id": "sylvan_female_02", "name": "Sylvan Female - Process Safety", "species": "sylvan",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Sylvan female: smooth young bark, delicate moss at collar, "
        "alert green eyes, chemical burn scar healed as lighter bark patch, "
        "standard PPE, no elf ears."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/sylvan_female_02.png"},
    {"id": "sylvan_nb_02", "name": "Sylvan Non-Binary - Junior Tech", "species": "sylvan",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Sylvan junior: fresh green bark, first moss sprouting at temples, "
        "bright curious eyes, oversized borrowed lab coat, "
        "seed pod earrings (cultural), no fantasy ears."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/sylvan_nb_02.png"},

    # Cinder-kin (6)
    {"id": "cinder_male_01", "name": "Cinder-kin Male - Pyrochemistry", "species": "cinder-kin",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Cinder-kin male: charcoal grey skin, fine glowing seams at knuckles, "
        "subtle heat shimmer at shoulders only, human dark eyes, "
        "no horns, no demon styling, flame-resistant lab coat."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/cinder_male_01.png"},
    {"id": "cinder_female_01", "name": "Cinder-kin Female - Combustion Analysis", "species": "cinder-kin",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Cinder-kin female: obsidian skin with ember veins at wrists, "
        "thermal shimmer at collar, amber-human eyes, "
        "heat-resistant gloves, no horns, practical bun."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/cinder_female_01.png"},
    {"id": "cinder_nb_01", "name": "Cinder-kin Non-Binary - Energetic Materials", "species": "cinder-kin",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Cinder-kin non-binary: volcanic rock texture, lava-seam fingerprints, "
        "molten gold irises, controlled thermal aura at neck, "
        "blast shield visor, no demon traits."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/cinder_nb_01.png"},
    {"id": "cinder_male_02", "name": "Cinder-kin Male - Senior Furnace Op", "species": "cinder-kin",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Cinder-kin elder: cracked basalt skin, cooled lava flow patterns, "
        "steady ember eyes, decades of thermal cycling etched in skin, "
        "worn aluminized coat, no horns."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/cinder_male_02.png"},
    {"id": "cinder_female_02", "name": "Cinder-kin Female - Hot Cell Operator", "species": "cinder-kin",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Cinder-kin female: smooth obsidian, precise ember traceries, "
        "calm amber eyes, remote manipulator wrist implant visible, "
        "lead-lined apron, no fantasy elements."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/cinder_female_02.png"},
    {"id": "cinder_nb_02", "name": "Cinder-kin Non-Binary - Reactor Tech", "species": "cinder-kin",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Cinder-kin junior: fresh charcoal skin, first ignition seams forming, "
        "bright copper eyes, heat-shimmer at temples when excited, "
        "standard fire-retardant coveralls, no horns."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/cinder_nb_02.png"},

    # Deep-kin (6)
    {"id": "deep_male_01", "name": "Deep-kin Male - High-Pressure Chemistry", "species": "deep-kin",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Deep-kin male: pale blue-grey skin, small translucent eyelid ridge, "
        "wet-looking dark hair, pressure-adapted physiology, "
        "no fish scales, no gills on neck, standard lab attire."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/deep_male_01.png"},
    {"id": "deep_female_01", "name": "Deep-kin Female - Abyssal Sampling", "species": "deep-kin",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Deep-kin female: luminescent blue-grey skin, nictitating membrane visible, "
        "slicked-back hair, barometric pressure port at temple, "
        "no gills, no scales, pressure-rated suit."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/deep_female_01.png"},
    {"id": "deep_nb_01", "name": "Deep-kin Non-Binary - Cryogenics", "species": "deep-kin",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Deep-kin non-binary: frost-pale skin, crystalline eyelid ridge, "
        "ice-crystal hair texture, thermal regulation implant, "
        "no gills, no scales, cryogenic PPE."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/deep_nb_01.png"},
    {"id": "deep_male_02", "name": "Deep-kin Male - Veteran Diver", "species": "deep-kin",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Deep-kin elder: weathered blue-grey skin, pronounced nictitating membranes, "
        "deep-set human eyes, saturation diving history in skin folds, "
        "worn saturation suit, no fantasy features."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/deep_male_02.png"},
    {"id": "deep_female_02", "name": "Deep-kin Female - Submersible Pilot", "species": "deep-kin",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Deep-kin female: smooth pale skin, subtle bioluminescent freckles, "
        "calm dark eyes, mixed-gas rebreather mouthpiece scar, "
        "flight suit collar, no gills or scales."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/deep_female_02.png"},
    {"id": "deep_nb_02", "name": "Deep-kin Non-Binary - ROV Operator", "species": "deep-kin",
     "prompt": (
        "Head-and-shoulders character portrait, neutral dark laboratory background, "
        "soft key light from camera left at 4500 K, practical rim light from a fume hood "
        "on the right, documentary photography realism, visible skin texture and pores, "
        "calm neutral expression, work clothes with subtle chemical stains, no jewelry, "
        "no text, 3:4. "
        "Deep-kin junior: fresh pale skin, first pressure ridges forming, "
        "bright curious eyes, neural interface ports at temples, "
        "standard jumpsuit, no fish traits."
    ),
     "negative": "fantasy armor, glowing eyes, horns, anime, plastic skin, symmetric beauty filter, text",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/deep_nb_02.png"},

    # Working Animals (8)
    {"id": "lab_rat_01", "name": "Lab Rat - Transgenic Model", "species": "animal",
     "prompt": (
        "Single animal portrait, neutral laboratory background, soft lighting, "
        "documentary realism, visible fur texture, no text, 3:4. "
        "Albino Sprague-Dawley rat, transgenic GFP marker visible under blue light, "
        "clean coat, alert posture, research identification ear tag."
    ),
     "negative": "anthropomorphic, clothing, fantasy, text, cartoon",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/lab_rat_01.png"},
    {"id": "lab_mouse_01", "name": "Lab Mouse - Knockout Model", "species": "animal",
     "prompt": (
        "Single animal portrait, neutral laboratory background, soft lighting, "
        "documentary realism, visible fur texture, no text, 3:4. "
        "C57BL/6 mouse, conditional knockout, ear punch ID, "
        "healthy coat, curious expression, standard housing."
    ),
     "negative": "anthropomorphic, clothing, fantasy, text, cartoon",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/lab_mouse_01.png"},
    {"id": "zebrafish_01", "name": "Zebrafish - Developmental Model", "species": "animal",
     "prompt": (
        "Single animal portrait, aquatic environment, soft lighting, "
        "documentary realism, visible scale detail, no text, 3:4. "
        "Adult zebrafish, wild-type stripe pattern, transgenic fluorescent line, "
        "28°C tank reflection, research facility standard."
    ),
     "negative": "anthropomorphic, clothing, fantasy, text, cartoon",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/zebrafish_01.png"},
    {"id": "fruit_fly_01", "name": "Fruit Fly - Genetic Model", "species": "animal",
     "prompt": (
        "Macro portrait, neutral background, soft diffuse lighting, "
        "documentary realism, visible compound eye detail, no text, 1:1. "
        "Drosophila melanogaster, white-eyed mutant, genetic marker visible, "
        "standard cornmeal agar vial background, research grade."
    ),
     "negative": "anthropomorphic, clothing, fantasy, text, cartoon",
     "aspect": "1:1", "model": "nano-banana-pro", "output": "game/assets/characters/fruit_fly_01.png"},
    {"id": "c_elegans_01", "name": "C. elegans - Nematode Model", "species": "animal",
     "prompt": (
        "Microscopy view, agar plate background, DIC illumination, "
        "documentary realism, visible anatomy, no text, 16:9. "
        "Caenorhabditis elegans adult hermaphrodite, fluorescent neuron marker, "
        "standard NGM plate, OP50 lawn, research standard."
    ),
     "negative": "anthropomorphic, clothing, fantasy, text, cartoon",
     "aspect": "16:9", "model": "nano-banana-pro", "output": "game/assets/characters/c_elegans_01.png"},
    {"id": "xenopus_01", "name": "Xenopus - Embryology Model", "species": "animal",
     "prompt": (
        "Single animal portrait, aquatic laboratory background, soft lighting, "
        "documentary realism, visible skin texture, no text, 3:4. "
        "Xenopus laevis adult female, pigmented strain, research identification, "
        "temperature-controlled tank, standard husbandry."
    ),
     "negative": "anthropomorphic, clothing, fantasy, text, cartoon",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/xenopus_01.png"},
    {"id": "axolotl_01", "name": "Axolotl - Regeneration Model", "species": "animal",
     "prompt": (
        "Single animal portrait, aquatic laboratory background, soft lighting, "
        "documentary realism, visible gill detail, no text, 3:4. "
        "Axolotl (Ambystoma mexicanum), leucistic morph, external gills, "
        "limb regeneration study subject, research facility standard."
    ),
     "negative": "anthropomorphic, clothing, fantasy, text, cartoon",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/axolotl_01.png"},
    {"id": "service_dog_01", "name": "Lab Safety Dog - Detection", "species": "animal",
     "prompt": (
        "Single animal portrait, laboratory corridor background, soft lighting, "
        "documentary realism, visible coat texture, no text, 3:4. "
        "Labrador retriever, chemical detection vest, trained alert posture, "
        "handler's leash visible, certified working dog, calm focus."
    ),
     "negative": "anthropomorphic, clothing, fantasy, text, cartoon",
     "aspect": "3:4", "model": "nano-banana-pro", "output": "game/assets/characters/service_dog_01.png"},
]


def load_manifest() -> dict:
    """Load existing asset manifest or create new one."""
    if ASSET_MANIFEST.exists():
        with open(ASSET_MANIFEST, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"version": 1, "assets": []}


def save_manifest(manifest: dict):
    """Save asset manifest."""
    ASSET_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(ASSET_MANIFEST, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def get_items_by_mode(mode: str):
    """Get generation items for the specified mode."""
    if mode == "environments":
        return LAB_ENVIRONMENTS
    elif mode == "equipment":
        return EQUIPMENT_CLOSEUPS
    elif mode == "characters":
        return CHARACTERS
    elif mode == "all":
        return LAB_ENVIRONMENTS + EQUIPMENT_CLOSEUPS + CHARACTERS
    else:
        return []


def generate_asset(item: dict, api_key: str | None, use_bridge: bool, dry_run: bool) -> dict:
    """Generate a single asset. Returns result dict."""
    result = {
        "id": item["id"],
        "name": item["name"],
        "status": "pending",
        "output_path": item["output"],
        "prompt": item["prompt"],
        "negative": item.get("negative", ""),
        "model": item["model"],
        "aspect": item.get("aspect", "16:9"),
    }

    if dry_run:
        result["status"] = "dry-run"
        return result

    output_path = ROOT / item["output"]
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Use browser bridge if no API key
    if use_bridge or not api_key:
        # Call google_bridge.py
        import subprocess
        cmd = [
            sys.executable, str(ROOT / "tools" / "google_bridge.py"),
            "--prompt", item["prompt"],
            "--out", str(output_path),
            "--headless"
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if proc.returncode == 0:
                result["status"] = "generated"
                result["bytes"] = output_path.stat().st_size if output_path.exists() else 0
            else:
                result["status"] = "failed"
                result["error"] = proc.stderr[-500:] if proc.stderr else "Unknown error"
        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["error"] = "Generation timed out after 180s"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
    else:
        # TODO: Implement direct API call when Gemini image API is available
        result["status"] = "skipped"
        result["error"] = "Direct API not yet implemented; use --bridge"

    return result


def main():
    parser = argparse.ArgumentParser(description="Nano Banana Pro Asset Generator")
    parser.add_argument("--mode", choices=["environments", "equipment", "characters", "all"],
                        default="all", help="Generation mode")
    parser.add_argument("--api-key", help="Gemini API key (from aistudio.google.com/apikey)")
    parser.add_argument("--bridge", action="store_true", help="Use browser bridge (google_bridge.py)")
    parser.add_argument("--dry-run", action="store_true", help="Show prompts without generating")
    parser.add_argument("--limit", type=int, help="Limit number of items to generate")
    parser.add_argument("--resume", action="store_true", help="Skip already-generated assets")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if not api_key and not args.bridge and not args.dry_run:
        print("No API key provided. Use --bridge to use browser bridge, or set GEMINI_API_KEY.")
        print("Get API key from: https://aistudio.google.com/apikey")
        return 1

    items = get_items_by_mode(args.mode)
    if args.limit:
        items = items[:args.limit]

    manifest = load_manifest()
    existing_ids = {a["id"] for a in manifest.get("assets", [])}

    print(f"Mode: {args.mode}")
    print(f"Items to process: {len(items)}")
    if args.dry_run:
        print("\n--- DRY RUN: Prompts ---\n")
        for item in items:
            if args.resume and item["id"] in existing_ids:
                continue
            print(f"[{item['id']}] {item['name']}")
            print(f"  Model: {item['model']} | Aspect: {item.get('aspect', '16:9')}")
            print(f"  Prompt: {item['prompt'][:120]}...")
            print(f"  Negative: {item.get('negative', '')[:80]}...")
            print(f"  Output: {item['output']}")
            print()
        return 0

    results = []
    for i, item in enumerate(items, 1):
        if args.resume and item["id"] in existing_ids:
            print(f"[{i}/{len(items)}] Skipping {item['id']} (already in manifest)")
            continue

        print(f"[{i}/{len(items)}] Generating {item['id']} ({item['name']})...")
        result = generate_asset(item, api_key, args.bridge, args.dry_run)
        results.append(result)

        # Update manifest
        manifest.setdefault("assets", []).append(result)
        save_manifest(manifest)

        status = result["status"]
        if status == "generated":
            print(f"  ✓ Generated ({result.get('bytes', 0)} bytes)")
        elif status == "dry-run":
            print(f"  ○ Dry run")
        else:
            print(f"  ✗ Failed: {result.get('error', 'Unknown')}")

        # Rate limiting: brief pause between generations
        if not args.dry_run and i < len(items):
            time.sleep(2)

    # Summary
    generated = sum(1 for r in results if r["status"] == "generated")
    failed = sum(1 for r in results if r["status"] in ("failed", "error", "timeout"))
    print(f"\n--- Summary ---")
    print(f"Generated: {generated}")
    print(f"Failed: {failed}")
    print(f"Manifest updated: {ASSET_MANIFEST}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())