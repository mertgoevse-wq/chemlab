"""
ChemLab Graphics Engine Package.
Houses rendering optimization pipelines, Intel Iris Xe hardware offload profiles,
and EEVEE viewport scaling.
"""

from chemlab.graphics.iris_xe_optimizer import (
    EEVEEViewportSettings,
    GPUVendor,
    GraphicsHardwareProfile,
    IntelIrisXeOptimizer,
    MemoryPartitionPlan,
    UpscalePreset,
)

__all__ = [
    "EEVEEViewportSettings",
    "GPUVendor",
    "GraphicsHardwareProfile",
    "IntelIrisXeOptimizer",
    "MemoryPartitionPlan",
    "UpscalePreset",
]
