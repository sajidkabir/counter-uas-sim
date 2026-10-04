# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and versions follow
[Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-10-04

Guidance comparisons now price flight time honestly.

### Added

- Interceptor energy budget (`InterceptorSpec.endurance_s`, default
  60 s): when the budget is spent the attempt ends with outcome
  `energy_exhausted`. The default is a placeholder parameter; set it
  per platform from motor or battery data. Use `float("inf")` for the
  old unlimited-endurance behavior.
- `ENERGY EXHAUSTED` event-log entry and `intercept_failed` mapping in
  the engagement runner.
- `--endurance` option on the `run` and `montecarlo` CLI subcommands,
  and an `endurance_s` parameter on `run_monte_carlo`.
- 7 new tests (26 total): budget exhaustion, unlimited-endurance
  recovery, monotonic intercepts under shorter budgets, the pursuit
  chase effect, the budgeted guidance comparison, log surfacing, and
  reproducibility.

### Changed

- With the default 60 s budget, the seed-42 Monte Carlo reference
  numbers move: PN 136 of 200 intercepts (was 159), pure pursuit 132
  of 200 (was 175); mean miss distance 244.6 m (was 104.1 m). The
  budgeted comparison favors PN's fast collision courses over
  pursuit's long chases, and the README documents both the budgeted
  and the unlimited-budget numbers.

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
