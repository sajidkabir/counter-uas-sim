"""Example: Monte Carlo comparison of PN and pure pursuit, with costs."""

from counter_uas_sim import run_monte_carlo

for law in ("pn", "pure_pursuit"):
    result = run_monte_carlo(runs=200, seed=42, guidance=law)
    print(f"Guidance: {law}")
    print(f"  Intercept probability: {result.intercept_probability:.3f}")
    print(f"  Mean miss distance:    {result.mean_miss_distance_m:.1f} m")
    print(f"  Cost per successful intercept, low-cost concept: "
          f"USD {result.low_cost_per_success_usd:,.0f}")
    print(f"  Cost per successful intercept, missile estimate: "
          f"USD {result.missile_per_success_usd:,.0f}")
