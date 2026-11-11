"""
ChemLab Total Syntheses & Pharmaceutical Protocol Database.
Houses rigorous multi-stage chemical recipes for active pharmaceutical ingredients (APIs),
organic pigments, and natural product extractions (Aspirin, Paracetamol, Caffeine, Indigo, Benzocaine).
Includes stoichiometry, temperature control windows, quenching, and recrystallization stages.
"""

from __future__ import annotations

from dataclasses import dataclass

from chemlab.compat import StrEnum


class TechniqueType(StrEnum):
    """Laboratory unit operations involved in organic synthesis."""

    REFLUX_HEATING = "reflux_heating"
    ICE_BATH_QUENCHING = "ice_bath_quenching"
    VACUUM_FILTRATION = "vacuum_filtration"
    RECRYSTALLIZATION = "recrystallization"
    LIQUID_EXTRACTION = "liquid_extraction"
    SUBLIMATION = "sublimation"
    PRECIPITATION = "precipitation"


@dataclass(frozen=True)
class SynthesisStage:
    """A distinct milestone/step within a multi-stage chemical synthesis protocol."""

    stage_number: int
    name: str
    description: str
    technique: TechniqueType
    required_inputs: tuple[str, ...]
    temperature_target_c: float
    duration_s: float
    safety_notes: str = ""


@dataclass(frozen=True)
class SynthesisProtocol:
    """Full architectural synthesis recipe for a target pharmaceutical or chemical compound."""

    id: str
    target_molecule: str
    cas_number: str
    molar_mass_g_mol: float
    description: str
    initial_reagents: tuple[str, ...]
    catalysts: tuple[str, ...]
    stages: tuple[SynthesisStage, ...]
    final_color_rgb: tuple[float, float, float] = (0.95, 0.95, 0.98)
    produces_colored_precipitate: bool = False
    sublimation_point_c: float | None = None

    def theoretical_yield_g(self, moles_limiting: float) -> float:
        """Calculates 100% stoichiometric yield in grams for a given limiting reagent molar input."""
        return round(moles_limiting * self.molar_mass_g_mol, 4)


class SynthesisRegistry:
    """Central store for all validated total synthesis and pharmaceutical protocols."""

    def __init__(self) -> None:
        self._protocols: dict[str, SynthesisProtocol] = self._build_protocols()

    def list_available_protocols(self) -> list[str]:
        return list(self._protocols.keys())

    def get_protocol(self, protocol_id: str) -> SynthesisProtocol:
        pid = protocol_id.lower().strip()
        if pid not in self._protocols:
            raise KeyError(f"Synthesis protocol '{protocol_id}' not found in registry.")
        return self._protocols[pid]

    def _build_protocols(self) -> dict[str, SynthesisProtocol]:
        return {
            "aspirin": SynthesisProtocol(
                id="aspirin",
                target_molecule="Acetylsalicylsäure (Aspirin)",
                cas_number="50-78-2",
                molar_mass_g_mol=180.16,
                description="Synthese des weltweit am häufigsten verwendeten Analgetikums durch Veresterung der phenolischen OH-Gruppe.",
                initial_reagents=("salicylic_acid", "acetic_anhydride"),
                catalysts=("h2so4",),
                final_color_rgb=(0.96, 0.96, 0.98),
                produces_colored_precipitate=True,
                stages=(
                    SynthesisStage(
                        stage_number=1,
                        name="Elektrophile O-Acylierung",
                        description="Salicylsäure und Essigsäureanhydrid unter Zugabe von 3 Tropfen konzentrierter H2SO4 erhitzen.",
                        technique=TechniqueType.REFLUX_HEATING,
                        required_inputs=("salicylic_acid", "acetic_anhydride", "h2so4"),
                        temperature_target_c=65.0,
                        duration_s=60.0,
                        safety_notes="Essigsäureanhydrid reizt die Atemwege stark. Nur im Abzug handhaben!",
                    ),
                    SynthesisStage(
                        stage_number=2,
                        name="Quenching & Kristallisation",
                        description="Langsames Hinzufügen von eiskaltem Wasser zur Hydrolyse von überschüssigem Anhydrid.",
                        technique=TechniqueType.ICE_BATH_QUENCHING,
                        required_inputs=("water",),
                        temperature_target_c=5.0,
                        duration_s=30.0,
                        safety_notes="Stark exotherme Hydrolyse! Tropfenweise unter Rühren zugeben.",
                    ),
                    SynthesisStage(
                        stage_number=3,
                        name="Umkristallisation aus Ethanol/Wasser",
                        description="Reinigung der rohen Aspirin-Nadelkristalle zur Beseitigung von Restspuren freier Salicylsäure.",
                        technique=TechniqueType.RECRYSTALLIZATION,
                        required_inputs=("ethanol", "water"),
                        temperature_target_c=78.0,
                        duration_s=45.0,
                        safety_notes="Ethanol ist leicht entzündlich; offenen Bunsenbrenner fernhalten.",
                    ),
                ),
            ),
            "paracetamol": SynthesisProtocol(
                id="paracetamol",
                target_molecule="Paracetamol (Acetaminophen)",
                cas_number="103-90-2",
                molar_mass_g_mol=151.16,
                description="Direkte N-Acetylierung von 4-Aminophenol. Selektive Reaktion an der Aminogruppe vor der Hydroxylgruppe.",
                initial_reagents=("aminophenol", "acetic_anhydride"),
                catalysts=(),
                final_color_rgb=(0.94, 0.92, 0.88),
                produces_colored_precipitate=True,
                stages=(
                    SynthesisStage(
                        stage_number=1,
                        name="Selektive N-Acylierung",
                        description="4-Aminophenol in warmem Wasser suspendieren und äquimolares Essigsäureanhydrid zugeben.",
                        technique=TechniqueType.REFLUX_HEATING,
                        required_inputs=("aminophenol", "acetic_anhydride"),
                        temperature_target_c=60.0,
                        duration_s=50.0,
                        safety_notes="4-Aminophenol ist umweltgefährdend und gesundheitsschädlich.",
                    ),
                    SynthesisStage(
                        stage_number=2,
                        name="Eisbad-Fällung",
                        description="Abkühlen des Ansatzes auf 0 °C zur vollständigen Abscheidung der weißen Kristallblättchen.",
                        technique=TechniqueType.ICE_BATH_QUENCHING,
                        required_inputs=(),
                        temperature_target_c=0.0,
                        duration_s=30.0,
                    ),
                ),
            ),
            "caffeine_extraction": SynthesisProtocol(
                id="caffeine_extraction",
                target_molecule="Coffein (1,3,7-Trimethylxanthin)",
                cas_number="58-08-2",
                molar_mass_g_mol=194.19,
                description="Fest-Flüssig-Extraktion aus biologischem Rohmaterial mit anschließender Sublimation des reinen Alkaloids.",
                initial_reagents=("tea_leaves", "water", "sodium_carbonate", "dichloromethane"),
                catalysts=(),
                final_color_rgb=(0.98, 0.98, 1.0),
                sublimation_point_c=178.0,
                stages=(
                    SynthesisStage(
                        stage_number=1,
                        name="Wässrig-alkalische Extraktion",
                        description="Auskochen des Tees mit Na2CO3 zur Fällung störender Gerbstoffe (Tannine).",
                        technique=TechniqueType.REFLUX_HEATING,
                        required_inputs=("tea_leaves", "water", "sodium_carbonate"),
                        temperature_target_c=100.0,
                        duration_s=60.0,
                    ),
                    SynthesisStage(
                        stage_number=2,
                        name="Flüssig-Flüssig-Extraktion",
                        description="Ausschütteln der wässrigen Phase mit Dichlormethan im Scheidetrichter.",
                        technique=TechniqueType.LIQUID_EXTRACTION,
                        required_inputs=("dichloromethane",),
                        temperature_target_c=20.0,
                        duration_s=40.0,
                        safety_notes="Dichlormethan-Dämpfe sind narkotisch und gesundheitsschädlich (GHS08).",
                    ),
                    SynthesisStage(
                        stage_number=3,
                        name="Vakuum-Sublimation",
                        description="Erhitzen des Roh-Coffeins auf 178 °C unter Kühlen des Sublimationsfingers.",
                        technique=TechniqueType.SUBLIMATION,
                        required_inputs=(),
                        temperature_target_c=178.0,
                        duration_s=30.0,
                    ),
                ),
            ),
            "indigo_dye": SynthesisProtocol(
                id="indigo_dye",
                target_molecule="Indigo-Farbstoff",
                cas_number="482-89-3",
                molar_mass_g_mol=262.26,
                description="Klassische Baeyer-Drewson-Synthese von Indigo aus 2-Nitrobenzaldehyd und Aceton in alkalischer Lösung.",
                initial_reagents=("nitrobenzaldehyde", "acetone", "naoh"),
                catalysts=(),
                final_color_rgb=(0.08, 0.12, 0.52),  # Deep royal blue
                produces_colored_precipitate=True,
                stages=(
                    SynthesisStage(
                        stage_number=1,
                        name="Kondensation & Dimerisierung",
                        description="Tropfenweise Zugabe von Natronlauge zum Gemisch aus Nitrobenzaldehyd und Aceton.",
                        technique=TechniqueType.PRECIPITATION,
                        required_inputs=("nitrobenzaldehyde", "acetone", "naoh"),
                        temperature_target_c=25.0,
                        duration_s=40.0,
                        safety_notes="Intensiver spontaner Farbumschlag zu Tiefblau. Hohe Färbekraft!",
                    ),
                ),
            ),
            "benzocaine": SynthesisProtocol(
                id="benzocaine",
                target_molecule="Benzocain (4-Aminobenzoesäureethylester)",
                cas_number="94-09-7",
                molar_mass_g_mol=165.19,
                description="Fischer-Veresterung von 4-Aminobenzoesäure (PABA) mit absolutem Ethanol unter Säurekatalyse.",
                initial_reagents=("paba", "ethanol"),
                catalysts=("h2so4",),
                final_color_rgb=(0.95, 0.95, 0.95),
                produces_colored_precipitate=True,
                stages=(
                    SynthesisStage(
                        stage_number=1,
                        name="Fischer-Veresterung am Rückfluss",
                        description="Kochen unter Rückfluss mit konzentrierter Schwefelsäure als wasserentziehendes Reagenz.",
                        technique=TechniqueType.REFLUX_HEATING,
                        required_inputs=("paba", "ethanol", "h2so4"),
                        temperature_target_c=78.0,
                        duration_s=60.0,
                        safety_notes="Konzentrierte Schwefelsäure wirkt stark dehydratisierend und ätzend.",
                    ),
                ),
            ),
            "robinson_tropinone": SynthesisProtocol(
                id="robinson_tropinone",
                target_molecule="Tropinon",
                cas_number="532-24-1",
                molar_mass_g_mol=139.19,
                description="Biomimetische Eintopf-Doppel-Mannich-Kondensation nach Sir Robert Robinson (1917).",
                initial_reagents=("succindialdehyde", "methylamine_hcl", "acetonedicarboxylic_acid"),
                catalysts=("sodium_acetate_buffer",),
                final_color_rgb=(0.91, 0.76, 0.42),
                produces_colored_precipitate=False,
                stages=(
                    SynthesisStage(
                        stage_number=1,
                        name="Acetal-Hydrolyse zu Succindialdehyd",
                        description="Hydrolyse von 2,5-Dimethoxytetrahydrofuran in 0.1 M HCl.",
                        technique=TechniqueType.REFLUX_HEATING,
                        required_inputs=("dimethoxytetrahydrofuran", "hcl_aq"),
                        temperature_target_c=75.0,
                        duration_s=45.0,
                    ),
                    SynthesisStage(
                        stage_number=2,
                        name="Biomimetische Doppel-Mannich-Kondensation",
                        description="Reaktion bei pH 5.5 gepuffert mit Natriumacetat bei Raumtemperatur.",
                        technique=TechniqueType.PRECIPITATION,
                        required_inputs=("succindialdehyde", "methylamine_hcl", "acetonedicarboxylic_acid", "sodium_acetate"),
                        temperature_target_c=25.0,
                        duration_s=90.0,
                    ),
                ),
            ),
            "atropine": SynthesisProtocol(
                id="atropine",
                target_molecule="(±)-Atropin",
                cas_number="51-55-8",
                molar_mass_g_mol=289.37,
                description="Totalsynthese von Atropin durch Reduktion von Tropinon zu Tropin und anschließende Fischer-Veresterung mit Tropasäure.",
                initial_reagents=("tropinone", "sodium_amalgam", "tropic_acid"),
                catalysts=("hcl_gas",),
                final_color_rgb=(0.98, 0.98, 0.96),
                produces_colored_precipitate=True,
                stages=(
                    SynthesisStage(
                        stage_number=1,
                        name="Stereoselektive Reduktion zu Tropin",
                        description="Reduktion der Carbonylgruppe von Tropinon mit Natriumamalgam zu 3-alpha-Tropanol.",
                        technique=TechniqueType.ICE_BATH_QUENCHING,
                        required_inputs=("tropinone", "sodium_amalgam"),
                        temperature_target_c=10.0,
                        duration_s=60.0,
                    ),
                    SynthesisStage(
                        stage_number=2,
                        name="Säurekatalysierte Ester-Kondensation",
                        description="Veresterung von Tropin mit (±)-Tropasäure unter Einleitung von trockenem HCl-Gas.",
                        technique=TechniqueType.REFLUX_HEATING,
                        required_inputs=("tropine", "tropic_acid", "hcl_gas"),
                        temperature_target_c=100.0,
                        duration_s=90.0,
                        safety_notes="Atropin ist ein hochpotentes Parasympatholytikum (GHS06). Antidot: Physostigmin.",
                    ),
                ),
            ),
            "triphenylmethanol_grignard": SynthesisProtocol(
                id="triphenylmethanol_grignard",
                target_molecule="Triphenylmethanol",
                cas_number="76-84-6",
                molar_mass_g_mol=260.33,
                description="Klassische Grignard-Reaktion: Phenylmagnesiumbromid reagiert mit Benzophenon unter C-C-Knüpfung.",
                initial_reagents=("bromobenzene", "magnesium_turnings", "benzophenone", "diethyl_ether"),
                catalysts=("iodine_crystal",),
                final_color_rgb=(0.97, 0.97, 0.98),
                produces_colored_precipitate=True,
                stages=(
                    SynthesisStage(
                        stage_number=1,
                        name="Grignard-Reagenz-Bildung",
                        description="Bildung von Phenylmagnesiumbromid aus Brombenzol und Magnesiumspänen in trockenem Ether.",
                        technique=TechniqueType.REFLUX_HEATING,
                        required_inputs=("bromobenzene", "magnesium_turnings", "diethyl_ether", "iodine_crystal"),
                        temperature_target_c=35.0,
                        duration_s=60.0,
                        safety_notes="Absolut wasserfrei arbeiten! Etherdämpfe extrem entzündlich.",
                    ),
                    SynthesisStage(
                        stage_number=2,
                        name="Elektrophile Addition an Benzophenon",
                        description="Tropfenweise Zugabe von Benzophenon-Etherlösung zum Grignard-Reagenz.",
                        technique=TechniqueType.ICE_BATH_QUENCHING,
                        required_inputs=("phenylmagnesium_bromide", "benzophenone"),
                        temperature_target_c=0.0,
                        duration_s=45.0,
                    ),
                ),
            ),
            "anthracene_diels_alder": SynthesisProtocol(
                id="anthracene_diels_alder",
                target_molecule="9,10-Dihydroanthracen-9,10-endo-alpha,beta-succinanhydrid",
                cas_number="5443-49-2",
                molar_mass_g_mol=276.29,
                description="[4+2]-Cycloaddition von Anthracen (Dien) mit Maleinsäureanhydrid (Dienophil) in Xylol.",
                initial_reagents=("anthracene", "maleic_anhydride", "xylene"),
                catalysts=(),
                final_color_rgb=(0.96, 0.96, 0.95),
                produces_colored_precipitate=True,
                stages=(
                    SynthesisStage(
                        stage_number=1,
                        name="Thermisches [4+2]-Cycloadditions-Refluxieren",
                        description="Kochen von Anthracen und Maleinsäureanhydrid in trockenem Xylol am Rückfluss.",
                        technique=TechniqueType.REFLUX_HEATING,
                        required_inputs=("anthracene", "maleic_anhydride", "xylene"),
                        temperature_target_c=140.0,
                        duration_s=60.0,
                    ),
                ),
            ),
        }
