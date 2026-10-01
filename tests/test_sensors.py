"""Sensor model: detection falls with range, noise is seeded."""

import numpy as np

from counter_uas_sim.sensors import RadarSensor, SensorSpec


def test_detection_probability_falls_with_range():
    spec = SensorSpec()
    assert spec.detection_probability(0.0) == 1.0
    near = spec.detection_probability(2000.0)
    mid = spec.detection_probability(4000.0)
    far = spec.detection_probability(4900.0)
    assert near > mid > far > 0.0
    assert abs(mid - 0.5) < 1e-9  # r50 is the half-probability range
    assert spec.detection_probability(6000.0) == 0.0  # beyond max range


def test_measurements_are_reproducible_with_a_seed():
    spec = SensorSpec()
    position = np.array([1000.0, 500.0])
    first = RadarSensor(spec, np.random.default_rng(5))
    second = RadarSensor(spec, np.random.default_rng(5))
    for _ in range(10):
        a = first.measure(position)
        b = second.measure(position)
        assert (a is None) == (b is None)
        if a is not None:
            assert np.allclose(a, b)


def test_no_detection_beyond_max_range():
    spec = SensorSpec()
    sensor = RadarSensor(spec, np.random.default_rng(1))
    assert sensor.measure(np.array([9000.0, 0.0])) is None
