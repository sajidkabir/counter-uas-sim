"""Threat scoring: direct and fast beats slow and tangential."""

import numpy as np

from counter_uas_sim.assessment import assess_track, time_to_perimeter


def test_time_to_perimeter_head_on():
    # 3,000 m out, closing at 45 m/s, perimeter at 500 m: (3000-500)/45.
    ttp = time_to_perimeter((3000.0, 0.0), (-45.0, 0.0), 500.0)
    assert abs(ttp - 2500.0 / 45.0) < 1e-9


def test_time_to_perimeter_never_crosses():
    # Flying tangentially past the circle, and flying away from it.
    assert np.isinf(time_to_perimeter((3000.0, 0.0), (0.0, 45.0), 500.0))
    assert np.isinf(time_to_perimeter((3000.0, 0.0), (45.0, 0.0), 500.0))
    # Already inside counts as zero.
    assert time_to_perimeter((100.0, 0.0), (0.0, 0.0), 500.0) == 0.0


def test_fast_direct_intruder_outranks_slow_tangential():
    fast_direct = assess_track((3000.0, 0.0), (-45.0, 0.0),
                               track_std_m=10.0, perimeter_radius_m=500.0)
    slow_tangential = assess_track((2000.0, 0.0), (0.0, 10.0),
                                   track_std_m=10.0, perimeter_radius_m=500.0)
    assert fast_direct.score > slow_tangential.score
    assert fast_direct.recommend_engagement
    assert not slow_tangential.recommend_engagement


def test_high_score_on_a_bad_track_is_not_enough():
    # Same geometry as the fast direct intruder, but the track is too
    # uncertain to shoot on: recommendation must switch off.
    assessment = assess_track((3000.0, 0.0), (-45.0, 0.0),
                              track_std_m=200.0, perimeter_radius_m=500.0)
    assert assessment.score >= 0.60
    assert not assessment.recommend_engagement
