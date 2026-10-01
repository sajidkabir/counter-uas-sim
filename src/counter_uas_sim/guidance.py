"""Interceptor guidance: proportional navigation and a pure-pursuit baseline.

The interceptor is a kinematic point mass with hard, documented limits
from ``InterceptorSpec``:

- a maximum speed (the velocity vector is rescaled, never exceeded),
- a maximum acceleration (every guidance command is clamped to it),
- a capture radius: closing to within it counts as an intercept.

It leaves the launcher at a fixed launch speed aimed at the target's
position at launch time. That initial condition abstracts the boost
phase: pure proportional navigation from a standing start commands
almost no acceleration on a collision course (the line-of-sight rate is
near zero), which is exactly why real interceptors are boosted to speed
before the guidance law takes over.

Two guidance laws are provided so they can be compared honestly:

- **Proportional navigation (PN)**: commands acceleration proportional
  to the line-of-sight rotation rate, a = N * Vc * LOS_rate, applied
  perpendicular to the line of sight. PN flies a near-straight
  collision course, which is why real systems use it.
- **Pure pursuit**: continuously steers the velocity vector at the
  target's current position. Simple, and visibly worse on crossing
  targets: it curves in behind the target and wastes energy. It is the
  baseline PN has to beat.

``run_intercept`` integrates one engagement against a ground-truth
target model with semi-implicit Euler steps at a fixed dt.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class InterceptorSpec:
    max_speed_mps: float = 70.0
    max_accel_mps2: float = 40.0
    capture_radius_m: float = 15.0
    navigation_constant: float = 4.0
    launch_speed_mps: float = 55.0


def _clamp_accel(accel: np.ndarray, spec: InterceptorSpec) -> np.ndarray:
    magnitude = float(np.linalg.norm(accel))
    if magnitude > spec.max_accel_mps2:
        accel = accel * (spec.max_accel_mps2 / magnitude)
    return accel


def pn_acceleration(int_pos, int_vel, tgt_pos, tgt_vel,
                    spec: InterceptorSpec) -> np.ndarray:
    """True proportional navigation acceleration command."""
    r = np.asarray(tgt_pos, dtype=float) - np.asarray(int_pos, dtype=float)
    distance = float(np.linalg.norm(r))
    if distance < 1e-9:
        return np.zeros(2)
    r_hat = r / distance
    v_rel = np.asarray(tgt_vel, dtype=float) - np.asarray(int_vel, dtype=float)
    closing_speed = -float(r_hat @ v_rel)
    los_rate = float(r[0] * v_rel[1] - r[1] * v_rel[0]) / (distance * distance)
    accel_mag = spec.navigation_constant * closing_speed * los_rate
    perpendicular = np.array([-r_hat[1], r_hat[0]])
    return _clamp_accel(accel_mag * perpendicular, spec)


def pure_pursuit_acceleration(int_pos, int_vel, tgt_pos,
                              spec: InterceptorSpec) -> np.ndarray:
    """Pure pursuit: steer the velocity vector at the target."""
    r = np.asarray(tgt_pos, dtype=float) - np.asarray(int_pos, dtype=float)
    distance = float(np.linalg.norm(r))
    if distance < 1e-9:
        return np.zeros(2)
    desired = r / distance
    int_vel = np.asarray(int_vel, dtype=float)
    speed = float(np.linalg.norm(int_vel))
    if speed < 1e-6:
        return _clamp_accel(spec.max_accel_mps2 * desired, spec)
    heading = int_vel / speed
    steer = desired - heading * float(desired @ heading)
    steer_norm = float(np.linalg.norm(steer))
    if steer_norm < 1e-9:
        return np.zeros(2)
    gain = min(1.0, 2.0 * steer_norm)
    return _clamp_accel(spec.max_accel_mps2 * gain * (steer / steer_norm), spec)


@dataclass
class InterceptResult:
    intercepted: bool
    miss_distance_m: float
    intercept_time_s: float | None
    flight_time_s: float
    max_speed_mps: float
    outcome: str


def run_intercept(target, launch_position, t_start: float,
                  spec: InterceptorSpec, guidance: str = "pn",
                  dt: float = 0.02, max_duration_s: float = 180.0,
                  perimeter_radius_m: float | None = None,
                  protected_point=(0.0, 0.0)) -> InterceptResult:
    """Simulate one interceptor flyout against a ground-truth target.

    The interceptor leaves the launch position at the spec's launch
    speed, aimed at the target's position at ``t_start``. Integration
    stops on intercept, on the target crossing the protected perimeter
    (when a perimeter is given), or at ``max_duration_s``.
    """
    pos = np.asarray(launch_position, dtype=float).copy()
    protected = np.asarray(protected_point, dtype=float)
    t = float(t_start)
    initial_target = target.position_at(t)
    to_target = initial_target - pos
    distance0 = float(np.linalg.norm(to_target))
    if distance0 > 1e-9:
        vel = spec.launch_speed_mps * (to_target / distance0)
    else:
        vel = np.zeros(2)
    min_range = float("inf")
    max_speed = float(np.linalg.norm(vel))
    steps = int(max_duration_s / dt)

    for _ in range(steps + 1):
        tgt_pos = target.position_at(t)
        tgt_vel = target.velocity_at(t)
        separation = float(np.linalg.norm(tgt_pos - pos))
        min_range = min(min_range, separation)
        if separation <= spec.capture_radius_m:
            return InterceptResult(True, separation, t, t - t_start,
                                   max_speed, "intercept")
        if perimeter_radius_m is not None:
            if float(np.linalg.norm(tgt_pos - protected)) <= perimeter_radius_m:
                return InterceptResult(False, min_range, None, t - t_start,
                                       max_speed, "target_reached_perimeter")
        if guidance == "pn":
            accel = pn_acceleration(pos, vel, tgt_pos, tgt_vel, spec)
        elif guidance == "pure_pursuit":
            accel = pure_pursuit_acceleration(pos, vel, tgt_pos, spec)
        else:
            raise ValueError(f"unknown guidance law: {guidance!r}")
        vel = vel + accel * dt
        speed = float(np.linalg.norm(vel))
        if speed > spec.max_speed_mps:
            vel = vel * (spec.max_speed_mps / speed)
            speed = spec.max_speed_mps
        max_speed = max(max_speed, speed)
        pos = pos + vel * dt
        t += dt

    return InterceptResult(False, min_range, None, t - t_start,
                           max_speed, "timeout")
