"""Target tracking with a constant-velocity Kalman filter.

The filter state is [x, y, vx, vy]. Measurements are positions only, so
velocity is inferred over successive updates. Process noise uses the
standard continuous white-noise acceleration model, which lets the
filter follow gentle maneuvers without trusting any single noisy fix.

The point of the tracker in this simulator is measurable: after a short
convergence period its position error against ground truth is well below
the raw sensor noise. The test suite checks exactly that.
"""

from __future__ import annotations

import numpy as np


class KalmanTracker:
    """Constant-velocity Kalman filter for one target."""

    def __init__(self, dt: float, process_noise: float = 3.0,
                 measurement_sigma: float = 25.0):
        self.dt = float(dt)
        dt = self.dt
        self.F = np.array([
            [1.0, 0.0, dt, 0.0],
            [0.0, 1.0, 0.0, dt],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ])
        self.H = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
        ])
        q = float(process_noise)
        self.Q = q * np.array([
            [dt ** 4 / 4.0, 0.0, dt ** 3 / 2.0, 0.0],
            [0.0, dt ** 4 / 4.0, 0.0, dt ** 3 / 2.0],
            [dt ** 3 / 2.0, 0.0, dt ** 2, 0.0],
            [0.0, dt ** 3 / 2.0, 0.0, dt ** 2],
        ])
        sigma = float(measurement_sigma)
        self.R = (sigma ** 2) * np.eye(2)
        self.state = np.zeros(4)
        self.covariance = np.eye(4)
        self.updates = 0
        self._initialized = False

    def initialize(self, position) -> None:
        """Start the track from a first measurement."""
        position = np.asarray(position, dtype=float)
        self.state = np.array([position[0], position[1], 0.0, 0.0])
        sigma = float(np.sqrt(self.R[0, 0]))
        self.covariance = np.diag([sigma ** 2, sigma ** 2, 50.0 ** 2, 50.0 ** 2])
        self.updates = 1
        self._initialized = True

    def predict(self) -> None:
        self.state = self.F @ self.state
        self.covariance = self.F @ self.covariance @ self.F.T + self.Q

    def update(self, measurement) -> None:
        """Fuse one position measurement."""
        z = np.asarray(measurement, dtype=float)
        y = z - self.H @ self.state
        s = self.H @ self.covariance @ self.H.T + self.R
        gain = self.covariance @ self.H.T @ np.linalg.inv(s)
        self.state = self.state + gain @ y
        self.covariance = (np.eye(4) - gain @ self.H) @ self.covariance
        self.updates += 1

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def position(self) -> np.ndarray:
        return self.state[:2].copy()

    @property
    def velocity(self) -> np.ndarray:
        return self.state[2:].copy()

    @property
    def position_std_m(self) -> float:
        """Root-mean-square position standard deviation from the covariance."""
        return float(np.sqrt(0.5 * (self.covariance[0, 0]
                                    + self.covariance[1, 1])))

    def position_error(self, true_position) -> float:
        """Distance between the track estimate and ground truth."""
        return float(np.linalg.norm(self.position
                                    - np.asarray(true_position, dtype=float)))
