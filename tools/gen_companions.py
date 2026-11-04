"""Generate game/data/companions/species_database.json.

The companion roster is written as compact tuples and expanded into the full
schema consumed by CompanionManager. Names are original to Athanor Ascension:
the old borrowed "fantastic beast" roster is gone.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "game" / "data" / "companions" / "species_database.json"


def species(
    sid: str,
    name: str,
    category: str,
    rarity: str,
    description: str,
    stats: tuple[int, int, int, int, int, int],
    bonuses: list[tuple[str, str, float, int, list[str]]],
    role: str,
    abilities: list[str],
    evolution: tuple[str, int] | None = None,
    unlock: tuple[str, int | None] | None = None,
    food: list[str] | None = None,
    breeding_group: str = "unknown",
    offspring: list[str] | None = None,
) -> dict:
    labels = ["health", "mana", "attack", "defense", "speed", "intelligence"]
    base_stats = {label: value for label, value in zip(labels, stats)}
    growth = {
        "health": 1.10 + stats[0] / 900.0,
        "mana": 1.09 + stats[1] / 900.0,
        "attack": 1.09 + stats[2] / 1100.0,
        "defense": 1.09 + stats[3] / 1100.0,
        "speed": 1.08 + stats[4] / 1200.0,
        "intelligence": 1.10 + stats[5] / 900.0,
    }
    ability_levels = {ability: 1 + index * 7 for index, ability in enumerate(abilities)}
    entry: dict = {
        "species_id": sid,
        "display_name": name,
        "category": category,
        "rarity": rarity,
        "description": description,
        "base_stats": base_stats,
        "growth_rates": {key: round(value, 3) for key, value in growth.items()},
        "chemistry_bonuses": [
            {
                "bonus_type": btype,
                "description": bdesc,
                "magnitude": magnitude,
                "unlock_level": level,
                "skill_synergy": synergy,
            }
            for btype, bdesc, magnitude, level, synergy in bonuses
        ],
        "battle_role": role,
        "battle_abilities": abilities,
        "ability_unlock_levels": ability_levels,
        "evolution_line": (
            {"evolves_to": evolution[0], "trigger": "LEVEL_UP", "condition": {"level": evolution[1]}}
            if evolution
            else {"evolves_to": None, "trigger": "NONE", "condition": {}}
        ),
        "care_profile": {
            "hunger_rate": 0.8 + stats[4] / 200.0,
            "happiness_decay": 0.5 + stats[5] / 250.0,
            "preferred_food": food or ["lab pellets"],
            "favorite_activity": "bench_supervision",
        },
        "breeding": {
            "breeding_group": breeding_group,
            "breeding_time_hours": 4,
            "egg_type": "live_birth",
            "offspring_species": offspring or [sid],
            "inheritable_traits": ["intelligence", "speed"],
        },
        "unlock_requirement": (
            {"type": unlock[0], "value": unlock[1]} if unlock else {"type": "DEFAULT", "value": None}
        ),
        "sprite_path": f"res://assets/companions/{sid}.tscn",
        "portrait_path": f"res://assets/companions/portraits/{sid}.png",
    }
    return entry


SPECIES = [
    # --- Real animals: the working, non-magical baseline -------------------
    species(
        "lab_rat", "Lab Rat", "REAL_ANIMAL", "COMMON",
        "Keen-nosed and unimpressed. Learns a maze faster than most interns learn the SDS.",
        (45, 15, 8, 6, 18, 14),
        [("IMPURITY_DETECTION", "Flags off-odour reagent lots 15% faster", 0.15, 1, ["analytical", "safety"])],
        "UTILITY", ["sniff_out", "quick_bite", "scurry"], ("enhanced_lab_rat", 25),
        food=["cheese", "seeds", "pellets"], breeding_group="rodent",
        offspring=["lab_rat", "enhanced_lab_rat"],
    ),
    species(
        "enhanced_lab_rat", "Instrumented Lab Rat", "REAL_ANIMAL", "UNCOMMON",
        "A rat with a subcutaneous telemetry chip; its stress response is a real toxicity readout.",
        (60, 25, 10, 9, 22, 20),
        [("IMPURITY_DETECTION", "Live toxicity telemetry during dosing studies", 0.3, 1, ["toxicology"]),
         ("XP_MULTIPLIER", "+8% toxicology XP from animal work", 0.08, 15, ["toxicology"])],
        "UTILITY", ["sniff_out", "telemetry_ping", "scurry"], None,
        food=["pellets", "seeds"], breeding_group="rodent",
    ),
    species(
        "lab_cat", "Contraband Cat", "REAL_ANIMAL", "COMMON",
        "Sleeps on the fume hood, wakes for solvent vapours and strangers.",
        (55, 20, 14, 8, 24, 16),
        [("HAZARD_IMMUNITY", "Detects hidden solvent containers nearby", 0.2, 1, ["forensics"])],
        "CONTROL", ["silent_step", "swipe", "hiss"], None,
        food=["fish", "poultry"], breeding_group="feline",
    ),
    species(
        "lab_dog", "Search Dog", "REAL_ANIMAL", "UNCOMMON",
        "Trained on three odour signatures and stubbornly loyal to all of them.",
        (80, 15, 18, 14, 20, 12),
        [("REAGENT_FINDER", "Finds misplaced reagents on site", 0.18, 1, ["fieldwork"]),
         ("SAFETY_BUFFER", "Warns before you enter a contaminated room", 0.1, 10, ["safety"])],
        "TANK", ["track", "bark_alert", "guard"], None,
        food=["kibble", "meat"], breeding_group="canine",
    ),
    species(
        "carrier_pigeon", "Carrier Pigeon", "REAL_ANIMAL", "COMMON",
        "A living sample courier. Temperature-sensitive and utterly unimpressed by weather.",
        (30, 10, 5, 4, 30, 10),
        [("LOOT_QUALITY", "Reliable sample transfer between sites", 0.1, 1, ["fieldwork"])],
        "UTILITY", ["fly", "homing_return", "peck"], None,
        food=["grain"], breeding_group="avian",
    ),
    species(
        "gecko", "Wall Gecko", "REAL_ANIMAL", "COMMON",
        "Sticks to glassware cupboards and eats the insects you did not know were there.",
        (35, 18, 6, 7, 26, 9),
        [("IMPURITY_DETECTION", "Catches fungal and insect contamination early", 0.12, 1, ["biology"])],
        "UTILITY", ["cling", "tongue_flick", "camouflage"], None,
        food=["insects"], breeding_group="reptile",
    ),
    species(
        "axolotl", "Lab Axolotl", "REAL_ANIMAL", "RARE",
        "Regenerates limbs and, in this lab, your confidence in vertebrate models.",
        (50, 40, 6, 10, 12, 22),
        [("XP_MULTIPLIER", "+12% developmental biology XP", 0.12, 1, ["biology"]),
         ("REBIRTH", "Once per session, a failed protocol is not fatal to the batch", 0.25, 30, ["biology"])],
        "SUPPORT", ["regenerate", "gill_pulse", "heal_aura"], None,
        food=["brine shrimp", "worms"], breeding_group="amphibian",
    ),
    species(
        "raven", "Archive Raven", "REAL_ANIMAL", "UNCOMMON",
        "Steals labels, remembers faces, and has strong opinions about your handwriting.",
        (40, 25, 10, 6, 27, 24),
        [("XP_MULTIPLIER", "+10% notebook and literature XP", 0.1, 1, ["research"]),
         ("REAGENT_FINDER", "Retrieves dropped small items", 0.08, 12, ["research"])],
        "UTILITY", ["recon", "mimic", "retrieve"], None,
        food=["nuts", "fruit"], breeding_group="avian",
    ),
    # --- Aetherkin: original creatures born from alchemical process --------
    species(
        "cinderling", "Cinderling", "AETHERKIN", "COMMON",
        "A palm-sized ember that nests in burner cones. It eats soot and sulks when the flame is too lean.",
        (40, 35, 16, 5, 22, 12),
        [("HEAT_RESISTANCE", "Cuts heat damage by 20% and steadies a flame", 0.2, 1, ["safety", "synthesis"]),
         ("CATALYST_EFFICIENCY", "Combustion catalysts last 10% longer", 0.1, 12, ["synthesis"])],
        "DPS", ["ember_spit", "flare", "ash_veil"], None,
        unlock=("QUEST", 2), food=["soot", "charcoal", "ethanol"], breeding_group="elemental",
    ),
    species(
        "brinejack", "Brinejack", "AETHERKIN", "COMMON",
        "A crab-like scavenger with salt crystals on its shell. Drinks brine and spits distilled water.",
        (65, 20, 12, 20, 12, 14),
        [("PURITY_BOOST", "+8% purity on aqueous workups", 0.08, 1, ["analytical"]),
         ("IMPURITY_DETECTION", "Senses chloride and sulfate contamination", 0.2, 8, ["analytical"])],
        "TANK", ["brine_spray", "shell_guard", "desalinate"], None,
        unlock=("QUEST", 3), food=["seawater", "salt"], breeding_group="aquatic",
    ),
    species(
        "glasswing_moth", "Glasswing Moth", "AETHERKIN", "UNCOMMON",
        "Wings of silica scale so thin they show Newton's rings. It lands on cracks and refuses to move.",
        (30, 30, 6, 4, 26, 26),
        [("IMPURITY_DETECTION", "Detects microfractures in glassware before they fail", 0.35, 1, ["safety"]),
         ("PURITY_BOOST", "UV inspection improves crystal purity checks", 0.1, 14, ["analytical"])],
        "UTILITY", ["fracture_sense", "uv_flash", "dust_wing"], None,
        unlock=("QUEST", 4), food=["nectar", "silica dust"], breeding_group="insect",
    ),
    species(
        "calcine_hound", "Calcine Hound", "AETHERKIN", "UNCOMMON",
        "An ash-grey canid with furnace breath. Tracks residues by their thermal signature.",
        (90, 30, 24, 16, 24, 18),
        [("REAGENT_FINDER", "Follows a residue trail across the facility", 0.25, 1, ["forensics"]),
         ("HEAT_RESISTANCE", "Shrugs off radiant heat near furnaces", 0.3, 10, ["safety"])],
        "TANK", ["track_ash", "heat_wave", "guard"], None,
        unlock=("QUEST", 6), food=["ash", "bone char"], breeding_group="elemental",
    ),
    species(
        "mercurial_ferret", "Mercurial Ferret", "AETHERKIN", "RARE",
        "Its fur flows like liquid metal. It can round up a mercury spill into a single bright bead.",
        (50, 40, 18, 10, 30, 20),
        [("REAGENT_FINDER", "Recovers spilled reagents instead of losing them", 0.3, 1, ["preparative"]),
         ("HAZARD_IMMUNITY", "Safe handling of mercury and heavy-metal spills", 0.4, 18, ["safety"])],
        "UTILITY", ["spill_recover", "amalgam_sense", "slip_through"], None,
        unlock=("QUEST", 8), food=["metal dust", "oil"], breeding_group="elemental",
    ),
    species(
        "lumen_eel", "Lumen Eel", "AETHERKIN", "UNCOMMON",
        "A ribbon of cold light in a dark tank. Its glow tracks reactive oxygen species.",
        (45, 55, 10, 8, 20, 24),
        [("IMPURITY_DETECTION", "Reactive-oxygen and peroxide sensing", 0.28, 1, ["analytical"]),
         ("MANA_REGEN", "Restores stamina faster during long protocols", 0.15, 12, ["endurance"])],
        "SUPPORT", ["glow", "ros_pulse", "shock"], None,
        unlock=("QUEST", 5), food=["plankton", "hydrogen peroxide"], breeding_group="aquatic",
    ),
    species(
        "verdant_sloth", "Verdant Sloth", "AETHERKIN", "RARE",
        "Moss grows in its fur in the exact pattern of its last meal. It moves once an hour, decisively.",
        (85, 45, 8, 22, 5, 20),
        [("YIELD_BOOST", "+18% yield from plant extractions", 0.18, 1, ["phytochemistry"]),
         ("PURITY_BOOST", "Slows oxidation of sensitive botanicals", 0.12, 16, ["phytochemistry"])],
        "SUPPORT", ["slow_aura", "terpene_sense", "regrow"], None,
        unlock=("SKILL", 25), food=["leaves", "moss"], breeding_group="plant",
    ),
    species(
        "obsidian_beetle", "Obsidian Beetle", "AETHERKIN", "RARE",
        "Its carapace is a natural radiation shield. It walks toward the source, which is the problem.",
        (95, 20, 20, 34, 10, 10),
        [("FIRE_RESISTANCE", "Reduces fire and arc-flash damage by 35%", 0.35, 1, ["safety"]),
         ("HAZARD_IMMUNITY", "Shields against beta and low-energy gamma", 0.3, 20, ["radiological"])],
        "TANK", ["shell_wall", "radiation_soak", "iridesce"], None,
        unlock=("SKILL", 30), food=["minerals", "basalt dust"], breeding_group="insect",
    ),
    species(
        "null_moth", "Null Moth", "AETHERKIN", "RARE",
        "It feeds on static. Balances settle in its presence, and so do your nerves.",
        (35, 45, 5, 8, 24, 30),
        [("CATALYST_EFFICIENCY", "Removes static interference from microbalances", 0.25, 1, ["analytical"]),
         ("SAFETY_BUFFER", "Prevents solvent-vapour ignition from static discharge", 0.2, 15, ["safety"])],
        "SUPPORT", ["static_ward", "calm", "dust_wing"], None,
        unlock=("QUEST", 9), food=["static", "pollen"], breeding_group="insect",
    ),
    species(
        "tideglass_serpent", "Tideglass Serpent", "AETHERKIN", "EPIC",
        "Swims through microgravity water without surface tension. Its scales nucleate crystals on command.",
        (70, 60, 22, 14, 26, 28),
        [("YIELD_BOOST", "+20% crystal yield; controls nucleation", 0.2, 1, ["crystallography"]),
         ("REACTION_ACCELERATOR", "Crystallisation runs 15% faster", 0.15, 22, ["crystallography"])],
        "CONTROL", ["nucleate", "fluid_weave", "coil"], None,
        unlock=("QUEST", 12), food=["mineral water", "glass"], breeding_group="aquatic",
    ),
    species(
        "auric_kite", "Auric Kite", "AETHERKIN", "RARE",
        "A paper-thin raptor that circles anything conductive. Its feathers ring faintly near gold.",
        (45, 35, 18, 8, 32, 22),
        [("LOOT_QUALITY", "Locates noble-metal residues and ore traces", 0.3, 1, ["fieldwork"]),
         ("REAGENT_FINDER", "Aerial recon of the site", 0.15, 10, ["fieldwork"])],
        "DPS", ["dive", "metal_sense", "wind_slash"], None,
        unlock=("QUEST", 10), food=["insects", "copper"], breeding_group="avian",
    ),
    species(
        "sable_lynx", "Sable Lynx", "AETHERKIN", "EPIC",
        "A shadow with eyes. It sees heat, hears lies, and dislikes being photographed.",
        (80, 40, 28, 12, 34, 20),
        [("HAZARD_IMMUNITY", "Night operations and contraband detection", 0.35, 1, ["forensics"]),
         ("XP_MULTIPLIER", "+12% investigation XP", 0.12, 20, ["forensics"])],
        "DPS", ["pounce", "thermal_sight", "vanish"], None,
        unlock=("QUEST", 14), food=["meat"], breeding_group="feline",
    ),
    species(
        "halide_newt", "Halide Newt", "AETHERKIN", "UNCOMMON",
        "Its skin changes colour with halogen concentration. A living indicator paper with opinions.",
        (40, 35, 10, 8, 18, 24),
        [("IMPURITY_DETECTION", "Halide and halogen sensing in the fume hood", 0.3, 1, ["analytical"]),
         ("SAFETY_BUFFER", "Early warning for chlorine and bromine leaks", 0.15, 10, ["safety"])],
        "SUPPORT", ["halide_sense", "colour_flash", "slip"], None,
        unlock=("QUEST", 7), food=["brine", "insects"], breeding_group="amphibian",
    ),
    species(
        "xenon_owl", "Xenon Owl", "AETHERKIN", "EPIC",
        "It hunts vacuum leaks by sound. Its eyes are the colour of a discharge tube.",
        (55, 50, 12, 10, 24, 34),
        [("IMPURITY_DETECTION", "Locates vacuum leaks and noble-gas contamination", 0.4, 1, ["physics"]),
         ("CATALYST_EFFICIENCY", "Improves vacuum stability during distillations", 0.15, 20, ["physics"])],
        "UTILITY", ["leak_sense", "silent_flight", "glow_eyes"], None,
        unlock=("QUEST", 16), food=["moths", "argon"], breeding_group="avian",
    ),
    species(
        "prism_finch", "Prism Finch", "AETHERKIN", "RARE",
        "Its plumage splits light across a spectrum. It can tell two nearly identical yellows apart.",
        (35, 30, 8, 6, 30, 28),
        [("PURITY_BOOST", "Colour-based purity grading at a glance", 0.22, 1, ["analytical"]),
         ("XP_MULTIPLIER", "+10% spectroscopy XP", 0.1, 14, ["analytical"])],
        "UTILITY", ["spectrum_sight", "colour_call", "dart"], None,
        unlock=("QUEST", 11), food=["seeds", "nectar"], breeding_group="avian",
    ),
    species(
        "ferro_snail", "Ferro Snail", "AETHERKIN", "UNCOMMON",
        "Its shell is a magnetic lattice. It hoovers iron nanoparticles off glass without scratching.",
        (55, 20, 6, 26, 4, 12),
        [("PURITY_BOOST", "Removes magnetic nanoparticle contamination", 0.25, 1, ["materials"]),
         ("REAGENT_FINDER", "Recovers magnetic catalysts", 0.15, 12, ["materials"])],
        "UTILITY", ["magnet_shell", "slow_crawl", "adsorb"], None,
        unlock=("QUEST", 9), food=["iron oxide", "algae"], breeding_group="mollusc",
    ),
    species(
        "ember_drake", "Ember Drake", "AETHERKIN", "MYTHIC",
        "A furnace with wings. Bonding one is less a capture and more a negotiated ceasefire.",
        (140, 90, 42, 30, 30, 26),
        [("HEAT_RESISTANCE", "Ignores furnace heat; can carry a crucible", 0.6, 1, ["synthesis"]),
         ("HAZARD_IMMUNITY", "Fire and molten-metal splash protection", 0.55, 40, ["safety"]),
         ("YIELD_BOOST", "+15% yield on high-temperature syntheses", 0.15, 55, ["synthesis"])],
        "DPS", ["breath_fire", "wing_buffet", "crucible_carry", "molten_roar"], None,
        unlock=("SKILL", 75), food=["coal", "metal ore", "ethanol"], breeding_group="elemental",
    ),
    species(
        "chrysalis_warden", "Chrysalis Warden", "AETHERKIN", "MYTHIC",
        "A cocoon that never quite hatches. It absorbs one fatal mistake per cycle and remembers it.",
        (110, 100, 14, 36, 18, 38),
        [("REBIRTH", "Once per session, prevents a fatal laboratory accident", 1.0, 1, ["safety"]),
         ("SAFETY_BUFFER", "Cuts safety-rating decay by 40%", 0.4, 30, ["safety"]),
         ("MANA_REGEN", "Restores stamina between long protocols", 0.2, 45, ["endurance"])],
        "SUPPORT", ["ward", "rebirth", "cocoon_shield"], None,
        unlock=("QUEST", 20), food=["silk", "moonlight"], breeding_group="insect",
    ),
]


def main() -> None:
    payload = {
        "version": 1,
        "category_note": "REAL_ANIMAL are ordinary working animals. AETHERKIN are original alchemical creatures; no borrowed bestiary names remain.",
        "species": {entry["species_id"]: entry for entry in SPECIES},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(SPECIES)} species to {OUT}")


if __name__ == "__main__":
    main()
