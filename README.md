# counter-uas-sim

[![CI](https://github.com/sajidkabir/counter-uas-sim/actions/workflows/ci.yml/badge.svg)](https://github.com/sajidkabir/counter-uas-sim/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23077802.svg)](https://doi.org/10.5281/zenodo.23077802)

A counter-drone (counter-UAS) defence simulator for research and
education. It plays the full engagement chain end to end: a sensor
**detects** an intruder, a Kalman filter **tracks** it, a threat model
**assesses** it, and a low-cost interceptor is launched and **guided**
to intercept, with proportional navigation and a pure-pursuit baseline
to compare against. A seeded Monte Carlo runner then measures how often
the chain works, and what a successful intercept costs.

The question behind the project is economic. Missile-defence
interceptors are publicly reported to cost tens of thousands of dollars
per shot, while the intruder drones they are used against can cost a
few hundred. This simulator exists to study the alternative: whether a
low-cost interceptor concept (USD 500 per unit in the author's
published concept work) can close the engagement at all, and what the
cost per successful intercept looks like next to about USD 50,000 per
interceptor missile, a publicly reported estimate. Both figures are
reported estimates used in a cost model, not exact procurement data.

**Scope, stated plainly:** this is a research and education simulation.
Everything runs on synthetic scenarios generated in code. There are no
hardware interfaces, no real-world targeting data, and no connection to
any real system. The models are textbook kinematics in a 2D plane,
built to study the detection-to-intercept chain and the cost argument,
not to design or operate a weapon.

## Features

- **Synthetic intruder models**: constant-velocity, constant-turn
  maneuvering, and diving (constant-acceleration) profiles, each an exact
  ground-truth function of time that the rest of the chain is scored
  against.
- **Sensor model**: maximum range, detection probability falling
  smoothly with range, Gaussian measurement noise, and a fixed update
  rate. All randomness is seeded, so scenarios reproduce exactly.
- **Kalman tracking**: a constant-velocity Kalman filter that turns
  noisy position fixes into a track with velocity and covariance. In
  validation it cuts position error from 34.5 m (raw fixes) to 14.0 m.
- **Threat assessment**: a documented 0 to 1 score combining
  time-to-perimeter (weight 0.45), speed (0.25), and trajectory
  directness (0.30), with an engagement recommendation that also
  requires the track to be accurate enough to act on.
- **Guidance**: proportional navigation (PN) for a kinematic
  interceptor with hard speed and acceleration limits and a capture
  radius, plus a pure-pursuit baseline flown under identical limits.
- **End-to-end engagements**: detect, track, assess, launch, guide,
  outcome, returned with a timestamped event log.
- **Monte Carlo analysis**: randomized intruders (range, bearing, aim
  offset, speed, and a maneuvering subset) over seeded runs, reporting
  intercept probability, mean miss distance, and cost per successful
  intercept for both interceptor price points.
- **CLI**: `counter-uas run` for one demo engagement and
  `counter-uas montecarlo` for the seeded analysis, plus a Python API.

## Installation

Requires Python 3.10 or newer.

```bash
git clone https://github.com/sajidkabir/counter-uas-sim.git
cd counter-uas-sim
pip install -e .
```

For development (adds the test runner):

```bash
pip install -e . pytest
pytest -q
```

## Quickstart

### Command line

Run the demo engagement: a 38 m/s intruder flying straight at the
protected point from 4,080 m out:

```bash
counter-uas run
```

```text
Counter-UAS engagement simulation
  Guidance:        pn

  t=   3.0 s  DETECTED at range 3,965 m
  t=   6.0 s  TRACK ESTABLISHED, position std 20.6 m
  t=  16.0 s  LAUNCH, threat score 0.60, time to perimeter 81 s
  t=  53.2 s  INTERCEPT, miss distance 13.5 m

  Outcome:         intercepted
  Miss distance:   13.5 m
  Intercept time:  53.2 s
```

Run the Monte Carlo analysis (200 seeded engagements):

```bash
counter-uas montecarlo --runs 200
```

```text
Counter-UAS Monte Carlo summary
  Runs:                    200
  Guidance:                pn
  Seed:                    42
  Launches:                175
  Intercepts:              159
  Intercept probability:   0.795
  Mean miss distance:      104.1 m

  Cost per successful intercept (reported estimates):
    Low-cost interceptor (USD 500 per unit):  USD 550
    Missile-defence interceptor (about USD 50,000 per missile):  USD 55,031
```

One interceptor is expended per launch in both systems, so the
100-to-1 unit price gap survives the division almost intact: a
successful intercept costs USD 550 of low-cost interceptors against
USD 55,031 of missile-defence interceptors at the same success rate.

Compare guidance laws on the same seed:

```bash
counter-uas montecarlo --runs 200 --guidance pure_pursuit
```

### Python API

```python
import numpy as np

from counter_uas_sim import ConstantVelocityTarget, Scenario, run_engagement

start = np.array([3500.0, -1200.0])
direction = -start / np.linalg.norm(start)
target = ConstantVelocityTarget(start, direction * 40.0)

result = run_engagement(Scenario(target=target, seed=7))
print(result.outcome)          # 'intercepted'
print(result.miss_distance_m)  # closest approach / miss distance
for line in result.event_log:
    print(line)
```

## How it works

| Module | Responsibility |
| --- | --- |
| `targets.py` | Ground-truth intruder tracks (straight, turning, diving) |
| `sensors.py` | Detection probability, measurement noise, update rate |
| `tracking.py` | Constant-velocity Kalman filter and track quality |
| `assessment.py` | Threat score and the engagement recommendation |
| `guidance.py` | Proportional navigation and pure pursuit, interceptor limits |
| `engagement.py` | The full detect-track-assess-launch-guide chain |
| `montecarlo.py` | Seeded randomized runs and the cost comparison |
| `cli.py` | Command-line interface |

Key relations:

- Detection probability: P_d(r) = 1 / (1 + (r / r50) ** n), with
  P_d = 0.5 at r = r50 (default 4,000 m), and no detections beyond the
  maximum range (default 5,000 m).
- Time to perimeter: the smallest positive root of |p + v t| = R for
  the track position p, velocity v, and perimeter radius R. A track
  that never crosses scores zero time pressure.
- Threat score: 0.45 * time pressure + 0.25 * speed score + 0.30 *
  directness, each component in [0, 1]. Engagement is recommended at a
  score of 0.60 or more, and only if the track position standard
  deviation is at most 50 m.
- Proportional navigation: a = N * Vc * LOS_rate, applied perpendicular
  to the line of sight, with navigation constant N = 4, closing speed
  Vc, and the command clamped to the interceptor's acceleration limit
  (40 m/s2). The interceptor leaves the launcher at 55 m/s toward the
  target and can never exceed 70 m/s. Closing within the 15 m capture
  radius counts as an intercept.
- Cost per successful intercept: unit cost * launches / intercepts,
  computed identically for both price points so the comparison is
  apples to apples.

## Validation and sanity checks

The test suite (19 tests) checks the physics and the logic, not just
the plumbing:

- Target models reproduce textbook values exactly: a full constant-rate
  turn returns to its start point, and the diving profile matches the
  constant-acceleration integral.
- Detection probability is 1 at zero range, exactly 0.5 at r50, and 0
  beyond maximum range.
- On a seeded track with 25 m sensor noise, the Kalman filter's
  position RMS error after convergence is 14.0 m against 34.5 m for the
  raw fixes, and it recovers the true velocity.
- A fast, direct intruder outranks a slow, tangential one, and the same
  fast intruder on a deliberately degraded track (200 m standard
  deviation) is scored high but NOT recommended for engagement.
- PN intercepts a constant-velocity target inside the capture radius,
  beats pure pursuit's miss distance on a crossing target, and the
  interceptor never exceeds its speed limit under either law.
- No engagement in the chain can intercept before detection: the event
  log order and timestamps are asserted.
- Monte Carlo with a fixed seed returns identical results on repeat
  runs, field for field.

One Monte Carlo finding worth stating honestly, because it shapes the
roadmap: split the seed-42 runs by target type and the two guidance
laws trade places. Against straight-line intruders both laws intercept
every launched engagement, but PN gets there faster (mean flight
35.7 s against 39.5 s). Against continuously maneuvering intruders
launched on at long range, pure pursuit eventually spirals in (41 of
41, mean flight 89.3 s) while PN's collision course keeps being
invalidated by the turn (25 of 41). The model gives the interceptor
unlimited endurance, which flatters pursuit; a real low-cost
interceptor would run out of energy on those long chases. Both effects
are visible in the numbers, and neither is hidden.

## Honest limitations

- 2D plane only: no altitude, no diving geometry out of the plane, no
  terrain or earth curvature.
- After launch, the interceptor flies against ground truth, standing in
  for an onboard terminal seeker. The ground tracker cues the launch;
  its accuracy is measured where it matters, at the decision.
- The interceptor has no energy or endurance limit, which (as the
  validation section shows) flatters pure pursuit on long chases.
- The threat score uses instantaneous velocity. A maneuvering target
  can look committed and then turn away, which is the main source of
  failed engagements in the Monte Carlo mix.
- The sensor is a single generic model: no clutter, no false alarms, no
  weather, no electronic warfare, no multi-sensor fusion.
- Targets do not react to being engaged. There is no evasion model
  beyond the fixed maneuvering profile.
- Cost figures are reported estimates in a simple model (one
  interceptor expended per launch), not procurement analysis.

## Roadmap and room for exploration

Ideas are welcome. Roughly in order of expected value:

- **Augmented and predictive guidance** for maneuvering targets:
  feed-forward of target lateral acceleration, and launch-commit logic
  that accounts for target turn rate, aimed squarely at the Monte
  Carlo weakness documented above.
- **Interceptor endurance**: an energy budget that ends long chases,
  so guidance comparisons price flight time honestly.
- **3D engagement geometry**: altitude, diving profiles out of the
  plane, and a sensor model with elevation coverage.
- **Seeker-based terminal phase**: fly the endgame on noisy seeker
  measurements instead of ground truth, and measure how much the miss
  distance grows.
- **Multi-target raids**: several simultaneous intruders, track
  management, and interceptor allocation under a magazine limit.
- **Sensor realism**: false alarms, clutter, track initiation and
  drop logic, and a second fused sensor.
- **Evasive targets**: intruders that maneuver when an interceptor
  launches, turning the study into a pursuit-evasion analysis.
- **Cost-model depth**: salvo logic (two interceptors per high-value
  track), magazine reload cost, and sensitivity of the comparison to
  the assumed unit prices.

If you build one of these, open an issue or a pull request. Design
notes in the PR description are appreciated: what assumption changed,
and what it did to the intercept probability at the reference seed.

## Project structure

```text
src/counter_uas_sim/   the package (targets, sensors, tracking,
                       assessment, guidance, engagement, montecarlo,
                       cli)
tests/                 pytest suite, physics and logic checks included
examples/              runnable demo engagement and Monte Carlo summary
.github/workflows/     CI: install and run the test suite on every push
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The short version: fork, branch,
test, pull request. Every change should keep `pytest -q` green, stay
seeded and reproducible, and not move the validated numbers without
explaining why in the PR.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Citation

If you use this project in research, please cite the archived release:

Sajid Kabir Saji (2026). counter-uas-sim (v1.0.1) [Software]. Zenodo. https://doi.org/10.5281/zenodo.23077803

The concept DOI https://doi.org/10.5281/zenodo.23077802 always resolves to the latest version.

## License

MIT. See [LICENSE](LICENSE).

## Author

Sajid Kabir Saji, aeronautical engineer. Research interests: onboard
autonomous decision-making for UAVs, solar-electric flight endurance,
and low-cost counter-drone defence.
More at [sajidkabir.com](https://sajidkabir.com).
