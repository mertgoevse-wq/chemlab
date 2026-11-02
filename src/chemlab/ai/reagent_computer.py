"""
ChemLab AI Reagent Computer — Multi-Provider Reaction Computation Bridge.
Connects to:
  • Local Omniroute (localhost:20128) — primary local inference gateway
  • NVIDIA NIM (NVIDIA-hosted inference endpoints)
  • Google Gemini API (text + multimodal chemistry reasoning)
  • Deterministic analytical chemistry fallback (local Arrhenius kinetics)

Provides robust automatic fallback chain when any provider is offline,
quota-exhausted, or returns invalid responses.
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from chemlab.ai.omniroute_bridge import ChemicalReactionPrediction, ReactionFactorRequest

logger = logging.getLogger("chemlab.ai.reagent_computer")


class AIProviderStatus:
    """Tracks availability and quota status of AI providers."""

    def __init__(self, name: str, priority: int) -> None:
        self.name = name
        self.priority = priority
        self.available = False
        self.quota_exhausted = False
        self.last_error: str | None = None
        self.last_successful_call: float | None = None
        self.failure_count: int = 0
        self.cooldown_until: float = 0.0

    def can_attempt(self) -> bool:
        """Determines if a provider should be attempted right now."""
        if self.cooldown_until and time.time() < self.cooldown_until:
            return False
        return not self.quota_exhausted

    def mark_success(self) -> None:
        self.available = True
        self.quota_exhausted = False
        self.failure_count = 0
        self.last_successful_call = time.time()
        self.last_error = None

    def mark_failure(self, error: str, is_quota: bool = False) -> None:
        self.available = False
        self.last_error = error
        self.failure_count += 1
        if is_quota:
            self.quota_exhausted = True
            self.cooldown_until = time.time() + 600  # 10-minute cooldown on quota
        else:
            self.cooldown_until = time.time() + 30  # 30-second cooldown on failure


@dataclass
class ReagentComputationRequest:
    """Request payload for AI reagent computation across providers."""

    reagents: list[str]
    temperature_c: float = 22.0
    pressure_atm: float = 1.0
    volume_ml: float = 100.0
    catalysts: list[str] = field(default_factory=list)
    target_compound: str | None = None
    reaction_type: str | None = None
    time_dilation: float = 1.0


@dataclass
class ReagentComputationResult:
    """Comprehensive reaction computation result from any AI provider."""

    success: bool
    provider_used: str
    prediction: ChemicalReactionPrediction | None = None
    raw_response: dict[str, Any] | None = None
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    error_message: str | None = None
    fallback_used: bool = False


class AIReagentComputer:
    """
    Multi-provider AI reagent computation engine with automatic fallback.
    Chain: Omniroute → NVIDIA NIM → Google Gemini → Local Deterministic Fallback
    """

    def __init__(self) -> None:
        self.providers: dict[str, AIProviderStatus] = {}
        self.provider_order: list[str] = []
        self.endpoints: dict[str, str] = {}
        self.api_keys: dict[str, str] = {}
        self.models: dict[str, str] = {}
        self.timeout_seconds: float = 1.5

        # Setup default provider chain
        self._setup_default_providers()

        # Local deterministic fallback (always available)
        from chemlab.ai.omniroute_bridge import LocalReactionAIBridge

        self.local_bridge = LocalReactionAIBridge()

    def _setup_default_providers(self) -> None:
        """Configures the default provider chain with priorities."""
        provider_configs = [
            ("omniroute", 1, "http://127.0.0.1:20128/v1", None, "kc/kilo-auto/free"),
            (
                "nvidia_nim",
                2,
                "https://integrate.api.nvidia.com/v1",
                None,
                "meta/llama-3.1-70b-instruct",
            ),
            (
                "google_gemini",
                3,
                "https://generativelanguage.googleapis.com/v1beta",
                None,
                "gemini-2.5-pro",
            ),
        ]

        for name, priority, endpoint, api_key, model in provider_configs:
            self.providers[name] = AIProviderStatus(name, priority)
            self.endpoints[name] = endpoint
            self.api_keys[name] = api_key
            self.models[name] = model
            self.provider_order.append(name)

    def add_provider(
        self, name: str, priority: int, endpoint: str, api_key: str | None, model: str
    ) -> None:
        """Registers an additional AI provider in the chain."""
        self.providers[name] = AIProviderStatus(name, priority)
        self.endpoints[name] = endpoint
        self.api_keys[name] = api_key
        self.models[name] = model

        # Insert into ordered chain by priority (lower number = higher priority; equal priority prepends)
        inserted = False
        for i, existing_name in enumerate(self.provider_order):
            if self.providers[existing_name].priority >= priority:
                self.provider_order.insert(i, name)
                inserted = True
                break
        if not inserted:
            self.provider_order.append(name)

    def compute_reaction(self, request: ReagentComputationRequest) -> ReagentComputationResult:
        """
        Computes reaction dynamics using the first available AI provider.
        Falls through the chain: Omniroute → NVIDIA NIM → Gemini → Local Fallback.
        """
        # Try providers in priority order
        for provider_name in self.provider_order:
            provider = self.providers[provider_name]
            if not provider.can_attempt():
                continue

            start_time = time.time()
            try:
                prediction = self._call_provider(provider_name, request)
                latency_ms = (time.time() - start_time) * 1000.0
                if prediction:
                    provider.mark_success()
                    return ReagentComputationResult(
                        success=True,
                        provider_used=provider_name,
                        prediction=prediction,
                        latency_ms=latency_ms,
                        fallback_used=provider_name != "omniroute",
                    )
                else:
                    provider.mark_failure("Provider returned None prediction")
            except Exception as exc:  # noqa: BLE001 — broad catch for provider failover
                latency_ms = (time.time() - start_time) * 1000.0
                provider.mark_failure(str(exc), is_quota=self._is_quota_error(exc))
                logger.debug("Provider %s failed: %s", provider_name, exc)

        # All providers failed — use local deterministic fallback
        logger.info("All AI providers unavailable — using local deterministic fallback")
        try:
            factor_request = ReactionFactorRequest(
                reagents=request.reagents,
                temperature_c=request.temperature_c,
                pressure_atm=request.pressure_atm,
                volume_ml=request.volume_ml,
                catalysts=request.catalysts,
            )
            prediction = self.local_bridge.predict_reaction(factor_request)
            return ReagentComputationResult(
                success=True,
                provider_used="local_deterministic_fallback",
                prediction=prediction,
                fallback_used=True,
            )
        except Exception as exc:  # noqa: BLE001
            return ReagentComputationResult(
                success=False,
                provider_used="none",
                error_message=str(exc),
            )

    def _call_provider(
        self, name: str, request: ReagentComputationRequest
    ) -> ChemicalReactionPrediction | None:
        """Calls a specific AI provider and parses its response."""
        if name == "omniroute":
            return self._call_omniroute(request)
        if name == "nvidia_nim":
            return self._call_nvidia_nim(request)
        if name == "google_gemini":
            return self._call_google_gemini(request)
        logger.warning("Unknown provider: %s", name)
        return None

    def _call_omniroute(
        self, request: ReagentComputationRequest
    ) -> ChemicalReactionPrediction | None:
        """Calls local Omniroute inference gateway."""
        endpoint = self.endpoints["omniroute"]
        payload = {
            "model": self.models["omniroute"],
            "messages": [
                {
                    "role": "system",
                    "content": "You are a chemistry reaction prediction engine. Respond only in JSON.",
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "reagents": request.reagents,
                            "temperature_c": request.temperature_c,
                            "pressure_atm": request.pressure_atm,
                            "volume_ml": request.volume_ml,
                            "catalysts": request.catalysts,
                            "target_compound": request.target_compound,
                            "time_dilation": request.time_dilation,
                        }
                    ),
                },
            ],
            "temperature": 0.1,
            "max_tokens": 512,
        }
        return self._json_post(endpoint + "/chat/completions", payload)

    def _call_nvidia_nim(
        self, request: ReagentComputationRequest
    ) -> ChemicalReactionPrediction | None:
        """Calls NVIDIA NIM inference endpoint."""
        endpoint = self.endpoints["nvidia_nim"]
        api_key = self.api_keys.get("nvidia_nim")
        if not api_key:
            logger.debug("NVIDIA NIM API key not configured")
            return None

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.models["nvidia_nim"],
            "messages": [
                {
                    "role": "system",
                    "content": "You are a chemistry reaction prediction engine. Respond only in JSON.",
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "reagents": request.reagents,
                            "temperature_c": request.temperature_c,
                            "pressure_atm": request.pressure_atm,
                            "volume_ml": request.volume_ml,
                            "catalysts": request.catalysts,
                        }
                    ),
                },
            ],
            "temperature": 0.1,
            "max_tokens": 512,
        }
        return self._json_post_with_headers(endpoint + "/chat/completions", payload, headers)

    def _call_google_gemini(
        self, request: ReagentComputationRequest
    ) -> ChemicalReactionPrediction | None:
        """Calls Google Gemini API for chemistry reasoning."""
        api_key = (
            self.api_keys.get("google_gemini")
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
        )
        if not api_key:
            logger.debug("Google Gemini API key not configured")
            return None

        model = self.models.get("google_gemini", "gemini-2.5-pro")
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        prompt = (
            f"Predict the chemical reaction for reagents: {', '.join(request.reagents)}. "
            f"Temperature: {request.temperature_c}°C, Pressure: {request.pressure_atm} atm, "
            f"Volume: {request.volume_ml} mL, Catalysts: {', '.join(request.catalysts) or 'none'}. "
            "Respond with JSON only: reaction_name, balanced_equation, products (dict id:mol), "
            "enthalpy_kj_mol, activation_energy_kj_mol, rate_constant_k, target_color_rgb [r,g,b], "
            "produces_gas, precipitate_formed, emission_glow, safety_warnings."
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 512,
                "topP": 0.9,
                "topK": 40,
            },
        }
        return self._json_post(endpoint, payload)

    def _json_post(self, url: str, payload: dict[str, Any]) -> ChemicalReactionPrediction | None:
        """Sends JSON POST and parses reaction prediction."""
        return self._json_post_with_headers(url, payload, {"Content-Type": "application/json"})

    def _json_post_with_headers(
        self, url: str, payload: dict[str, Any], headers: dict[str, str]
    ) -> ChemicalReactionPrediction | None:
        """Sends JSON POST with custom headers."""
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                body = resp.read().decode("utf-8")
                result = json.loads(body)
                return self._parse_provider_response(result)
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 429):
                logger.info("Provider quota exhausted: %s", url)
            return None
        except Exception as exc:  # noqa: BLE001
            logger.debug("Provider call failed: %s", exc)
            return None

    def _parse_provider_response(self, raw: dict[str, Any]) -> ChemicalReactionPrediction | None:
        """Parses a provider JSON response into ChemicalReactionPrediction."""
        try:
            # Handle different response formats (OpenAI-compatible vs Gemini)
            content = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                parts = raw.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
                content = parts[0].get("text", "") if parts else ""

            if not content:
                return None

            # Clean markdown code fences if present (e.g. ```json ... ```)
            cleaned = content.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                cleaned = re.sub(r"\s*```$", "", cleaned)

            data = json.loads(cleaned)
            return ChemicalReactionPrediction(
                reaction_name=data.get("reaction_name", "Unknown Reaction"),
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
        except (KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError) as exc:
            logger.debug("Failed to parse provider response: %s", exc)
            return None

    @staticmethod
    def _is_quota_error(exc: Exception) -> bool:
        """Determines if an exception indicates quota exhaustion."""
        msg = str(exc).lower()
        return "429" in msg or "quota" in msg or "rate limit" in msg or "billing" in msg

    def get_provider_status(self) -> dict[str, dict[str, Any]]:
        """Returns status of all registered AI providers."""
        return {
            name: {
                "priority": p.priority,
                "available": p.available,
                "quota_exhausted": p.quota_exhausted,
                "failure_count": p.failure_count,
                "last_error": p.last_error,
                "cooldown_until": p.cooldown_until,
            }
            for name, p in self.providers.items()
        }

    def step_with_time_dilation(
        self,
        mixture: Any,
        dt_s: float,
        time_dilation: float = 1.0,
    ) -> tuple[Any, ChemicalReactionPrediction]:
        """
        Advances a liquid mixture forward in time using reaction kinetics
        from the best available AI provider, with local fallback.
        """
        from chemlab.ai.omniroute_bridge import ReactionFactorRequest

        effective_dt = dt_s * max(0.1, min(100.0, time_dilation))
        req = ReactionFactorRequest(
            reagents=list(getattr(mixture, "reagent_moles", {}).keys()),
            temperature_c=getattr(mixture, "temperature_c", 22.0),
            volume_ml=getattr(mixture, "volume_ml", 100.0),
        )
        result = self.compute_reaction(
            ReagentComputationRequest(
                reagents=list(getattr(mixture, "reagent_moles", {}).keys()),
                temperature_c=getattr(mixture, "temperature_c", 22.0),
                volume_ml=getattr(mixture, "volume_ml", 100.0),
                time_dilation=time_dilation,
            )
        )

        prediction = result.prediction or self.local_bridge.predict_reaction(req)

        # Apply kinetics to mixture
        res = mixture.clone() if hasattr(mixture, "clone") else mixture
        if prediction.rate_constant_k > 0.0:
            gas_const = 8.314
            t_kelvin = max(200.0, getattr(res, "temperature_c", 22.0) + 273.15)
            t_ref = 298.15
            ea_j = prediction.activation_energy_kj_mol * 1000.0
            temp_factor = math.exp(-ea_j / gas_const * (1.0 / t_kelvin - 1.0 / t_ref))
            k_actual = prediction.rate_constant_k * temp_factor
            extent = min(1.0, k_actual * effective_dt)

            reagent_moles = getattr(res, "reagent_moles", {})
            for prod, moles in prediction.products.items():
                reagent_moles[prod] = reagent_moles.get(prod, 0.0) + moles * extent

            delta_t = -prediction.enthalpy_kj_mol * extent * 0.15
            res.temperature_c = round(getattr(res, "temperature_c", 22.0) + delta_t, 3)

        return res, prediction


# Global default instance for convenience

_default_computer: AIReagentComputer | None = None


def get_reagent_computer() -> AIReagentComputer:
    """Returns the global AI reagent computer instance."""
    global _default_computer
    if _default_computer is None:
        _default_computer = AIReagentComputer()
    return _default_computer
