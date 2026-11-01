"""
ChemLab Time Controller — Free Simulation Mode
Multi-scale temporal engine for chemical reaction dynamics:
- Pause (0.0x) for freezing transient intermediates
- 0.5x slow-motion for rapid color changes and explosive fronts
- 1.0x real-time simulation
- Up to 50x time-lapse for slow crystal growth and diffusion
"""

from enum import Enum


class TimeScale(Enum):
    PAUSE = 0.0
    SLOW_MOTION = 0.5
    NORMAL = 1.0
    TIME_LAPSE_2X = 2.0
    TIME_LAPSE_5X = 5.0
    TIME_LAPSE_10X = 10.0
    TIME_LAPSE_25X = 25.0
    TIME_LAPSE_50X = 50.0


class TimeController:
    """Manages simulation clock, sub-stepping, and playback scaling."""

    def __init__(self, initial_scale: TimeScale = TimeScale.NORMAL):
        self._current_scale: TimeScale = initial_scale
        self._scale_factor: float = initial_scale.value
        self._elapsed_simulation_seconds: float = 0.0
        self._total_real_seconds: float = 0.0
        self._tick_count: int = 0

    @property
    def current_scale(self) -> TimeScale:
        return self._current_scale

    @property
    def scale_factor(self) -> float:
        return self._scale_factor

    @property
    def is_paused(self) -> bool:
        return self._current_scale == TimeScale.PAUSE or self._scale_factor == 0.0

    @property
    def elapsed_simulation_seconds(self) -> float:
        return self._elapsed_simulation_seconds

    @property
    def total_real_seconds(self) -> float:
        return self._total_real_seconds

    @property
    def tick_count(self) -> int:
        return self._tick_count

    def set_scale(self, scale: TimeScale) -> None:
        self._current_scale = scale
        self._scale_factor = scale.value

    MAX_SCALE: float = 50.0

    def set_custom_scale(self, factor: float) -> None:
        if factor < 0.0:
            raise ValueError("Time scale cannot be negative")
        self._scale_factor = min(factor, self.MAX_SCALE)
        if self._scale_factor == TimeScale.PAUSE.value:
            self._current_scale = TimeScale.PAUSE
        elif self._scale_factor == TimeScale.SLOW_MOTION.value:
            self._current_scale = TimeScale.SLOW_MOTION
        elif self._scale_factor == TimeScale.NORMAL.value:
            self._current_scale = TimeScale.NORMAL
        elif self._scale_factor == TimeScale.TIME_LAPSE_50X.value:
            self._current_scale = TimeScale.TIME_LAPSE_50X

    def pause(self) -> None:
        self.set_scale(TimeScale.PAUSE)

    def resume(self) -> None:
        self.set_scale(TimeScale.NORMAL)

    def update(self, dt: float) -> float:
        """Advance time by real dt seconds; returns scaled simulation dt."""
        self._total_real_seconds += dt
        self._tick_count += 1
        sim_dt = dt * self._scale_factor
        self._elapsed_simulation_seconds += sim_dt
        return sim_dt

    def step_frame(self, fixed_dt: float = 0.01667) -> float:
        """Advance a single simulation frame regardless of pause status."""
        self._tick_count += 1
        self._elapsed_simulation_seconds += fixed_dt
        return fixed_dt

    def reset(self) -> None:
        self._elapsed_simulation_seconds = 0.0
        self._total_real_seconds = 0.0
        self._tick_count = 0
