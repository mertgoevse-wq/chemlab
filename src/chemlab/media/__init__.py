"""
ChemLab Media Bridge Package.
Provides access to Google's complete service ecosystem for asset generation,
NPC creation, quest design, and laboratory content generation.
"""

from chemlab.media.google_media_bridge import (
    GoogleCredentials,
    GoogleMediaBridge,
    GoogleService,
    LabAssetPackage,
    MediaGenerationRequest,
    MediaGenerationResponse,
)

__all__ = [
    "GoogleCredentials",
    "GoogleMediaBridge",
    "GoogleService",
    "LabAssetPackage",
    "MediaGenerationRequest",
    "MediaGenerationResponse",
]
