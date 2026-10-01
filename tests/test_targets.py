"""Ground-truth target models: textbook kinematics, exact values."""

import numpy as np

from counter_uas_sim.targets import (
    ConstantVelocityTarget,
    DivingTarget,
    ManeuveringTarget,
)


def test_constant_velocity_position_is_linear():
    target = ConstantVelocityTarget((100.0, -50.0), (30.0, 12.0))
    assert np.allclose(target.position_at(0.0), [100.0, -50.0])
    assert np.allclose(target.position_at(10.0), [400.0, 70.0])
    assert np.allclose(target.velocity_at(10.0), [30.0, 12.0])


def test_maneuvering_target_preserves_speed():
    target = ManeuveringTarget((0.0, 0.0), (40.0, 0.0), turn_rate_rad_s=0.1)
    for t in (0.0, 3.0, 7.5, 20.0):
        assert abs(np.linalg.norm(target.velocity_at(t)) - 40.0) < 1e-9
    # A full turn returns to the starting point.
    period = 2.0 * np.pi / 0.1
    assert np.allclose(target.position_at(period), [0.0, 0.0], atol=1e-6)


def test_diving_target_speeds_up_along_track():
    start = np.array([-2000.0, 0.0])
    velocity = np.array([30.0, 0.0])
    accel = np.array([3.0, 0.0])
    target = DivingTarget(start, velocity, accel)
    assert np.allclose(target.position_at(10.0),
                       start + velocity * 10.0 + 0.5 * accel * 100.0)
    assert np.linalg.norm(target.velocity_at(10.0)) > np.linalg.norm(
        target.velocity_at(0.0))
