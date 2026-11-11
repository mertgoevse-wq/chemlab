"""
Corrosion simulation: mixed potential theory, Tafel kinetics, Pourbaix regions,
pitting risk and corrosion rate in mm/y.

All potentials in V vs SHE, current densities in A/cm².
"""

from __future__ import annotations

from dataclasses import dataclass

from chemlab.simulation.electrochemistry.constants import T0


@dataclass
class CorrosionSystem:
    metal: str
    environment: str  # "seawater", "acidic", "atmospheric"
    temperature_k: float
    ph: float
    chloride_mol_l: float
    oxygen_ppm: float
    anodic_tafel_slope_v_dec: float  # b_a
    cathodic_tafel_slope_v_dec: float  # b_c
    i_corr_a_cm2: float | None = None
    e_corr_v: float | None = None
    corrosion_rate_mm_y: float | None = None
    pitting_potential_v: float | None = None


@dataclass
class TafelCurve:
    potentials_v: list[float]
    anodic_currents_a_cm2: list[float]
    cathodic_currents_a_cm2: list[float]


@dataclass
class PourbaixRegion:
    ph_min: float
    ph_max: float
    potential_min_v: float
    potential_max_v: float
    dominant_species: str
    stable: bool


class CorrosionSimulator:
    """Mixed-potential corrosion modelling."""

    K_MM_Y: float = 3.27e-3  # mm·g/(µA·cm·y) conversion constant

    def mixed_potential(
        self,
        cs: CorrosionSystem,
        e_range_v: tuple[float, float] = (-1.0, 1.0),
        num_points: int = 200,
    ) -> tuple[float, float]:
        """Find E_corr and i_corr where anodic + cathodic currents sum to zero.

        Uses simple Tafel extrapolation:
            i_a = i0_a * 10^((E - E_eq_a) / b_a)
            i_c = -i0_c * 10^((E_eq_c - E) / b_c)
        Solved by bisection on net current.
        """
        e_lo, e_hi = e_range_v

        def net_current(e: float) -> float:
            i_a = 1e-6 * 10 ** ((e - (-0.76)) / cs.anodic_tafel_slope_v_dec)  # approx Zn
            i_c = -1e-5 * 10 ** (((0.34) - e) / cs.cathodic_tafel_slope_v_dec)  # approx O2
            return i_a + i_c

        f_lo = net_current(e_lo)
        f_hi = net_current(e_hi)
        if f_lo * f_hi > 0:
            # No sign change in range; expand
            e_lo, e_hi = -2.0, 2.0
            f_lo = net_current(e_lo)
            f_hi = net_current(e_hi)

        for _ in range(100):
            e_mid = (e_lo + e_hi) / 2.0
            f_mid = net_current(e_mid)
            if abs(f_mid) < 1e-15:
                break
            if f_lo * f_mid <= 0:
                e_hi = e_mid
            else:
                e_lo = e_mid
                f_lo = f_mid

        e_corr = (e_lo + e_hi) / 2.0
        i_corr = abs(net_current(e_corr)) * 1e6  # µA/cm²

        cs.e_corr_v = e_corr
        cs.i_corr_a_cm2 = i_corr / 1e6
        cs.corrosion_rate_mm_y = self.corrosion_rate(
            i_corr_a_cm2=cs.i_corr_a_cm2,
            molar_mass_g_mol=65.38,
            n_electrons=2,
            density_g_cm3=7.14,
        )
        return e_corr, cs.i_corr_a_cm2

    def tafel_curves(
        self,
        cs: CorrosionSystem,
        e_range_v: tuple[float, float] | None = None,
        num_points: int = 100,
    ) -> TafelCurve:
        """Generate anodic/cathodic Tafel curves around E_corr."""
        if e_range_v is None:
            e_corr, _ = self.mixed_potential(cs)
            e_range_v = (e_corr - 0.5, e_corr + 0.5)
        e_lo, e_hi = e_range_v
        potentials = [e_lo + (e_hi - e_lo) * i / max(num_points - 1, 1) for i in range(num_points)]
        i_a = []
        i_c = []
        for e in potentials:
            i_a.append(1e-6 * 10 ** ((e - (-0.76)) / cs.anodic_tafel_slope_v_dec))
            i_c.append(-1e-5 * 10 ** (((0.34) - e) / cs.cathodic_tafel_slope_v_dec))
        return TafelCurve(
            potentials_v=potentials, anodic_currents_a_cm2=i_a, cathodic_currents_a_cm2=i_c
        )

    def corrosion_rate(
        self,
        i_corr_a_cm2: float,
        molar_mass_g_mol: float,
        n_electrons: int,
        density_g_cm3: float,
    ) -> float:
        """CR (mm/y) = i_corr * M * K / (n * rho)."""
        if i_corr_a_cm2 <= 0 or n_electrons <= 0 or density_g_cm3 <= 0:
            return 0.0
        i_corr_ua = i_corr_a_cm2 * 1e6  # µA/cm²
        return (i_corr_ua * molar_mass_g_mol * self.K_MM_Y) / (n_electrons * density_g_cm3)

    def pourbaix_regions(
        self,
        metal: str,
        temperature_k: float = T0,
        activity: float = 1.0,
    ) -> list[PourbaixRegion]:
        """Approximate Pourbaix stability regions for a metal (placeholder data).

        Returns coarse regions: immune / corrosion / passivation based on
        simplified metal oxide thermodynamics.
        """
        # Simplified, illustrative regions (not authoritative for engineering)
        regions: list[PourbaixRegion] = [
            PourbaixRegion(
                ph_min=0.0,
                ph_max=7.0,
                potential_min_v=-2.0,
                potential_max_v=-0.6,
                dominant_species=f"{metal}(aq)",
                stable=True,
            ),
            PourbaixRegion(
                ph_min=7.0,
                ph_max=14.0,
                potential_min_v=-1.2,
                potential_max_v=-0.4,
                dominant_species=f"{metal}(OH)2(s)",
                stable=True,
            ),
            PourbaixRegion(
                ph_min=0.0,
                ph_max=14.0,
                potential_min_v=-0.4,
                potential_max_v=1.5,
                dominant_species="corrosion",
                stable=False,
            ),
        ]
        return regions

    def pitting_risk(
        self,
        cs: CorrosionSystem,
        critical_chloride_mol_l: float = 0.1,
    ) -> tuple[bool, str]:
        """Assess pitting risk: E_pit > E_corr + margin and [Cl-] above threshold."""
        e_corr, _ = self.mixed_potential(cs)
        e_pit = e_corr + 0.3  # V, rough margin
        cs.pitting_potential_v = e_pit
        chloride_exceeds = cs.chloride_mol_l > critical_chloride_mol_l
        anodic_driving = cs.anodic_tafel_slope_v_dec > 0.05
        at_risk = chloride_exceeds and anodic_driving
        if at_risk:
            reason = (
                f"Pitting risk: [Cl-]={cs.chloride_mol_l:.4f} M > {critical_chloride_mol_l} M "
                f"and E_pit≈{e_pit:.3f} V vs SHE."
            )
        else:
            reason = "No significant pitting risk under current conditions."
        return at_risk, reason
