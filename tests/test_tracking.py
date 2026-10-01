"""The tracker must beat the raw sensor noise on the same track."""

import numpy as np

from counter_uas_sim.sensors import RadarSensor, SensorSpec
from counter_uas_sim.targets import ConstantVelocityTarget
from counter_uas_sim.tracking import KalmanTracker


def _run_track(seed=3, steps=90, window_start=40.0):
    target = ConstantVelocityTarget((-3000.0, 500.0), (30.0, -4.0))
    spec = SensorSpec(noise_sigma_m=25.0)
    sensor = RadarSensor(spec, np.random.default_rng(seed))
    tracker = KalmanTracker(dt=1.0, measurement_sigma=spec.noise_sigma_m)
    raw_errors = []
    track_errors = []
    t = 0.0
    for _ in range(steps):
        true_pos = target.position_at(t)
        measurement = sensor.measure(true_pos)
        if tracker.initialized:
            tracker.predict()
        if measurement is not None:
            if t >= window_start:
                raw_errors.append(float(np.linalg.norm(measurement - true_pos)))
            if tracker.initialized:
                tracker.update(measurement)
            else:
                tracker.initialize(measurement)
        if tracker.initialized and t >= window_start:
            track_errors.append(tracker.position_error(true_pos))
        t += 1.0
    return raw_errors, track_errors


def test_kalman_position_error_beats_raw_measurement_error():
    raw_errors, track_errors = _run_track()
    assert len(track_errors) > 20
    raw_rms = float(np.sqrt(np.mean(np.square(raw_errors))))
    track_rms = float(np.sqrt(np.mean(np.square(track_errors))))
    assert track_rms < raw_rms
    assert track_rms < 0.6 * raw_rms


def test_tracker_recovers_velocity():
    target = ConstantVelocityTarget((0.0, 0.0), (25.0, 5.0))
    spec = SensorSpec(noise_sigma_m=10.0)
    sensor = RadarSensor(spec, np.random.default_rng(11))
    tracker = KalmanTracker(dt=1.0, measurement_sigma=spec.noise_sigma_m)
    t = 0.0
    for _ in range(60):
        measurement = sensor.measure(target.position_at(t))
        if tracker.initialized:
            tracker.predict()
        if measurement is not None:
            if tracker.initialized:
                tracker.update(measurement)
            else:
                tracker.initialize(measurement)
        t += 1.0
    assert np.linalg.norm(tracker.velocity - np.array([25.0, 5.0])) < 3.0
