from datetime import datetime, UTC
"""
ChemLab Experiment Book & Recipe Export — Free Simulation Mode
Saves, loads, exports custom chemical reaction setups (JSON format)
and manages in-game laboratory snapshot photos with camera and visual state metadata.
"""

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from simulation.consequence import ConsequenceType, VesselEnvironment



@dataclass
class ReagentAddition:
    reagent_id: str
    volume_ml: float | None = None
    mass_g: float | None = None
    concentration_molar: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "reagent_id": self.reagent_id,
            "volume_ml": self.volume_ml,
            "mass_g": self.mass_g,
            "concentration_molar": self.concentration_molar,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReagentAddition":
        return cls(
            reagent_id=data["reagent_id"],
            volume_ml=data.get("volume_ml"),
            mass_g=data.get("mass_g"),
            concentration_molar=data.get("concentration_molar"),
        )


@dataclass
class SnapshotPhoto:
    id: str
    recipe_id: str
    title: str
    timestamp: str
    camera_angle: dict[str, float]  # yaw, pitch, fov, position
    resolution: tuple[int, int]
    visual_state: dict[str, Any]  # liquid_color_rgba, turbidity, temperature_c, bubble_density

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "recipe_id": self.recipe_id,
            "title": self.title,
            "timestamp": self.timestamp,
            "camera_angle": self.camera_angle,
            "resolution": list(self.resolution),
            "visual_state": self.visual_state,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SnapshotPhoto":
        return cls(
            id=data["id"],
            recipe_id=data["recipe_id"],
            title=data["title"],
            timestamp=data["timestamp"],
            camera_angle=data["camera_angle"],
            resolution=tuple(data["resolution"]),  # type: ignore
            visual_state=data["visual_state"],
        )


@dataclass
class Recipe:
    id: str
    title: str
    author: str
    description: str
    apparatus: list[str]
    environment: VesselEnvironment
    reagents: list[ReagentAddition]
    expected_consequence: ConsequenceType
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    notes: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "description": self.description,
            "apparatus": self.apparatus,
            "environment": self.environment.value,
            "reagents": [r.to_dict() for r in self.reagents],
            "expected_consequence": self.expected_consequence.value,
            "timestamp": self.timestamp,
            "notes": self.notes,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Recipe":
        return cls(
            id=data["id"],
            title=data["title"],
            author=data["author"],
            description=data["description"],
            apparatus=data["apparatus"],
            environment=VesselEnvironment(data["environment"]),
            reagents=[ReagentAddition.from_dict(r) for r in data["reagents"]],
            expected_consequence=ConsequenceType(data["expected_consequence"]),
            timestamp=data.get("timestamp", datetime.now(UTC).isoformat()),
            notes=data.get("notes", ""),
            tags=data.get("tags", []),
        )


class ExperimentBook:
    """Manages custom recipes, experimental notes, and in-game photo snapshots."""

    def __init__(self):
        self._recipes: dict[str, Recipe] = {}
        self._snapshots: dict[str, SnapshotPhoto] = {}

    def save_recipe(self, recipe: Recipe) -> None:
        self._recipes[recipe.id] = recipe

    def get_recipe(self, recipe_id: str) -> Recipe | None:
        return self._recipes.get(recipe_id)

    def list_recipes(self) -> list[Recipe]:
        return list(self._recipes.values())

    def export_recipe_to_file(self, recipe_id: str, filepath: str) -> None:
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise KeyError(f"Recipe with id '{recipe_id}' not found.")
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(recipe.to_dict(), f, indent=2, ensure_ascii=False)

    def import_recipe_from_file(self, filepath: str) -> Recipe:
        path = Path(filepath)
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        recipe = Recipe.from_dict(data)
        self.save_recipe(recipe)
        return recipe

    def take_snapshot(
        self,
        recipe_id: str,
        title: str,
        camera_angle: dict[str, float],
        resolution: tuple[int, int] = (1920, 1080),
        visual_state: dict[str, Any] | None = None,
    ) -> SnapshotPhoto:
        snap_id = f"snap_{uuid.uuid4().hex[:8]}"
        photo = SnapshotPhoto(
            id=snap_id,
            recipe_id=recipe_id,
            title=title,
            timestamp=datetime.now(UTC).isoformat(),
            camera_angle=camera_angle,
            resolution=resolution,
            visual_state=visual_state or {},
        )
        self._snapshots[snap_id] = photo
        return photo

    def get_snapshots_for_recipe(self, recipe_id: str) -> list[SnapshotPhoto]:
        return [s for s in self._snapshots.values() if s.recipe_id == recipe_id]
