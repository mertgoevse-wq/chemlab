"""
ChemLab Free Simulation Engine
Unifies Reagent Catalog, Consequence Engine, Time Controller, and Experiment Book.
Serves as the central gameplay and simulation architect interface.
"""

import uuid
from dataclasses import dataclass

from simulation.catalog import ReagentCatalog
from simulation.consequence import (
    ConsequenceEngine,
    ConsequenceResult,
    ConsequenceType,
    VesselEnvironment,
)
from simulation.experiment_book import (
    ExperimentBook,
    ReagentAddition,
    Recipe,
    SnapshotPhoto,
)
from simulation.time_controller import TimeController


@dataclass
class ActiveExperimentState:
    id: str
    environment: VesselEnvironment
    apparatus: list[str]
    reagent_ids: list[str]
    quantities: list[float]
    consequence_result: ConsequenceResult | None = None
    current_temperature_c: float = 20.0
    liquid_color_rgba: tuple[float, float, float, float] = (0.95, 0.98, 1.0, 0.92)
    turbidity: float = 0.0
    bubble_rate: float = 0.0
    fume_density: float = 0.0


class FreeSimulationEngine:
    """Central engine orchestrating free-form experimentation in ChemLab."""

    def __init__(self):
        self.catalog = ReagentCatalog()
        self.consequence_engine = ConsequenceEngine()
        self.time_controller = TimeController()
        self.experiment_book = ExperimentBook()
        self.active_state: ActiveExperimentState | None = None

    def run_experiment(
        self,
        vessel_env: VesselEnvironment,
        reagent_ids: list[str],
        quantities: list[float] | None = None,
        apparatus: list[str] | None = None,
        initial_temp_c: float = 20.0,
    ) -> ConsequenceResult:
        if quantities is None:
            quantities = [50.0] * len(reagent_ids)
        if apparatus is None:
            apparatus = ["erlenmeyer_flask_250ml"]

        result = self.consequence_engine.mix(
            vessel_env=vessel_env,
            reagent_ids=reagent_ids,
            masses_or_volumes=quantities,
            initial_temp_c=initial_temp_c,
        )

        turbidity = 0.85 if result.precipitate_name else 0.05
        bubble_rate = 1.0 if result.gas_released_formula else 0.0
        fume_density = 0.9 if result.consequence == ConsequenceType.EXPLOSION else 0.0

        self.active_state = ActiveExperimentState(
            id=f"exp_{uuid.uuid4().hex[:8]}",
            environment=vessel_env,
            apparatus=apparatus,
            reagent_ids=reagent_ids,
            quantities=quantities,
            consequence_result=result,
            current_temperature_c=result.final_temp_c,
            liquid_color_rgba=result.mixture_color_rgba,
            turbidity=turbidity,
            bubble_rate=bubble_rate,
            fume_density=fume_density,
        )

        return result

    def capture_snapshot(
        self,
        title: str,
        camera_angle: dict[str, float] | None = None,
        resolution: tuple[int, int] = (1920, 1080),
    ) -> SnapshotPhoto:
        recipe_id = self.active_state.id if self.active_state else "unbound_session"
        angle = camera_angle or {"yaw": 30.0, "pitch": -12.0, "fov": 45.0}

        visual_state = {}
        if self.active_state:
            visual_state = {
                "liquid_color_rgba": list(self.active_state.liquid_color_rgba),
                "turbidity": self.active_state.turbidity,
                "temperature_c": self.active_state.current_temperature_c,
                "bubble_density": self.active_state.bubble_rate,
                "consequence": (
                    self.active_state.consequence_result.consequence.value
                    if self.active_state.consequence_result
                    else "none"
                ),
            }

        return self.experiment_book.take_snapshot(
            recipe_id=recipe_id,
            title=title,
            camera_angle=angle,
            resolution=resolution,
            visual_state=visual_state,
        )

    def export_current_setup_as_recipe(
        self,
        title: str,
        filepath: str,
        author: str = "Lead Chemist",
        description: str = "Free simulation experimental setup",
    ) -> Recipe:
        if not self.active_state:
            raise RuntimeError("No active experiment to export.")

        reagent_additions = [
            ReagentAddition(reagent_id=r_id, volume_ml=q)
            for r_id, q in zip(
                self.active_state.reagent_ids, self.active_state.quantities, strict=False
            )
        ]

        expected = (
            self.active_state.consequence_result.consequence
            if self.active_state.consequence_result
            else ConsequenceType.NO_VISIBLE_REACTION
        )

        recipe = Recipe(
            id=f"rec_{uuid.uuid4().hex[:8]}",
            title=title,
            author=author,
            description=description,
            apparatus=self.active_state.apparatus,
            environment=self.active_state.environment,
            reagents=reagent_additions,
            expected_consequence=expected,
            notes=(
                self.active_state.consequence_result.details
                if self.active_state.consequence_result
                else ""
            ),
        )

        self.experiment_book.save_recipe(recipe)
        self.experiment_book.export_recipe_to_file(recipe.id, filepath)
        return recipe
