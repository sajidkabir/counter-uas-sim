"""A simple detection and measurement sensor model.

The sensor stands in for a generic surveillance radar or electro-optical
tracker watching the protected point. It has:

- a hard maximum range: no detection attempts outside it,
- a detection probability that falls smoothly with range,
  P_d(r) = 1 / (1 + (r / r50) ** n), so P_d = 0.5 at r = r50,
- Gaussian position measurement noise with a fixed standard deviation,
- a fixed update rate.

All randomness comes from a caller-supplied ``numpy`` generator, so a
seeded scenario is exactly reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SensorSpec:
    max_range_m: float = 5000.0
    range_50_m: float = 4000.0
    falloff_exponent: float = 6.0
    noise_sigma_m: float = 25.0
    update_rate_hz: float = 1.0

    @property
    def update_interval_s(self) -> float:
        return 1.0 / self.update_rate_hz

    def detection_probability(self, range_m: float) -> float:
        """Probability of detecting a target at the given range."""
        if range_m > self.max_range_m:
            return 0.0
        ratio = range_m / self.range_50_m
        return float(1.0 / (1.0 + ratio ** self.falloff_exponent))


class RadarSensor:
    """Stateful sensor: call ``measure`` once per update tick."""

    def __init__(self, spec: SensorSpec, rng: np.random.Generator):
        self.spec = spec
        self.rng = rng

    def measure(self, true_position, origin=(0.0, 0.0)):
        """Return a noisy position measurement, or None if undetected."""
        true_position = np.asarray(true_position, dtype=float)
        origin = np.asarray(origin, dtype=float)
        range_m = float(np.linalg.norm(true_position - origin))
        if range_m > self.spec.max_range_m:
            return None
        if self.rng.random() > self.spec.detection_probability(range_m):
            return None
        noise = self.rng.normal(0.0, self.spec.noise_sigma_m, size=2)
        return true_position + noise
