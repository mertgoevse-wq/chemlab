"""
ChemLab Omniroute & Local AI Reaction Solver Bridge.
Connects ChemLab to local AI endpoints (localhost:20128, NVIDIA NIM, OpenAI-compatible APIs)
to compute reaction factors, stoichiometry, thermodynamic properties, and organic synthesis pathways.
Provides robust offline deterministic fallback when the local AI daemon is offline.
"""

from __future__ import annotations

import json
import logging
import math
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from chemlab.models import LiquidMixture

logger = logging.getLogger("chemlab.ai.omniroute")


@dataclass
class ReactionFactorRequest:
    """Request payload containing active laboratory vessel parameters."""

    reagents: list[str]
    temperature_c: float = 22.0
    pressure_atm: float = 1.0
    volume_ml: float = 100.0
    catalysts: list[str] = field(default_factory=list)


@dataclass
class ChemicalReactionPrediction:
    """Predicted reaction dynamics and products computed by AI or physics fallback."""

    reaction_name: str
    balanced_equation: str
    products: dict[str, float]  # molar quantities or ratio
    enthalpy_kj_mol: float  # <0 exothermic, >0 endothermic
    activation_energy_kj_mol: float
    rate_constant_k: float  # s^-1 at 298.15 K
    target_color_rgb: tuple[float, float, float]
    produces_gas: bool = False
    gas_emission_rate: float = 0.0
    precipitate_formed: bool = False
    precipitate_color_rgb: tuple[float, float, float] = (1.0, 1.0, 1.0)
    emission_glow: float = 0.0
    safety_warnings: list[str] = field(default_factory=list)

    @property
    def is_exothermic(self) -> bool:
        return self.enthalpy_kj_mol < 0.0


class LocalReactionAIBridge:
    """
    Communicates with local Omniroute (localhost:20128) or local LLM instances.
    Gracefully falls back to high-fidelity analytical chemistry kinetics when offline.
    """

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:20128/v1",
        model: str = "kc/kilo-auto/free",
        timeout_seconds: float = 1.5,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def predict_reaction(self, request: ReactionFactorRequest) -> ChemicalReactionPrediction:
        """
        Attempts to query the local AI model for reaction factors.
        Falls back to analytical deterministic chemistry when the endpoint is unreachable.
        """
        prompt = self._build_prompt(request)
        ai_response = self._call_ai_endpoint(prompt)
        if ai_response:
            parsed = self._parse_ai_response(ai_response)
            if parsed:
                return parsed

        # Analytical deterministic fallback
        return self._deterministic_fallback(request)

    def step_with_time_dilation(
        self,
        mixture: LiquidMixture,
        dt_s: float,
        time_dilation: float = 1.0,
    ) -> tuple[LiquidMixture, ChemicalReactionPrediction]:
        """
        Advances the mixture state forward in time applying Arrhenius reaction kinetics
        and user-controlled time dilation (Zeitraffer).
        """
        effective_dt = dt_s * max(0.1, min(100.0, time_dilation))
        req = ReactionFactorRequest(
            reagents=list(mixture.reagent_moles.keys()),
            temperature_c=mixture.temperature_c,
            volume_ml=mixture.volume_ml,
        )
        prediction = self.predict_reaction(req)

        res = mixture.clone()
        if prediction.rate_constant_k <= 0.0:
            return res, prediction

        # Arrhenius temperature correction: k(T) = k_ref * exp(-Ea/R * (1/T - 1/T_ref))
        gas_const = 8.314  # J/(mol*K)
        t_kelvin = max(200.0, res.temperature_c + 273.15)
        t_ref = 298.15  # 25 °C
        ea_j = prediction.activation_energy_kj_mol * 1000.0
        temp_factor = math.exp(-ea_j / gas_const * (1.0 / t_kelvin - 1.0 / t_ref))
        k_actual = prediction.rate_constant_k * temp_factor

        # Reaction extent fraction xi in [0, 1]
        extent = min(1.0, k_actual * effective_dt)

        # Apply products
        for prod, moles in prediction.products.items():
            res.reagent_moles[prod] = res.reagent_moles.get(prod, 0.0) + moles * extent

        # Thermal delta: Q = -DeltaH * moles * extent
        delta_t = -prediction.enthalpy_kj_mol * extent * 0.15
        res.temperature_c = round(res.temperature_c + delta_t, 3)

        # Color morphing
        w = min(1.0, extent)
        res.color_rgb = tuple(
            round((1.0 - w) * res.color_rgb[i] + w * prediction.target_color_rgb[i], 4)
            for i in range(3)
        )

        if prediction.precipitate_formed:
            res.turbidity = min(1.0, res.turbidity + 0.3 * extent)
        if prediction.produces_gas:
            res.bubble_rate = min(1.0, res.bubble_rate + 0.5 * extent)
        if prediction.emission_glow > 0.0:
            res.emission_glow = min(1.0, res.emission_glow + prediction.emission_glow * extent)

        return res, prediction

    def _call_ai_endpoint(self, prompt: str) -> dict[str, Any] | None:
        """Sends an OpenAI-compatible completion request to the local Omniroute daemon."""
        url = f"{self.endpoint}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Du bist die wissenschaftliche Reaktions-KI für ChemLab. Antworte ausschließlich in reinem JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 512,
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
        except Exception as exc:
            logger.debug("Local AI bridge skipped: %s", exc)
            return None
        return None

    def _parse_ai_response(self, data: dict[str, Any]) -> ChemicalReactionPrediction | None:
        try:
            return ChemicalReactionPrediction(
                reaction_name=data.get("reaction_name", "Unbekannte Reaktion"),
                balanced_equation=data.get("balanced_equation", ""),
                products=data.get("products", {}),
                enthalpy_kj_mol=float(data.get("enthalpy_kj_mol", 0.0)),
                activation_energy_kj_mol=float(data.get("activation_energy_kj_mol", 30.0)),
                rate_constant_k=float(data.get("rate_constant_k", 0.1)),
                target_color_rgb=tuple(data.get("target_color_rgb", [0.95, 0.98, 1.0])),
                produces_gas=bool(data.get("produces_gas", False)),
                precipitate_formed=bool(data.get("precipitate_formed", False)),
                emission_glow=float(data.get("emission_glow", 0.0)),
                safety_warnings=list(data.get("safety_warnings", [])),
            )
        except Exception:
            return None

    def _build_prompt(self, request: ReactionFactorRequest) -> str:
        return (
            f"Berechne die chemische Reaktion für folgende Reagenzien: {request.reagents}. "
            f"Temperatur: {request.temperature_c} C, Druck: {request.pressure_atm} atm. "
            "Gib JSON mit folgenden Keys zurück: reaction_name, balanced_equation, products (dict von id: mol), "
            "enthalpy_kj_mol (float), activation_energy_kj_mol (float), rate_constant_k (float), "
            "target_color_rgb (float array [r,g,b] 0..1), produces_gas (bool), precipitate_formed (bool), "
            "emission_glow (float 0..1), safety_warnings (string array)."
        )

    def _deterministic_fallback(self, req: ReactionFactorRequest) -> ChemicalReactionPrediction:
        """High-precision analytical chemistry lookup for common organic and inorganic reactions."""
        reagents = set(req.reagents)

        # 1) Aspirin synthesis (Salicylic acid + Acetic anhydride -> Acetylsalicylic acid)
        if "salicylic_acid" in reagents and "acetic_anhydride" in reagents:
            return ChemicalReactionPrediction(
                reaction_name="Aspirin-Totalsynthese (Veresterung)",
                balanced_equation="C7H6O3 + C4H6O3 --(H2SO4)--> C9H8O4 + C2H4O2",
                products={"aspirin": 0.05, "acetic_acid": 0.05},
                enthalpy_kj_mol=-18.4,
                activation_energy_kj_mol=42.0,
                rate_constant_k=0.08,
                target_color_rgb=(0.95, 0.95, 0.98),
                precipitate_formed=True,  # Kristallisiert beim Abkühlen aus
                safety_warnings=["Starke Essigsäuredämpfe! Im Abzug arbeiten."],
            )

        # 2) Paracetamol synthesis (4-Aminophenol + Acetic anhydride)
        if "aminophenol" in reagents and "acetic_anhydride" in reagents:
            return ChemicalReactionPrediction(
                reaction_name="Paracetamol-Synthese (N-Acetylierung)",
                balanced_equation="C6H7NO + C4H6O3 -> C8H9NO2 + C2H4O2",
                products={"paracetamol": 0.045, "acetic_acid": 0.045},
                enthalpy_kj_mol=-24.5,
                activation_energy_kj_mol=38.0,
                rate_constant_k=0.12,
                target_color_rgb=(0.92, 0.88, 0.82),
                precipitate_formed=True,
                safety_warnings=["4-Aminophenol ist gesundheitsschädlich. Hautkontakt vermeiden."],
            )

        # 3) Indigo dye synthesis (Baeyer-Drewson)
        if "nitrobenzaldehyde" in reagents and "acetone" in reagents and "naoh" in reagents:
            return ChemicalReactionPrediction(
                reaction_name="Indigo-Farbstoffsynthese (Baeyer-Drewson)",
                balanced_equation="2 C7H5NO3 + 2 C3H6O + 2 NaOH -> C16H10N2O2 + 2 CH3COONa + 4 H2O",
                products={"indigo": 0.03, "sodium_acetate": 0.06},
                enthalpy_kj_mol=-65.0,
                activation_energy_kj_mol=28.0,
                rate_constant_k=0.25,
                target_color_rgb=(0.08, 0.12, 0.52),  # Tiefes Indigoblau
                precipitate_formed=True,
                safety_warnings=["Stark färbendes Pigment. Schutzhandschuhe tragen."],
            )

        # 4) Acid-base neutralization
        if "hcl" in reagents and "naoh" in reagents:
            return ChemicalReactionPrediction(
                reaction_name="Säure-Base-Neutralisation",
                balanced_equation="HCl + NaOH -> NaCl + H2O",
                products={"nacl": 0.1, "water": 0.1},
                enthalpy_kj_mol=-57.3,  # Klassische Neutralisationsenthalpie
                activation_energy_kj_mol=12.0,
                rate_constant_k=1.2,
                target_color_rgb=(0.15, 0.82, 0.25),  # Indikatorgrün
                safety_warnings=["Exotherme Reaktion. Vorsicht bei hohen Konzentrationen."],
            )

        # 5) Catalytic foam decomposition (Elephant Toothpaste)
        if "hydrogen_peroxide" in reagents and "potassium_iodide" in reagents:
            return ChemicalReactionPrediction(
                reaction_name="Katalytische Peroxid-Zersetzung (Elefanten-Zahnpasta)",
                balanced_equation="2 H2O2 --(KI)--> 2 H2O + O2 (g)",
                products={"water": 0.2, "oxygen_gas": 0.1},
                enthalpy_kj_mol=-98.2,
                activation_energy_kj_mol=56.0,
                rate_constant_k=0.85,
                target_color_rgb=(0.95, 0.95, 0.98),
                produces_gas=True,
                gas_emission_rate=0.9,
                safety_warnings=[
                    "Starke Heißdampf- und Sauerstoffbildung! Spritzschutz verwenden."
                ],
            )

        # 6) Chemiluminescence (Luminol)
        if "luminol" in reagents and "hydrogen_peroxide" in reagents:
            return ChemicalReactionPrediction(
                reaction_name="Luminol-Chemolumineszenz",
                balanced_equation="Luminol + H2O2 + 2 OH- -> 3-APA* -> 3-APA + h*nu (425 nm)",
                products={"aminophthalate": 0.01, "nitrogen": 0.01},
                enthalpy_kj_mol=-120.0,
                activation_energy_kj_mol=35.0,
                rate_constant_k=0.45,
                target_color_rgb=(0.2, 0.5, 0.95),
                emission_glow=1.0,
                safety_warnings=["Dunkelkammerbedingungen für maximale Lichtausbeute."],
            )

        # Default unreactive mixture
        return ChemicalReactionPrediction(
            reaction_name="Keine Reaktion (Lösung/Suspension)",
            balanced_equation="Keine chemische Veränderung",
            products={},
            enthalpy_kj_mol=0.0,
            activation_energy_kj_mol=100.0,
            rate_constant_k=0.0,
            target_color_rgb=(0.95, 0.98, 1.0),
        )
