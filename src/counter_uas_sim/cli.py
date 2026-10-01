"""Command-line interface: ``counter-uas run`` and ``counter-uas montecarlo``."""

from __future__ import annotations

import argparse

from .engagement import default_scenario, run_engagement
from .montecarlo import run_monte_carlo


def _cmd_run(args) -> int:
    scenario = default_scenario()
    scenario.guidance = args.guidance
    scenario.seed = args.seed
    result = run_engagement(scenario)

    print("Counter-UAS engagement simulation")
    print(f"  Guidance:        {args.guidance}")
    print()
    for line in result.event_log:
        print(f"  {line}")
    print()
    print(f"  Outcome:         {result.outcome}")
    if result.miss_distance_m is not None:
        print(f"  Miss distance:   {result.miss_distance_m:.1f} m")
    if result.intercept_time_s is not None:
        print(f"  Intercept time:  {result.intercept_time_s:.1f} s")
    return 0


def _cmd_montecarlo(args) -> int:
    result = run_monte_carlo(runs=args.runs, seed=args.seed,
                              guidance=args.guidance)

    print("Counter-UAS Monte Carlo summary")
    print(f"  Runs:                    {result.runs}")
    print(f"  Guidance:                {args.guidance}")
    print(f"  Seed:                    {args.seed}")
    print(f"  Launches:                {result.launches}")
    print(f"  Intercepts:              {result.intercepts}")
    print(f"  Intercept probability:   {result.intercept_probability:.3f}")
    print(f"  Mean miss distance:      {result.mean_miss_distance_m:.1f} m")
    print()
    print("  Cost per successful intercept (reported estimates):")
    print(f"    Low-cost interceptor (USD {result.low_cost_unit_usd:,.0f} per unit):"
          f"  USD {result.low_cost_per_success_usd:,.0f}")
    print(f"    Missile-defence interceptor (about USD {result.missile_unit_usd:,.0f} per missile):"
          f"  USD {result.missile_per_success_usd:,.0f}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="counter-uas",
        description="Counter-UAS defence simulation for research and education.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="Run one demo engagement")
    run_parser.add_argument("--guidance", choices=["pn", "pure_pursuit"],
                            default="pn")
    run_parser.add_argument("--seed", type=int, default=7)
    run_parser.set_defaults(func=_cmd_run)

    mc_parser = sub.add_parser("montecarlo",
                               help="Run a seeded Monte Carlo analysis")
    mc_parser.add_argument("--runs", type=int, default=200)
    mc_parser.add_argument("--seed", type=int, default=42)
    mc_parser.add_argument("--guidance", choices=["pn", "pure_pursuit"],
                           default="pn")
    mc_parser.set_defaults(func=_cmd_montecarlo)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
