"""
Unit and integration tests for Computer Vision tracking and synthetic landmarks.
Executes completely headless in CI without physical camera hardware.
"""

import pytest

from chemlab_core.models import GestureType, Handedness
from chemlab_core.vision.gesture_classifier import GeometricGestureClassifier
from chemlab_core.vision.synthetic import SyntheticLandmarkGenerator


@pytest.mark.unit
def test_synthetic_landmark_generation(synthetic_generator: SyntheticLandmarkGenerator) -> None:
    """Verify synthetic landmark generator creates anatomically valid 21-point landmarks."""
    frame = synthetic_generator.get_next_frame()
    assert frame.frame_index == 0
    assert len(frame.landmarks) == 21
    assert frame.handedness == Handedness.RIGHT
    assert frame.confidence > 0.9

    # Check wrist anchor position
    wrist = frame.landmarks[0]
    assert 0.0 <= wrist.x <= 1.0
    assert 0.0 <= wrist.y <= 1.0


@pytest.mark.unit
def test_pinch_gesture_classification(synthetic_generator: SyntheticLandmarkGenerator) -> None:
    """Verify gesture classifier correctly identifies tight pinch between thumb and index."""
    classifier = GeometricGestureClassifier()

    # 1. Open hand should be IDLE
    open_frame = synthetic_generator.generate_frame(pinch_factor=0.0, grab_factor=0.0)
    open_gesture = classifier.classify(open_frame)
    assert open_gesture.gesture == GestureType.IDLE
    assert open_gesture.strength == 0.0

    # 2. Complete pinch should register PINCH with high confidence
    pinch_frame = synthetic_generator.generate_frame(pinch_factor=1.0, grab_factor=0.0)
    pinch_gesture = classifier.classify(pinch_frame)
    assert pinch_gesture.gesture == GestureType.PINCH
    assert pinch_gesture.strength > 0.85
    assert len(pinch_gesture.position) == 3


@pytest.mark.unit
def test_grab_gesture_classification(synthetic_generator: SyntheticLandmarkGenerator) -> None:
    """Verify gesture classifier identifies closed fist / grabbing gesture."""
    classifier = GeometricGestureClassifier()

    # Fully curled fingers (grab factor = 1.0)
    grab_frame = synthetic_generator.generate_frame(pinch_factor=0.0, grab_factor=1.0)
    grab_gesture = classifier.classify(grab_frame)
    assert grab_gesture.gesture == GestureType.GRAB
    assert grab_gesture.strength > 0.70


@pytest.mark.unit
def test_swipe_kinematic_classification(synthetic_generator: SyntheticLandmarkGenerator) -> None:
    """Verify dynamic kinematic gesture detection across sequential frames."""
    classifier = GeometricGestureClassifier()

    # Simulate hand swiping horizontally to the right across 10 frames
    for i in range(10):
        pos_x = 0.3 + (i * 0.02)
        frame = synthetic_generator.generate_frame(
            pinch_factor=0.0,
            grab_factor=0.0,
            wrist_pos=(pos_x, 0.7, 0.0),
        )
        gesture = classifier.classify(frame)

    # By the 10th frame, rightward velocity triggers SWIPE_RIGHT
    assert gesture.gesture == GestureType.SWIPE_RIGHT
    assert gesture.strength > 0.8


@pytest.mark.unit
def test_synthetic_sequence_generation(synthetic_generator: SyntheticLandmarkGenerator) -> None:
    """Verify batch sequence generation produces smooth monotonic progression."""
    pinch_sequence = synthetic_generator.generate_pinch_sequence(num_frames=15)
    assert len(pinch_sequence) == 15
    assert pinch_sequence[0].frame_index == 0
    assert pinch_sequence[-1].frame_index == 14
