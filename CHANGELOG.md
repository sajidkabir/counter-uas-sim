# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and versions follow
[Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-10-01

First stable release.

### Added

- Synthetic intruder target models (`targets`): constant-velocity,
  constant-turn maneuvering, and constant-acceleration diving profiles
  as ground-truth functions of time.
- Sensor model (`sensors`): maximum range, range-dependent detection
  probability, Gaussian measurement noise, fixed update rate, all driven
  by a seeded random generator.
- Kalman tracker (`tracking`): constant-velocity state model producing
  track estimates with covariance, converging well below raw sensor
  noise.
- Threat assessment (`assessment`): 0 to 1 score combining
  time-to-perimeter, speed, and trajectory directness with documented
  weights, plus an engagement recommendation gated on track quality.
- Guidance (`guidance`): proportional navigation and a pure-pursuit
  baseline for a speed-limited, acceleration-limited kinematic
  interceptor, with a capture-radius intercept criterion.
- End-to-end engagement runner (`engagement`): detect, track, assess,
  launch, guide, outcome, with a timestamped event log.
- Seeded Monte Carlo runner (`montecarlo`) with a cost-effectiveness
  summary comparing a USD 500 low-cost interceptor concept against a
  publicly reported estimate of about USD 50,000 per missile-defence
  interceptor.
- Command-line interface with `run` and `montecarlo` subcommands.
- Test suite of 19 tests covering the kinematics, the tracker accuracy,
  the scoring order, the guidance comparison, and Monte Carlo
  reproducibility, plus GitHub Actions CI on Python 3.12.
