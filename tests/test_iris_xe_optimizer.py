"""
Unit tests for the Intel Iris Xe Dynamic VRAM/RAM Offload & Upscaling Optimizer.
Tests GPU hardware profiling, shared memory tiering (128 MB dedicated to 16 GB system RAM),
dynamic resolution scaling (XeSS/CAS upscaler emulation), and EEVEE preset optimization.
"""

from __future__ import annotations

import pytest

from chemlab.graphics.iris_xe_optimizer import (
    GPUVendor,
    GraphicsHardwareProfile,
    IntelIrisXeOptimizer,
    UpscalePreset,
)


def test_hardware_profiling_detects_intel_integrated_architecture() -> None:
    profile = GraphicsHardwareProfile(
        vendor=GPUVendor.INTEL,
        gpu_name="Intel(R) Iris(R) Xe Graphics",
        dedicated_vram_mb=128,
        system_ram_mb=16384,
        max_shared_vram_mb=8192,
    )
    optimizer = IntelIrisXeOptimizer(profile=profile)

    assert optimizer.is_integrated_intel
    assert optimizer.total_usable_memory_mb >= 8000
    assert optimizer.requires_ram_offload


def test_apply_performance_tier_configures_eevee_settings() -> None:
    profile = GraphicsHardwareProfile(
        vendor=GPUVendor.INTEL,
        gpu_name="Intel Iris Xe",
        dedicated_vram_mb=128,
        system_ram_mb=16384,
        max_shared_vram_mb=8192,
    )
    optimizer = IntelIrisXeOptimizer(profile=profile)
    settings = optimizer.get_optimal_eevee_settings(target_fps=60)

    assert settings.viewport_samples <= 24
    assert settings.enable_half_res_trace is True
    assert settings.shadow_cube_size <= 1024
    assert settings.ao_distance_m <= 0.5
    assert settings.volumetric_tile_size >= 4


def test_dynamic_resolution_scaling_upscale_presets() -> None:
    profile = GraphicsHardwareProfile(
        vendor=GPUVendor.INTEL,
        gpu_name="Intel Iris Xe",
        dedicated_vram_mb=128,
        system_ram_mb=16384,
        max_shared_vram_mb=8192,
    )
    optimizer = IntelIrisXeOptimizer(profile=profile)

    # 1080p target
    render_scale, internal_res = optimizer.calculate_internal_resolution(
        target_width=1920,
        target_height=1080,
        preset=UpscalePreset.PERFORMANCE,
    )

    assert render_scale == pytest.approx(0.67, abs=0.02)
    assert internal_res[0] < 1920
    assert internal_res[1] < 1080
    assert internal_res[0] * internal_res[1] < (1920 * 1080 * 0.5)  # Less than 50% pixels


def test_vram_offload_buffer_partitioning() -> None:
    profile = GraphicsHardwareProfile(
        vendor=GPUVendor.INTEL,
        gpu_name="Intel Iris Xe",
        dedicated_vram_mb=128,
        system_ram_mb=16384,
        max_shared_vram_mb=8192,
    )
    optimizer = IntelIrisXeOptimizer(profile=profile)
    plan = optimizer.create_memory_partition_plan()

    assert plan.dedicated_vram_budget_mb <= 128
    assert plan.system_ram_staging_budget_mb >= 4000
    assert plan.texture_mip_clamp == 1024
    assert "System RAM Offload" in plan.status_description
