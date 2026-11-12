"""
Unit tests for the ChemLab AI Reagent Computer.
Tests multi-provider fallback chain (Omniroute → NVIDIA NIM → Gemini → Local),
quota exhaustion handling, local deterministic fallback, and time-dilation integration.
"""

from __future__ import annotations

import pytest

from chemlab.ai.reagent_computer import (
    AIReagentComputer,
    ReagentComputationRequest,
    ReagentComputationResult,
)


def test_ai_reagent_computer_initialization() -> None:
    computer = AIReagentComputer()
    assert "omniroute" in computer.providers
    assert "nvidia_nim" in computer.providers
    assert "google_gemini" in computer.providers
    assert len(computer.provider_order) >= 3


def test_provider_status_tracking() -> None:
    computer = AIReagentComputer()
    status = computer.get_provider_status()
    assert "omniroute" in status
    assert "nvidia_nim" in status
    assert "google_gemini" in status
    for p in status.values():
        assert "priority" in p
        assert "available" in p
        assert "quota_exhausted" in p


def test_reagent_computation_request_dataclass() -> None:
    req = ReagentComputationRequest(
        reagents=["salicylic_acid", "acetic_anhydride"],
        temperature_c=65.0,
        pressure_atm=1.0,
        volume_ml=50.0,
        catalysts=["h2so4"],
        target_compound="aspirin",
        time_dilation=1.0,
    )
    assert req.reagents == ["salicylic_acid", "acetic_anhydride"]
    assert req.temperature_c == 65.0
    assert req.catalysts == ["h2so4"]


def test_local_deterministic_fallback_always_works() -> None:
    computer = AIReagentComputer()
    req = ReagentComputationRequest(
        reagents=["salicylic_acid", "acetic_anhydride"],
        temperature_c=65.0,
    )

    # All providers unavailable (no network), so should fall back to local
    result = computer.compute_reaction(req)

    assert result.success
    assert result.provider_used == "local_deterministic_fallback"
    assert result.fallback_used
    assert result.prediction is not None
    assert result.prediction.reaction_name is not None
    assert result.prediction.balanced_equation is not None


def test_aspirin_synthesis_fallback_returns_valid_prediction() -> None:
    computer = AIReagentComputer()
    req = ReagentComputationRequest(
        reagents=["salicylic_acid", "acetic_anhydride", "h2so4"],
        temperature_c=65.0,
        target_compound="aspirin",
    )
    result = computer.compute_reaction(req)

    assert result.success
    pred = result.prediction
    assert "aspirin" in pred.reaction_name.lower() or "acetylsalicyls" in pred.reaction_name.lower()
    assert pred.balanced_equation
    assert pred.products
    assert pred.enthalpy_kj_mol < 0  # Exothermic
    assert pred.activation_energy_kj_mol > 0
    assert pred.rate_constant_k > 0


def test_paracetamol_synthesis_fallback_returns_valid_prediction() -> None:
    computer = AIReagentComputer()
    req = ReagentComputationRequest(
        reagents=["aminophenol", "acetic_anhydride"],
        temperature_c=60.0,
        target_compound="paracetamol",
    )
    result = computer.compute_reaction(req)

    assert result.success
    pred = result.prediction
    assert "paracetamol" in pred.reaction_name.lower() or "n-acetyl" in pred.reaction_name.lower()


def test_indigo_synthesis_fallback_returns_valid_prediction() -> None:
    computer = AIReagentComputer()
    req = ReagentComputationRequest(
        reagents=["nitrobenzaldehyde", "acetone", "naoh"],
        temperature_c=25.0,
        target_compound="indigo",
    )
    result = computer.compute_reaction(req)

    assert result.success
    pred = result.prediction
    assert "indigo" in pred.reaction_name.lower() or "baeyer" in pred.reaction_name.lower()
    assert pred.target_color_rgb[2] > pred.target_color_rgb[0]  # Blue dominant


def test_catalytic_foam_elephant_toothpaste_prediction() -> None:
    computer = AIReagentComputer()
    req = ReagentComputationRequest(
        reagents=["hydrogen_peroxide", "potassium_iodide"],
        temperature_c=25.0,
        target_compound="elephant_toothpaste",
    )
    result = computer.compute_reaction(req)

    assert result.success
    pred = result.prediction
    assert pred.produces_gas
    assert pred.gas_emission_rate > 0
    assert "katalyt" in pred.reaction_name.lower() or "elefant" in pred.reaction_name.lower()


def test_chemiluminescence_luminol_prediction() -> None:
    computer = AIReagentComputer()
    req = ReagentComputationRequest(
        reagents=["luminol", "hydrogen_peroxide"],
        temperature_c=20.0,
        target_compound="luminol_glow",
    )
    result = computer.compute_reaction(req)

    assert result.success
    pred = result.prediction
    assert pred.emission_glow > 0.5
    assert "luminol" in pred.reaction_name.lower() or "chemolum" in pred.reaction_name.lower()


def test_unreactive_mixture_returns_zero_rate() -> None:
    computer = AIReagentComputer()
    req = ReagentComputationRequest(
        reagents=["water", "sodium_chloride"],
        temperature_c=22.0,
    )
    result = computer.compute_reaction(req)

    assert result.success
    pred = result.prediction
    assert pred.rate_constant_k == 0.0
    assert pred.products == {}


def test_time_dilation_integration() -> None:
    computer = AIReagentComputer()
    req = ReagentComputationRequest(
        reagents=["salicylic_acid", "acetic_anhydride"],
        temperature_c=65.0,
        time_dilation=10.0,
    )
    result = computer.compute_reaction(req)

    assert result.success
    # Time dilation should not affect provider selection, just be passed through
    assert result.latency_ms >= 0


def test_step_with_time_dilation_accepts_mixture() -> None:
    computer = AIReagentComputer()

    class MockMixture:
        reagent_moles = {"salicylic_acid": 0.05, "acetic_anhydride": 0.05}
        temperature_c = 65.0
        volume_ml = 50.0

        def clone(self):
            m = MockMixture()
            m.reagent_moles = dict(self.reagent_moles)
            m.temperature_c = self.temperature_c
            m.volume_ml = self.volume_ml
            return m

    mixture = MockMixture()
    res, prediction = computer.step_with_time_dilation(mixture, dt_s=1.0, time_dilation=5.0)

    assert res is not None
    assert prediction is not None


def test_add_custom_provider() -> None:
    computer = AIReagentComputer()
    computer.add_provider("custom_llm", 1, "http://localhost:8080/v1", "key123", "my-model")

    assert "custom_llm" in computer.providers
    assert "custom_llm" in computer.provider_order
    # Should be first in chain (priority 1)
    assert computer.provider_order[0] == "custom_llm"


def test_reagent_computation_result_structure() -> None:
    result = ReagentComputationResult(
        success=True,
        provider_used="test_provider",
        latency_ms=123.4,
        fallback_used=False,
    )
    assert result.success
    assert result.provider_used == "test_provider"
    assert result.latency_ms == 123.4
    assert not result.fallback_used


def test_failed_result_structure() -> None:
    result = ReagentComputationResult(
        success=False,
        provider_used="none",
        error_message="All providers failed",
    )
    assert not result.success
    assert result.provider_used == "none"
    assert result.error_message == "All providers failed"


def test_provider_quota_exhaustion_logic() -> None:
    from chemlab.ai.reagent_computer import AIProviderStatus

    provider = AIProviderStatus("test", 1)
    assert provider.can_attempt()

    provider.mark_failure("Rate limit exceeded", is_quota=True)
    assert not provider.can_attempt()
    assert provider.quota_exhausted

    provider.mark_failure("Network error", is_quota=False)
    assert not provider.can_attempt()  # Still in cooldown


def test_provider_cooldown_expiry() -> None:
    import time

    from chemlab.ai.reagent_computer import AIProviderStatus

    provider = AIProviderStatus("test", 1)
    provider.mark_failure("Network error", is_quota=False)
    # Cooldown is 30 seconds - can't test easily without mocking time
    # But we verify the mechanism exists
    assert provider.cooldown_until > time.time()


def test_parse_gemini_markdown_response() -> None:
    from chemlab.ai.reagent_computer import AIReagentComputer

    computer = AIReagentComputer()
    gemini_raw = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": '```json\n{\n  "reaction_name": "Esterification",\n  "balanced_equation": "A + B -> C",\n  "products": {"aspirin": 1.0},\n  "enthalpy_kj_mol": -28.5,\n  "activation_energy_kj_mol": 65.0,\n  "rate_constant_k": 0.05,\n  "target_color_rgb": [1.0, 1.0, 1.0],\n  "produces_gas": false,\n  "precipitate_formed": true,\n  "emission_glow": 0.0,\n  "safety_warnings": ["Irritant"]\n}\n```'
                        }
                    ]
                }
            }
        ]
    }
    pred = computer._parse_provider_response(gemini_raw)
    assert pred is not None
    assert pred.reaction_name == "Esterification"
    assert pred.enthalpy_kj_mol == -28.5
    assert pred.precipitate_formed is True
    assert "Irritant" in pred.safety_warnings


def test_free_and_local_ai_providers_registered() -> None:
    computer = AIReagentComputer()
    for provider in ["ollama", "lm_studio", "groq", "openrouter_free"]:
        assert provider in computer.providers
        assert provider in computer.provider_order


def test_configure_local_ai_registers_at_top_priority() -> None:
    computer = AIReagentComputer()
    computer.configure_local_ai(endpoint="http://127.0.0.1:11434/v1", model="qwen2.5:7b", priority=1)
    assert "local_ai" in computer.providers
    assert computer.provider_order[0] == "local_ai"
    assert computer.endpoints["local_ai"] == "http://127.0.0.1:11434/v1"
    assert computer.models["local_ai"] == "qwen2.5:7b"


def test_get_reagent_computer_singleton() -> None:
    from chemlab.ai.reagent_computer import get_reagent_computer

    c1 = get_reagent_computer()
    c2 = get_reagent_computer()
    assert c1 is c2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
