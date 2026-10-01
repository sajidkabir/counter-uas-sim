"""Monte Carlo: seeded runs must be exactly reproducible."""

from counter_uas_sim.montecarlo import run_monte_carlo


def test_monte_carlo_is_reproducible_with_a_fixed_seed():
    first = run_monte_carlo(runs=40, seed=123)
    second = run_monte_carlo(runs=40, seed=123)
    assert first == second


def test_monte_carlo_statistics_are_sane():
    result = run_monte_carlo(runs=40, seed=123)
    assert 0.0 <= result.intercept_probability <= 1.0
    assert result.intercepts > 0
    assert result.launches >= result.intercepts
    # Cost per success can never be below the unit cost itself.
    assert result.low_cost_per_success_usd >= result.low_cost_unit_usd
    # The missile estimate is two orders of magnitude above the concept.
    assert result.missile_per_success_usd > 50.0 * result.low_cost_per_success_usd
