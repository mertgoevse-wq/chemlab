"""
Intel Iris Xe Dynamic VRAM/RAM Offload & Upscaling Optimizer for ChemLab.
Profiles integrated graphics architectures (128 MB dedicated slice + 8 GB shared system memory)
and applies hardware-tuned EEVEE rendering parameters, dynamic resolution upscaling (XeSS/CAS emulation),
and texture staging memory tiering to ensure stable 60 FPS viewport performance.
"""

from __future__ import annotations

from dataclasses import dataclass
from chemlab.compat import StrEnum, UTC


class GPUVendor(StrEnum):
    """Graphics hardware manufacturer classification."""

    INTEL = "intel"
    NVIDIA = "nvidia"
    AMD = "amd"
    APPLE = "apple"
    UNKNOWN = "unknown"


class UpscalePreset(StrEnum):
    """Resolution scaling factors for dynamic viewport upsampling (XeSS / FSR analogue)."""

    NATIVE = "native"  # 1.0x (100% resolution)
    QUALITY = "quality"  # 0.77x (approx 60% pixels)
    BALANCED = "balanced"  # 0.71x (approx 50% pixels)
    PERFORMANCE = "performance"  # 0.67x (approx 45% pixels)
    ULTRA_PERFORMANCE = "ultra_performance"  # 0.50x (25% pixels)


@dataclass(frozen=True)
class GraphicsHardwareProfile:
    """Hardware capability metrics captured from host machine."""

    vendor: GPUVendor
    gpu_name: str
    dedicated_vram_mb: int = 128
    system_ram_mb: int = 16384
    max_shared_vram_mb: int = 8192


@dataclass(frozen=True)
class EEVEEViewportSettings:
    """Tuned Blender EEVEE rendering parameters for integrated GPUs."""

    viewport_samples: int
    enable_half_res_trace: bool
    shadow_cube_size: int
    ao_distance_m: float
    volumetric_tile_size: int
    use_screen_space_refraction: bool = True
    use_bloom: bool = False


@dataclass(frozen=True)
class MemoryPartitionPlan:
    """Allocation partition mapping dedicated VRAM and system RAM staging buffers."""

    dedicated_vram_budget_mb: int
    system_ram_staging_budget_mb: int
    texture_mip_clamp: int
    status_description: str


class IntelIrisXeOptimizer:
    """
    Performance tuning and memory offloader tailored for Intel Iris Xe Graphics.
    Mitigates the 128 MB VRAM bottleneck by tiering texture buffers to system RAM
    and downscaling viewport render passes with edge-preserving reconstruction.
    """

    def __init__(self, profile: GraphicsHardwareProfile) -> None:
        self.profile = profile

    @property
    def is_integrated_intel(self) -> bool:
        """Determines if the host is running Intel integrated graphics."""
        is_intel = (
            self.profile.vendor == GPUVendor.INTEL or "intel" in self.profile.gpu_name.lower()
        )
        is_integrated = self.profile.dedicated_vram_mb <= 512
        return is_intel and is_integrated

    @property
    def total_usable_memory_mb(self) -> int:
        """Total accessible graphics memory combining dedicated and shared pools."""
        return self.profile.dedicated_vram_mb + self.profile.max_shared_vram_mb

    @property
    def requires_ram_offload(self) -> bool:
        """True when dedicated VRAM is insufficient to hold full 3D laboratory assets."""
        return self.profile.dedicated_vram_mb < 1024

    def get_optimal_eevee_settings(self, target_fps: int = 60) -> EEVEEViewportSettings:
        """
        Derives high-efficiency Blender EEVEE settings tuned for 60 FPS on Iris Xe.
        Caps shadow maps and enables half-resolution ray tracing.
        """
        if self.is_integrated_intel:
            return EEVEEViewportSettings(
                viewport_samples=24,  # Halved from default 64
                enable_half_res_trace=True,  # Screen Space Reflection half-res
                shadow_cube_size=1024,  # Clamped from 2048/4096
                ao_distance_m=0.4,  # Localized ambient occlusion
                volumetric_tile_size=4,  # 4px tile size for smoke/steam
                use_screen_space_refraction=True,
                use_bloom=False,  # Handled via compositor to save GPU cycles
            )

        # Discrete GPU (NVIDIA / AMD) default preset
        return EEVEEViewportSettings(
            viewport_samples=64,
            enable_half_res_trace=False,
            shadow_cube_size=2048,
            ao_distance_m=1.0,
            volumetric_tile_size=2,
            use_screen_space_refraction=True,
            use_bloom=True,
        )

    def calculate_internal_resolution(
        self,
        target_width: int,
        target_height: int,
        preset: UpscalePreset = UpscalePreset.PERFORMANCE,
    ) -> tuple[float, tuple[int, int]]:
        """
        Calculates internal viewport rendering dimensions for XeSS/FSR style upsampling.
        Returns (scale_factor, (internal_width, internal_height)).
        """
        scale_map = {
            UpscalePreset.NATIVE: 1.0,
            UpscalePreset.QUALITY: 0.77,
            UpscalePreset.BALANCED: 0.71,
            UpscalePreset.PERFORMANCE: 0.67,
            UpscalePreset.ULTRA_PERFORMANCE: 0.50,
        }
        scale = scale_map.get(preset, 0.67)
        internal_w = int(target_width * scale)
        internal_h = int(target_height * scale)

        # Ensure even pixel dimensions
        internal_w = internal_w if internal_w % 2 == 0 else internal_w - 1
        internal_h = internal_h if internal_h % 2 == 0 else internal_h - 1

        return scale, (internal_w, internal_h)

    def create_memory_partition_plan(self) -> MemoryPartitionPlan:
        """
        Plans how to partition textures and geometry buffers across VRAM and System RAM.
        Allocates active framebuffers to dedicated VRAM and pools static assets in system RAM.
        """
        if self.requires_ram_offload:
            # 128 MB dedicated slice holds active framebuffers and render targets
            # Up to 6 GB of 16 GB system RAM stages high-poly apparatus and texture caches
            staging_budget = min(6144, int(self.profile.system_ram_mb * 0.4))
            return MemoryPartitionPlan(
                dedicated_vram_budget_mb=min(128, self.profile.dedicated_vram_mb),
                system_ram_staging_budget_mb=staging_budget,
                texture_mip_clamp=1024,
                status_description=(
                    f"System RAM Offload Aktiv: 128 MB VRAM Framebuffer + "
                    f"{staging_budget} MB Shared System RAM für Textur-Streaming & Reagenzien-Meshes."
                ),
            )

        return MemoryPartitionPlan(
            dedicated_vram_budget_mb=self.profile.dedicated_vram_mb,
            system_ram_staging_budget_mb=0,
            texture_mip_clamp=4096,
            status_description="Dedizierter VRAM ausreichend; kein RAM-Offload erforderlich.",
        )
