"""
Tests for Free Simulation Mode in ChemLab:
1. Complete chemical reagent catalog (>100 reagents with GHS pictograms)
2. Unrestricted experimentation and consequence matrices (endothermic, exothermic, precipitate, gas, explosion containment)
3. Time control (pause, 0.5x, 1.0x, up to 50x time-lapse)
4. Experiment Book & Export (recipe JSON format, in-game snapshot photos)
"""

import json

import pytest

from simulation.catalog import GHSPictogram, ReagentCatalog, ReagentCategory
from simulation.consequence import (
    ConsequenceEngine,
    ConsequenceType,
    ReactionEffect,
    VesselEnvironment,
)
from simulation.experiment_book import (
    ExperimentBook,
    ReagentAddition,
    Recipe,
)
from simulation.free_sim_engine import FreeSimulationEngine
from simulation.time_controller import TimeController, TimeScale


class TestReagentCatalog:
    def test_catalog_contains_over_100_reagents(self):
        catalog = ReagentCatalog()
        assert len(catalog.get_all()) >= 100

    def test_all_required_categories_present(self):
        catalog = ReagentCatalog()
        categories = catalog.get_categories()
        assert ReagentCategory.ACID in categories
        assert ReagentCategory.BASE in categories
        assert ReagentCategory.TRANSITION_METAL_SALT in categories
        assert ReagentCategory.INDICATOR in categories
        assert ReagentCategory.OXIDIZER in categories
        assert ReagentCategory.ORGANIC_SOLVENT in categories

    def test_all_reagents_have_valid_ghs_data(self):
        catalog = ReagentCatalog()
        valid_ghs_codes = {item.value for item in GHSPictogram}
        for reagent in catalog.get_all():
            assert reagent.id
            assert reagent.name
            assert reagent.formula
            assert reagent.category in ReagentCategory
            assert reagent.molar_mass > 0
            assert reagent.density > 0
            assert reagent.default_color_rgba is not None
            assert len(reagent.default_color_rgba) == 4
            for pic in reagent.ghs_pictograms:
                assert pic.value in valid_ghs_codes

    def test_search_and_filter(self):
        catalog = ReagentCatalog()
        acids = catalog.filter_by_category(ReagentCategory.ACID)
        assert len(acids) >= 12
        hcl = catalog.get_by_id("hydrochloric_acid_37")
        assert hcl is not None
        assert "HCl" in hcl.formula
        results = catalog.search("copper")
        assert len(results) >= 2


class TestConsequenceEngine:
    def test_exothermic_neutralization(self):
        engine = ConsequenceEngine()
        result = engine.mix(
            vessel_env=VesselEnvironment.MAIN_BENCH,
            reagent_ids=["hydrochloric_acid_37", "sodium_hydroxide_sol"],
            volumes_ml=[50.0, 50.0],
            initial_temp_c=22.0,
        )
        assert result.consequence == ConsequenceType.EXOTHERMIC_NEUTRALIZATION
        assert result.final_temp_c > 22.0
        assert result.temp_delta_c > 10.0
        assert ReactionEffect.HEAT_RELEASE in result.effects

    def test_endothermic_cooling(self):
        engine = ConsequenceEngine()
        result = engine.mix(
            vessel_env=VesselEnvironment.MAIN_BENCH,
            reagent_ids=["ammonium_nitrate", "water_deionized"],
            masses_or_volumes=[15.0, 50.0],
            initial_temp_c=22.0,
        )
        assert result.consequence == ConsequenceType.ENDOTHERMIC_DISSOLUTION
        assert result.final_temp_c < 22.0
        assert result.temp_delta_c < -5.0
        assert ReactionEffect.COOLING in result.effects

    def test_precipitate_formation(self):
        engine = ConsequenceEngine()
        result = engine.mix(
            vessel_env=VesselEnvironment.MAIN_BENCH,
            reagent_ids=["silver_nitrate_sol", "sodium_chloride_sol"],
            volumes_ml=[25.0, 25.0],
            initial_temp_c=20.0,
        )
        assert result.consequence == ConsequenceType.PRECIPITATION
        assert result.precipitate_name == "Silver Chloride (AgCl)"
        assert result.precipitate_color == (0.95, 0.95, 0.95, 1.0)
        assert ReactionEffect.PRECIPITATE in result.effects

    def test_gas_release(self):
        engine = ConsequenceEngine()
        result = engine.mix(
            vessel_env=VesselEnvironment.MAIN_BENCH,
            reagent_ids=["hydrochloric_acid_37", "sodium_bicarbonate"],
            masses_or_volumes=[40.0, 10.0],
            initial_temp_c=20.0,
        )
        assert result.consequence == ConsequenceType.GAS_EVOLUTION
        assert result.gas_released_formula == "CO2"
        assert ReactionEffect.EFFERVESCENCE in result.effects

    def test_fume_hood_explosion_containment(self):
        engine = ConsequenceEngine()
        # High energetic runaway: potassium permanganate + concentrated sulfuric acid (forms Mn2O7)
        hood_result = engine.mix(
            vessel_env=VesselEnvironment.FUME_HOOD,
            reagent_ids=["potassium_permanganate", "sulfuric_acid_conc"],
            masses_or_volumes=[10.0, 20.0],
            initial_temp_c=25.0,
        )
        assert hood_result.consequence == ConsequenceType.EXPLOSION
        assert hood_result.is_contained is True
        assert (
            "Fume hood blast shield contained explosive thermal decomposition"
            in hood_result.safety_report
        )

        # Same reaction on open bench: uncontained
        bench_result = engine.mix(
            vessel_env=VesselEnvironment.MAIN_BENCH,
            reagent_ids=["potassium_permanganate", "sulfuric_acid_conc"],
            masses_or_volumes=[10.0, 20.0],
            initial_temp_c=25.0,
        )
        assert bench_result.consequence == ConsequenceType.EXPLOSION
        assert bench_result.is_contained is False
        assert "Uncontained blast" in bench_result.safety_report

    def test_oscillating_reaction_briggs_rauscher(self):
        engine = ConsequenceEngine()
        result = engine.mix(
            vessel_env=VesselEnvironment.MAIN_BENCH,
            reagent_ids=[
                "hydrogen_peroxide_30",
                "potassium_iodate",
                "malonic_acid",
                "manganese_sulfate",
                "starch_indicator",
            ],
            masses_or_volumes=[20.0, 20.0, 20.0, 5.0, 5.0],
            initial_temp_c=21.0,
        )
        assert result.consequence == ConsequenceType.OSCILLATING_REACTION
        assert result.oscillation_cycle is not None
        assert len(result.oscillation_cycle.color_sequence) == 3


class TestTimeController:
    def test_time_scales_and_pause(self):
        tc = TimeController()
        assert tc.current_scale == TimeScale.NORMAL
        assert tc.scale_factor == 1.0

        tc.set_scale(TimeScale.PAUSE)
        assert tc.is_paused is True
        tc.update(dt=1.0)
        assert tc.elapsed_simulation_seconds == 0.0

        tc.set_scale(TimeScale.SLOW_MOTION)
        assert tc.scale_factor == 0.5
        tc.update(dt=2.0)
        assert tc.elapsed_simulation_seconds == 1.0

        tc.set_scale(TimeScale.TIME_LAPSE_50X)
        assert tc.scale_factor == 50.0
        tc.update(dt=2.0)
        assert tc.elapsed_simulation_seconds == 101.0

    def test_step_frame_while_paused(self):
        tc = TimeController()
        tc.set_scale(TimeScale.PAUSE)
        tc.step_frame(fixed_dt=0.016)
        assert tc.elapsed_simulation_seconds == pytest.approx(0.016)
        assert tc.is_paused is True


class TestExperimentBookAndExport:
    def test_recipe_serialization(self, tmp_path):
        book = ExperimentBook()
        recipe = Recipe(
            id="rec_001",
            title="Golden Rain Lead Iodide Precipitation",
            author="Lab Architect",
            description="Synthesis of gleaming lead iodide crystals through hot mixing and slow precipitation",
            apparatus=["erlenmeyer_flask_250ml", "bunsen_burner", "retort_stand"],
            environment=VesselEnvironment.MAIN_BENCH,
            reagents=[
                ReagentAddition(
                    reagent_id="lead_nitrate_sol", volume_ml=50.0, concentration_molar=0.1
                ),
                ReagentAddition(
                    reagent_id="potassium_iodide_sol", volume_ml=50.0, concentration_molar=0.2
                ),
            ],
            expected_consequence=ConsequenceType.PRECIPITATION,
        )
        book.save_recipe(recipe)
        export_file = tmp_path / "recipe_export.json"
        book.export_recipe_to_file(recipe.id, str(export_file))

        assert export_file.exists()
        with export_file.open(encoding="utf-8") as f:
            data = json.load(f)
        assert data["title"] == "Golden Rain Lead Iodide Precipitation"
        assert len(data["reagents"]) == 2

        # Round-trip load
        loaded = book.import_recipe_from_file(str(export_file))
        assert loaded.id == recipe.id
        assert loaded.reagents[0].reagent_id == "lead_nitrate_sol"

    def test_snapshot_photo_capture(self):
        book = ExperimentBook()
        photo = book.take_snapshot(
            recipe_id="rec_001",
            title="Peak Iodine Clock Oscillation",
            camera_angle={"yaw": 45.0, "pitch": -15.0, "fov": 50.0},
            resolution=(1920, 1080),
            visual_state={
                "liquid_color_rgba": [0.08, 0.05, 0.45, 0.95],
                "turbidity": 0.12,
                "temperature_c": 23.4,
                "bubble_density": 0.05,
            },
        )
        assert photo.id.startswith("snap_")
        assert photo.resolution == (1920, 1080)
        assert photo.visual_state["temperature_c"] == 23.4
        assert len(book.get_snapshots_for_recipe("rec_001")) == 1


class TestFreeSimulationEngine:
    def test_integrated_workflow(self, tmp_path):
        engine = FreeSimulationEngine()
        assert len(engine.catalog.get_all()) >= 100

        # Set up a reaction in the fume hood
        reaction = engine.run_experiment(
            vessel_env=VesselEnvironment.FUME_HOOD,
            reagent_ids=["hydrochloric_acid_37", "sodium_hydroxide_sol"],
            quantities=[50.0, 50.0],
            apparatus=["beaker_250ml", "magnetic_stirrer"],
        )
        assert reaction.consequence == ConsequenceType.EXOTHERMIC_NEUTRALIZATION

        # Change time control to slow-motion
        engine.time_controller.set_scale(TimeScale.SLOW_MOTION)
        assert engine.time_controller.scale_factor == 0.5

        # Take snapshot
        snap = engine.capture_snapshot(
            title="Neutralization Equilibrium",
            camera_angle={"pitch": -20.0, "yaw": 30.0},
        )
        assert snap is not None

        # Export recipe
        rec_path = tmp_path / "neutralization_recipe.json"
        engine.export_current_setup_as_recipe(
            title="Standard Acid-Base Neutralization",
            filepath=str(rec_path),
        )
        assert rec_path.exists()
