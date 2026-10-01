"""Threat assessment: turning a track into a 0 to 1 threat score.

The score combines three documented components:

- **Time pressure** (weight 0.45): how soon the track reaches the
  protected perimeter. A track that never crosses scores 0; a track
  already inside scores 1. In between, urgency rises linearly as
  time-to-perimeter falls toward zero over a 120 second horizon.
- **Speed** (weight 0.25): track speed against a 60 m/s reference,
  clipped to [0, 1]. Faster means less reaction time.
- **Directness** (weight 0.30): how directly the track is flying at the
  protected point, from the cosine between the velocity vector and the
  direction to the point, mapped from [-1, 1] to [0, 1].

An engagement is recommended only when the score reaches the engagement
threshold AND the track quality is good enough (position standard
deviation at or below the limit). A scary score on a bad track is not
enough: that separation is the point of the module.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

WEIGHT_TIME = 0.45
WEIGHT_SPEED = 0.25
WEIGHT_DIRECTNESS = 0.30
REFERENCE_SPEED_MPS = 60.0
URGENCY_HORIZON_S = 120.0
ENGAGE_THRESHOLD = 0.60
MAX_TRACK_STD_M = 50.0


def time_to_perimeter(position, velocity, perimeter_radius_m,
                      center=(0.0, 0.0)) -> float:
    """Seconds until the track crosses the protected perimeter circle.

    Solves |p + v t| = R for the smallest positive t. Returns 0.0 if the
    track is already inside, and ``math.inf`` if it never crosses.
    """
    p = np.asarray(position, dtype=float) - np.asarray(center, dtype=float)
    v = np.asarray(velocity, dtype=float)
    if np.linalg.norm(p) <= perimeter_radius_m:
        return 0.0
    a = float(v @ v)
    if a == 0.0:
        return float("inf")
    b = 2.0 * float(p @ v)
    c = float(p @ p) - perimeter_radius_m ** 2
    discriminant = b * b - 4.0 * a * c
    if discriminant < 0.0:
        return float("inf")
    root = np.sqrt(discriminant)
    candidates = [(-b - root) / (2.0 * a), (-b + root) / (2.0 * a)]
    positive = [t for t in candidates if t > 0.0]
    if not positive:
        return float("inf")
    return float(min(positive))


@dataclass
class ThreatAssessment:
    score: float
    time_score: float
    speed_score: float
    directness_score: float
    time_to_perimeter_s: float
    speed_mps: float
    recommend_engagement: bool


def assess_track(position, velocity, track_std_m, perimeter_radius_m,
                 center=(0.0, 0.0)) -> ThreatAssessment:
    """Score one track and decide whether engagement is recommended."""
    position = np.asarray(position, dtype=float)
    velocity = np.asarray(velocity, dtype=float)
    ttp = time_to_perimeter(position, velocity, perimeter_radius_m, center)

    if np.isinf(ttp):
        time_score = 0.0
    else:
        time_score = float(np.clip(1.0 - ttp / URGENCY_HORIZON_S, 0.0, 1.0))

    speed = float(np.linalg.norm(velocity))
    speed_score = float(np.clip(speed / REFERENCE_SPEED_MPS, 0.0, 1.0))

    to_center = np.asarray(center, dtype=float) - position
    distance = float(np.linalg.norm(to_center))
    if speed > 0.0 and distance > 0.0:
        cosine = float(velocity @ to_center) / (speed * distance)
    else:
        cosine = 0.0
    directness_score = 0.5 * (cosine + 1.0)

    score = (WEIGHT_TIME * time_score
             + WEIGHT_SPEED * speed_score
             + WEIGHT_DIRECTNESS * directness_score)

    recommend = (score >= ENGAGE_THRESHOLD
                 and track_std_m <= MAX_TRACK_STD_M
                 and np.isfinite(ttp))
    return ThreatAssessment(
        score=float(score),
        time_score=time_score,
        speed_score=speed_score,
        directness_score=float(directness_score),
        time_to_perimeter_s=float(ttp),
        speed_mps=speed,
        recommend_engagement=bool(recommend),
    )
