# Contributing

Contributions are welcome: bug reports, model corrections, new target
or guidance models, documentation, and examples. This project aims to
stay small, readable, and honest about its assumptions. It is a research
and education simulator: contributions must keep it that way, meaning
synthetic scenarios and textbook models only.

## Getting set up

```bash
git clone https://github.com/sajidkabir/counter-uas-sim.git
cd counter-uas-sim
python -m venv .venv
source .venv/bin/activate
pip install -e . pytest
pytest -q
```

All 19 tests should pass before you change anything.

## Making a change

1. Fork the repository and create a branch from `main`
   (`git checkout -b feature/short-name`).
2. Keep the change focused. One model, one fix, or one feature per pull
   request.
3. Add or update tests. Model changes need a sanity check against a
   hand-computed value or a published reference, and the test should say
   which. Anything randomized must be seeded so results reproduce.
4. Run `pytest -q` and make sure it is green.
5. Update the README, the docstrings, and `CHANGELOG.md` (Unreleased
   section) if behavior or numbers change.
6. Open a pull request against `main` describing what changed, why, and
   what it does to the Monte Carlo intercept probability and mean miss
   distance at the reference seed.

## Ground rules

- No silent changes to validated numbers. If a fix moves a result, say
  so in the pull request and in the changelog.
- Prefer explicit, textbook models over clever code. A reviewer should
  be able to check each formula against its source.
- New assumptions go in the README limitations list until they are
  modeled.
- Cost figures stay labeled as reported estimates with their source
  framing intact. Do not present them as exact procurement data.

## Reporting issues

Open an issue with the scenario or seed you ran, the command or code you
used, the output you got, and the output you expected. A seed that
reproduces the problem is worth more than a long description.
