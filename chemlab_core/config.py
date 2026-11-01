"""
Centralized Configuration and Quality Parameters.
Eliminates hardcoded magic numbers across Computer Vision, IPC, and Scene Control.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated


@dataclass(frozen=True)
class VisionConfig:
    """Configuration for Computer Vision Tracking and Landmark Synthesis."""

    target_fps: Annotated[int, "Target frames per second for video processing"] = 60
    synthetic_noise_std: Annotated[float, "Standard deviation for synthetic jitter"] = 0.002
    min_detection_confidence: Annotated[float, "Minimum landmark detection confidence"] = 0.75
    min_tracking_confidence: Annotated[float, "Minimum landmark tracking confidence"] = 0.70
    pinch_threshold_distance: Annotated[
        float, "Euclidean distance threshold between index and thumb for pinch"
    ] = 0.055
    grab_threshold_distance: Annotated[
        float, "Average finger tip to palm distance threshold for grab"
    ] = 0.12
    max_history_frames: Annotated[int, "Frames kept in memory for gesture velocity"] = 15


@dataclass(frozen=True)
class IPCConfig:
    """Configuration for IPC Network Transport between CV engine and Blender."""

    host: Annotated[str, "Localhost bind address"] = "127.0.0.1"
    port: Annotated[int, "TCP socket port for Blender MCP bridge"] = 8765
    fallback_port: Annotated[int, "Secondary port if primary is occupied"] = 9876
    buffer_size: Annotated[int, "Socket receive buffer size in bytes"] = 8192
    connect_timeout_seconds: Annotated[float, "Socket connection timeout"] = 5.0
    command_timeout_seconds: Annotated[float, "Command execution timeout"] = 10.0
    max_reconnect_attempts: Annotated[int, "Maximum connection retries"] = 3
    reconnect_backoff_seconds: Annotated[float, "Delay between reconnection attempts"] = 0.5


@dataclass(frozen=True)
class SceneConfig:
    """Configuration for Blender 3D Scene Controller and Chemical Rendering."""

    default_project_path: Annotated[Path, "Default .blend project file path"] = field(
        default_factory=lambda: Path(r"C:\Users\Win11 Pro\Desktop\chemlab\chemlab.blend")
    )
    viewport_timer_interval: Annotated[float, "Blender main thread timer interval in seconds"] = (
        0.05
    )
    material_preview_enabled: Annotated[bool, "Whether to force material preview shading"] = True
    workbench_fps_cap: Annotated[int, "Target render cap for Iris Xe energy saving"] = 60


@dataclass(frozen=True)
class ChemLabSettings:
    """Master application configuration container."""

    vision: VisionConfig = field(default_factory=VisionConfig)
    ipc: IPCConfig = field(default_factory=IPCConfig)
    scene: SceneConfig = field(default_factory=SceneConfig)


# Default global settings instance
SETTINGS = ChemLabSettings()
