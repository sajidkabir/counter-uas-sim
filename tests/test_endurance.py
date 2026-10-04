"""Interceptor endurance: energy budgets end long chases."""

import pytest

from counter_uas_sim import (
    ConstantVelocityTarget,
    InterceptorSpec,
    default_scenario,
    run_engagement,
    run_intercept,
    run_monte_carlo,
)


def _far_stationary_target():
    # 5 km out, motionless: about 90 s of guided flight to reach,
    # well past the 60 s default endurance.
    return ConstantVelocityTarget((5000.0, 0.0), (0.0, 0.0))


def test_energy_exhaustion_ends_a_long_chase():
    result = run_intercept(_far_stationary_target(), (0.0, 0.0), 0.0,
                           InterceptorSpec(), guidance="pn")
    assert not result.intercepted
    assert result.outcome == "energy_exhausted"
    assert result.flight_time_s == pytest.approx(
        InterceptorSpec().endurance_s, abs=0.05)


def test_unlimited_endurance_recovers_the_old_behavior():
    spec = InterceptorSpec(endurance_s=float("inf"))
    result = run_intercept(_far_stationary_target(), (0.0, 0.0), 0.0,
                           spec, guidance="pn")
    assert result.intercepted
    assert result.miss_distance_m <= spec.capture_radius_m


def test_endurance_can_only_reduce_intercepts_never_add_them():
    # An energy budget ends attempts that would have continued, so for
    # identical seeds a shorter budget cannot produce more intercepts.
    for law in ("pn", "pure_pursuit"):
        short = run_monte_carlo(runs=200, seed=42, guidance=law,
                                endurance_s=60.0)
        long = run_monte_carlo(runs=200, seed=42, guidance=law,
                               endurance_s=float("inf"))
        assert short.intercepts <= long.intercepts
        assert short.launches == long.launches


def test_endurance_prices_the_long_pursuit_chases():
    # The headline v1.1 effect: with unlimited endurance pure pursuit
    # wins by spiraling after maneuvering targets for over a minute;
    # a 60 s budget ends those chases.
    unlimited = run_monte_carlo(runs=200, seed=42, guidance="pure_pursuit",
                                endurance_s=float("inf"))
    budgeted = run_monte_carlo(runs=200, seed=42, guidance="pure_pursuit",
                               endurance_s=60.0)
    assert unlimited.intercepts > budgeted.intercepts


def test_pn_leads_the_guidance_comparison_with_a_budget():
    # At the reference seed with a 60 s budget, PN's fast collision
    # courses beat pursuit's long chases. Numbers are seed-42
    # specific; the mechanism is pinned by the tests above.
    pn = run_monte_carlo(runs=200, seed=42, guidance="pn",
                         endurance_s=60.0)
    pursuit = run_monte_carlo(runs=200, seed=42, guidance="pure_pursuit",
                              endurance_s=60.0)
    assert pn.intercepts >= pursuit.intercepts


def test_energy_exhaustion_surfaces_in_the_engagement_log():
    scenario = default_scenario()
    scenario.interceptor.endurance_s = 1.0
    result = run_engagement(scenario)
    assert result.outcome == "intercept_failed"
    assert not result.intercepted
    assert any("ENERGY EXHAUSTED" in line for line in result.event_log)


def test_monte_carlo_stays_reproducible_with_endurance():
    first = run_monte_carlo(runs=40, seed=123, endurance_s=60.0)
    second = run_monte_carlo(runs=40, seed=123, endurance_s=60.0)
    assert first == second
