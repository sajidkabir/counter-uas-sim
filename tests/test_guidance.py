"""Guidance laws against ground truth, including the PN comparison."""

import numpy as np

from counter_uas_sim.guidance import InterceptorSpec, run_intercept
from counter_uas_sim.targets import ConstantVelocityTarget


def test_pn_intercepts_constant_velocity_target():
    target = ConstantVelocityTarget((-2500.0, 300.0), (35.0, -4.0))
    spec = InterceptorSpec()
    result = run_intercept(target, (0.0, 0.0), 0.0, spec, guidance="pn")
    assert result.intercepted
    assert result.miss_distance_m <= spec.capture_radius_m


def test_pn_beats_pure_pursuit_on_a_crossing_target():
    # Crossing target passing 900 m north of the launch point.
    target = ConstantVelocityTarget((-1500.0, 900.0), (40.0, 0.0))
    spec = InterceptorSpec()
    pn = run_intercept(target, (0.0, 0.0), 0.0, spec, guidance="pn")
    pp = run_intercept(target, (0.0, 0.0), 0.0, spec,
                       guidance="pure_pursuit")
    assert pn.intercepted
    assert pn.miss_distance_m <= pp.miss_distance_m


def test_interceptor_never_exceeds_its_speed_limit():
    target = ConstantVelocityTarget((-3000.0, -800.0), (38.0, 8.0))
    spec = InterceptorSpec()
    for law in ("pn", "pure_pursuit"):
        result = run_intercept(target, (0.0, 0.0), 0.0, spec, guidance=law)
        assert result.max_speed_mps <= spec.max_speed_mps + 1e-9
