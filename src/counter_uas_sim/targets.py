"""Synthetic intruder target models: ground-truth tracks in a 2D plane.

Every target is a pure function of time, so a scenario can be replayed
exactly and the tracker and guidance code can be scored against known
truth. Positions are (x, y) in metres in a local tangent plane. By
convention the protected point sits at the origin.

These models exist only to generate synthetic scenarios for study. They
use textbook kinematics and no real-world data of any kind.
"""

from __future__ import annotations

import numpy as np


def _vec(values) -> np.ndarray:
    return np.asarray(values, dtype=float)


class ConstantVelocityTarget:
    """Straight-line flight at a constant velocity."""

    name = "constant-velocity"

    def __init__(self, start, velocity):
        self.start = _vec(start)
        self.velocity = _vec(velocity)

    def position_at(self, t: float) -> np.ndarray:
        return self.start + self.velocity * t

    def velocity_at(self, t: float) -> np.ndarray:
        return self.velocity.copy()


class ManeuveringTarget:
    """Constant-speed flight with a constant turn rate.

    The velocity vector rotates at ``turn_rate_rad_s`` (positive turns
    left, counter-clockwise). Position is the closed-form integral of
    the rotating velocity, so speed is preserved exactly.
    """

    name = "maneuvering"

    def __init__(self, start, velocity, turn_rate_rad_s: float):
        self.start = _vec(start)
        self.initial_velocity = _vec(velocity)
        self.speed = float(np.linalg.norm(self.initial_velocity))
        self.heading0 = float(np.arctan2(self.initial_velocity[1],
                                         self.initial_velocity[0]))
        self.turn_rate = float(turn_rate_rad_s)

    def velocity_at(self, t: float) -> np.ndarray:
        heading = self.heading0 + self.turn_rate * t
        return self.speed * np.array([np.cos(heading), np.sin(heading)])

    def position_at(self, t: float) -> np.ndarray:
        if abs(self.turn_rate) < 1e-12:
            return self.start + self.initial_velocity * t
        heading = self.heading0 + self.turn_rate * t
        dx = (self.speed / self.turn_rate) * (np.sin(heading)
                                              - np.sin(self.heading0))
        dy = -(self.speed / self.turn_rate) * (np.cos(heading)
                                               - np.cos(self.heading0))
        return self.start + np.array([dx, dy])


class DivingTarget:
    """Flight under a constant acceleration vector.

    Used for a terminal dive profile: pick the acceleration along (or
    partly along) the velocity and the target speeds up as it closes.
    Position and velocity are the standard constant-acceleration
    integrals.
    """

    name = "diving"

    def __init__(self, start, velocity, acceleration):
        self.start = _vec(start)
        self.velocity = _vec(velocity)
        self.acceleration = _vec(acceleration)

    def position_at(self, t: float) -> np.ndarray:
        return self.start + self.velocity * t + 0.5 * self.acceleration * t * t

    def velocity_at(self, t: float) -> np.ndarray:
        return self.velocity + self.acceleration * t
