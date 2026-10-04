"""Seeded Monte Carlo analysis and the cost-effectiveness comparison.

Single engagements prove the chain works. Monte Carlo shows how often:
each run draws a fresh intruder (starting range, bearing, aim offset,
and speed all randomized) and plays the full engagement. Everything is
driven from one master seed, so a published result can be reproduced
exactly by re-running with the same seed.

The cost summary is the reason this project exists. Missile-defence
interceptors are widely reported to cost tens of thousands of dollars
per shot, against intruder drones that can cost less than the missile.
The comparison below uses:

- **USD 500 per unit** for the low-cost interceptor concept, the figure
  from the author's published concept work, and
- **about USD 50,000 per interceptor missile**, a publicly reported
  estimate for a short-range missile-defence interceptor.

Both are treated as reported estimates for a cost model, not as exact
procurement figures. Cost per successful intercept assumes one
interceptor is expended per launched engagement in both systems and
divides total spend by successful intercepts.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .engagement import Scenario, run_engagement
from .targets import ConstantVelocityTarget, ManeuveringTarget

LOW_COST_UNIT_USD = 500.0
MISSILE_UNIT_USD = 50_000.0


def random_scenario(rng: np.random.Generator, seed: int) -> Scenario:
    """Draw one randomized intruder scenario.

    The intruder starts 3,400 to 4,400 m out on a random bearing, aims
    at a point offset up to 600 m from the protected point, and flies
    28 to 45 m/s. About a third of draws maneuver with a constant turn
    of 0.04 to 0.10 rad/s in a random direction; the rest fly straight.
    """
    bearing = rng.uniform(0.0, 2.0 * np.pi)
    start_range = rng.uniform(3400.0, 4400.0)
    start = start_range * np.array([np.cos(bearing), np.sin(bearing)])
    perpendicular = np.array([-np.sin(bearing), np.cos(bearing)])
    aim_point = perpendicular * rng.uniform(-600.0, 600.0)
    direction = aim_point - start
    direction = direction / np.linalg.norm(direction)
    speed = rng.uniform(28.0, 45.0)
    velocity = direction * speed
    if rng.random() < 0.35:
        turn = rng.uniform(0.04, 0.10) * (1.0 if rng.random() < 0.5 else -1.0)
        target = ManeuveringTarget(start, velocity, turn)
    else:
        target = ConstantVelocityTarget(start, velocity)
    return Scenario(target=target, seed=seed)


@dataclass
class MonteCarloResult:
    runs: int
    launches: int
    intercepts: int
    intercept_probability: float
    mean_miss_distance_m: float
    low_cost_unit_usd: float
    missile_unit_usd: float
    low_cost_per_success_usd: float
    missile_per_success_usd: float


def run_monte_carlo(runs: int = 200, seed: int = 42,
                    guidance: str = "pn",
                    endurance_s: float = 60.0) -> MonteCarloResult:
    """Run ``runs`` seeded engagements and aggregate the outcomes.

    ``endurance_s`` is the interceptor energy budget applied to every
    run (see ``InterceptorSpec``); the default matches the spec
    default.
    """
    master = np.random.default_rng(seed)
    launches = 0
    intercepts = 0
    miss_distances: list[float] = []

    for _ in range(runs):
        run_seed = int(master.integers(0, 2 ** 31 - 1))
        scenario = random_scenario(master, run_seed)
        scenario.guidance = guidance
        scenario.interceptor.endurance_s = endurance_s
        result = run_engagement(scenario)
        if result.launch_time_s is not None:
            launches += 1
            miss_distances.append(result.miss_distance_m)
        if result.intercepted:
            intercepts += 1

    probability = intercepts / runs if runs else 0.0
    mean_miss = float(np.mean(miss_distances)) if miss_distances else float("inf")
    if intercepts:
        low_cost_per_success = LOW_COST_UNIT_USD * launches / intercepts
        missile_per_success = MISSILE_UNIT_USD * launches / intercepts
    else:
        low_cost_per_success = float("inf")
        missile_per_success = float("inf")

    return MonteCarloResult(
        runs=runs,
        launches=launches,
        intercepts=intercepts,
        intercept_probability=probability,
        mean_miss_distance_m=mean_miss,
        low_cost_unit_usd=LOW_COST_UNIT_USD,
        missile_unit_usd=MISSILE_UNIT_USD,
        low_cost_per_success_usd=low_cost_per_success,
        missile_per_success_usd=missile_per_success,
    )
