"""
Chemical Reagent Registry & Database
Stores authentic physical properties, color RGB signatures, and GHS hazard labels.
"""

from chemlab.models import ChemicalReagent, GHSHazard

REAGENT_REGISTRY: dict[str, ChemicalReagent] = {
    "water": ChemicalReagent(
        id="water",
        name="Destilliertes Wasser",
        formula="H2O",
        molar_mass=18.015,
        density_g_ml=1.0,
        ph=7.0,
        color_rgb=(0.95, 0.98, 1.0),
        description="Reinstes Lösungsmittel für alle Versuchsansätze.",
    ),
    "hcl": ChemicalReagent(
        id="hcl",
        name="Salzsäure (1M)",
        formula="HCl",
        molar_mass=36.46,
        density_g_ml=1.02,
        ph=0.1,
        color_rgb=(0.95, 0.98, 1.0),
        ghs_hazards=(GHSHazard.CORROSIVE, GHSHazard.HEALTH_HAZARD),
        description="Starke anorganische Säure, ätzend.",
    ),
    "naoh": ChemicalReagent(
        id="naoh",
        name="Natronlauge (1M)",
        formula="NaOH",
        molar_mass=39.997,
        density_g_ml=1.04,
        ph=14.0,
        color_rgb=(0.95, 0.98, 1.0),
        ghs_hazards=(GHSHazard.CORROSIVE,),
        description="Starke alkalische Lauge, stark ätzend.",
    ),
    "universal_indicator": ChemicalReagent(
        id="universal_indicator",
        name="Universalindikator-Lösung",
        formula="Indikator",
        molar_mass=100.0,
        ph=7.0,
        color_rgb=(0.2, 0.75, 0.3),  # Neutral green
        description="Farbstoffgemisch zur optischen Anzeige des pH-Wertes.",
    ),
    "hydrogen_peroxide": ChemicalReagent(
        id="hydrogen_peroxide",
        name="Wasserstoffperoxid (30%)",
        formula="H2O2",
        molar_mass=34.014,
        density_g_ml=1.11,
        ph=4.5,
        color_rgb=(0.94, 0.97, 1.0),
        ghs_hazards=(GHSHazard.OXIDIZING, GHSHazard.CORROSIVE),
        description="Starkes Oxidationsmittel für Schaumreaktionen und Oszillatoren.",
    ),
    "potassium_iodide": ChemicalReagent(
        id="potassium_iodide",
        name="Kaliumiodid-Lösung (1M)",
        formula="KI",
        molar_mass=166.0,
        density_g_ml=1.12,
        ph=7.0,
        color_rgb=(0.98, 0.96, 0.92),
        is_catalyst=True,
        description="Salz, fungiert als Katalysator bei der Zersetzung von Peroxid.",
    ),
    "dish_soap": ChemicalReagent(
        id="dish_soap",
        name="Tensid-Spülmittel",
        formula="Surfactant",
        molar_mass=250.0,
        density_g_ml=1.03,
        ph=7.5,
        color_rgb=(0.2, 0.7, 0.9),
        description="Herabsetzung der Oberflächenspannung zur stabilen Schaumbildung.",
    ),
    "malonic_acid": ChemicalReagent(
        id="malonic_acid",
        name="Malonsäure",
        formula="CH2(COOH)2",
        molar_mass=104.06,
        density_g_ml=1.62,
        ph=2.8,
        color_rgb=(0.98, 0.98, 0.98),
        description="Dicarbonsäure als Kohlenstoff-Substrat für die Briggs-Rauscher-Reaktion.",
    ),
    "potassium_iodate": ChemicalReagent(
        id="potassium_iodate",
        name="Kaliumiodat",
        formula="KIO3",
        molar_mass=214.0,
        density_g_ml=3.89,
        ph=6.5,
        color_rgb=(0.96, 0.96, 0.98),
        ghs_hazards=(GHSHazard.OXIDIZING,),
        description="Iodat-Quelle für die zyklische Redox-Oszillation.",
    ),
    "manganese_sulfate": ChemicalReagent(
        id="manganese_sulfate",
        name="Mangansulfat",
        formula="MnSO4",
        molar_mass=151.0,
        density_g_ml=2.95,
        ph=5.0,
        color_rgb=(0.97, 0.88, 0.90),  # Pale pink
        is_catalyst=True,
        description="Mn(II)/Mn(III) Übergangsmetallkatalysator für die chemische Uhr.",
    ),
    "starch": ChemicalReagent(
        id="starch",
        name="Stärke-Lösung",
        formula="(C6H10O5)n",
        molar_mass=5000.0,
        density_g_ml=1.01,
        ph=7.0,
        color_rgb=(0.92, 0.92, 0.95),
        description="Indikator: bildet mit Polyiodid-Ionen einen tiefdunkelblauen Einschlusskomplex.",
    ),
    "lead_nitrate": ChemicalReagent(
        id="lead_nitrate",
        name="Bleinitrat",
        formula="Pb(NO3)2",
        molar_mass=331.2,
        density_g_ml=4.53,
        ph=4.0,
        color_rgb=(0.98, 0.98, 1.0),
        ghs_hazards=(GHSHazard.TOXIC, GHSHazard.ENVIRONMENTAL),
        description="Edukt für die Fällungsreaktion des Goldenen Regens (Bleiiadid).",
    ),
    "luminol": ChemicalReagent(
        id="luminol",
        name="Luminol-Reagenz",
        formula="C8H7N3O2",
        molar_mass=177.16,
        density_g_ml=1.05,
        ph=11.0,
        color_rgb=(0.85, 0.92, 0.98),
        description="Lumineszenz-Farbstoff; emittiert bei Oxidation hellblaues Licht (425 nm).",
    ),
    "nacl": ChemicalReagent(
        id="nacl",
        name="Natriumchlorid (Kochsalz)",
        formula="NaCl",
        molar_mass=58.44,
        density_g_ml=2.16,
        ph=7.0,
        color_rgb=(0.96, 0.98, 1.0),
        description="Harmloses Salz, Produkt der Säure-Base-Neutralisation.",
    ),
}


def get_reagent(reagent_id: str) -> ChemicalReagent:
    """Retrieve chemical reagent by identifier, raising KeyError if unknown."""
    rid = reagent_id.lower().strip()
    if rid not in REAGENT_REGISTRY:
        raise KeyError(f"Unknown chemical reagent: {reagent_id}")
    return REAGENT_REGISTRY[rid]
