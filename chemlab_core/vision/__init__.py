"""
Computer Vision tracking and gesture classification module.
Fully decoupled from network transport and rendering.
"""

from chemlab_core.vision.contracts import GestureClassifier, LandmarkProvider
from chemlab_core.vision.gesture_classifier import GeometricGestureClassifier
from chemlab_core.vision.synthetic import SyntheticLandmarkGenerator

__all__ = [
    "GestureClassifier",
    "GeometricGestureClassifier",
    "LandmarkProvider",
    "SyntheticLandmarkGenerator",
]
