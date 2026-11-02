"""
ChemLab Precursor & Starting Material Synthesis Database.
Provides complete multi-stage synthetic pathways for generating fundamental starting reagents
(Benzaldehyde, Nitroethane, 4-Aminophenol, Indole, Salicylic Acid) from basic commodity chemicals.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReactionStep:
    """Single synthetic step in precursor preparation."""

    step_number: int
    name: str
    equation: str
    reagents: tuple[str, ...]
    catalysts: tuple[str, ...] = ()
    temperature_c: float = 22.0
    pressure_bar: float = 1.0
    acid_catalyst: str | None = None
    yield_fraction: float = 0.85
    hazard_notes: str = ""


@dataclass(frozen=True)
class PrecursorPathway:
    """Full retrosynthetic pathway detailing how to prepare an essential chemical precursor."""

    id: str
    target_compound: str
    primary_feedstock: str
    cas_number: str
    description: str
    steps: tuple[ReactionStep, ...]


class PrecursorRegistry:
    """Central store for precursor chemical production chains."""

    def __init__(self) -> None:
        self._pathways: dict[str, PrecursorPathway] = self._build_pathways()

    def list_precursors(self) -> list[str]:
        return list(self._pathways.keys())

    def get_pathway(self, precursor_id: str) -> PrecursorPathway:
        pid = precursor_id.lower().strip()
        if pid not in self._pathways:
            raise KeyError(f"Precursor pathway '{precursor_id}' not found in registry.")
        return self._pathways[pid]

    def _build_pathways(self) -> dict[str, PrecursorPathway]:
        return {
            # 1) Benzaldehyde from Toluene
            "benzaldehyde": PrecursorPathway(
                id="benzaldehyde",
                target_compound="Benzaldehyd",
                primary_feedstock="Toluol",
                cas_number="100-52-7",
                description="Synthese von Benzaldehyd durch radikalische Seitenkettenchlorierung von Toluol zu Benzalchlorid gefolgt von wässriger Hydrolyse.",
                steps=(
                    ReactionStep(
                        step_number=1,
                        name="Radikalische Chlorierung zu Benzalchlorid",
                        equation="C7H8 + 2 Cl2 --(h*nu)--> C7H6Cl2 + 2 HCl",
                        reagents=("toluene", "chlorine_gas"),
                        catalysts=("uv_light",),
                        temperature_c=110.0,
                        hazard_notes="Chlorgas und HCl sind hochgiftig und ätzend. Streng im Abzug arbeiten.",
                    ),
                    ReactionStep(
                        step_number=2,
                        name="Basisch gepufferte Hydrolyse zu Benzaldehyd",
                        equation="C7H6Cl2 + H2O --(CaCO3)--> C7H6O + 2 HCl",
                        reagents=("benzal_chloride", "water", "caco3"),
                        catalysts=(),
                        temperature_c=100.0,
                        hazard_notes="Refluxkühlung erforderlich zur Vermeidung von Benzaldehyd-Verlusten.",
                    ),
                ),
            ),
            # 2) Salicylic Acid via Kolbe-Schmitt Reaction
            "salicylic_acid": PrecursorPathway(
                id="salicylic_acid",
                target_compound="Salicylsäure",
                primary_feedstock="Phenol",
                cas_number="69-72-7",
                description="Industrielle Kolbe-Schmitt-Synthese: Überführung von Phenol in Natriumphenolat gefolgt von Carboxylierung unter überkritischem/hochkomprimiertem CO2.",
                steps=(
                    ReactionStep(
                        step_number=1,
                        name="Deprotonierung zu Natriumphenolat",
                        equation="C6H5OH + NaOH -> C6H5ONa + H2O",
                        reagents=("phenol", "naoh"),
                        temperature_c=25.0,
                    ),
                    ReactionStep(
                        step_number=2,
                        name="Kolbe-Schmitt Carboxylierung unter Druck",
                        equation="C6H5ONa + CO2 -> C7H5O3Na",
                        reagents=("sodium_phenolate", "co2"),
                        temperature_c=125.0,
                        pressure_bar=6.0,  # 6 bar CO2 pressure
                        hazard_notes="Druckreaktor (Autoklav) erforderlich. Berstscheibe prüfen.",
                    ),
                    ReactionStep(
                        step_number=3,
                        name="Säuerung zur freien Salicylsäure",
                        equation="C7H5O3Na + HCl -> C7H6O3 + NaCl",
                        reagents=("sodium_salicylate", "hcl"),
                        temperature_c=15.0,
                        acid_catalyst="hcl",
                    ),
                ),
            ),
            # 3) Nitroethane from Bromoethane
            "nitroethane": PrecursorPathway(
                id="nitroethane",
                target_compound="Nitroethan",
                primary_feedstock="Bromoethan (Ethylbromid)",
                cas_number="79-24-3",
                description="Klassische Victor-Meyer-Reaktion: Nukleophile Substitution von Ethylbromid mit Natriumnitrit in polarem aprotischem Lösungsmittel.",
                steps=(
                    ReactionStep(
                        step_number=1,
                        name="Nukleophile Nitrierung (Victor Meyer)",
                        equation="CH3CH2Br + NaNO2 -> CH3CH2NO2 + NaBr",
                        reagents=("bromoethane", "nano2", "dmso"),
                        temperature_c=35.0,
                        hazard_notes="Als Nebenprodukt entsteht flüchtiges Ethylnitrit; kühlen und fraktionieren.",
                    ),
                ),
            ),
            # 4) 4-Aminophenol from Phenol
            "aminophenol": PrecursorPathway(
                id="aminophenol",
                target_compound="4-Aminophenol",
                primary_feedstock="Phenol",
                cas_number="123-30-8",
                description="Regioselektive elektrophile Nitrierung von Phenol zu 4-Nitrophenol gefolgt von Reduktion der Nitrogruppe zur Aminogruppe.",
                steps=(
                    ReactionStep(
                        step_number=1,
                        name="Para-selektive Nitrierung von Phenol",
                        equation="C6H5OH + HNO3 -> C6H5NO3 (para) + H2O",
                        reagents=("phenol", "hno3"),
                        temperature_c=10.0,
                        acid_catalyst="h2so4",
                    ),
                    ReactionStep(
                        step_number=2,
                        name="Béchamp-Reduktion mit Eisen und Salzsäure",
                        equation="4-Nitrophenol + 3 Fe + 6 HCl -> 4-Aminophenol + 3 FeCl2 + 2 H2O",
                        reagents=("nitrophenol", "iron_filings", "hcl"),
                        temperature_c=80.0,
                    ),
                ),
            ),
            # 5) Indole via Fischer Indole Synthesis
            "indole": PrecursorPathway(
                id="indole",
                target_compound="Indol",
                primary_feedstock="Phenylhydrazin",
                cas_number="120-72-9",
                description="Fischer-Indolsynthese: Säurekatalysierte Kondensation von Phenylhydrazin mit Acetaldehyd oder Brenztraubensäure mit nachfolgender Umlagerung.",
                steps=(
                    ReactionStep(
                        step_number=1,
                        name="Fischer-Indolsynthese",
                        equation="C6H5NHNH2 + C2H4O --(ZnCl2)--> C8H7N + NH3 + H2O",
                        reagents=("phenylhydrazine", "acetaldehyde"),
                        catalysts=("zncl2",),
                        acid_catalyst="zncl2",
                        temperature_c=140.0,
                        hazard_notes="Phenylhydrazin ist starkes Kontaktgift und Karzinogen. Nur in geschlossener Apparatur.",
                    ),
                ),
            ),
        }
