"""counter-uas-sim: counter-UAS defence simulation for research and education."""

from .assessment import ThreatAssessment, assess_track, time_to_perimeter
from .engagement import (
    EngagementResult,
    Scenario,
    default_scenario,
    run_engagement,
)
from .guidance import (
    InterceptResult,
    InterceptorSpec,
    pn_acceleration,
    pure_pursuit_acceleration,
    run_intercept,
)
from .montecarlo import MonteCarloResult, random_scenario, run_monte_carlo
from .sensors import RadarSensor, SensorSpec
from .targets import (
    ConstantVelocityTarget,
    DivingTarget,
    ManeuveringTarget,
)
from .tracking import KalmanTracker

__version__ = "1.0.0"

__all__ = [
    "ConstantVelocityTarget",
    "ManeuveringTarget",
    "DivingTarget",
    "SensorSpec",
    "RadarSensor",
    "KalmanTracker",
    "ThreatAssessment",
    "assess_track",
    "time_to_perimeter",
    "InterceptorSpec",
    "InterceptResult",
    "pn_acceleration",
    "pure_pursuit_acceleration",
    "run_intercept",
    "Scenario",
    "EngagementResult",
    "default_scenario",
    "run_engagement",
    "random_scenario",
    "MonteCarloResult",
    "run_monte_carlo",
]
