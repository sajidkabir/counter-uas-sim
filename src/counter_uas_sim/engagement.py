"""End-to-end engagement: detect, track, assess, launch, guide, outcome.

``run_engagement`` plays one scenario through the full chain:

1. The sensor watches for the intruder at its update rate.
2. The first detection starts a Kalman track.
3. Once the track has a few updates, every tick is scored by the threat
   assessment module.
4. When the assessment recommends engagement, an interceptor launches
   from the protected point and the guidance module flies it out.
5. The result reports the outcome, the miss distance, the intercept
   time, and a timestamped event log of the whole chain.

One documented simplification: after launch, the interceptor is flown
against ground truth, standing in for an onboard terminal seeker. The
ground tracker's job in this model is cueing the launch decision, which
is where its accuracy matters and where the tests measure it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .assessment import assess_track
from .guidance import InterceptorSpec, run_intercept
from .sensors import RadarSensor, SensorSpec
from .targets import ConstantVelocityTarget
from .tracking import KalmanTracker


@dataclass
class Scenario:
    target: object
    sensor: SensorSpec = field(default_factory=SensorSpec)
    interceptor: InterceptorSpec = field(default_factory=InterceptorSpec)
    guidance: str = "pn"
    perimeter_radius_m: float = 500.0
    protected_point: tuple = (0.0, 0.0)
    seed: int = 7
    max_time_s: float = 400.0
    min_track_updates: int = 4


@dataclass
class EngagementResult:
    outcome: str
    intercepted: bool
    detection_time_s: float | None
    launch_time_s: float | None
    intercept_time_s: float | None
    miss_distance_m: float | None
    threat_score_at_launch: float | None
    event_log: list


def default_scenario() -> Scenario:
    """Demo scenario: a 38 m/s intruder flying straight at the perimeter.

    Starts 4,080 m out, heading for the protected point, seed fixed so
    the demo output is reproducible.
    """
    start = np.array([-4000.0, 800.0])
    direction = -start / np.linalg.norm(start)
    target = ConstantVelocityTarget(start, direction * 38.0)
    return Scenario(target=target, seed=7)


def run_engagement(scenario: Scenario) -> EngagementResult:
    rng = np.random.default_rng(scenario.seed)
    sensor = RadarSensor(scenario.sensor, rng)
    protected = np.asarray(scenario.protected_point, dtype=float)
    dt = scenario.sensor.update_interval_s
    tracker: KalmanTracker | None = None

    log: list[str] = []
    detection_time = None
    launch_time = None
    score_at_launch = None
    launched = False

    t = 0.0
    while t <= scenario.max_time_s:
        true_pos = scenario.target.position_at(t)
        range_to_protected = float(np.linalg.norm(true_pos - protected))
        if range_to_protected <= scenario.perimeter_radius_m:
            log.append(f"t={t:6.1f} s  TARGET CROSSED the protected "
                       f"perimeter at {range_to_protected:,.0f} m")
            return EngagementResult("target_reached_perimeter", False,
                                     detection_time, None, None, None,
                                     None, log)

        measurement = sensor.measure(true_pos, origin=protected)
        if tracker is None:
            if measurement is not None:
                tracker = KalmanTracker(
                    dt,
                    measurement_sigma=scenario.sensor.noise_sigma_m,
                )
                tracker.initialize(measurement)
                detection_time = t
                log.append(f"t={t:6.1f} s  DETECTED at range "
                           f"{range_to_protected:,.0f} m")
        else:
            tracker.predict()
            if measurement is not None:
                tracker.update(measurement)

        if (tracker is not None and not launched
                and tracker.updates >= scenario.min_track_updates):
            if tracker.updates == scenario.min_track_updates:
                log.append(f"t={t:6.1f} s  TRACK ESTABLISHED, position "
                           f"std {tracker.position_std_m:.1f} m")
            assessment = assess_track(
                tracker.position, tracker.velocity,
                tracker.position_std_m, scenario.perimeter_radius_m,
                center=protected,
            )
            if assessment.recommend_engagement:
                launched = True
                launch_time = t
                score_at_launch = assessment.score
                log.append(f"t={t:6.1f} s  LAUNCH, threat score "
                           f"{assessment.score:.2f}, time to perimeter "
                           f"{assessment.time_to_perimeter_s:.0f} s")
                break
        t += dt

    if not launched:
        outcome = "not_detected" if detection_time is None else "no_launch"
        if outcome == "not_detected":
            log.append("t=   end  NO DETECTION during the scenario window")
        else:
            log.append("t=   end  TRACKED but engagement was never "
                       "recommended")
        return EngagementResult(outcome, False, detection_time, None, None,
                                None, None, log)

    intercept = run_intercept(
        scenario.target, protected, launch_time, scenario.interceptor,
        guidance=scenario.guidance,
        perimeter_radius_m=scenario.perimeter_radius_m,
        protected_point=protected,
    )
    if intercept.intercepted:
        log.append(f"t={intercept.intercept_time_s:6.1f} s  INTERCEPT, "
                   f"miss distance {intercept.miss_distance_m:.1f} m")
        outcome = "intercepted"
    elif intercept.outcome == "target_reached_perimeter":
        log.append(f"t={launch_time + intercept.flight_time_s:6.1f} s  "
                   f"TARGET CROSSED the perimeter before intercept, "
                   f"closest approach {intercept.miss_distance_m:.1f} m")
        outcome = "intercept_failed"
    elif intercept.outcome == "energy_exhausted":
        log.append(f"t={launch_time + intercept.flight_time_s:6.1f} s  "
                   f"ENERGY EXHAUSTED, no intercept, closest approach "
                   f"{intercept.miss_distance_m:.1f} m")
        outcome = "intercept_failed"
    else:
        log.append(f"t={launch_time + intercept.flight_time_s:6.1f} s  "
                   f"NO INTERCEPT, closest approach "
                   f"{intercept.miss_distance_m:.1f} m")
        outcome = "intercept_failed"

    return EngagementResult(
        outcome, intercept.intercepted, detection_time, launch_time,
        intercept.intercept_time_s, intercept.miss_distance_m,
        score_at_launch, log,
    )
