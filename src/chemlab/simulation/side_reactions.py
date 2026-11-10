"""
ChemLab Side-Reaction & Non-Ideal Impurity Engine.
Calculates competitive side-product formations, thermal decomposition, tarring/polymerization,
addition order hazards (water into acid), and incomplete conversion when reaction parameters deviate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from chemlab.compat import StrEnum, UTC


class ImpuritySeverity(StrEnum):
    """Classification of impurity impact on target chemical product."""

    NEGLIGIBLE = "negligible"  # < 1% trace, separable via standard wash
    MINOR = "minor"  # 1-5%, lowers melting point slightly
    MODERATE = "moderate"  # 5-20%, requires recrystallization
    CRITICAL = "critical"  # > 20%, ruined reaction mixture or toxic byproduct


@dataclass(frozen=True)
class ImpurityProduct:
    """Individual chemical side-product or degradation artifact."""

    name: str
    formula: str
    mass_fraction: float
    severity: ImpuritySeverity
    description: str


@dataclass
class ReactionConditionParameters:
    """Observable physical conditions applied to a reaction vessel."""

    reaction_id: str
    temperature_c: float
    has_catalyst: bool = True
    addition_order_correct: bool = True
    stirring_rpm: int = 400
    reaction_time_s: float = 60.0


@dataclass
class SideReactionReport:
    """Comprehensive evaluation of impurities, safety events, and yield quality."""

    is_successful: bool
    purity_percentage: float
    tarring_extent: float = 0.0  # 0.0 (crystal clear) to 1.0 (black tar)
    unreacted_fraction: float = 0.0
    violent_exotherm: bool = False
    aerosol_splashing: bool = False
    impurities: list[ImpurityProduct] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    color_discoloration_rgb: tuple[float, float, float] = (1.0, 1.0, 1.0)


class SideReactionAnalyzer:
    """
    Simulates non-ideal reaction dynamics based on temperature deviations,
    missing catalysts, improper addition sequences, and prolonged thermal exposure.
    """

    def evaluate_conditions(self, params: ReactionConditionParameters) -> SideReactionReport:
        """Processes vessel conditions and returns an impurity and safety report."""
        rid = params.reaction_id.lower().strip()

        # 1) Physical Hazard Check: Inverted addition of water into concentrated acid
        if not params.addition_order_correct:
            return SideReactionReport(
                is_successful=False,
                purity_percentage=10.0,
                tarring_extent=0.0,
                unreacted_fraction=0.8,
                violent_exotherm=True,
                aerosol_splashing=True,
                impurities=[
                    ImpurityProduct(
                        name="Aerosolisierte Schwefelsäuretröpfchen",
                        formula="H2SO4 (aq, aerosol)",
                        mass_fraction=0.15,
                        severity=ImpuritySeverity.CRITICAL,
                        description="Siedeverzug durch extreme Hydratationswärme.",
                    )
                ],
                warnings=[
                    "GEFAHR: Erst das Wasser, dann die Säure, sonst geschieht das Ungeheure!",
                    "Plötzliches Sieden und Verspritzen von ätzender Säure durch unzureichende Wärmeabfuhr.",
                ],
                color_discoloration_rgb=(0.95, 0.95, 0.95),
            )

        # 2) Aspirin Acylation Analysis
        if "aspirin" in rid:
            return self._evaluate_aspirin(params)

        # 3) Paracetamol Acylation Analysis
        if "paracetamol" in rid:
            return self._evaluate_paracetamol(params)

        # 4) Acetanilide Acylation Analysis
        if "acetanilide" in rid:
            return self._evaluate_acetanilide(params)

        # Generic default fallback evaluation
        return self._evaluate_generic(params)

    def _evaluate_aspirin(self, p: ReactionConditionParameters) -> SideReactionReport:
        optimal_t = 65.0
        delta_t = p.temperature_c - optimal_t
        impurities: list[ImpurityProduct] = []
        warnings: list[str] = []
        tarring = 0.0
        unreacted = 0.0
        color = (0.96, 0.96, 0.98)

        # Catalyst missing: reaction rate drops precipitously
        if not p.has_catalyst:
            unreacted = 0.72
            warnings.append(
                "Fehlender Katalysator (H2SO4): Reaktion verlaeuft unvollstaendig. Hoher Eduktanteil."
            )
            impurities.append(
                ImpurityProduct(
                    name="Unreagierte Salicylsäure",
                    formula="C7H6O3",
                    mass_fraction=unreacted,
                    severity=ImpuritySeverity.CRITICAL,
                    description="Ausgangsmaterial verunreinigt den Kristallkuchen.",
                )
            )

        # Thermal runaway / overheating (> 85 °C)
        if delta_t > 20.0:
            tarring = min(1.0, 0.15 + (delta_t - 20.0) * 0.015)
            poly_fraction = min(0.45, 0.1 + (delta_t - 20.0) * 0.012)
            impurities.append(
                ImpurityProduct(
                    name="Polysalicylate & Braune Verharzung (Teer)",
                    formula="[-C7H4O2-]n",
                    mass_fraction=poly_fraction,
                    severity=ImpuritySeverity.CRITICAL,
                    description="Selbstkondensation der Salicylsäure durch extreme Überhitzung.",
                )
            )
            warnings.append(
                f"Kritische Überhitzung ({p.temperature_c:.1f} °C > 85 °C): Zersetzung und Verharzung aufgetreten."
            )
            # Brown discoloration
            color = (0.45, 0.28, 0.12)

        # Calculate final purity
        loss = unreacted + tarring + sum(imp.mass_fraction for imp in impurities)
        purity = max(5.0, min(99.0, (1.0 - loss * 0.85) * 100.0))
        is_success = purity >= 80.0 and tarring < 0.15 and unreacted < 0.2

        return SideReactionReport(
            is_successful=is_success,
            purity_percentage=round(purity, 2),
            tarring_extent=round(tarring, 3),
            unreacted_fraction=round(unreacted, 3),
            impurities=impurities,
            warnings=warnings,
            color_discoloration_rgb=color,
        )

    def _evaluate_paracetamol(self, p: ReactionConditionParameters) -> SideReactionReport:
        impurities: list[ImpurityProduct] = []
        warnings: list[str] = []
        color = (0.94, 0.92, 0.88)
        unreacted = 0.0
        tarring = 0.0

        if p.temperature_c > 80.0:
            # Overheating causes oxidation to benzoquinone and double acylation
            ox_fraction = min(0.35, (p.temperature_c - 80.0) * 0.015)
            diacetyl_fraction = min(0.20, (p.temperature_c - 80.0) * 0.008)
            impurities.append(
                ImpurityProduct(
                    name="N-Acetyl-p-benzochinonimin (NAPQI-Derivate)",
                    formula="C8H7NO2",
                    mass_fraction=round(ox_fraction, 3),
                    severity=ImpuritySeverity.CRITICAL,
                    description="Oxidatives Nebenprodukt. Stark verfärbend und zelltoxisch.",
                )
            )
            impurities.append(
                ImpurityProduct(
                    name="N,O-Diacetyl-4-aminophenol",
                    formula="C10H11NO3",
                    mass_fraction=round(diacetyl_fraction, 3),
                    severity=ImpuritySeverity.MODERATE,
                    description="Zweifache Acylierung an Hydroxyl- und Aminogruppe.",
                )
            )
            warnings.append(
                "Thermische Überhitzung begünstigt chinoiden Abbau und doppelte Acylierung."
            )
            # Dark violet/brown hue
            color = (0.35, 0.18, 0.42)
            tarring = min(0.5, (p.temperature_c - 80.0) * 0.01)

        loss = unreacted + tarring + sum(imp.mass_fraction for imp in impurities)
        purity = max(8.0, min(99.0, (1.0 - loss * 0.8) * 100.0))
        is_success = purity >= 80.0 and tarring < 0.1

        return SideReactionReport(
            is_successful=is_success,
            purity_percentage=round(purity, 2),
            tarring_extent=round(tarring, 3),
            unreacted_fraction=round(unreacted, 3),
            impurities=impurities,
            warnings=warnings,
            color_discoloration_rgb=color,
        )

    def _evaluate_acetanilide(self, p: ReactionConditionParameters) -> SideReactionReport:
        """
        Evaluates Acetanilide acylation from Aniline and Acetic Anhydride.
        Optimal temperature range: 50.0°C - 80.0°C.
        - T < 45°C: Sluggish kinetics, high unreacted aniline fraction.
        - T > 105°C: Severe air oxidation of aniline to dark azobenzene & resinous tar.
        - Missing catalyst (glacial acetic acid / zinc dust): Slower yield with colored impurities.
        """
        impurities: list[ImpurityProduct] = []
        warnings: list[str] = []
        color = (0.97, 0.97, 0.99)  # Pure white crystalline appearance
        unreacted = 0.0
        tarring = 0.0

        if p.temperature_c < 45.0:
            unreacted = min(0.65, 0.20 + (45.0 - p.temperature_c) * 0.015)
            warnings.append(
                "Niedrige Temperatur: Unvollständige Acetylierung, unreagiertes Anilin verbleibt."
            )
            impurities.append(
                ImpurityProduct(
                    name="Unreagiertes Anilin",
                    formula="C6H7N",
                    mass_fraction=round(unreacted, 3),
                    severity=ImpuritySeverity.MODERATE,
                    description="Flüssiges aromatisches Amin mindert Kristallinität.",
                )
            )

        if p.temperature_c > 105.0:
            ox_delta = p.temperature_c - 105.0
            tarring = min(0.60, 0.12 + ox_delta * 0.018)
            azo_fraction = min(0.30, 0.05 + ox_delta * 0.01)
            impurities.append(
                ImpurityProduct(
                    name="Azobenzol & dunkelbraune Oxidationsharze",
                    formula="C12H10N2",
                    mass_fraction=round(azo_fraction, 3),
                    severity=ImpuritySeverity.CRITICAL,
                    description="Thermisch-oxidative Dimerisierung des Anilins.",
                )
            )
            warnings.append(
                f"Thermische Überhitzung ({p.temperature_c:.1f}°C): Oxidation zu Azobenzol und Verharzung."
            )
            # Brown-amber discoloration
            color = (0.42, 0.22, 0.08)

        loss = unreacted + tarring + sum(imp.mass_fraction for imp in impurities)
        purity = max(5.0, min(99.0, (1.0 - loss * 0.8) * 100.0))
        is_success = purity >= 80.0 and tarring < 0.12 and unreacted < 0.25

        return SideReactionReport(
            is_successful=is_success,
            purity_percentage=round(purity, 2),
            tarring_extent=round(tarring, 3),
            unreacted_fraction=round(unreacted, 3),
            impurities=impurities,
            warnings=warnings,
            color_discoloration_rgb=color,
        )

    def _evaluate_generic(self, p: ReactionConditionParameters) -> SideReactionReport:
        return SideReactionReport(
            is_successful=True,
            purity_percentage=96.0,
            tarring_extent=0.0,
            unreacted_fraction=0.04,
            impurities=[],
            warnings=[],
            color_discoloration_rgb=(1.0, 1.0, 1.0),
        )
