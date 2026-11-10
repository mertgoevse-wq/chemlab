"""
Comprehensive Worldwide Laboratory Taxonomy & Equipment Registry.
Classifies international laboratory archetypes, safety containment levels,
specialized analytical instruments, glassware, and hazard profiles:
  1. Academic Teaching & Fundamental Chemistry Lab
  2. Analytical Spectroscopy & Chromatography Core Facility
  3. Organic Synthesis & Medicinal Chemistry Laboratory
  4. Biosafety Level Containment Facility (BSL-2 / BSL-3 / BSL-4)
  5. High-Temperature Inorganic Materials & Solid-State Lab
  6. Electrochemistry, Fuel Cell & Battery Research Facility
  7. Industrial Chemical Engineering Pilot Plant
  8. Forensic Toxicology & Crime Scene Investigation Lab
  9. Mobile Emergency HazMat & Environmental Field Unit
 10. Clandestine / Improvisational Synthesis & Hazard Mitigation Lab
 11. Orbital Microgravity & Extreme Planetary Laboratory
"""

from __future__ import annotations

from dataclasses import dataclass
from chemlab.compat import StrEnum, UTC


class SafetyContainmentLevel(StrEnum):
    """International biosafety and chemical containment classifications."""

    STANDARD_CLASS_1 = "Standard Class 1 (General Chemical)"
    CONTROLLED_CLASS_2 = "Controlled Class 2 (Fume Hood Mandatory)"
    HIGH_CONTAINMENT_CLASS_3 = "High Containment Class 3 (BSL-3 / Glovebox Negative Pressure)"
    MAXIMUM_CONTAINMENT_CLASS_4 = "Maximum Containment Class 4 (Positive Pressure Hazmat Suit)"
    HAZMAT_EXPLOSION_PROOF = "ATEX Zone 0/1 Explosion Proof"
    IMPROVISED_UNREGULATED = "Unregulated Improvised (High Risk)"


class EquipmentCategory(StrEnum):
    """Classification of apparatus and machinery found across laboratory archetypes."""

    GLASSWARE_SYNTHETIC = "glassware_synthetic"
    ANALYTICAL_SPECTROSCOPY = "analytical_spectroscopy"
    THERMAL_HEATING_COOLING = "thermal_heating_cooling"
    SEPARATION_PURIFICATION = "separation_purification"
    SAFETY_CONTAINMENT = "safety_containment"
    PRESSURE_VACUUM = "pressure_vacuum"
    MEASUREMENT_SENSING = "measurement_sensing"


@dataclass(frozen=True)
class EquipmentDefinition:
    """Specific laboratory instrument or apparatus model specification."""

    item_id: str
    name: str
    category: EquipmentCategory
    description: str
    power_watts: float
    operating_temp_range_c: tuple[float, float]
    materials: list[str]
    features: list[str]


@dataclass
class LaboratoryArchetype:
    """Complete specification of a distinct laboratory archetype worldwide."""

    archetype_id: str
    title: str
    short_description: str
    containment_level: SafetyContainmentLevel
    ventilation_type: str  # Ducted Fume Hood, Laminar Flow, Recirculating, None
    dimensions_meters: tuple[float, float, float]
    key_equipment: list[EquipmentDefinition]
    reagent_palette: list[str]
    hazard_profile: list[str]
    narrative_context: str


# Comprehensive Equipment Catalog
EQUIPMENT_CATALOG: dict[str, EquipmentDefinition] = {
    # Analytical
    "nmr_400mhz": EquipmentDefinition(
        "nmr_400mhz",
        "400 MHz Superconducting FT-NMR Spectrometer",
        EquipmentCategory.ANALYTICAL_SPECTROSCOPY,
        "High-resolution 1H/13C/19F/31P nuclear magnetic resonance spectrometer with liquid He cryostat.",
        3500.0,
        (-196.0, 100.0),
        ["Superconducting Niobium-Titanium", "Austenitic Stainless Steel"],
        ["Auto-sampler carousel", "Fourier Transform processor", "Cryogenic level sensors"],
    ),
    "hplc_diodearray": EquipmentDefinition(
        "hplc_diodearray",
        "Analytical HPLC with UV-Vis Diode Array Detector",
        EquipmentCategory.ANALYTICAL_SPECTROSCOPY,
        "High-performance liquid chromatograph capable of 600 bar operating pressure.",
        1200.0,
        (4.0, 80.0),
        ["PEEK", "316L Stainless Steel", "Fused Silica"],
        ["Quaternary gradient pump", "Degasser", "Diode array spectrophotometer (190-800 nm)"],
    ),
    "gc_ms_quadrupole": EquipmentDefinition(
        "gc_ms_quadrupole",
        "Gas Chromatograph with Single Quadrupole Mass Spectrometer",
        EquipmentCategory.ANALYTICAL_SPECTROSCOPY,
        "Volatile compound separator coupled to electron ionization (EI) mass analyzer.",
        2200.0,
        (30.0, 450.0),
        ["Fused Quartz Capillary", "Gold-plated Quadrupole"],
        [
            "Split/splitless injector",
            "Turbo molecular vacuum pump (10^-6 mbar)",
            "NIST spectral library",
        ],
    ),
    "ftir_spectrometer": EquipmentDefinition(
        "ftir_spectrometer",
        "Fourier-Transform Infrared Spectrometer with ATR Diamond Crystal",
        EquipmentCategory.ANALYTICAL_SPECTROSCOPY,
        "Attenuated total reflectance infrared identifier for functional groups.",
        450.0,
        (15.0, 40.0),
        ["Monocrystalline Diamond", "Zinc Selenide optics"],
        ["Michelson interferometer", "Deuterated triglycine sulfate (DTGS) detector"],
    ),
    # Synthetic & Vacuum
    "schlenk_line_dual": EquipmentDefinition(
        "schlenk_line_dual",
        "Dual-Manifold Inert Gas / High-Vacuum Schlenk Line",
        EquipmentCategory.PRESSURE_VACUUM,
        "Four-port double manifold allowing simultaneous evacuation and argon backfilling.",
        800.0,
        (-196.0, 200.0),
        ["Borosilicate 3.3 Glass", "PTFE Stopcocks"],
        ["Liquid nitrogen cold trap", "Mercury bubbler pressure relief", "Pirani gauge connector"],
    ),
    "rotavapor_chiller": EquipmentDefinition(
        "rotavapor_chiller",
        "Digital Rotary Evaporator with Recirculating Chiller",
        EquipmentCategory.SEPARATION_PURIFICATION,
        "Gentle solvent removal under reduced vacuum with motorized lift.",
        1400.0,
        (-10.0, 180.0),
        ["Borosilicate 3.3 Glass", "PTFE Diaphragm", "Stainless Steel"],
        [
            "Digital vapor temperature probe",
            "Auto-distillation sensor",
            "Secondary cold-finger condenser",
        ],
    ),
    "magnetic_stirrer_hotplate": EquipmentDefinition(
        "magnetic_stirrer_hotplate",
        "Digital Ceramic Hotplate Magnetic Stirrer",
        EquipmentCategory.THERMAL_HEATING_COOLING,
        "Precision micro-controlled heating and stirring platform up to 1500 RPM.",
        650.0,
        (20.0, 500.0),
        ["Chemical Resistant Ceramic Deck", "Aluminum Housing"],
        ["PTFE stir bar", "PT1000 external temperature sensor", "Runaway overheating cut-off"],
    ),
    "tube_furnace_1600c": EquipmentDefinition(
        "tube_furnace_1600c",
        "Horizontal High-Temperature Split Tube Furnace",
        EquipmentCategory.THERMAL_HEATING_COOLING,
        "Atmosphere-controlled sintering and solid-state reaction chamber up to 1600°C.",
        4200.0,
        (20.0, 1600.0),
        ["Silicon Carbide (SiC) Heating Elements", "Alumina Tube (Al2O3)"],
        [
            "Multi-segment PID programmer",
            "Gas mixing manifold (Ar, H2/Ar, O2)",
            "Vacuum flange seals",
        ],
    ),
    "glovebox_inert": EquipmentDefinition(
        "glovebox_inert",
        "Hermetic Dual-Workstation Inert Atmosphere Glovebox",
        EquipmentCategory.SAFETY_CONTAINMENT,
        "Closed-loop gas purification maintaining < 0.1 ppm O2 and < 0.1 ppm H2O.",
        1500.0,
        (15.0, 30.0),
        ["304 Stainless Steel", "Butyl Rubber Gloves", "Polycarbonate Window"],
        [
            "Automatic regenerable copper catalyst",
            "Molecular sieve moisture trap",
            "Antechamber purge lock",
        ],
    ),
    # Improvised / Clandestine / Field
    "makeshift_heating_mantle": EquipmentDefinition(
        "makeshift_heating_mantle",
        "Improvised Rheostat Heating Mantle with Sand Bath",
        EquipmentCategory.THERMAL_HEATING_COOLING,
        "Modified electric element with dry silica sand bath for distributed thermal load.",
        850.0,
        (20.0, 380.0),
        ["Nichrome wire", "Cast iron skillet", "Quartz sand"],
        ["Analog voltage dimmer", "Prone to hotspots if unmonitored"],
    ),
    "clandestine_condenser_loop": EquipmentDefinition(
        "clandestine_condenser_loop",
        "Coiled Copper Tubing Ice-Chest Reflux Condenser",
        EquipmentCategory.SEPARATION_PURIFICATION,
        "Refrigeration copper coil submerged in saltwater/ice slurry for solvent capture.",
        60.0,
        (-5.0, 110.0),
        ["Copper", "PVC tubing", "Styrofoam reservoir"],
        ["High flow resistance", "Corrosion risk with acidic fumes"],
    ),
    "portable_raman_hazmat": EquipmentDefinition(
        "portable_raman_hazmat",
        "Handheld Point-and-Shoot Raman HazMat Identifier",
        EquipmentCategory.ANALYTICAL_SPECTROSCOPY,
        "785 nm laser spectrometer analyzing substances directly through clear glass or bags.",
        15.0,
        (-20.0, 50.0),
        ["Impact-resistant ABS", "IP67 sealed optic"],
        ["Instant GHS hazard match", "Fluorescence suppression", "15,000+ chemical library"],
    ),
}


# Worldwide Laboratory Archetypes
LABORATORY_ARCHETYPES: dict[str, LaboratoryArchetype] = {
    "academic_organic": LaboratoryArchetype(
        archetype_id="academic_organic",
        title="Universitäres Organisch-Chemisches Syntheselabor",
        short_description="Standardisiertes Hochschullabor für Mehrstufensynthesen und präparative Chemie.",
        containment_level=SafetyContainmentLevel.CONTROLLED_CLASS_2,
        ventilation_type="Umluftunabhängige Digestorien (Abluft 650 m³/h pro Abzug)",
        dimensions_meters=(10.0, 8.0, 3.4),
        key_equipment=[
            EQUIPMENT_CATALOG["schlenk_line_dual"],
            EQUIPMENT_CATALOG["rotavapor_chiller"],
            EQUIPMENT_CATALOG["magnetic_stirrer_hotplate"],
            EQUIPMENT_CATALOG["ftir_spectrometer"],
        ],
        reagent_palette=[
            "salicylic_acid",
            "acetic_anhydride",
            "H2SO4_aq",
            "ethanol",
            "acetone",
            "NaOH_aq",
            "HCl_aq",
            "CuSO4_aq",
            "KMnO4_s",
        ],
        hazard_profile=["Lösemittelbrände", "Exotherme Säurehydratation", "Siedeverzug"],
        narrative_context="Grundausbildung und Forschung in organischer Methodik. Gepflegt, protokolliert, strikte GSP-Vorgaben.",
    ),
    "analytical_spectroscopy": LaboratoryArchetype(
        archetype_id="analytical_spectroscopy",
        title="Zentrales Analytik- und Spektroskopie-Institut",
        short_description="Klimatisierte Präzisionsmessumgebung für Strukturaufklärung und Reinheitskontrollen.",
        containment_level=SafetyContainmentLevel.STANDARD_CLASS_1,
        ventilation_type="Laminare Reinstluft (HEPA H14, Temperaturstabil ±0,5°C)",
        dimensions_meters=(14.0, 10.0, 3.8),
        key_equipment=[
            EQUIPMENT_CATALOG["nmr_400mhz"],
            EQUIPMENT_CATALOG["hplc_diodearray"],
            EQUIPMENT_CATALOG["gc_ms_quadrupole"],
            EQUIPMENT_CATALOG["ftir_spectrometer"],
        ],
        reagent_palette=["CDCl3", "DMSO_d6", "Methanol_HPLC", "Acetonitril_HPLC", "Wasser_MilliQ"],
        hazard_profile=[
            "Kryogene Erstickung (He/N2-Quench)",
            "Starke Magnetfelder (5 Gauss-Linie)",
        ],
        narrative_context="Validierung von Syntheseprodukten. Fehlerfreie Peak-Zuordnung und quantitative Reinheitsanalysen.",
    ),
    "solid_state_materials": LaboratoryArchetype(
        archetype_id="solid_state_materials",
        title="Festkörper- und Feststoff-Materialforschung",
        short_description="Hochtemperatur-Ofenstrecken und inerte Gloveboxen für Batteriematerialien und Halbleiter.",
        containment_level=SafetyContainmentLevel.HIGH_CONTAINMENT_CLASS_3,
        ventilation_type="Argon-Schutzgas-Reinigungskreislauf (< 0.1 ppm O2/H2O)",
        dimensions_meters=(12.0, 9.0, 3.5),
        key_equipment=[
            EQUIPMENT_CATALOG["tube_furnace_1600c"],
            EQUIPMENT_CATALOG["glovebox_inert"],
            EQUIPMENT_CATALOG["magnetic_stirrer_hotplate"],
        ],
        reagent_palette=[
            "Lithium_metallisch",
            "Titandioxid",
            "Graphenoxid",
            "Argon_5.0",
            "Stickstoff_5.0",
        ],
        hazard_profile=[
            "Pyrophore Substanzen",
            "Extreme Hitze (1600°C)",
            "Druckbehälter-Überhitzung",
        ],
        narrative_context="Synthese neuartiger Kathodenmaterialien und Supraleiter unter striktem Luftausschluss.",
    ),
    "forensic_investigation": LaboratoryArchetype(
        archetype_id="forensic_investigation",
        title="Forensisches Kriminal- und Toxikologielabor",
        short_description="Spurenanalyse, Brandmittelidentifikation und toxikologische Substanznachweise.",
        containment_level=SafetyContainmentLevel.CONTROLLED_CLASS_2,
        ventilation_type="Gerichtete Absaugung mit Aktivkohlefilter",
        dimensions_meters=(9.0, 7.0, 3.2),
        key_equipment=[
            EQUIPMENT_CATALOG["portable_raman_hazmat"],
            EQUIPMENT_CATALOG["gc_ms_quadrupole"],
            EQUIPMENT_CATALOG["hplc_diodearray"],
        ],
        reagent_palette=[
            "Luminol",
            "Ninhydrin",
            "Wasserstoffperoxid_30",
            "Methanol",
            "Salzsäure_1M",
        ],
        hazard_profile=[
            "Bioaktive Gifte",
            "Biologische Kontamination",
            "Kettenantriebs-Rückstände",
        ],
        narrative_context="Ermittlungsunterstützung bei chemischen Vorfällen. Beweiskräftige Dokumentation und Fingerabdruck-Fuming.",
    ),
    "clandestine_improvised": LaboratoryArchetype(
        archetype_id="clandestine_improvised",
        title="Improvisiertes Clandestines Sicherheits-Labor",
        short_description="Abgelegenes, behelfsmäßiges Labor mit improvisierter Apparatur und extremem Gefahrenpotenzial.",
        containment_level=SafetyContainmentLevel.IMPROVISED_UNREGULATED,
        ventilation_type="Passives Kellerfenster / Rohrlüfter (Ungenügend)",
        dimensions_meters=(6.0, 5.0, 2.5),
        key_equipment=[
            EQUIPMENT_CATALOG["makeshift_heating_mantle"],
            EQUIPMENT_CATALOG["clandestine_condenser_loop"],
            EQUIPMENT_CATALOG["portable_raman_hazmat"],
        ],
        reagent_palette=[
            "Aceton",
            "Salzsäure_konz",
            "Natriumhydroxid",
            "Schwefelsäure_technisch",
            "Toluol",
        ],
        hazard_profile=[
            "Akute Verpuffungsgefahr (Dämpfe)",
            "Thermisches Durchgehen (Runaway)",
            "Toxische Chlorgas- / Stickoxidfreisetzung",
            "Mangelnde Notausrüstung",
        ],
        narrative_context="Untersuchung von Gefahrenquellen und Katastrophenschutz-Training. Verdeutlicht drastisch, warum formelle Sicherheitsstandards überlebenswichtig sind.",
    ),
    "industrial_pilot_plant": LaboratoryArchetype(
        archetype_id="industrial_pilot_plant",
        title="Industrielle chemische Pilot- und Reaktionsanlage",
        short_description="Großtechnische Skalierung mit 50L Doppelmantel-Reaktoren und automatisierter Prozessleittechnik.",
        containment_level=SafetyContainmentLevel.HAZMAT_EXPLOSION_PROOF,
        ventilation_type="Industrie-Gaswäscher (Scrubber) mit kontinuierlicher Raumluftüberwachung",
        dimensions_meters=(20.0, 15.0, 6.0),
        key_equipment=[
            EQUIPMENT_CATALOG["hplc_diodearray"],
            EQUIPMENT_CATALOG["schlenk_line_dual"],
        ],
        reagent_palette=["Toluol_bulk", "Ethanol_99_bulk", "Stickstoff_bulk", "Natronlauge_50pct"],
        hazard_profile=["Statische Entladung", "Druckentlastungsvolumen", "Toxische Großleckagen"],
        narrative_context="Prozessoptimierung und Massenbilanzierung vor der weltweiten Produktionsfreigabe.",
    ),
}


class GlobalLabRegistry:
    """Provides querying, generation, and equipment inspection for open-world labs."""

    def __init__(self) -> None:
        self.archetypes = LABORATORY_ARCHETYPES
        self.equipment = EQUIPMENT_CATALOG

    def get_archetype(self, archetype_id: str) -> LaboratoryArchetype | None:
        return self.archetypes.get(archetype_id)

    def list_all_archetypes(self) -> list[LaboratoryArchetype]:
        return list(self.archetypes.values())

    def get_equipment(self, item_id: str) -> EquipmentDefinition | None:
        return self.equipment.get(item_id)


# Global singleton
LAB_REGISTRY = GlobalLabRegistry()
